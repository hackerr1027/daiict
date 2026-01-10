"""
Edit Operations Module
Handles all semantic edit operations on the Infrastructure Model.

This is the ONLY way to modify the model from diagram or Terraform edits.
All operations:
1. Apply changes to the model
2. Track edit source to prevent loops
3. Run security validation
4. Return validation results

Edit Flow:
  Diagram/Terraform → Edit Operation → Model → Security Check → Accept/Reject
"""

from typing import Dict, Any, Optional, List
from .model import (
    InfrastructureModel, VPC, Subnet, EC2Instance, RDSDatabase, LoadBalancer,
    S3Bucket, SecurityGroup, SubnetType, InstanceType, DatabaseEngine, EditSource
)
from .security import validate_security, SecurityWarning
import copy


class EditResult:
    """Result of an edit operation"""
    def __init__(self, success: bool, model: Optional[InfrastructureModel], 
                 warnings: List[SecurityWarning], error: Optional[str] = None):
        self.success = success
        self.model = model
        self.warnings = warnings
        self.error = error
    
    def to_dict(self) -> Dict:
        return {
            "success": self.success,
            "warnings": [w.to_dict() for w in self.warnings] if self.warnings else [],
            "error": self.error,
            "model_id": self.model.model_id if self.model else None
        }


def add_resource(model: InfrastructureModel, resource_type: str, 
                 properties: Dict[str, Any], source: EditSource) -> EditResult:
    """
    Add a new resource to the model
    
    Supported resource types: ec2, rds, load_balancer, subnet
    
    Security: Validates the new resource doesn't violate policies
    Loop Prevention: Tracks edit source
    """
    # Create a copy to test changes
    model_copy = copy.deepcopy(model)
    
    try:
        if resource_type == "ec2":
            # Add EC2 instance
            instance = EC2Instance(
                id=properties.get("id", f"ec2-{len(model_copy.ec2_instances) + 1}"),
                name=properties.get("name", f"instance-{len(model_copy.ec2_instances) + 1}"),
                instance_type=properties.get("instance_type", "t2.micro"),
                subnet_id=properties["subnet_id"]  # Required
            )
            model_copy.add_ec2(instance)
            
        elif resource_type == "rds":
            # Add RDS database
            database = RDSDatabase(
                id=properties.get("id", f"rds-{len(model_copy.rds_databases) + 1}"),
                name=properties.get("name", f"database-{len(model_copy.rds_databases) + 1}"),
                engine=properties.get("engine", "postgres"),
                instance_class=properties.get("instance_class", "db.t3.micro"),
                subnet_ids=properties["subnet_ids"]  # Required
            )
            model_copy.add_rds(database)
            
        elif resource_type == "load_balancer" or resource_type == "elb":
            # Add Load Balancer (support both 'load_balancer' and 'elb')
            lb = LoadBalancer(
                id=properties.get("id", f"lb-{len(model_copy.load_balancers) + 1}"),
                name=properties.get("name", f"lb-{len(model_copy.load_balancers) + 1}"),
                subnet_ids=properties["subnet_ids"],  # Required
                target_instance_ids=properties.get("target_instance_ids", [])
            )
            model_copy.add_load_balancer(lb)
            
        elif resource_type == "subnet":
            # Add subnet to existing VPC
            vpc_id = properties.get("vpc_id")
            if not vpc_id:
                return EditResult(False, None, [], "VPC ID required for subnet")
            
            vpc = next((v for v in model_copy.vpcs if v.id == vpc_id), None)
            if not vpc:
                return EditResult(False, None, [], f"VPC {vpc_id} not found")
            
            subnet = Subnet(
                id=properties.get("id", f"subnet-{len(vpc.subnets) + 1}"),
                name=properties.get("name", f"subnet-{len(vpc.subnets) + 1}"),
                cidr=properties["cidr"],  # Required
                subnet_type=SubnetType(properties.get("type", "private")),
                availability_zone=properties.get("az", "us-east-1a")
            )
            vpc.add_subnet(subnet)
            
        elif resource_type == "s3":
            # Add S3 Bucket
            bucket = S3Bucket(
                id=properties.get("id", f"s3-{len(model_copy.s3_buckets) + 1}"),
                name=properties.get("name", f"bucket-{len(model_copy.s3_buckets) + 1}"),
                versioning_enabled=properties.get("versioning_enabled", False),
                encryption_enabled=properties.get("encryption_enabled", True)
            )
            model_copy.add_s3_bucket(bucket)
            
        elif resource_type == "security_group":
            # Add Security Group
            vpc_id = properties.get("vpc_id", "vpc-main")  # Use existing VPC or default
            sg = SecurityGroup(
                id=properties.get("id", f"sg-{len(model_copy.security_groups) + 1}"),
                name=properties.get("name", f"security-group-{len(model_copy.security_groups) + 1}"),
                vpc_id=vpc_id,
                description=properties.get("description", "Security group"),
                ingress_rules=properties.get("ingress_rules", []),
                egress_rules=properties.get("egress_rules", [])
            )
            model_copy.add_security_group(sg)
        else:
            return EditResult(False, None, [], f"Unknown resource type: {resource_type}")
        
        # Validate security
        warnings = validate_security(model_copy)
        
        # Check for HIGH severity violations
        high_severity = [w for w in warnings if w.severity == "HIGH"]
        if high_severity:
            return EditResult(
                False, None, warnings,
                f"Security violation: {high_severity[0].message}"
            )
        
        # Update edit tracking
        model_copy.update_edit_tracking(source)
        
        return EditResult(True, model_copy, warnings)
        
    except Exception as e:
        return EditResult(False, None, [], f"Error adding resource: {str(e)}")


def remove_resource(model: InfrastructureModel, resource_id: str, 
                   source: EditSource) -> EditResult:
    """
    Remove a resource from the model
    
    Security: Ensures removal doesn't break dependencies
    """
    model_copy = copy.deepcopy(model)
    
    try:
        # Find and remove the resource
        removed = False
        
        # Check EC2 instances
        for i, ec2 in enumerate(model_copy.ec2_instances):
            if ec2.id == resource_id:
                model_copy.ec2_instances.pop(i)
                removed = True
                break
        
        # Check RDS databases
        if not removed:
            for i, rds in enumerate(model_copy.rds_databases):
                if rds.id == resource_id:
                    model_copy.rds_databases.pop(i)
                    removed = True
                    break
        
        # Check Load Balancers
        if not removed:
            for i, lb in enumerate(model_copy.load_balancers):
                if lb.id == resource_id:
                    model_copy.load_balancers.pop(i)
                    removed = True
                    break
        
        # Check S3 Buckets
        if not removed:
            for i, bucket in enumerate(model_copy.s3_buckets):
                if bucket.id == resource_id:
                    model_copy.s3_buckets.pop(i)
                    removed = True
                    break
        
        # Check Security Groups
        if not removed:
            for i, sg in enumerate(model_copy.security_groups):
                if sg.id == resource_id:
                    model_copy.security_groups.pop(i)
                    removed = True
                    break
        
        if not removed:
            return EditResult(False, None, [], f"Resource {resource_id} not found")
        
        # CRITICAL FIX: Clean up dangling references to deleted resource
        # If we deleted an EC2 instance, remove it from load balancer targets
        for lb in model_copy.load_balancers:
            if resource_id in lb.target_instance_ids:
                lb.target_instance_ids.remove(resource_id)
        
        # Validate security (might expose new issues)
        warnings = validate_security(model_copy)
        
        # Update edit tracking
        model_copy.update_edit_tracking(source)
        
        return EditResult(True, model_copy, warnings)
        
    except Exception as e:
        return EditResult(False, None, [], f"Error removing resource: {str(e)}")


def move_resource(model: InfrastructureModel, resource_id: str, 
                  target_subnet_id: str, source: EditSource) -> EditResult:
    """
    Move a resource (EC2 or RDS) to a different subnet
    
    Security: Critical check - prevents moving DBs to public subnets
    Common use case: Moving EC2 between public/private subnets
    """
    model_copy = copy.deepcopy(model)
    
    try:
        # Verify target subnet exists
        target_subnet = model_copy.get_subnet_by_id(target_subnet_id)
        if not target_subnet:
            return EditResult(False, None, [], f"Target subnet {target_subnet_id} not found")
        
        moved = False
        
        # Move EC2 instance
        for ec2 in model_copy.ec2_instances:
            if ec2.id == resource_id:
                ec2.subnet_id = target_subnet_id
                moved = True
                break
        
        # Move RDS (update subnet_ids)
        if not moved:
            for rds in model_copy.rds_databases:
                if rds.id == resource_id:
                    # For RDS, we need to maintain multi-AZ, so add to subnet list
                    if target_subnet_id not in rds.subnet_ids:
                        rds.subnet_ids = [target_subnet_id] + rds.subnet_ids[:1]  # Keep 2 subnets
                    moved = True
                    break
        
        if not moved:
            return EditResult(False, None, [], f"Resource {resource_id} not found. It may have been deleted.")
        
        # CRITICAL: Validate security after move
        warnings = validate_security(model_copy)
        
        # Block HIGH severity violations (e.g., DB in public subnet)
        high_severity = [w for w in warnings if w.severity == "HIGH"]
        if high_severity:
            return EditResult(
                False, None, warnings,
                f"Move blocked: {high_severity[0].message}"
            )
        
        # Update edit tracking
        model_copy.update_edit_tracking(source)
        
        return EditResult(True, model_copy, warnings)
        
    except Exception as e:
        return EditResult(False, None, [], f"Error moving resource: {str(e)}")


def update_resource_property(model: InfrastructureModel, resource_id: str,
                             property_name: str, value: Any, 
                             source: EditSource) -> EditResult:
    """
    Update a specific property of a resource
    
    Allowed properties (safe to edit):
    - EC2: instance_type
    - RDS: instance_class, allocated_storage
    - LoadBalancer: target_instance_ids
    
    Blocked properties: IDs, names (would break references)
    """
    model_copy = copy.deepcopy(model)
    
    # Whitelist of editable properties
    SAFE_PROPERTIES = {
        "ec2": ["instance_type"],
        "rds": ["instance_class", "allocated_storage"],
        "load_balancer": ["target_instance_ids"]
    }
    
    try:
        updated = False
        
        # Update EC2
        for ec2 in model_copy.ec2_instances:
            if ec2.id == resource_id:
                if property_name not in SAFE_PROPERTIES["ec2"]:
                    return EditResult(False, None, [], 
                                    f"Property {property_name} is not editable for EC2")
                if property_name == "instance_type":
                    ec2.instance_type = value  # String, will be converted by __post_init__
                updated = True
                break
        
        # Update RDS
        if not updated:
            for rds in model_copy.rds_databases:
                if rds.id == resource_id:
                    if property_name not in SAFE_PROPERTIES["rds"]:
                        return EditResult(False, None, [], 
                                        f"Property {property_name} is not editable for RDS")
                    setattr(rds, property_name, value)
                    updated = True
                    break
        
        # Update Load Balancer
        if not updated:
            for lb in model_copy.load_balancers:
                if lb.id == resource_id:
                    if property_name not in SAFE_PROPERTIES["load_balancer"]:
                        return EditResult(False, None, [], 
                                        f"Property {property_name} is not editable for Load Balancer")
                    setattr(lb, property_name, value)
                    updated = True
                    break
        
        if not updated:
            return EditResult(False, None, [], f"Resource {resource_id} not found")
        
        # Validate security
        warnings = validate_security(model_copy)
        
        # Update edit tracking
        model_copy.update_edit_tracking(source)
        
        return EditResult(True, model_copy, warnings)
        
    except Exception as e:
        return EditResult(False, None, [], f"Error updating property: {str(e)}")
