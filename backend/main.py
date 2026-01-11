"""
FastAPI Main Application
Orchestrates the model-centric infrastructure generation pipeline.

Flow: Text → Parser → Model → [Diagram, Terraform, Security]
The model is the single source of truth.
"""

import os
from datetime import datetime
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Any
from sqlalchemy.orm import Session

from .parser import parse_text_to_model
from .diagram import generate_mermaid_diagram, generate_diagram_description
from .terraform import generate_terraform_code
from .security import validate_security, generate_security_report
from .validator import validate_and_fix
from .model import EditSource
from .edits import add_resource, remove_resource, move_resource, update_resource_property
from .terraform_parser import parse_terraform_edits
from .websocket_manager import manager
from .database import get_db, init_db, test_connection
from .repository import InfrastructureRepository


# Initialize FastAPI app
app = FastAPI(
    title="AI-Driven Infrastructure Generator",
    description="Generate infrastructure diagrams and IaC from natural language",
    version="1.0.0"
)

# Request ID Middleware - Track all requests with unique IDs
import uuid
from starlette.middleware.base import BaseHTTPMiddleware

class RequestIDMiddleware(BaseHTTPMiddleware):
    """Add unique request ID to each request for tracing and debugging"""
    async def dispatch(self, request, call_next):
        # Generate or use existing request ID
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request.state.request_id = request_id
        
        # Process request
        response = await call_next(request)
        
        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id
        return response

app.add_middleware(RequestIDMiddleware)

# Get frontend URL from environment or use wildcard
FRONTEND_URL = os.getenv("FRONTEND_URL", "")

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8080",      # Local development (Vite)
        "http://localhost:5173",      # Local development (Vite default)
    ] + ([FRONTEND_URL] if FRONTEND_URL else []),
    allow_origin_regex=r"https://.*\.vercel\.app",  # All Vercel deployments (production & preview)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



# Global Exception Handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc: Exception):
    """
    Catch-all exception handler for production safety.
    Returns proper HTTP status codes and user-friendly error messages.
    """
    import logging
    from backend.error_handling import map_exception_to_error_code, create_error_response
    
    logger = logging.getLogger(__name__)
    
    # Log the full error with traceback and request context
    logger.error(
        f"Unhandled exception: {exc}",
        extra={
            "method": request.method,
            "url": str(request.url),
            "error_type": type(exc).__name__
        },
        exc_info=True
    )
    
    # Map exception to error code and return standardized response
    error_code = map_exception_to_error_code(exc)
    
    return create_error_response(
        error_code=error_code,
        technical_detail=str(exc),
        include_debug=os.getenv("DEBUG", "false").lower() == "true"
    )


# Application startup: Initialize database
@app.on_event("startup")
async def startup_event():
    """Initialize database on application startup"""
    print("🚀 Starting AI-Driven Infrastructure Generator...")
    test_connection()
    init_db()
    print("✅ Application ready!")


# Request/Response Models
class TextRequest(BaseModel):
    """Request body for /text endpoint"""
    text: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "text": "Create a VPC with public and private subnets. Deploy an EC2 instance in the public subnet and a PostgreSQL RDS database in the private subnet. Add a load balancer."
            }
        }


class InfrastructureResponse(BaseModel):
    """Response from /text endpoint"""
    success: bool
    description: str
    mermaid_diagram: str
    terraform_code: str
    security_warnings: List[Dict[str, str]]
    security_report: str
    model_summary: Dict[str, Any]
    model_id: str
    corrections: List[str] = []  # Architecture auto-corrections applied


class DiagramEditRequest(BaseModel):
    """Request for diagram edit operations"""
    current_model_id: str  # For conflict detection
    operation: str  # add_resource, remove_resource, move_resource, update_resource_property
    resource_type: str = None  # For add_resource
    resource_id: str = None  # For remove/move/update
    properties: Dict[str, Any] = {}  # Operation-specific data
    target_subnet_id: str = None  # For move_resource
    property_name: str = None  # For update_resource_property
    value: Any = None  # For update_resource_property


class TerraformEditRequest(BaseModel):
    """Request for Terraform code edits"""
    current_model_id: str
    original_terraform: str
    modified_terraform: str


# API Endpoints
@app.get("/")
def read_root():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "AI-Driven Infrastructure Generator",
        "version": "1.0.0",
        "endpoints": {
            "POST /text": "Generate infrastructure from text description",
            "POST /edit/diagram": "Edit infrastructure via diagram events",
            "POST /edit/terraform": "Edit infrastructure via Terraform code",
            "GET /health": "Health check"
        }
    }


@app.get("/health")
def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "components": {
            "parser": "operational",
            "diagram_generator": "operational",
            "terraform_generator": "operational",
            "security_validator": "operational",
            "edit_operations": "operational",
            "terraform_parser": "operational"
        }
    }


@app.post("/text", response_model=InfrastructureResponse)
def generate_infrastructure(request: TextRequest, db: Session = Depends(get_db)):
    """
    Main endpoint: Generate infrastructure from text description.
    
    Pipeline:
    1. Text → Parser → Infrastructure Model
    2. Model → Diagram Generator → Mermaid
    3. Model → Terraform Generator → IaC Code
    4. Model → Security Validator → Warnings
    
    The model is the single source of truth - all outputs derive from it.
    """
    try:
        # Step 1: Parse text into infrastructure model
        # This is where AI/LLM is used (mock for now)
        model = parse_text_to_model(request.text)
        
        # Step 2: VALIDATE AND AUTO-FIX (Architecture Compiler)
        model, validation_result = validate_and_fix(model)
        
        # Step 3: Generate Mermaid diagram from validated model
        mermaid_diagram = generate_mermaid_diagram(model)
        diagram_desc = generate_diagram_description(model)
        
        # Step 4: Generate Terraform code from validated model
        terraform_code = generate_terraform_code(model)
        
        # Step 5: Validate security at model level
        security_warnings = validate_security(model)
        security_report = generate_security_report(security_warnings)
        
        # Store model in database
        repository = InfrastructureRepository(db)
        repository.save_model(model)
        
        # Step 6: Return combined response with corrections
        return InfrastructureResponse(
            success=True,
            description=diagram_desc,
            mermaid_diagram=mermaid_diagram,
            terraform_code=terraform_code,
            security_warnings=[w.to_dict() for w in security_warnings],
            security_report=security_report,
            model_summary=model.to_dict(),
            model_id=model.model_id,
            corrections=validation_result.corrections  # Architecture auto-corrections
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating infrastructure: {str(e)}"
        )


@app.post("/validate")
def validate_infrastructure(request: TextRequest, db: Session = Depends(get_db)):
    """
    Validation-only endpoint: Parse text and return security warnings.
    Useful for checking infrastructure before generation.
    """
    try:
        # Parse text into model
        model = parse_text_to_model(request.text)
        
        # Validate security
        security_warnings = validate_security(model)
        security_report = generate_security_report(security_warnings)
        
        return {
            "success": True,
            "warnings_count": len(security_warnings),
            "security_warnings": [w.to_dict() for w in security_warnings],
            "security_report": security_report,
            "model_summary": model.to_dict()
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error validating infrastructure: {str(e)}"
        )


@app.post("/edit/diagram")
def edit_via_diagram(request: DiagramEditRequest, db: Session = Depends(get_db)):
    """
    Edit infrastructure via diagram events
    
    Flow: Diagram Edit → Model Update → Security Check → Regenerate Terraform
    
    Loop Prevention: Tracks EditSource.DIAGRAM
    """
    try:
        # Get current model from database
        repository = InfrastructureRepository(db)
        current_model = repository.get_model(request.current_model_id)
        if not current_model:
            raise HTTPException(404, f"Model {request.current_model_id} not found")
        
        # Execute edit operation
        result = None
        if request.operation == "add_resource":
            result = add_resource(current_model, request.resource_type, request.properties, EditSource.DIAGRAM)
        elif request.operation == "remove_resource":
            result = remove_resource(current_model, request.resource_id, EditSource.DIAGRAM)
        elif request.operation == "move_resource":
            result = move_resource(current_model, request.resource_id, request.target_subnet_id, EditSource.DIAGRAM)
        elif request.operation == "update_resource_property":
            result = update_resource_property(current_model, request.resource_id, request.property_name, request.value, EditSource.DIAGRAM)
        else:
            raise HTTPException(400, f"Unknown operation: {request.operation}")
        
        if not result.success:
            return {"success": False, "error": result.error, "warnings": [w.to_dict() for w in result.warnings] if result.warnings else []}
        
        # Store updated model in database
        updated_model = result.model
        repository.save_model(updated_model)
        
        # Regenerate both diagram and Terraform for frontend display
        mermaid_diagram = generate_mermaid_diagram(updated_model)
        terraform_code = generate_terraform_code(updated_model)
        security_report = generate_security_report(result.warnings)
        
        return {
            "success": True,
            "model_id": updated_model.model_id,
            "model_summary": updated_model.to_dict(),  # CRITICAL: Frontend needs this for React Flow
            "mermaid_diagram": mermaid_diagram,
            "terraform_code": terraform_code,
            "security_warnings": [w.to_dict() for w in result.warnings],
            "security_report": security_report,
            "message": f"Applied {request.operation} successfully"
        }
    except Exception as e:
        raise HTTPException(500, f"Edit failed: {str(e)}")


@app.post("/edit/terraform")
def edit_via_terraform(request: TerraformEditRequest, db: Session = Depends(get_db)):
    """
    Edit infrastructure via Terraform code modifications
    
    Flow: Terraform Edit → Parse → Model Update → Security → Regenerate Diagram
    
    Loop Prevention: Tracks EditSource.TERRAFORM
    """
    try:
        repository = InfrastructureRepository(db)
        current_model = repository.get_model(request.current_model_id)
        if not current_model:
            raise HTTPException(404, f"Model {request.current_model_id} not found")
        
        # Parse Terraform changes
        edit_operations = parse_terraform_edits(request.original_terraform, request.modified_terraform)
        
        if not edit_operations:
            return {"success": True, "message": "No changes detected", "model_id": current_model.model_id}
        
        # Apply operations
        working_model = current_model
        all_warnings = []
        
        for op in edit_operations:
            if op['operation'] == 'update_resource_property':
                result = update_resource_property(working_model, op['resource_id'], op['property'], op['value'], EditSource.TERRAFORM)
            elif op['operation'] == 'move_resource':
                result = move_resource(working_model, op['resource_id'], op['target_subnet_id'], EditSource.TERRAFORM)
            elif op['operation'] == 'remove_resource':
                result = remove_resource(working_model, op['resource_id'], EditSource.TERRAFORM)
            else:
                continue
            
            if not result.success:
                return {"success": False, "error": f"Failed: {result.error}", "warnings": [w.to_dict() for w in result.warnings] if result.warnings else []}
            
            working_model = result.model
            all_warnings.extend(result.warnings)
        
        # Store updated model in database
        repository.save_model(working_model)
        
        # Regenerate both diagram AND Terraform (so code doesn't disappear)
        mermaid_diagram = generate_mermaid_diagram(working_model)
        terraform_code = generate_terraform_code(working_model)  # CRITICAL FIX: Regenerate Terraform
        diagram_desc = generate_diagram_description(working_model)
        security_report = generate_security_report(all_warnings)
        
        return {
            "success": True,
            "model_id": working_model.model_id,
            "mermaid_diagram": mermaid_diagram,
            "terraform_code": terraform_code,  # CRITICAL FIX: Include in response
            "description": diagram_desc,
            "security_warnings": [w.to_dict() for w in all_warnings],
            "security_report": security_report,
            "operations_applied": len(edit_operations),
            "message": f"Applied {len(edit_operations)} operation(s)"
        }
    except Exception as e:
        raise HTTPException(500, f"Terraform edit failed: {str(e)}")


# WebSocket Endpoint for Real-Time Collaboration
# Note: WebSocket doesn't use Depends() the same way, we'll create db sessions inline
@app.websocket("/ws/{model_id}")
async def websocket_endpoint(websocket: WebSocket, model_id: str):
    """
    WebSocket endpoint for real-time collaboration
    
    Query parameters:
    - user_id: Optional user identifier
    
    Message types:
    - edit_event: Infrastructure edit (add/remove/move resource)
    - cursor_update: Cursor position in diagram/code
    - position_update: Node position in interactive diagram
    - sync_request: Request full model state
    """
    # Get user_id from query parameters
    user_id = websocket.query_params.get('user_id')
    
    # Connect user
    connection_info = await manager.connect(websocket, model_id, user_id)
    
    try:
        # Send initial connection confirmation
        active_users_list = await manager.get_active_users(model_id)
        await manager.send_personal_message({
            "type": "connected",
            "model_id": model_id,
            "user_id": connection_info["user_id"],
            "active_users": active_users_list,
            "timestamp": datetime.utcnow().isoformat()
        }, websocket)
        
        # Load current model from database and send initial state
        from backend.database import SessionLocal
        db = SessionLocal()
        try:
            repository = InfrastructureRepository(db)
            current_model = repository.get_model(model_id)
        finally:
            db.close()
        
        if current_model:
            mermaid_diagram = generate_mermaid_diagram(current_model)
            terraform_code = generate_terraform_code(current_model)
            
            await manager.send_personal_message({
                "type": "initial_state",
                "model_id": model_id,
                "mermaid_diagram": mermaid_diagram,
                "terraform_code": terraform_code,
                "model_summary": current_model.to_dict()
            }, websocket)
        
        # Handle incoming messages
        while True:
            data = await websocket.receive_json()
            message_type = data.get("type")
            
            if message_type == "edit_event":
                # Handle edit event and broadcast to others
                await manager.handle_edit_event(websocket, data.get("event", {}))
                
            elif message_type == "cursor_update":
                # Broadcast cursor position
                await manager.handle_cursor_position(websocket, data.get("position", {}))
                
            elif message_type == "position_update":
                # Handle node position update in interactive diagram
                await manager.broadcast_to_model(model_id, {
                    "type": "position_update",
                    "user_id": connection_info["user_id"],
                    "resource_id": data.get("resource_id"),
                    "position": data.get("position"),
                    "timestamp": datetime.utcnow().isoformat()
                }, exclude=[websocket])
                
            elif message_type == "sync_request":
                # Send full model state from database
                db = SessionLocal()
                try:
                    repository = InfrastructureRepository(db)
                    current_model = repository.get_model(model_id)
                finally:
                    db.close()
                
                if current_model:
                    mermaid_diagram = generate_mermaid_diagram(current_model)
                    terraform_code = generate_terraform_code(current_model)
                    
                    await manager.send_personal_message({
                        "type": "sync_response",
                        "model_id": model_id,
                        "mermaid_diagram": mermaid_diagram,
                        "terraform_code": terraform_code,
                        "model_summary": current_model.to_dict()
                    }, websocket)
                
    except WebSocketDisconnect:
        await manager.disconnect(websocket)
    except Exception as e:
        print(f"WebSocket error: {e}")
        await manager.disconnect(websocket)


# Run with: uvicorn backend.main:app --reload
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

