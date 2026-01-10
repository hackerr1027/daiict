"""
Text-to-Model Parser
Converts natural language infrastructure descriptions into structured InfrastructureModel.
Now supports Google Gemini API with fallback to mock LLM.
"""

import json
import re
import os
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import Google Gemini (optional - graceful fallback if not available)
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
    
    # Configure Gemini if API key is present
    api_key = os.getenv("GOOGLE_API_KEY")
    if api_key:
        genai.configure(api_key=api_key)
        GEMINI_CONFIGURED = True
    else:
        GEMINI_CONFIGURED = False
except ImportError:
    GEMINI_AVAILABLE = False
    GEMINI_CONFIGURED = False

from .model import (
    InfrastructureModel, VPC, Subnet, EC2Instance, RDSDatabase, LoadBalancer,
    SubnetType, InstanceType, DatabaseEngine
)


def gemini_extract(text: str) -> Optional[Dict[str, Any]]:
    """
    Use Google Gemini API to extract structured infrastructure intent from text.
    Returns None if Gemini is not available or fails.
    """
    if not GEMINI_AVAILABLE or not GEMINI_CONFIGURED:
        return None
    
    try:
        # Initialize Gemini model (using gemini-pro for text)
        model = genai.GenerativeModel('gemini-pro')
        
        # Craft a detailed prompt for infrastructure extraction
        prompt = f"""You are an expert AWS infrastructure architect. Extract infrastructure requirements from the following text and return ONLY a valid JSON object with this exact structure:

{{
  "vpcs": [
    {{
      "id": "vpc-main",
      "name": "main-vpc",
      "cidr": "10.0.0.0/16",
      "subnets": [
        {{
          "id": "subnet-public-1",
          "name": "public-subnet-1",
          "cidr": "10.0.1.0/24",
          "type": "public",
          "az": "us-east-1a"
        }}
      ]
    }}
  ],
  "ec2_instances": [
    {{
      "id": "ec2-web-1",
      "name": "web-server-1",
      "instance_type": "t2.micro",
      "subnet_id": "subnet-public-1"
    }}
  ],
  "rds_databases": [
    {{
      "id": "rds-main",
      "name": "main-database",
      "engine": "postgres",
      "instance_class": "db.t3.micro",
      "subnet_ids": ["subnet-private-1", "subnet-private-2"],
      "allocated_storage": 20
    }}
  ],
  "load_balancers": [
    {{
      "id": "lb-main",
      "name": "main-load-balancer",
      "subnet_ids": ["subnet-public-1"],
      "target_instance_ids": ["ec2-web-1"]
    }}
  ]
}}

Rules:
1. Always create at least one VPC if infrastructure is mentioned
2. Public subnets for internet-facing resources (EC2 web servers, load balancers)
3. Private subnets for databases (RDS requires at least 2 subnets in different AZs)
4. Use appropriate instance types (t2.micro, t2.small, t3.micro, etc.)
5. Database engines: postgres, mysql, or mariadb
6. Subnet types: "public" or "private"
7. Return ONLY the JSON, no markdown, no explanations

User request: {text}

JSON output:"""

        # Generate response
        response = model.generate_content(prompt)
        
        # Extract JSON from response
        response_text = response.text.strip()
        
        # Remove markdown code blocks if present
        if response_text.startswith('```'):
            response_text = re.sub(r'^```(?:json)?\n', '', response_text)
            response_text = re.sub(r'\n```$', '', response_text)
        
        # Parse JSON
        intent = json.loads(response_text)
        
        print(f"✅ Gemini API successfully parsed infrastructure request")
        return intent
        
    except Exception as e:
        print(f"⚠️ Gemini API failed: {str(e)}, falling back to mock LLM")
        return None


def mock_llm_extract(text: str) -> Dict[str, Any]:
    """
    Mock LLM that extracts structured intent from text.
    In production, this would call OpenAI/Anthropic/etc. to get JSON.
    
    For now, we use simple keyword matching to demonstrate the concept.
    The LLM's job is ONLY to extract intent, not generate Terraform/diagrams.
    """
    text_lower = text.lower()
    
    # Default structure
    intent = {
        "vpcs": [],
        "ec2_instances": [],
        "rds_databases": [],
        "load_balancers": []
    }
    
    # CRITICAL: Always create a VPC if ANY infrastructure is mentioned
    # This follows AWS best practices - all resources must be in a VPC
    needs_infrastructure = any(keyword in text_lower for keyword in [
        'ec2', 'instance', 'server', 'rds', 'database', 'load balancer', 
        'alb', 'elb', 'web', 'application', 'infrastructure'
    ])
    
    if needs_infrastructure:
        # Extract VPC CIDR if specified
        vpc_match = re.search(r'(\d+\.\d+\.\d+\.\d+/\d+)', text_lower)
        vpc_cidr = vpc_match.group(1) if vpc_match else "10.0.0.0/16"
        
        vpc = {
            "id": "vpc-main",
            "name": "main-vpc",
            "cidr": vpc_cidr,
            "subnets": []
        }
        
        # Determine if we need public and/or private subnets
        needs_public = any(keyword in text_lower for keyword in [
            'public', 'load balancer', 'alb', 'elb', 'internet-facing', 'web'
        ])
        needs_private = any(keyword in text_lower for keyword in [
            'private', 'database', 'rds', 'internal', 'backend'
        ])
        
        # If neither explicitly mentioned, create both (best practice)
        if not needs_public and not needs_private:
            needs_public = True
            needs_private = True
        
        # Add public subnet (for load balancers, bastion hosts)
        if needs_public:
            vpc["subnets"].append({
                "id": "subnet-public-1",
                "name": "public-subnet-1",
                "cidr": "10.0.1.0/24",
                "type": "public",
                "az": "us-east-1a"
            })
        
        # Add private subnets (for EC2 app servers, databases)
        if needs_private:
            vpc["subnets"].append({
                "id": "subnet-private-1",
                "name": "private-subnet-1",
                "cidr": "10.0.2.0/24",
                "type": "private",
                "az": "us-east-1a"
            })
            # Add second private subnet for RDS (requires multi-AZ)
            vpc["subnets"].append({
                "id": "subnet-private-2",
                "name": "private-subnet-2",
                "cidr": "10.0.3.0/24",
                "type": "private",
                "az": "us-east-1b"
            })
        
        intent["vpcs"].append(vpc)
    
    # Extract EC2 information
    if 'ec2' in text_lower or 'instance' in text_lower or 'server' in text_lower or 'web' in text_lower:
        instance_type = "t2.micro"
        if 't2.small' in text_lower:
            instance_type = "t2.small"
        elif 't2.medium' in text_lower:
            instance_type = "t2.medium"
        elif 't3' in text_lower:
            instance_type = "t3.small"
        
        # Place EC2 in PRIVATE subnet by default (best practice)
        # Only use public if explicitly mentioned or if it's a bastion/jump host
        subnet_id = "subnet-private-1"
        if 'public' in text_lower and ('ec2' in text_lower or 'bastion' in text_lower):
            subnet_id = "subnet-public-1"
        
        intent["ec2_instances"].append({
            "id": "ec2-web-1",
            "name": "web-server-1",
            "instance_type": instance_type,
            "subnet_id": subnet_id
        })
    
    # Extract RDS information
    if 'rds' in text_lower or 'database' in text_lower or 'postgres' in text_lower or 'mysql' in text_lower:
        engine = "postgres"
        if 'mysql' in text_lower:
            engine = "mysql"
        elif 'mariadb' in text_lower:
            engine = "mariadb"
        
        intent["rds_databases"].append({
            "id": "rds-main",
            "name": "main-database",
            "engine": engine,
            "instance_class": "db.t3.micro",
            "subnet_ids": ["subnet-private-1", "subnet-private-2"],
            "allocated_storage": 20
        })
    
    # Extract Load Balancer information
    if 'load balancer' in text_lower or 'alb' in text_lower or 'elb' in text_lower or ('web' in text_lower and 'application' in text_lower):
        intent["load_balancers"].append({
            "id": "lb-main",
            "name": "main-load-balancer",
            "subnet_ids": ["subnet-public-1"],  # LB must be in public subnet
            "target_instance_ids": ["ec2-web-1"]
        })
    
    return intent


def parse_text_to_model(text: str) -> InfrastructureModel:
    """
    Main parser function: Text → Model
    
    This is the entry point for converting natural language to our infrastructure model.
    Steps:
    1. Try Google Gemini API first (if configured)
    2. Fallback to mock LLM if Gemini unavailable or fails
    3. Build InfrastructureModel from the JSON
    4. Return the model (which becomes the source of truth)
    """
    # Step 1: Try Gemini API first
    intent = gemini_extract(text)
    
    # Step 2: Fallback to mock LLM if Gemini failed
    if intent is None:
        print("ℹ️ Using mock LLM parser")
        intent = mock_llm_extract(text)
    
    # Step 2: Build the infrastructure model
    model = InfrastructureModel()
    
    # Add VPCs and their subnets
    for vpc_data in intent.get("vpcs", []):
        vpc = VPC(
            id=vpc_data["id"],
            name=vpc_data["name"],
            cidr=vpc_data["cidr"]
        )
        
        # Add subnets to VPC
        for subnet_data in vpc_data.get("subnets", []):
            subnet = Subnet(
                id=subnet_data["id"],
                name=subnet_data["name"],
                cidr=subnet_data["cidr"],
                subnet_type=SubnetType(subnet_data["type"]),
                availability_zone=subnet_data.get("az", "us-east-1a")
            )
            vpc.add_subnet(subnet)
        
        model.add_vpc(vpc)
    
    # Add EC2 instances
    for ec2_data in intent.get("ec2_instances", []):
        ec2 = EC2Instance(
            id=ec2_data["id"],
            name=ec2_data["name"],
            instance_type=ec2_data["instance_type"],  # Pass string, __post_init__ will convert to enum
            subnet_id=ec2_data["subnet_id"]
        )
        model.add_ec2(ec2)
    
    # Add RDS databases
    for rds_data in intent.get("rds_databases", []):
        rds = RDSDatabase(
            id=rds_data["id"],
            name=rds_data["name"],
            engine=rds_data["engine"],  # Pass string, __post_init__ will convert to enum
            instance_class=rds_data["instance_class"],
            subnet_ids=rds_data["subnet_ids"],
            allocated_storage=rds_data.get("allocated_storage", 20)
        )
        model.add_rds(rds)
    
    # Add Load Balancers
    for lb_data in intent.get("load_balancers", []):
        lb = LoadBalancer(
            id=lb_data["id"],
            name=lb_data["name"],
            subnet_ids=lb_data["subnet_ids"],
            target_instance_ids=lb_data.get("target_instance_ids", [])
        )
        model.add_load_balancer(lb)
    
    return model
