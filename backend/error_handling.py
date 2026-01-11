"""
Improved Error Handling Module
Provides standardized error responses, user-friendly messages, and proper HTTP status codes
"""

from enum import Enum
from typing import Optional, Dict, Any
from datetime import datetime
import uuid
import logging

from fastapi import status
from fastapi.responses import JSONResponse


class ErrorCode(Enum):
    """Standard error codes for consistent error handling"""
    
    # Client Errors (4xx)
    VALIDATION_ERROR = "VALIDATION_ERROR"
    MISSING_FIELD = "MISSING_FIELD"
    INVALID_FORMAT = "INVALID_FORMAT"
    MODEL_NOT_FOUND = "MODEL_NOT_FOUND"
    UNAUTHORIZED = "UNAUTHORIZED"
    
    # Server Errors (5xx)
    DATABASE_ERROR = "DATABASE_ERROR"
    DATABASE_TIMEOUT = "DATABASE_TIMEOUT"
    LLM_ERROR = "LLM_ERROR"
    LLM_TIMEOUT = "LLM_TIMEOUT"
    INTERNAL_ERROR = "INTERNAL_ERROR"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"


# User-friendly error messages  
ERROR_MESSAGES = {
    ErrorCode.VALIDATION_ERROR: "The information you provided is invalid. Please check and try again.",
    ErrorCode.MISSING_FIELD: "Required information is missing. Please provide all required fields.",
    ErrorCode.INVALID_FORMAT: "The format of your request is incorrect. Please check your input.",
    ErrorCode.MODEL_NOT_FOUND: "The infrastructure model you're looking for doesn't exist.",
    ErrorCode.UNAUTHORIZED: "You don't have permission to access this resource.",
    
    ErrorCode.DATABASE_ERROR: "We're having trouble saving your data. Please try again in a moment.",
    ErrorCode.DATABASE_TIMEOUT: "The database is taking longer than expected. Please try again.",
    ErrorCode.LLM_ERROR: "We couldn't process your infrastructure description. Please try rephrasing it.",
    ErrorCode.LLM_TIMEOUT: "Processing is taking longer than expected. Please try again with a simpler request.",
    ErrorCode.INTERNAL_ERROR: "Something unexpected happened. We're looking into it.",
    ErrorCode.SERVICE_UNAVAILABLE: "The service is temporarily unavailable. Please try again later.",
}


# HTTP status code mapping
ERROR_STATUS_CODES = {
    ErrorCode.VALIDATION_ERROR: status.HTTP_400_BAD_REQUEST,
    ErrorCode.MISSING_FIELD: status.HTTP_400_BAD_REQUEST,
    ErrorCode.INVALID_FORMAT: status.HTTP_400_BAD_REQUEST,
    ErrorCode.MODEL_NOT_FOUND: status.HTTP_404_NOT_FOUND,
    ErrorCode.UNAUTHORIZED: status.HTTP_401_UNAUTHORIZED,
    
    ErrorCode.DATABASE_ERROR: status.HTTP_500_INTERNAL_SERVER_ERROR,
    ErrorCode.DATABASE_TIMEOUT: status.HTTP_504_GATEWAY_TIMEOUT,
    ErrorCode.LLM_ERROR: status.HTTP_500_INTERNAL_SERVER_ERROR,
    ErrorCode.LLM_TIMEOUT: status.HTTP_504_GATEWAY_TIMEOUT,
    ErrorCode.INTERNAL_ERROR: status.HTTP_500_INTERNAL_SERVER_ERROR,
    ErrorCode.SERVICE_UNAVAILABLE: status.HTTP_503_SERVICE_UNAVAILABLE,
}


logger = logging.getLogger(__name__)


def create_error_response(
    error_code: ErrorCode,
    detail: Optional[str] = None,
    technical_detail: Optional[str] = None,
    include_debug: bool = False
) -> JSONResponse:
    """
    Create a standardized error response.
    
    Args:
        error_code: Standard error code enum
        detail: Optional custom user message (overrides default)
        technical_detail: Technical error details (logged, not shown to user)
        include_debug: Whether to include debug info (from DEBUG env var)
        
    Returns:
        JSONResponse with standardized error structure
        
    Example:
        return create_error_response(
            ErrorCode.DATABASE_ERROR,
            technical_detail=str(e)
        )
    """
    request_id = str(uuid.uuid4())
    
    # User-friendly message
    user_message = detail or ERROR_MESSAGES.get(error_code, "An error occurred")
    
    # HTTP status code
    status_code = ERROR_STATUS_CODES.get(error_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    # Log detailed error for developers
    logger.error(
        f"Error Response: {error_code.value}",
        extra={
            "request_id": request_id,
            "error_code": error_code.value,
            "user_message": user_message,
            "technical_detail": technical_detail,
            "status_code": status_code
        }
    )
    
    # Build response
    response_data = {
        "success": False,
        "error": {
            "code": error_code.value,
            "message": user_message,
            "request_id": request_id,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    }
    
    # Include debug info only if explicitly enabled
    if include_debug and technical_detail:
        response_data["error"]["debug"] = {
            "detail": technical_detail
        }
    
    return JSONResponse(
        status_code=status_code,
        content=response_data
    )


def create_success_response(data: Dict[str, Any], message: Optional[str] = None) -> Dict[str, Any]:
    """
    Create a standardized success response.
    
    Args:
        data: Response data
        message: Optional success message
        
    Returns:
        Dictionary with standardized success structure
    """
    response = {
        "success": True,
        **data
    }
    
    if message:
        response["message"] = message
    
    return response


# Exception mapping helpers
def map_exception_to_error_code(exc: Exception) -> ErrorCode:
    """
    Map Python exceptions to error codes.
    
    Args:
        exc: The exception that occurred
        
    Returns:
        Appropriate ErrorCode enum value
    """
    exc_name = type(exc).__name__
    exc_str = str(exc).lower()
    
    # SQLAlchemy / Database errors
    if "sqlalchemy" in exc_name.lower() or "psycopg2" in exc_name.lower():
        if "timeout" in exc_str:
            return ErrorCode.DATABASE_TIMEOUT
        return ErrorCode.DATABASE_ERROR
    
    # Timeout errors
    if "timeout" in exc_name.lower():
        if "llm" in exc_str or "gemini" in exc_str:
            return ErrorCode.LLM_TIMEOUT
        return ErrorCode.DATABASE_TIMEOUT
    
    # Validation errors
    if "validation" in exc_name.lower():
        return ErrorCode.VALIDATION_ERROR
    
    # Not found errors
    if "notfound" in exc_name.lower() or "does not exist" in exc_str:
        return ErrorCode.MODEL_NOT_FOUND
    
    # Default to internal error
    return ErrorCode.INTERNAL_ERROR


# Example usage in endpoints:
"""
from backend.error_handling import create_error_response, create_success_response, ErrorCode

@app.post("/text")
def generate_infrastructure(request: TextRequest, db: Session = Depends(get_db)):
    try:
        # ... processing ...
        return create_success_response(
            data={"model_id": model.model_id, "diagram": diagram},
            message="Infrastructure generated successfully"
        )
    except SQLAlchemyError as e:
        return create_error_response(
            ErrorCode.DATABASE_ERROR,
            technical_detail=str(e)
        )
    except ValueError as e:
        return create_error_response(
            ErrorCode.VALIDATION_ERROR,
            detail="Invalid infrastructure description",
            technical_detail=str(e)
        )
"""
