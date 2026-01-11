"""
Architecture Validator - Cloud Architecture Compiler
Enforces cloud best practices as mandatory rules.
Auto-corrects violations to ensure diagrams are always architecturally correct.

Philosophy: Treat correctness as higher priority than creativity.
"""

from typing import List, Tuple
from .model import (
    InfrastructureModel, VPC, Subnet, EC2Instance, RDSDatabase, LoadBalancer,
    SubnetType, InstanceType, DatabaseEngine, NATGateway, VPCFlowLogs
)


class ValidationResult:
    """Result of validation with corrections and warnings"""
    def __init__(self):
        self.is_valid = True
        self.corrections: List[str] = []  # Auto-fixes applied
        self.warnings: List[str] = []     # Non-blocking issues
    
    def add_correction(self, message: str):
        """Add a correction that was automatically applied"""
        self.corrections.append(message)
    
    def add_warning(self, message: str):
        """Add a warning (non-blocking)"""
        self.warnings.append(message)


def validate_and_fix(model: InfrastructureModel) -> Tuple[InfrastructureModel, ValidationResult]:
    """
    Validate infrastructure model and auto-fix violations.
    
    This is the main entry point for the validation layer.
    Returns: (corrected_model, validation_result)
    """
    result = ValidationResult()
    
    print("🔍 [Validator] Starting architecture validation...")
    
    # Rule 1: Exactly one VPC (MANDATORY)
    model = enforce_single_vpc(model, result)
    
    # Rule 2: Required subnets (MANDATORY)
    model = enforce_required_subnets(model, result)
    
    # Rule 3: Correct resource placement (MANDATORY)
    model = enforce_resource_placement(model, result)
    
    # Rule 4: No floating resources (MANDATORY)
    model = enforce_network_boundaries(model, result)
    
    # Rule 5: NAT Gateway and Flow Logs (MANDATORY)
    model = enforce_nat_and_flow_logs(model, result)
    
    print(f"✅ [Validator] Validation complete: {len(result.corrections)} corrections, {len(result.warnings)} warnings")
    
    return model, result


def enforce_single_vpc(model: InfrastructureModel, result: ValidationResult) -> InfrastructureModel:
    """
    Rule: Exactly one VPC per infrastructure.
    Auto-fix: Create VPC if missing, merge if multiple.
    """
    if len(model.vpcs) == 0:
        # No VPC - create default
        print("⚠️ [Validator] No VPC found, creating default VPC")
        vpc = VPC(
            id="vpc-main",
            name="main-vpc",
            cidr="10.0.0.0/16"
        )
        model.add_vpc(vpc)
        result.add_correction("Created default VPC (10.0.0.0/16) - all AWS resources must be in a VPC")
    
    elif len(model.vpcs) > 1:
        # Multiple VPCs - merge into first one
        print(f"⚠️ [Validator] Found {len(model.vpcs)} VPCs, merging into one")
        main_vpc = model.vpcs[0]
        
        # Merge subnets from other VPCs
        for vpc in model.vpcs[1:]:
            for subnet in vpc.subnets:
                main_vpc.add_subnet(subnet)
        
        # Keep only the main VPC
        model.vpcs = [main_vpc]
        result.add_correction(f"Merged multiple VPCs into one - AWS best practice is single VPC per environment")
    
    return model


def enforce_required_subnets(model: InfrastructureModel, result: ValidationResult) -> InfrastructureModel:
    """
    Rule: VPC must have at least one public and one private subnet.
    Auto-fix: Create missing subnets with proper CIDR allocation.
    """
    if len(model.vpcs) == 0:
        return model  # Will be fixed by enforce_single_vpc
    
    vpc = model.vpcs[0]
    
    # Check for public subnet
    has_public = any(s.subnet_type == SubnetType.PUBLIC for s in vpc.subnets)
    if not has_public:
        print("⚠️ [Validator] No public subnet found, creating one")
        public_subnet = Subnet(
            id="subnet-public-1",
            name="public-subnet-1",
            cidr="10.0.1.0/24",
            subnet_type=SubnetType.PUBLIC,
            availability_zone="us-east-1a"
        )
        vpc.add_subnet(public_subnet)
        result.add_correction("Created public subnet (10.0.1.0/24) - required for internet-facing resources")
    
    # Check for private subnets (need at least 2 for RDS multi-AZ)
    private_subnets = [s for s in vpc.subnets if s.subnet_type == SubnetType.PRIVATE]
    if len(private_subnets) == 0:
        print("⚠️ [Validator] No private subnets found, creating two (multi-AZ)")
        private_subnet_1 = Subnet(
            id="subnet-private-1",
            name="private-subnet-1",
            cidr="10.0.2.0/24",
            subnet_type=SubnetType.PRIVATE,
            availability_zone="us-east-1a"
        )
        private_subnet_2 = Subnet(
            id="subnet-private-2",
            name="private-subnet-2",
            cidr="10.0.3.0/24",
            subnet_type=SubnetType.PRIVATE,
            availability_zone="us-east-1b"
        )
        vpc.add_subnet(private_subnet_1)
        vpc.add_subnet(private_subnet_2)
        result.add_correction("Created private subnets in 2 AZs (10.0.2.0/24, 10.0.3.0/24) - required for databases and app servers")
    elif len(private_subnets) == 1:
        print("⚠️ [Validator] Only one private subnet, adding second for multi-AZ")
        private_subnet_2 = Subnet(
            id="subnet-private-2",
            name="private-subnet-2",
            cidr="10.0.3.0/24",
            subnet_type=SubnetType.PRIVATE,
            availability_zone="us-east-1b"
        )
        vpc.add_subnet(private_subnet_2)
        result.add_correction("Added second private subnet (10.0.3.0/24) in different AZ - required for RDS high availability")
    
    return model


def enforce_resource_placement(model: InfrastructureModel, result: ValidationResult) -> InfrastructureModel:
    """
    Rule: Resources must be in correct subnet types.
    - Load Balancers → public subnet
    - EC2 → private subnet (unless bastion)
    - RDS → private subnet only
    """
    if len(model.vpcs) == 0:
        return model
    
    vpc = model.vpcs[0]
    
    # Get first public and private subnets
    public_subnet = next((s for s in vpc.subnets if s.subnet_type == SubnetType.PUBLIC), None)
    private_subnets = [s for s in vpc.subnets if s.subnet_type == SubnetType.PRIVATE]
    
    if not public_subnet or not private_subnets:
        return model  # Will be fixed by enforce_required_subnets
    
    # Fix Load Balancers - MUST be in public subnet
    for lb in model.load_balancers:
        # Check if any subnet is private
        has_private_subnet = any(
            subnet_id in [s.id for s in private_subnets]
            for subnet_id in lb.subnet_ids
        )
        
        if has_private_subnet or not lb.subnet_ids:
            print(f"⚠️ [Validator] Moving load balancer {lb.id} to public subnet")
            lb.subnet_ids = [public_subnet.id]
            result.add_correction(f"Moved load balancer '{lb.name}' to public subnet - load balancers must be internet-facing")
    
    # Fix EC2 - should be in private subnet (best practice)
    for ec2 in model.ec2_instances:
        subnet = model.get_subnet_by_id(ec2.subnet_id)
        
        # If in public subnet and not a bastion, move to private
        if subnet and subnet.subnet_type == SubnetType.PUBLIC:
            if 'bastion' not in ec2.name.lower() and 'jump' not in ec2.name.lower():
                print(f"⚠️ [Validator] Moving EC2 {ec2.id} to private subnet")
                ec2.subnet_id = private_subnets[0].id
                result.add_correction(f"Moved EC2 instance '{ec2.name}' to private subnet - best practice for security")
    
    # Fix RDS - MUST be in private subnet (security requirement)
    for rds in model.rds_databases:
        # Check if any subnet is public
        has_public_subnet = any(
            subnet_id == public_subnet.id
            for subnet_id in rds.subnet_ids
        )
        
        if has_public_subnet or not rds.subnet_ids:
            print(f"🚫 [Validator] Moving database {rds.id} to private subnets (SECURITY)")
            # Use first two private subnets for multi-AZ
            rds.subnet_ids = [s.id for s in private_subnets[:2]]
            result.add_correction(f"Moved RDS database '{rds.name}' to private subnets - databases MUST NOT be publicly accessible")
    
    return model


def enforce_network_boundaries(model: InfrastructureModel, result: ValidationResult) -> InfrastructureModel:
    """
    Rule: No floating resources - all must be in valid subnets.
    Auto-fix: Assign orphaned resources to appropriate subnets.
    """
    if len(model.vpcs) == 0:
        return model
    
    vpc = model.vpcs[0]
    valid_subnet_ids = {s.id for s in vpc.subnets}
    
    public_subnet = next((s for s in vpc.subnets if s.subnet_type == SubnetType.PUBLIC), None)
    private_subnets = [s for s in vpc.subnets if s.subnet_type == SubnetType.PRIVATE]
    
    # Fix EC2 instances with invalid subnet_id
    for ec2 in model.ec2_instances:
        if ec2.subnet_id not in valid_subnet_ids:
            print(f"⚠️ [Validator] EC2 {ec2.id} has invalid subnet, assigning to private subnet")
            ec2.subnet_id = private_subnets[0].id if private_subnets else public_subnet.id
            result.add_correction(f"Assigned EC2 instance '{ec2.name}' to valid subnet - was floating outside network")
    
    # Fix RDS databases with invalid subnet_ids
    for rds in model.rds_databases:
        invalid_subnets = [sid for sid in rds.subnet_ids if sid not in valid_subnet_ids]
        if invalid_subnets or not rds.subnet_ids:
            print(f"⚠️ [Validator] RDS {rds.id} has invalid subnets, assigning to private subnets")
            rds.subnet_ids = [s.id for s in private_subnets[:2]]
            result.add_correction(f"Assigned RDS database '{rds.name}' to valid private subnets - was floating outside network")
    
    # Fix Load Balancers with invalid subnet_ids
    for lb in model.load_balancers:
        invalid_subnets = [sid for sid in lb.subnet_ids if sid not in valid_subnet_ids]
        if invalid_subnets or not lb.subnet_ids:
            print(f"⚠️ [Validator] Load balancer {lb.id} has invalid subnets, assigning to public subnet")
            lb.subnet_ids = [public_subnet.id] if public_subnet else []
            result.add_correction(f"Assigned load balancer '{lb.name}' to valid public subnet - was floating outside network")
            
    return model


# Enforce NAT Gateway presence and Flow Logs
def enforce_nat_and_flow_logs(model: InfrastructureModel, result: ValidationResult) -> InfrastructureModel:
    """Ensure NAT Gateways and VPC Flow Logs exist.
    - If private subnets exist without a NAT Gateway, create one in the first public subnet.
    - If a VPC lacks flow logs, create a default VPCFlowLogs resource.
    Auto‑corrections are added to `result`.
    """
    if not model.vpcs:
        return model
    vpc = model.vpcs[0]
    # Identify subnets
    public_subnet = next((s for s in vpc.subnets if s.subnet_type == SubnetType.PUBLIC), None)
    private_subnets = [s for s in vpc.subnets if s.subnet_type == SubnetType.PRIVATE]
    # Ensure NAT Gateway
    nat_gateways = getattr(model, 'nat_gateways', [])
    if private_subnets and not nat_gateways:
        if public_subnet:
            nat = NATGateway(
                id=f"nat-{vpc.id}",
                name="auto-nat-gateway",
                subnet_id=public_subnet.id,
                elastic_ip=None,
            )
            model.add_nat_gateway(nat)
            result.add_correction("Created NAT Gateway in public subnet to enable outbound traffic for private subnets")
    # Ensure Flow Logs
    flow_logs = getattr(model, 'flow_logs', [])
    if not flow_logs:
        fl = VPCFlowLogs(
            id=f"flowlog-{vpc.id}",
            vpc_id=vpc.id,
            log_destination_type="cloud-watch-logs",
            traffic_type="ALL",
            log_group_name=None,
        )
        model.add_flow_logs(fl)
        result.add_correction("Created VPC Flow Log for VPC to capture network traffic")
    return model


