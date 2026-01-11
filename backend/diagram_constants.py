"""
Diagram constants and configuration
Icons, thresholds, and user-configurable settings
"""

class DiagramIcons:
    """Unicode emoji icons for diagram elements"""
    
    # Entry points
    USER = "👤"
    CLOUD = "☁️"
    
    # Tier icons
    EDGE = "🔀"
    COMPUTE = "💻"
    DATABASE = "💾"
    SUPPORT = "⚙️"
    
    # Component badges
    LOCK = "🔒"        # Encryption
    DOCUMENT = "📋"   # Versioning
    COLOR_KEY = "🎨"  # Color legend


class DiagramConfig:
    """User-configurable diagram settings"""
    
    # Layout configuration
    NODE_SPACING = 50
    RANK_SPACING = 80
    PADDING = 20
    CURVE = "basis"
    DIRECTION = "TB"  # Top-to-bottom
    
    # Behavioral thresholds
    POOL_THRESHOLD = 3        # When to pool resources (e.g., EC2 instances)
    MAX_CONNECTIONS = 3       # Max explicit connections to show
    
    # Feature flags
    SHOW_LEGEND = True
    SHOW_COLOR_KEY = True
    INCLUDE_NOTES = True
    
    # Text formatting
    MAX_LABEL_LENGTH = 30


class DiagramText:
    """Text content and labels used in diagrams"""
    
    # User entry point
    USERS_LABEL = "Users / Internet"
    
    # Tier headers
    EDGE_TIER = "Edge Tier | Traffic Distribution"
    APP_TIER = "Application Tier | Compute"
    DATABASE_TIER = "Database Tier | Data Storage"
    SUPPORT_TIER = "Support Tier | Infrastructure"
    
    # Common labels
    INTERNET_GATEWAY = "Internet Gateway"
    ENTRY_POINT = "Entry Point"
    APPLICATION_LB = "Application LB"
    S3_BUCKET = "S3 Bucket"
    STORAGE = "Storage"
    AUTO_SCALING = "Auto-Scaling"
    
    # Availability zones
    @staticmethod
    def az_count(count: int) -> str:
        """Format AZ count label"""
        return f"{count} AZs" if count != 1 else "1 AZ"
    
    # Multi-AZ status
    MULTI_AZ = "Multi-AZ"
    SINGLE_AZ = "Single AZ"
    
    # Connection notes
    @staticmethod
    def more_connections(count: int) -> str:
        """Format 'more connections' note"""
        return f"+ {count} more connections"
    
    ALL_EC2_CONNECT_DB = "All EC2 instances connect to database"
    
    # EC2 Pool label
    @staticmethod
    def ec2_pool_label(count: int) -> str:
        """Format EC2 pool label"""
        return f"EC2 Pool ({count})"
    
    # Legends
    ARROW_LEGEND = "━━ User Traffic Flow | ┄┄ Internal/Backend Connections"
    COLOR_KEY = "🎨 Tier Colors: Amber=Edge | Green=Compute | Red=Database | Gray=Support"
    
    # VPC label
    @staticmethod
    def vpc_label(name: str) -> str:
        """Format VPC label"""
        return f"VPC: {name}"
    
    # Subnet count
    @staticmethod
    def subnet_count(count: int) -> str:
        """Format subnet count label"""
        return f"{count} subnets" if count != 1 else "1 subnet"
