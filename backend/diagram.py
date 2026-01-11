"""
Model-to-Diagram Generator
Tier-Based Architecture Diagram
Converts InfrastructureModel to professional tier-based Mermaid diagram.
"""

from .model import InfrastructureModel, SubnetType


def generate_mermaid_diagram(model: InfrastructureModel) -> str:
    """
    Generate a tier-based Mermaid diagram from the infrastructure model.
    
    Layout: Edge Tier → Application Tier → Database Tier → Support Tier
    All tiers shown even if empty for consistent structure.
    """
    lines = ["graph TB"]
    lines.append("    %% Tier-Based Architecture Diagram")
    lines.append("")
    
    # ==== USERS / INTERNET ENTRY POINT ====
    lines.append("    Users[\"👥 Users / Internet\"]")
    lines.append("    style Users fill:#ffffff,stroke:#22c55e,stroke-width:3px,color:#000")
    lines.append("")
    
    # ==== EDGE TIER (Load Balancers) - ALWAYS SHOWN ====
    lines.append("    subgraph EdgeTier[\"⚖️ EDGE TIER - Load Balancing\"]")
    lines.append("        direction LR")
    
    has_edge = False
    
    # Internet Gateway
    if model.vpcs:
        lines.append("        IGW[\"🌐 Internet Gateway<br/>VPC Entry Point\"]")
        lines.append("        style IGW fill:#ffffff,stroke:#3b82f6,stroke-width:3px,color:#000")
        has_edge = True
    
    # Application Load Balancers
    if model.load_balancers:
        has_edge = True
        for lb in model.load_balancers:
            az_count = len(lb.subnet_ids)
            lines.append(f"        {lb.id}[\"⚖️ {lb.name}<br/>Application Load Balancer<br/>📍 {az_count} AZs\"]")
            lines.append(f"        style {lb.id} fill:#ffffff,stroke:#f59e0b,stroke-width:3px,color:#000")
    
    
    # NAT Gateways
    nat_gateways = getattr(model, 'nat_gateways', [])
    if nat_gateways:
        for nat in nat_gateways:
            lines.append(f"        {nat.id}[\"⚡ {nat.name}\"]")
            lines.append(f"        style {nat.id} fill:#ffffff,stroke:#10b981,stroke-width:3px,color:#000")
    else:
        lines.append("        NATEmpty[\"✓ No NAT gateways deployed\"]")
        lines.append("        style NATEmpty fill:#e0f2fe,stroke:#38bdf8,stroke-dasharray: 5 5,color:#0369a1")
    # Show empty state if no edge resources
    if not has_edge:
        lines.append("        EdgeEmpty[\"✓ No load balancers deployed\"]")
        lines.append("        style EdgeEmpty fill:#fffbeb,stroke:#fbbf24,stroke-dasharray: 5 5,color:#78350f")
    
    lines.append("    end")
    lines.append("    style EdgeTier fill:#fffbeb,stroke:#f59e0b,stroke-width:2px,color:#78350f")
    lines.append("")
    
    # ==== APPLICATION TIER (EC2) - ALWAYS SHOWN ====
    lines.append("    subgraph AppTier[\"🖥️ APPLICATION TIER - Compute\"]")
    lines.append("        direction LR")
    
    has_compute = False
    
    # EC2 Instances
    if model.ec2_instances:
        has_compute = True
        for ec2 in model.ec2_instances:
            lines.append(f"        {ec2.id}[\"🖥️ {ec2.name}<br/>{ec2.instance_type.value}<br/>EC2 Instance\"]")
            lines.append(f"        style {ec2.id} fill:#ffffff,stroke:#10b981,stroke-width:3px,color:#000")
    
    # Show empty state if no compute resources
    if not has_compute:
        lines.append("        AppEmpty[\"✓ No compute resources deployed\"]")
        lines.append("        style AppEmpty fill:#ecfdf5,stroke:#86efac,stroke-dasharray: 5 5,color:#166534")
    
    lines.append("    end")
    lines.append("    style AppTier fill:#ecfdf5,stroke:#10b981,stroke-width:2px,color:#065f46")
    lines.append("")
    
    # ==== DATABASE TIER (RDS) - ALWAYS SHOWN ====
    lines.append("    subgraph DataTier[\"🗄️ DATABASE TIER - Data Storage\"]")
    lines.append("        direction LR")
    
    has_database = False
    
    # RDS Databases
    if model.rds_databases:
        has_database = True
        for rds in model.rds_databases:
            # Safely check for attributes that may not exist in all model versions
            multi_az_badge = "Multi-AZ ✓" if getattr(rds, 'multi_az', False) else "Single AZ"
            encrypted_badge = "🔒" if getattr(rds, 'storage_encrypted', False) else ""
            az_count = len(rds.subnet_ids)
            lines.append(f"        {rds.id}[\"🗄️ {rds.name}<br/>{rds.engine.value}<br/>{rds.instance_class}<br/>{multi_az_badge} {encrypted_badge}<br/>📍 {az_count} AZs\"]")
            lines.append(f"        style {rds.id} fill:#ffffff,stroke:#ef4444,stroke-width:3px,color:#000")
    
    # Show empty state if no databases
    if not has_database:
        lines.append("        DataEmpty[\"✓ No databases deployed\"]")
        lines.append("        style DataEmpty fill:#fef2f2,stroke:#fca5a5,stroke-dasharray: 5 5,color:#7f1d1d")
    
    lines.append("    end")
    lines.append("    style DataTier fill:#fef2f2,stroke:#ef4444,stroke-width:2px,color:#7f1d1d")
    lines.append("")
    
    # ==== SUPPORT TIER (VPC Info, S3, Security Groups) - ALWAYS SHOWN ====
    lines.append("    subgraph SupportTier[\"🔧 SUPPORT TIER - Infrastructure Services\"]")
    lines.append("        direction LR")
    
    has_support = False
    
    # VPC Information
    if model.vpcs:
        has_support = True
        for vpc in model.vpcs:
            subnet_count = len(vpc.subnets)
            lines.append(f"        {vpc.id}[\"☁️ VPC: {vpc.name}<br/>{vpc.cidr}<br/>📍 {subnet_count} subnets\"]")
            lines.append(f"        style {vpc.id} fill:#ffffff,stroke:#64748b,stroke-width:3px,color:#000")
    
    # S3 Buckets
    if model.s3_buckets:
        has_support = True
        for bucket in model.s3_buckets:
            encryption_badge = "🔒" if getattr(bucket, 'encryption_enabled', False) else ""
            versioning_badge = "📋" if getattr(bucket, 'versioning_enabled', False) else ""
            lines.append(f"        {bucket.id}[\"🗂️ S3: {bucket.name}<br/>{encryption_badge} {versioning_badge}\"]")
            lines.append(f"        style {bucket.id} fill:#ffffff,stroke:#f59e0b,stroke-width:3px,color:#000")
    
    # Security Groups (show count)
    if model.security_groups:
        has_support = True
        sg_count = len(model.security_groups)
        lines.append(f"        SG[\"🛡️ Security Groups<br/>{sg_count} configured\"]")
        lines.append(f"        style SG fill:#ffffff,stroke:#8b5cf6,stroke-width:3px,color:#000")
    
    # Show empty state if no support services
    if not has_support:
        lines.append("        SupportEmpty[\"✓ No additional services\"]")
        lines.append("        style SupportEmpty fill:#f8fafc,stroke:#cbd5e1,stroke-dasharray: 5 5,color:#1e293b")
    
    lines.append("    end")
    lines.append("    style SupportTier fill:#f8fafc,stroke:#64748b,stroke-width:2px,color:#1e293b")
    lines.append("")
    
    # ==== TRAFFIC FLOW ARROWS ====
    lines.append("    %% Traffic Flow")
    
    # Users → Internet Gateway (if VPC exists)
    if model.vpcs:
        lines.append("    Users ==> IGW")
    
    # Internet Gateway → Load Balancers (solid arrows for user traffic)
    if model.vpcs and model.load_balancers:
        for lb in model.load_balancers:
            lines.append(f"    IGW ==> {lb.id}")
    
    # Load Balancers → EC2 (solid arrows)
    if model.load_balancers and model.ec2_instances:
        for lb in model.load_balancers:
            for ec2_id in lb.target_instance_ids:
                if ec2_id:  # Only if target is specified
                    lines.append(f"    {lb.id} ==> {ec2_id}")
    
    # EC2 → RDS (dashed arrows for backend traffic)
    if model.ec2_instances and model.rds_databases:
        # Connect first EC2 to first RDS as example
        if model.ec2_instances and model.rds_databases:
            lines.append(f"    {model.ec2_instances[0].id} -.-> {model.rds_databases[0].id}")
    
    # VPC → Security Groups (dashed arrow showing relationship)
    if model.vpcs and model.security_groups:
        lines.append(f"    {model.vpcs[0].id} -.-> SG")
    
    lines.append("")
    return "\n".join(lines)


def generate_diagram_description(model: InfrastructureModel) -> str:
    """Generate a text description of the diagram."""
    parts = []
    
    if model.vpcs:
        parts.append(f"{len(model.vpcs)} VPC(s)")
    if model.load_balancers:
        parts.append(f"{len(model.load_balancers)} Load Balancer(s)")
    if model.ec2_instances:
        parts.append(f"{len(model.ec2_instances)} EC2 Instance(s)")
    if model.rds_databases:
        parts.append(f"{len(model.rds_databases)} RDS Database(s)")
    if model.s3_buckets:
        parts.append(f"{len(model.s3_buckets)} S3 Bucket(s)")
    if model.security_groups:
        parts.append(f"{len(model.security_groups)} Security Group(s)")
    
    if not parts:
        return "Empty infrastructure"
    
<<<<<<< HEAD
    return "Tier-based architecture with " + ", ".join(parts)
=======
    return "Tier-based architecture with " + ", ".join(parts)
>>>>>>> 9b7510c85e7d10b729118326e538e63d97fa0468
