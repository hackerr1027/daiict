"""
FastAPI Main Application
Orchestrates the model-centric infrastructure generation pipeline.

Flow: Text → Parser → Model → [Diagram, Terraform, Security]
The model is the single source of truth.
"""

import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Any

from .parser import parse_text_to_model
from .diagram import generate_mermaid_diagram, generate_diagram_description
from .terraform import generate_terraform_code
from .security import validate_security, generate_security_report
from .model import EditSource
from .edits import add_resource, remove_resource, move_resource, update_resource_property
from .terraform_parser import parse_terraform_edits


# Initialize FastAPI app
app = FastAPI(
    title="AI-Driven Infrastructure Generator",
    description="Generate infrastructure diagrams and IaC from natural language",
    version="1.0.0"
)

# Get frontend URL from environment or use wildcard
FRONTEND_URL = os.getenv("FRONTEND_URL", "https://*.vercel.app")

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8080",      # Local development (Vite)
        "http://localhost:5173",      # Local development (Vite default)
        FRONTEND_URL,                 # Production frontend (configurable)
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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
def generate_infrastructure(request: TextRequest):
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
        
        # Step 2: Generate Mermaid diagram from model
        mermaid_diagram = generate_mermaid_diagram(model)
        diagram_desc = generate_diagram_description(model)
        
        # Step 3: Generate Terraform code from model
        terraform_code = generate_terraform_code(model)
        
        # Step 4: Validate security at model level
        security_warnings = validate_security(model)
        security_report = generate_security_report(security_warnings)
        
        # Store model for edit operations
        MODEL_STORE[model.model_id] = model
        
        # Step 5: Return combined response
        return InfrastructureResponse(
            success=True,
            description=diagram_desc,
            mermaid_diagram=mermaid_diagram,
            terraform_code=terraform_code,
            security_warnings=[w.to_dict() for w in security_warnings],
            security_report=security_report,
            model_summary=model.to_dict(),
            model_id=model.model_id  # ADD THIS - include model_id in response
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating infrastructure: {str(e)}"
        )


@app.post("/validate")
def validate_infrastructure(request: TextRequest):
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


# Global model store (in production, use a database)
MODEL_STORE = {}


@app.post("/edit/diagram")
def edit_via_diagram(request: DiagramEditRequest):
    """
    Edit infrastructure via diagram events
    
    Flow: Diagram Edit → Model Update → Security Check → Regenerate Terraform
    
    Loop Prevention: Tracks EditSource.DIAGRAM
    """
    try:
        # Get current model from store
        current_model = MODEL_STORE.get(request.current_model_id)
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
        
        # Store updated model
        updated_model = result.model
        MODEL_STORE[updated_model.model_id] = updated_model
        
        # Regenerate both diagram and Terraform for frontend display
        mermaid_diagram = generate_mermaid_diagram(updated_model)
        terraform_code = generate_terraform_code(updated_model)
        security_report = generate_security_report(result.warnings)
        
        return {
            "success": True,
            "model_id": updated_model.model_id,
            "mermaid_diagram": mermaid_diagram,
            "terraform_code": terraform_code,
            "security_warnings": [w.to_dict() for w in result.warnings],
            "security_report": security_report,
            "message": f"Applied {request.operation} successfully"
        }
    except Exception as e:
        raise HTTPException(500, f"Edit failed: {str(e)}")


@app.post("/edit/terraform")
def edit_via_terraform(request: TerraformEditRequest):
    """
    Edit infrastructure via Terraform code modifications
    
    Flow: Terraform Edit → Parse → Model Update → Security → Regenerate Diagram
    
    Loop Prevention: Tracks EditSource.TERRAFORM
    """
    try:
        current_model = MODEL_STORE.get(request.current_model_id)
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
        
        # Store updated model
        MODEL_STORE[working_model.model_id] = working_model
        
        # Regenerate diagram only (Terraform edit source)
        mermaid_diagram = generate_mermaid_diagram(working_model)
        diagram_desc = generate_diagram_description(working_model)
        security_report = generate_security_report(all_warnings)
        
        return {
            "success": True,
            "model_id": working_model.model_id,
            "mermaid_diagram": mermaid_diagram,
            "description": diagram_desc,
            "security_warnings": [w.to_dict() for w in all_warnings],
            "security_report": security_report,
            "operations_applied": len(edit_operations),
            "message": f"Applied {len(edit_operations)} operation(s)"
        }
    except Exception as e:
        raise HTTPException(500, f"Terraform edit failed: {str(e)}")


# Run with: uvicorn backend.main:app --reload
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
