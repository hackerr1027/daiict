"""
Model-to-Diagram Generator
Converts InfrastructureModel to Mermaid diagram format.
This reads from the model, never directly from text or Terraform.
"""

from .model import InfrastructureModel, SubnetType


def generate_mermaid_diagram(model: InfrastructureModel) -> str:
    """
    Generate a Mermaid diagram from the infrastructure model.
    
    Follows cloud architecture best practices:
    - Explicit VPC and subnet boundaries
    - Correct resource placement (LB in public, DB in private)
    - Directional network flow
    - Clear security isolation
    - Comprehensive labeling
    """
    lines = ["graph TB"]
    lines.append("    %% Cloud Infrastructure Diagram - Architecture Review Ready")
    lines.append("")
    
    # Add Internet Gateway as entry point
    lines.append("    Internet([\"🌐 Internet\"])")
    lines.append("    style Internet fill:#e3f2fd,stroke:#1976d2,stroke-width:3px")
    lines.append("")
    
    # Track all components for relationship mapping
    all_subnets = {}
    public_subnets = []
    private_subnets = []
    
    # Generate VPCs and Subnets
    for vpc in model.vpcs:
        vpc_label = f"VPC: {vpc.name}<br/>{vpc.cidr}"
        lines.append(f"    subgraph {vpc.id}[\"{vpc_label}\"]")
        lines.append(f"        direction TB")
        lines.append("")
        
        # Add Internet Gateway for this VPC
        igw_id = f"igw-{vpc.id}"
        lines.append(f"        {igw_id}[\"🚪 Internet Gateway\"]")
        lines.append(f"        style {igw_id} fill:#c8e6c9,stroke:#388e3c,stroke-width:2px")
        lines.append("")
        
        # Separate public and private subnets
        for subnet in vpc.subnets:
            all_subnets[subnet.id] = subnet
            if subnet.subnet_type == SubnetType.PUBLIC:
                public_subnets.append(subnet)
            else:
                private_subnets.append(subnet)
        
        # Generate PUBLIC subnets first
        for subnet in vpc.subnets:
            if subnet.subnet_type == SubnetType.PUBLIC:
                subnet_label = f"PUBLIC SUBNET<br/>{subnet.name}<br/>{subnet.cidr}<br/>AZ: {subnet.availability_zone}"
                lines.append(f"        subgraph {subnet.id}[\"{subnet_label}\"]")
                lines.append(f"            direction TB")
                
                # Add Load Balancers in public subnet
                for lb in model.load_balancers:
                    # Check if LB is in this subnet
                    if subnet.id in lb.subnet_ids:
                        lines.append(f"            {lb.id}[\"⚖️ Load Balancer<br/>{lb.name}<br/>ID: {lb.id}<br/>Application LB\"]")
                
                # Add EC2 instances in public subnet (if any - not recommended but possible)
                for ec2 in model.ec2_instances:
                    if ec2.subnet_id == subnet.id:
                        lines.append(f"            {ec2.id}[\"🖥️ EC2 Instance<br/>{ec2.name}<br/>ID: {ec2.id}<br/>{ec2.instance_type.value}<br/>⚠️ PUBLIC\"]")
                
                lines.append(f"        end")
                lines.append(f"        style {subnet.id} fill:#d4edda,stroke:#28a745,stroke-width:2px")
                lines.append("")
        
        # Generate PRIVATE subnets
        for subnet in vpc.subnets:
            if subnet.subnet_type == SubnetType.PRIVATE:
                subnet_label = f"PRIVATE SUBNET<br/>{subnet.name}<br/>{subnet.cidr}<br/>AZ: {subnet.availability_zone}"
                lines.append(f"        subgraph {subnet.id}[\"{subnet_label}\"]")
                lines.append(f"            direction TB")
                
                # Add EC2 instances in private subnet
                for ec2 in model.ec2_instances:
                    if ec2.subnet_id == subnet.id:
                        lines.append(f"            {ec2.id}[\"🖥️ EC2 Instance<br/>{ec2.name}<br/>ID: {ec2.id}<br/>{ec2.instance_type.value}<br/>🔒 PRIVATE\"]")
                
                # Add RDS databases in private subnet (if primary subnet)
                for rds in model.rds_databases:
                    if subnet.id in rds.subnet_ids and subnet.id == rds.subnet_ids[0]:
                        lines.append(f"            {rds.id}[\"🗄️ RDS Database<br/>{rds.name}<br/>ID: {rds.id}<br/>{rds.engine.value}<br/>{rds.instance_class}<br/>🔒 PRIVATE ONLY\"]")
                
                lines.append(f"        end")
                lines.append(f"        style {subnet.id} fill:#f8d7da,stroke:#dc3545,stroke-width:2px")
                lines.append("")
        
        lines.append(f"    end")
        lines.append(f"    style {vpc.id} fill:#d1ecf1,stroke:#0c5460,stroke-width:3px")
        lines.append("")
    
    # Add S3 Buckets (outside VPC)
    if model.s3_buckets:
        lines.append("    %% S3 Buckets (Global Service)")
        for bucket in model.s3_buckets:
            encryption_label = "🔐 Encrypted" if bucket.encryption_enabled else "⚠️ Unencrypted"
            versioning_label = "📦 Versioned" if bucket.versioning_enabled else "No Versioning"
            lines.append(f"    {bucket.id}[\"💾 S3 Bucket<br/>{bucket.name}<br/>ID: {bucket.id}<br/>{encryption_label}<br/>{versioning_label}\"]")
            lines.append(f"    style {bucket.id} fill:#fff3cd,stroke:#856404,stroke-width:2px")
        lines.append("")
    
    lines.append("    %% Network Flow (Directional)")
    lines.append("")
    
    # Internet → Internet Gateway
    if model.vpcs:
        igw_id = f"igw-{model.vpcs[0].id}"
        lines.append(f"    Internet ===> {igw_id}")
    
    # Internet Gateway → Load Balancers (in public subnets)
    for lb in model.load_balancers:
        if model.vpcs:
            igw_id = f"igw-{model.vpcs[0].id}"
            lines.append(f"    {igw_id} ===> {lb.id}")
    
    # Load Balancer → EC2 instances (targets)
    for lb in model.load_balancers:
        for target_id in lb.target_instance_ids:
            lines.append(f"    {lb.id} --> {target_id}")
    
    # EC2 → RDS (application tier to database tier)
    for ec2 in model.ec2_instances:
        subnet = model.get_subnet_by_id(ec2.subnet_id)
        if subnet and subnet.subnet_type == SubnetType.PRIVATE:
            for rds in model.rds_databases:
                lines.append(f"    {ec2.id} -.->|Database Query| {rds.id}")
    
    # EC2 → S3 (if S3 buckets exist)
    if model.s3_buckets and model.ec2_instances:
        for ec2 in model.ec2_instances:
            for bucket in model.s3_buckets:
                lines.append(f"    {ec2.id} -.->|S3 API| {bucket.id}")
    
    lines.append("")
    lines.append("    %% Legend")
    lines.append("    classDef publicSubnet fill:#d4edda,stroke:#28a745")
    lines.append("    classDef privateSubnet fill:#f8d7da,stroke:#dc3545")
    lines.append("    classDef vpc fill:#d1ecf1,stroke:#0c5460")
    
    return "\n".join(lines)


def generate_diagram_description(model: InfrastructureModel) -> str:
    """
    Generate a human-readable description of the infrastructure.
    Useful for documentation or API responses.
    """
    parts = []
    
    # VPC summary
    for vpc in model.vpcs:
        parts.append(f"VPC '{vpc.name}' ({vpc.cidr}) with {len(vpc.subnets)} subnet(s)")
    
    # EC2 summary
    if model.ec2_instances:
        parts.append(f"{len(model.ec2_instances)} EC2 instance(s)")
    
    # RDS summary
    if model.rds_databases:
        parts.append(f"{len(model.rds_databases)} RDS database(s)")
    
    # Load Balancer summary
    if model.load_balancers:
        parts.append(f"{len(model.load_balancers)} load balancer(s)")
    
    return ", ".join(parts)
