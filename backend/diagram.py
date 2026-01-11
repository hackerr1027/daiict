"""
Model-to-Diagram Generator
Tier-Based Architecture Diagram
Converts InfrastructureModel to professional tier-based Mermaid diagram.
"""

from .model import InfrastructureModel, SubnetType
from .diagram_styles import StylePalette
from .diagram_constants import DiagramIcons, DiagramConfig, DiagramText


def format_node_label(primary: str, secondary: str = "", tertiary: str = "", max_len: int = DiagramConfig.MAX_LABEL_LENGTH) -> str:
    """
    Create consistent 3-line node label with visual hierarchy and smart truncation.
    
    Args:
        primary: First line (primary name - will be bold)
        secondary: Second line (type/class - will be small)
        tertiary: Third line (metadata - will be small)
        max_len: Maximum character length per line (default 30)
        
    Returns:
        Formatted label with HTML tags for visual hierarchy
    """
    # Smart truncation: preserve both start and end
    def truncate(text: str) -> str:
        if len(text) <= max_len:
            return text
        # Keep first part and last part for context
        if max_len >= 20:
            mid = max_len - 6  # Reserve 6 chars (3 for "..." + 3 for end)
            return text[:mid] + "..." + text[-3:]
        return text[:max_len - 3] + "..."
    
    # Apply truncation
    primary = truncate(primary) if primary else ""
    secondary = truncate(secondary) if secondary else "&nbsp;"
    tertiary = truncate(tertiary) if tertiary else "&nbsp;"
    
    # Add visual hierarchy: bold primary, small secondary/tertiary
    primary_formatted = f"<b>{primary}</b>" if primary else "&nbsp;"
    secondary_formatted = f"<small>{secondary}</small>" if secondary and secondary != "&nbsp;" else "&nbsp;"
    tertiary_formatted = f"<small>{tertiary}</small>" if tertiary and tertiary != "&nbsp;" else "&nbsp;"
    
    return f"{primary_formatted}<br/>{secondary_formatted}<br/>{tertiary_formatted}"


def generate_mermaid_diagram(model: InfrastructureModel, dark_mode: bool = False) -> str:
    """
    Generate a tier-based Mermaid diagram from the infrastructure model.
    
    Layout: Edge Tier → Application Tier → Database Tier → Support Tier
    All tiers shown even if empty for consistent structure.
    
    Args:
        model: Infrastructure model to visualize
        dark_mode: If True, use dark color scheme for dark backgrounds
    
    Color Scheme: WCAG AA/AAA compliant
    - High contrast ratios for accessibility
    - Semantic color coding by tier
    - Pattern fills for grayscale/colorblind users
    """
    lines = ["graph TB"]
    
    # Add Mermaid spacing configuration for better layout
    lines.append(f"    %%{{init: {{'flowchart': {{'nodeSpacing': {DiagramConfig.NODE_SPACING}, 'rankSpacing': {DiagramConfig.RANK_SPACING}, 'padding': {DiagramConfig.PADDING}, 'curve': '{DiagramConfig.CURVE}'}}}}}}%%")
    
    lines.append("    %% Tier-Based Architecture Diagram")
    lines.append("")
    
    # ==== USERS / INTERNET ENTRY POINT ====
    lines.append(f'    Users["{DiagramIcons.USER} {DiagramText.USERS_LABEL}"]')
    lines.append(f"    style Users {StylePalette.node_style(StylePalette.USERS_STROKE)}")
    lines.append("")
    
    # ==== EDGE TIER (Load Balancers) - ALWAYS SHOWN ====
    lines.append(f'    subgraph EdgeTier["{DiagramIcons.EDGE} {DiagramText.EDGE_TIER}"]')
    lines.append("        direction LR")
    
    has_edge = False
    
    # Internet Gateway (simplified - no icon duplication)
    if model.vpcs:
        igw_label = format_node_label(
            DiagramText.INTERNET_GATEWAY,
            DiagramText.ENTRY_POINT,
            ""
        )
        lines.append(f'        IGW["{igw_label}"]')
        lines.append(f"        style IGW {StylePalette.node_style(StylePalette.IGW_STROKE)}")
        has_edge = True
    
    # Application Load Balancers
    if model.load_balancers:
        has_edge = True
        for lb in model.load_balancers:
            az_count = len(lb.subnet_ids)
            # Simplified label (no duplicate icon, shorter text)
            lb_label = format_node_label(
                lb.name,
                DiagramText.APPLICATION_LB,
                DiagramText.az_count(az_count)
            )
            lines.append(f'        {lb.id}["{lb_label}"]')
            lines.append(f"        style {lb.id} {StylePalette.node_style(StylePalette.AMBER['stroke'])}")
    
    # No empty state nodes (removed redundancy)
    
    lines.append("    end")
    lines.append(f"    style EdgeTier {StylePalette.tier_style(StylePalette.AMBER)}")
    lines.append("")
    
    # ==== APPLICATION TIER (EC2) - ALWAYS SHOWN ====
    lines.append(f'    subgraph AppTier["{DiagramIcons.COMPUTE} {DiagramText.APP_TIER}"]')
    lines.append("        direction LR")
    
    has_compute = False
    
    # EC2 Instances - Pool if >3, otherwise show individually
    if model.ec2_instances:
        has_compute = True
        
        if len(model.ec2_instances) > 3:
            # Resource pooling for visual clarity
            instance_types = set(ec2.instance_type.value for ec2 in model.ec2_instances)
            types_str = ", ".join(sorted(instance_types))
            pool_label = format_node_label(
                DiagramText.ec2_pool_label(len(model.ec2_instances)),
                types_str,
                DiagramText.AUTO_SCALING
            )
            lines.append(f'        EC2Pool["{pool_label}"]')
            lines.append(f"        style EC2Pool {StylePalette.node_style(StylePalette.EMERALD['stroke'])}")
        else:
            # Show individual instances (simplified labels)
            for ec2 in model.ec2_instances:
                ec2_label = format_node_label(
                    ec2.name,
                    ec2.instance_type.value,
                    ""
                )
                lines.append(f'        {ec2.id}["{ec2_label}"]')
                lines.append(f"        style {ec2.id} {StylePalette.node_style(StylePalette.EMERALD['stroke'])}")
    
    # No empty state nodes
    
    lines.append("    end")
    lines.append(f"    style AppTier {StylePalette.tier_style(StylePalette.EMERALD)}")
    lines.append("")
    
    # ==== DATABASE TIER (RDS) - ALWAYS SHOWN ====
    lines.append(f'    subgraph DataTier["{DiagramIcons.DATABASE} {DiagramText.DATABASE_TIER}"]')
    lines.append("        direction LR")
    
    has_database = False
    
    # RDS Databases
    if model.rds_databases:
        has_database = True
        for rds in model.rds_databases:
            # Safely check for attributes that may not exist in all model versions
            multi_az = DiagramText.MULTI_AZ if getattr(rds, 'multi_az', False) else DiagramText.SINGLE_AZ
            encrypted = DiagramIcons.LOCK if getattr(rds, 'storage_encrypted', False) else ""
            az_count = len(rds.subnet_ids)
            
            # Simplified label (no duplicate icon, condensed info)
            rds_label = format_node_label(
                rds.name,
                f"{rds.engine.value} {rds.instance_class}",
                f"{multi_az} {encrypted}"
            )
            lines.append(f'        {rds.id}["{rds_label}"]')
            # Add dashed stroke for critical data (helps in grayscale)
            lines.append(f"        style {rds.id} {StylePalette.node_style(StylePalette.RED['stroke'], dashed=True)}")
    
    # No empty state nodes
    
    lines.append("    end")
    lines.append(f"    style DataTier {StylePalette.tier_style(StylePalette.RED)}")
    lines.append("")
    
    # ==== SUPPORT TIER (VPC Info, S3) - Simplified ====
    lines.append(f'    subgraph SupportTier["{DiagramIcons.SUPPORT} {DiagramText.SUPPORT_TIER}"]')
    lines.append("        direction LR")
    
    has_support = False
    
    # VPC Information (simplified)
    if model.vpcs:
        has_support = True
        for vpc in model.vpcs:
            subnet_count = len(vpc.subnets)
            vpc_label = format_node_label(
                DiagramText.vpc_label(vpc.name),
                vpc.cidr,
                DiagramText.subnet_count(subnet_count)
            )
            lines.append(f'        {vpc.id}["{vpc_label}"]')
            lines.append(f"        style {vpc.id} {StylePalette.node_style(StylePalette.SLATE['stroke'])}")
    
    # S3 Buckets (simplified with clear icon in badge)
    if model.s3_buckets:
        has_support = True
        for bucket in model.s3_buckets:
            encrypted = DiagramIcons.LOCK if getattr(bucket, 'encryption_enabled', False) else ""
            versioned = DiagramIcons.DOCUMENT if getattr(bucket, 'versioning_enabled', False) else ""
            badges = f"{encrypted}{versioned}".strip() or DiagramText.STORAGE
            
            s3_label = format_node_label(
                bucket.name,
                DiagramText.S3_BUCKET,
                badges
            )
            lines.append(f'        {bucket.id}["{s3_label}"]')
            # Fixed: Use Slate color to match Support tier
            lines.append(f"        style {bucket.id} {StylePalette.node_style(StylePalette.SLATE['stroke'])}")
    
    # Security Groups removed from visual (confusing, will add connection notes instead)
    
    # No empty state nodes
        lines.append("        style SupportEmpty fill:#f8fafc,stroke:#cbd5e1,stroke-dasharray: 5 5,color:#1e293b")
    
    lines.append("    end")
    lines.append(f"    style SupportTier {StylePalette.tier_style(StylePalette.SLATE)}")
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
    
    # Load Balancers → EC2 - Handle pooling vs individual
    if model.load_balancers and model.ec2_instances:
        if len(model.ec2_instances) > 3:
            # Connect to pool
            for lb in model.load_balancers:
                lines.append(f"    {lb.id} ==> EC2Pool")
        else:
            # Connect individually (limit to 3 to avoid clutter)
            connections_shown = 0
            total_connections = 0
            
            for lb in model.load_balancers:
                for ec2_id in lb.target_instance_ids:
                    if ec2_id:
                        total_connections += 1
                        if connections_shown < DiagramConfig.MAX_CONNECTIONS:
                            lines.append(f"    {lb.id} ==> {ec2_id}")
                            connections_shown += 1
            
            if total_connections > DiagramConfig.MAX_CONNECTIONS:
                remaining = total_connections - DiagramConfig.MAX_CONNECTIONS
                lines.append(f'    LBNote["{DiagramText.more_connections(remaining)}"]')
                lines.append(f'    style LBNote {StylePalette.note_style(StylePalette.NOTE_BG_AMBER, StylePalette.AMBER["stroke"], StylePalette.AMBER["text"])}')
    
    # EC2 → RDS with clear note
    if model.ec2_instances and model.rds_databases:
        # Show one example connection
        ec2_id = "EC2Pool" if len(model.ec2_instances) > DiagramConfig.POOL_THRESHOLD else model.ec2_instances[0].id
        lines.append(f"    {ec2_id} -.-> {model.rds_databases[0].id}")
        
        # Add clarifying note
        if len(model.ec2_instances) > 1:
            lines.append(f'    DBNote["{DiagramText.ALL_EC2_CONNECT_DB}"]')
            lines.append(f'    style DBNote {StylePalette.note_style(StylePalette.RED["bg"], StylePalette.RED["stroke"], StylePalette.RED["text"])}')
    
    # VPC → SG relationship removed (was confusing)
    
    # Add arrow legend for clarity
    lines.append("")
    lines.append(f'    Legend["{DiagramText.ARROW_LEGEND}"]')
    lines.append(f'    style Legend {StylePalette.legend_style()}')
    
    # Add color legend for tier identification
    lines.append("")
    lines.append(f'    ColorKey["{DiagramText.COLOR_KEY}"]')
    lines.append(f'    style ColorKey {StylePalette.color_key_style()}')
    
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
    
    return "Tier-based architecture with " + ", ".join(parts)
