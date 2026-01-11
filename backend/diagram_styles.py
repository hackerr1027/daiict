"""
Centralized diagram styling
WCAG AAA compliant color palette
"""

class StylePalette:
    """Centralized color and style definitions for diagrams"""
    
    # Base node styles
    NODE_FILL = "#ffffff"
    NODE_TEXT = "#000"
    STROKE_WIDTH = "3px"
    
    # Tier color schemes (50/500/900 pattern for consistency)
    AMBER = {
        "bg": "#fffbeb",
        "stroke": "#f59e0b",
        "text": "#78350f"
    }
    
    EMERALD = {
        "bg": "#ecfdf5",
        "stroke": "#10b981",
        "text": "#065f46"
    }
    
    RED = {
        "bg": "#fef2f2",
        "stroke": "#ef4444",
        "text": "#7f1d1d"
    }
    
    SLATE = {
        "bg": "#f8fafc",
        "stroke": "#64748b",
        "text": "#1e293b"
    }
    
    # Special colors
    USERS_STROKE = "#22c55e"  # Green for entry point
    IGW_STROKE = "#3b82f6"    # Blue for gateway
    
    # Note and legend styles
    NOTE_BG_AMBER = "#fef3c7"
    LEGEND_BG = "#f3f4f6"
    LEGEND_STROKE = "#9ca3af"
    LEGEND_TEXT = "#6b7280"
    COLOR_KEY_BG = "#fafafa"
    COLOR_KEY_STROKE = "#d1d5db"
    
    # Font sizes
    NOTE_FONT_SIZE = "12px"
    LEGEND_FONT_SIZE = "12px"
    COLOR_KEY_FONT_SIZE = "11px"
    
    @staticmethod
    def node_style(stroke_color: str, dashed: bool = False) -> str:
        """
        Generate consistent node style string.
        
        Args:
            stroke_color: Hex color for stroke
            dashed: If True, add dashed pattern (for critical components)
        
        Returns:
            Complete style string
        """
        dash = ",stroke-dasharray:5 5" if dashed else ""
        return (f"fill:{StylePalette.NODE_FILL},"
                f"stroke:{stroke_color},"
                f"stroke-width:{StylePalette.STROKE_WIDTH}{dash},"
                f"color:{StylePalette.NODE_TEXT}")
    
    @staticmethod
    def tier_style(colors: dict) -> str:
        """
        Generate consistent tier/subgraph style string.
        
        Args:
            colors: Dict with 'bg', 'stroke', 'text' keys
        
        Returns:
            Complete tier style string
        """
        return (f"fill:{colors['bg']},"
                f"stroke:{colors['stroke']},"
                f"stroke-width:2px,"
                f"color:{colors['text']}")
    
    @staticmethod
    def note_style(bg_color: str, stroke_color: str, text_color: str) -> str:
        """Generate style for annotation notes"""
        return (f"fill:{bg_color},"
                f"stroke:{stroke_color},"
                f"stroke-dasharray:5 5,"
                f"color:{text_color},"
                f"font-size:{StylePalette.NOTE_FONT_SIZE}")
    
    @staticmethod
    def legend_style() -> str:
        """Generate style for arrow legend"""
        return (f"fill:{StylePalette.LEGEND_BG},"
                f"stroke:{StylePalette.LEGEND_STROKE},"
                f"stroke-width:1px,"
                f"color:{StylePalette.LEGEND_TEXT},"
                f"font-size:{StylePalette.LEGEND_FONT_SIZE}")
    
    @staticmethod
    def color_key_style() -> str:
        """Generate style for color key legend"""
        return (f"fill:{StylePalette.COLOR_KEY_BG},"
                f"stroke:{StylePalette.COLOR_KEY_STROKE},"
                f"stroke-width:1px,"
                f"color:{StylePalette.LEGEND_TEXT},"
                f"font-size:{StylePalette.COLOR_KEY_FONT_SIZE}")
