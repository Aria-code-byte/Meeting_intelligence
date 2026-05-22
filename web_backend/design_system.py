"""
Jinni AI Intelligence System - Design System V2
Based on "Intelligent Precision" design language
"""

# ============================================================
# Color Palette
# ============================================================

class Colors:
    """Color tokens based on the design system"""

    # Surface Colors
    SURFACE = "#F9F9FF"
    SURFACE_DIM = "#CFDAF2"
    SURFACE_BRIGHT = "#F9F9FF"
    SURFACE_CONTAINER_LOWEST = "#FFFFFF"
    SURFACE_CONTAINER_LOW = "#F0F3FF"
    SURFACE_CONTAINER = "#E7EEFF"
    SURFACE_CONTAINER_HIGH = "#DEE8FF"
    SURFACE_CONTAINER_HIGHEST = "#D8E3FB"

    # On Surface Colors
    ON_SURFACE = "#111C2D"
    ON_SURFACE_VARIANT = "#43474E"
    INVERSE_SURFACE = "#263143"
    INVERSE_ON_SURFACE = "#ECF1FF"

    # Primary Colors (Brand Core)
    PRIMARY = "#002542"
    ON_PRIMARY = "#FFFFFF"
    PRIMARY_CONTAINER = "#163B5C"
    ON_PRIMARY_CONTAINER = "#84A5CC"
    INVERSE_PRIMARY = "#A8C9F2"

    # Primary Fixed (for lighter backgrounds)
    PRIMARY_FIXED = "#D0E4FF"
    PRIMARY_FIXED_DIM = "#A8C9F2"
    ON_PRIMARY_FIXED = "#001D35"
    ON_PRIMARY_FIXED_VARIANT = "#26496B"

    # Secondary Colors (The Assistant Layer)
    SECONDARY = "#4D6171"
    ON_SECONDARY = "#FFFFFF"
    SECONDARY_CONTAINER = "#D0E5F8"
    ON_SECONDARY_CONTAINER = "#536777"

    # Secondary Fixed
    SECONDARY_FIXED = "#D0E5F8"
    SECONDARY_FIXED_DIM = "#B4C9DB"
    ON_SECONDARY_FIXED = "#081D2B"
    ON_SECONDARY_FIXED_VARIANT = "#354958"

    # Tertiary Colors (Warm Accents)
    TERTIARY = "#371D00"
    ON_TERTIARY = "#FFFFFF"
    TERTIARY_CONTAINER = "#553000"
    ON_TERTIARY_CONTAINER = "#D6954B"

    # Tertiary Fixed (Dawn Orange - AI Insights)
    TERTIARY_FIXED = "#FFDCBC"
    TERTIARY_FIXED_DIM = "#FFB86B"
    ON_TERTIARY_FIXED = "#2C1700"
    ON_TERTIARY_FIXED_VARIANT = "#683D00"

    # Error Colors
    ERROR = "#BA1A1A"
    ON_ERROR = "#FFFFFF"
    ERROR_CONTAINER = "#FFDAD6"
    ON_ERROR_CONTAINER = "#93000A"

    # Semantic Colors
    ACTION_BLUE = "#2F80ED"
    DAWN_ORANGE = "#FFB86B"
    AI_BLUE = "#D7ECFF"

    # Legacy Compatibility (from V1)
    PRIMARY_V1 = "#173B57"
    BACKGROUND_V1 = "#F4FAFF"
    SIDEBAR_V1 = "#EAF5FF"


# ============================================================
# Typography
# ============================================================

class Typography:
    """Typography tokens"""

    # Font Family
    FONT_FAMILY = "Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif"

    # Headlines
    DISPLAY_LG = {
        "font_family": FONT_FAMILY,
        "font_size": "48px",
        "font_weight": "700",
        "line_height": "1.2",
        "letter_spacing": "-0.02em"
    }

    HEADLINE_LG = {
        "font_family": FONT_FAMILY,
        "font_size": "32px",
        "font_weight": "700",
        "line_height": "40px",
        "letter_spacing": "-0.02em"
    }

    HEADLINE_LG_MOBILE = {
        "font_family": FONT_FAMILY,
        "font_size": "28px",
        "font_weight": "700",
        "line_height": "36px",
        "letter_spacing": "-0.02em"
    }

    HEADLINE_MD = {
        "font_family": FONT_FAMILY,
        "font_size": "20px",
        "font_weight": "600",
        "line_height": "28px"
    }

    HEADLINE_SM = {
        "font_family": FONT_FAMILY,
        "font_size": "18px",
        "font_weight": "600",
        "line_height": "1.4"
    }

    # Body
    BODY_LG = {
        "font_family": FONT_FAMILY,
        "font_size": "18px",
        "font_weight": "400",
        "line_height": "1.6"
    }

    BODY_MD = {
        "font_family": FONT_FAMILY,
        "font_size": "16px",
        "font_weight": "400",
        "line_height": "24px"
    }

    BODY_SM = {
        "font_family": FONT_FAMILY,
        "font_size": "14px",
        "font_weight": "400",
        "line_height": "1.5"
    }

    # Labels
    LABEL_MD = {
        "font_family": FONT_FAMILY,
        "font_size": "14px",
        "font_weight": "600",
        "line_height": "1.2"
    }

    LABEL_SM = {
        "font_family": FONT_FAMILY,
        "font_size": "13px",
        "font_weight": "500",
        "line_height": "18px",
        "letter_spacing": "0.01em"
    }


# ============================================================
# Spacing
# ============================================================

class Spacing:
    """Spacing tokens based on 4px grid"""

    BASE = "4px"
    XS = "8px"
    SM = "12px"
    MD = "16px"
    LG = "24px"
    XL = "32px"
    XXL = "48px"
    XXXL = "64px"

    GUTTER = "16px"
    MARGIN_MOBILE = "16px"
    MARGIN_DESKTOP = "32px"

    SIDEBAR_WIDTH = "280px"


# ============================================================
# Border Radius
# ============================================================

class Radius:
    """Border radius tokens"""

    SM = "0.25rem"    # 4px
    DEFAULT = "0.5rem"  # 8px
    MD = "0.75rem"    # 12px
    LG = "1rem"       # 16px
    XL = "1.5rem"     # 24px
    FULL = "9999px"   # Pill shape


# ============================================================
# Shadows & Elevation
# ============================================================

class Shadows:
    """Shadow tokens for elevation"""

    # Level 0 - Flat
    NONE = "none"

    # Level 1 - Cards (Subtle)
    CARD = "0 4px 12px rgba(22, 59, 92, 0.05)"

    # Level 2 - Hover/Interactive
    HOVER = "0 8px 20px rgba(22, 59, 92, 0.08)"

    # Level 3 - Modals/Popovers
    MODAL = "0 12px 32px rgba(22, 59, 92, 0.12)"

    # Focus Glow
    FOCUS = "0 0 0 3px rgba(0, 37, 66, 0.1)"

    # AI Glow (Orange tint)
    AI_GLOW = "0 0 0 3px rgba(255, 184, 107, 0.2)"


# ============================================================
# CSS Generator
# ============================================================

def generate_css() -> str:
    """Generate complete CSS for Streamlit"""

    return f"""
    /* ============================================================
       Jinni AI Intelligence System - Design System V2
       Intelligent Precision Design Language
       ============================================================ */

    /* Global Styles */
    .main {{
        background-color: {Colors.SURFACE};
        font-family: {Typography.FONT_FAMILY};
        color: {Colors.ON_SURFACE};
    }}

    /* Hide Streamlit Default Elements */
    #MainMenu {{ visibility: hidden; }}
    footer {{ visibility: hidden; }}
    stAppHeader {{ display: none; }}

    /* ============================================================
       Typography
       ============================================================ */

    h1 {{
        font-family: {Typography.FONT_FAMILY};
        font-size: {Typography.HEADLINE_LG['font_size']};
        font-weight: {Typography.HEADLINE_LG['font_weight']};
        line-height: {Typography.HEADLINE_LG['line_height']};
        letter-spacing: {Typography.HEADLINE_LG['letter_spacing']};
        color: {Colors.PRIMARY};
        margin-bottom: {Spacing.LG};
    }}

    h2 {{
        font-family: {Typography.FONT_FAMILY};
        font-size: {Typography.HEADLINE_MD['font_size']};
        font-weight: {Typography.HEADLINE_MD['font_weight']};
        line-height: {Typography.HEADLINE_MD['line_height']};
        color: {Colors.PRIMARY};
        margin-bottom: {Spacing.MD};
    }}

    h3 {{
        font-family: {Typography.FONT_FAMILY};
        font-size: {Typography.HEADLINE_SM['font_size']};
        font-weight: {Typography.HEADLINE_SM['font_weight']};
        color: {Colors.ON_SURFACE};
        margin-bottom: {Spacing.SM};
    }}

    p, .stMarkdown {{
        font-family: {Typography.FONT_FAMILY};
        font-size: {Typography.BODY_MD['font_size']};
        font-weight: {Typography.BODY_MD['font_weight']};
        line-height: {Typography.BODY_MD['line_height']};
        color: {Colors.ON_SURFACE};
    }}

    /* ============================================================
       Card Component
       ============================================================ */

    .jinni-card {{
        background: {Colors.SURFACE_CONTAINER_LOWEST};
        border: 1px solid {Colors.SURFACE_CONTAINER};
        border-radius: {Radius.LG};
        box-shadow: {Shadows.CARD};
        padding: {Spacing.XL};
        margin-bottom: {Spacing.LG};
        transition: all 0.2s ease;
    }}

    .jinni-card:hover {{
        box-shadow: {Shadows.HOVER};
    }}

    /* AI Card - with top border accent */
    .jinni-card-ai {{
        background: {Colors.SURFACE_CONTAINER_LOWEST};
        border: 1px solid {Colors.SURFACE_CONTAINER};
        border-top: 3px solid {Colors.DAWN_ORANGE};
        border-radius: {Radius.LG};
        box-shadow: {Shadows.CARD};
        padding: {Spacing.XL};
        margin-bottom: {Spacing.LG};
    }}

    /* ============================================================
       Button Component
       ============================================================ */

    /* Primary Button */
    .stButton > button {{
        background: {Colors.PRIMARY_CONTAINER} !important;
        color: {Colors.ON_PRIMARY} !important;
        border: none !important;
        border-radius: {Radius.DEFAULT} !important;
        padding: {Spacing.SM} {Spacing.LG} !important;
        font-family: {Typography.FONT_FAMILY} !important;
        font-size: {Typography.LABEL_SM['font_size']} !important;
        font-weight: {Typography.LABEL_SM['font_weight']} !important;
        transition: all 0.2s ease !important;
        box-shadow: {Shadows.CARD} !important;
    }}

    .stButton > button:hover {{
        background: {Colors.PRIMARY} !important;
        box-shadow: {Shadows.HOVER} !important;
        transform: translateY(-1px) !important;
    }}

    /* Primary Button (Type="primary") */
    .stButton > button[kind="primary"] {{
        background: {Colors.ACTION_BLUE} !important;
    }}

    .stButton > button[kind="primary"]:hover {{
        background: {Colors.PRIMARY} !important;
    }}

    /* Secondary Button (outline style) */
    .jinni-button-secondary {{
        background: transparent !important;
        color: {Colors.PRIMARY} !important;
        border: 1px solid {Colors.PRIMARY} !important;
    }}

    /* AI Button (orange accent) */
    .jinni-button-ai {{
        background: {Colors.DAWN_ORANGE} !important;
        color: {Colors.ON_TERTIARY_FIXED} !important;
    }}

    .jinni-button-ai:hover {{
        background: {Colors.TERTIARY_FIXED_DIM} !important;
    }}

    /* ============================================================
       Input Component
       ============================================================ */

    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stSelectbox > div > div > select {{
        background: {Colors.SURFACE_CONTAINER_LOWEST};
        border: 1px solid {Colors.SURFACE_CONTAINER_HIGH};
        border-radius: {Radius.DEFAULT};
        padding: {Spacing.SM} {Spacing.MD};
        font-family: {Typography.FONT_FAMILY};
        font-size: {Typography.BODY_MD['font_size']};
        color: {Colors.ON_SURFACE};
        transition: all 0.2s ease;
    }}

    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus,
    .stSelectbox > div > div > select:focus {{
        border: 2px solid {Colors.PRIMARY};
        box-shadow: {Shadows.FOCUS};
        outline: none;
    }}

    /* File Uploader */
    .stFileUploader {{
        background: {Colors.SURFACE_CONTAINER_LOW};
        border: 2px dashed {Colors.SURFACE_CONTAINER_HIGH};
        border-radius: {Radius.LG};
        padding: {Spacing.XXL};
    }}

    /* ============================================================
       Progress Component
       ============================================================ */

    .stProgress > div > div > div > div {{
        background: {Colors.ACTION_BLUE};
        border-radius: {Radius.FULL};
    }}

    .stProgress > div > div > div {{
        background: {Colors.SURFACE_CONTAINER};
        border-radius: {Radius.FULL};
    }}

    /* ============================================================
       Status/Alert Components
       ============================================================ */

    .stSuccess {{
        background: {Colors.SECONDARY_CONTAINER};
        color: {Colors.ON_SECONDARY_FIXED};
        border-left: 4px solid {Colors.SECONDARY};
        border-radius: {Radius.DEFAULT};
        padding: {Spacing.MD};
    }}

    .stInfo {{
        background: {Colors.PRIMARY_FIXED};
        color: {Colors.ON_PRIMARY_FIXED};
        border-left: 4px solid {Colors.PRIMARY};
        border-radius: {Radius.DEFAULT};
        padding: {Spacing.MD};
    }}

    .stWarning {{
        background: {Colors.TERTIARY_FIXED};
        color: {Colors.ON_TERTIARY_FIXED};
        border-left: 4px solid {Colors.DAWN_ORANGE};
        border-radius: {Radius.DEFAULT};
        padding: {Spacing.MD};
    }}

    .stError {{
        background: {Colors.ERROR_CONTAINER};
        color: {Colors.ON_ERROR_CONTAINER};
        border-left: 4px solid {Colors.ERROR};
        border-radius: {Radius.DEFAULT};
        padding: {Spacing.MD};
    }}

    /* ============================================================
       Tabs Component
       ============================================================ */

    .stTabs [data-baseweb="tab-list"] {{
        gap: {Spacing.SM};
        background: {Colors.SURFACE_CONTAINER_LOW};
        padding: {Spacing.SM};
        border-radius: {Radius.LG};
    }}

    .stTabs [data-baseweb="tab"] {{
        background: transparent;
        color: {Colors.ON_SURFACE_VARIANT};
        border-radius: {Radius.DEFAULT};
        padding: {Spacing.SM} {Spacing.LG};
        font-family: {Typography.FONT_FAMILY};
        font-size: {Typography.LABEL_SM['font_size']};
        font-weight: {Typography.LABEL_SM['font_weight']};
        transition: all 0.2s ease;
    }}

    .stTabs [data-baseweb="tab"][aria-selected="true"] {{
        background: {Colors.SURFACE_CONTAINER_LOWEST};
        color: {Colors.PRIMARY};
        box-shadow: {Shadows.CARD};
    }}

    .stTabs [data-baseweb="tab"]:hover {{
        background: {Colors.SURFACE_CONTAINER_HIGH};
    }}

    /* ============================================================
       Radio Component
       ============================================================ */

    .stRadio {{
        background: {Colors.SURFACE_CONTAINER_LOWEST};
        border: 1px solid {Colors.SURFACE_CONTAINER};
        border-radius: {Radius.LG};
        padding: {Spacing.MD};
    }}

    .stRadio [role="radiogroup"] {{
        gap: {Spacing.SM};
    }}

    .stRadio [role="radio"] {{
        background: {Colors.SURFACE_CONTAINER_LOW};
        border: 1px solid {Colors.SURFACE_CONTAINER_HIGH};
        border-radius: {Radius.DEFAULT};
        padding: {Spacing.SM} {Spacing.MD};
        transition: all 0.2s ease;
    }}

    .stRadio [role="radio"][aria-checked="true"] {{
        background: {Colors.SECONDARY_CONTAINER};
        border-color: {Colors.SECONDARY};
        color: {Colors.ON_SECONDARY_FIXED};
    }}

    .stRadio [role="radio"]:hover {{
        background: {Colors.SURFACE_CONTAINER_HIGH};
    }}

    /* ============================================================
       Expander Component
       ============================================================ */

    .streamlit-expanderHeader {{
        background: {Colors.SURFACE_CONTAINER_LOW};
        border: 1px solid {Colors.SURFACE_CONTAINER};
        border-radius: {Radius.DEFAULT};
        padding: {Spacing.SM} {Spacing.MD};
        font-family: {Typography.FONT_FAMILY};
        font-size: {Typography.BODY_MD['font_size']};
        font-weight: {Typography.BODY_MD['font_weight']};
        color: {Colors.ON_SURFACE};
    }}

    .streamlit-expanderContent {{
        background: {Colors.SURFACE_CONTAINER_LOW};
        border: 1px solid {Colors.SURFACE_CONTAINER};
        border-top: none;
        border-radius: 0 0 {Radius.DEFAULT} {Radius.DEFAULT};
        padding: {Spacing.MD};
    }}

    /* ============================================================
       Sidebar
       ============================================================ */

    .css-1d391kg {{
        background: {Colors.SURFACE_CONTAINER};
    }}

    .css-1d391kg .stMarkdown {{
        color: {Colors.ON_SURFACE};
    }}

    /* ============================================================
       Chips/Badges
       ============================================================ */

    .jinni-chip {{
        display: inline-flex;
        align-items: center;
        gap: {Spacing.XS};
        background: {Colors.SECONDARY_CONTAINER};
        color: {Colors.ON_SECONDARY_FIXED};
        padding: {Spacing.XS} {Spacing.SM};
        border-radius: {Radius.FULL};
        font-size: {Typography.LABEL_SM['font_size']};
        font-weight: {Typography.LABEL_SM['font_weight']};
    }}

    .jinni-chip-ai {{
        background: {Colors.TERTIARY_FIXED};
        color: {Colors.ON_TERTIARY_FIXED};
    }}

    .jinni-chip-success {{
        background: {Colors.SECONDARY_CONTAINER};
        color: {Colors.ON_SECONDARY_CONTAINER};
    }}

    .jinni-chip-error {{
        background: {Colors.ERROR_CONTAINER};
        color: {Colors.ON_ERROR_CONTAINER};
    }}

    /* ============================================================
       Custom Components
       ============================================================ */

    /* Step Indicator */
    .jinni-step {{
        display: flex;
        align-items: center;
        gap: {Spacing.SM};
        padding: {Spacing.SM} {Spacing.MD};
        background: {Colors.SURFACE_CONTAINER_LOW};
        border-radius: {Radius.FULL};
        font-size: {Typography.LABEL_SM['font_size']};
        color: {Colors.ON_SURFACE_VARIANT};
    }}

    .jinni-step-active {{
        background: {Colors.PRIMARY_CONTAINER};
        color: {Colors.ON_PRIMARY_CONTAINER};
    }}

    .jinni-step-completed {{
        background: {Colors.SECONDARY_CONTAINER};
        color: {Colors.ON_SECONDARY_CONTAINER};
    }}

    /* Info Box */
    .jinni-info-box {{
        background: {Colors.PRIMARY_FIXED};
        border-left: 4px solid {Colors.PRIMARY};
        border-radius: {Radius.DEFAULT};
        padding: {Spacing.MD};
        margin-bottom: {Spacing.MD};
    }}

    .jinni-info-box-ai {{
        background: {Colors.TERTIARY_FIXED};
        border-left: 4px solid {Colors.DAWN_ORANGE};
    }}

    /* Divider */
    .jinni-divider {{
        border: none;
        border-top: 1px solid {Colors.SURFACE_CONTAINER};
        margin: {Spacing.XL} 0;
    }}

    /* ============================================================
       Utility Classes
       ============================================================ */

    .text-primary {{ color: {Colors.PRIMARY} !important; }}
    .text-secondary {{ color: {Colors.ON_SURFACE_VARIANT} !important; }}
    .text-ai {{ color: {Colors.DAWN_ORANGE} !important; }}
    .text-error {{ color: {Colors.ERROR} !important; }}
    .text-success {{ color: {Colors.SECONDARY} !important; }}

    .bg-surface {{ background: {Colors.SURFACE} !important; }}
    .bg-card {{ background: {Colors.SURFACE_CONTAINER_LOWEST} !important; }}
    .bg-ai {{ background: {Colors.TERTIARY_FIXED} !important; }}

    .mt-sm {{ margin-top: {Spacing.SM} !important; }}
    .mt-md {{ margin-top: {Spacing.MD} !important; }}
    .mt-lg {{ margin-top: {Spacing.LG} !important; }}
    .mt-xl {{ margin-top: {Spacing.XL} !important; }}

    .mb-sm {{ margin-bottom: {Spacing.SM} !important; }}
    .mb-md {{ margin-bottom: {Spacing.MD} !important; }}
    .mb-lg {{ margin-bottom: {Spacing.LG} !important; }}
    .mb-xl {{ margin-bottom: {Spacing.XL} !important; }}

    .p-sm {{ padding: {Spacing.SM} !important; }}
    .p-md {{ padding: {Spacing.MD} !important; }}
    .p-lg {{ padding: {Spacing.LG} !important; }}
    .p-xl {{ padding: {Spacing.XL} !important; }}

    /* ============================================================
       Animations
       ============================================================ */

    @keyframes fadeIn {{
        from {{ opacity: 0; transform: translateY(10px); }}
        to {{ opacity: 1; transform: translateY(0); }}
    }}

    @keyframes pulse {{
        0%, 100% {{ opacity: 1; }}
        50% {{ opacity: 0.7; }}
    }}

    @keyframes shimmer {{
        0% {{ background-position: -200% 0; }}
        100% {{ background-position: 200% 0; }}
    }}

    .animate-fadeIn {{
        animation: fadeIn 0.3s ease-out;
    }}

    .animate-pulse {{
        animation: pulse 2s ease-in-out infinite;
    }}

    /* Loading Skeleton */
    .jinni-skeleton {{
        background: linear-gradient(
            90deg,
            {Colors.SURFACE_CONTAINER_LOW} 0%,
            {Colors.SURFACE_CONTAINER} 50%,
            {Colors.SURFACE_CONTAINER_LOW} 100%
        );
        background-size: 200% 100%;
        animation: shimmer 1.5s ease-in-out infinite;
        border-radius: {Radius.DEFAULT};
    }}
    """


# ============================================================
# Helper Functions
# ============================================================

def get_status_color(status: str) -> str:
    """Get color for status"""
    status_colors = {
        "completed": Colors.SECONDARY,
        "processing": Colors.ACTION_BLUE,
        "pending": Colors.ON_SURFACE_VARIANT,
        "failed": Colors.ERROR,
        "ai": Colors.DAWN_ORANGE
    }
    return status_colors.get(status.lower(), Colors.ON_SURFACE_VARIANT)


def get_status_bg(status: str) -> str:
    """Get background color for status badge"""
    status_bgs = {
        "completed": Colors.SECONDARY_CONTAINER,
        "processing": Colors.PRIMARY_FIXED,
        "pending": Colors.SURFACE_CONTAINER,
        "failed": Colors.ERROR_CONTAINER,
        "ai": Colors.TERTIARY_FIXED
    }
    return status_bgs.get(status.lower(), Colors.SURFACE_CONTAINER)
