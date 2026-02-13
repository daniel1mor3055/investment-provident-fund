"""
Custom CSS and formatting utilities for the Gemel Lehashkaa app.

Provides consistent styling and currency/percentage formatting for Israeli Shekels.
"""

# ============================================================================
# Custom CSS
# ============================================================================

CUSTOM_CSS = """
<style>
    /* Main container */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }

    /* Metric cards */
    [data-testid="metric-container"] {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 15px;
        margin: 5px;
    }

    [data-testid="metric-container"] label {
        color: #31333F;
        font-weight: 600;
    }

    /* Positive delta styling */
    [data-testid="stMetricDelta"] svg {
        display: none;
    }

    /* Table styling */
    .dataframe {
        font-size: 14px;
    }

    .dataframe th {
        background-color: #262730;
        color: white;
        padding: 10px;
    }

    .dataframe td {
        padding: 8px;
    }

    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }

    .stTabs [data-baseweb="tab"] {
        padding: 10px 20px;
        border-radius: 4px 4px 0 0;
    }

    /* Sidebar styling */
    section[data-testid="stSidebar"] {
        background-color: #f8f9fa;
    }

    section[data-testid="stSidebar"] .stMarkdown {
        color: #1f1f1f;
    }

    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3 {
        color: #0e1117;
    }

    /* Sidebar input labels */
    section[data-testid="stSidebar"] label {
        color: #0e1117;
        font-weight: 500;
    }

    /* Sidebar number inputs */
    section[data-testid="stSidebar"] input[type="number"] {
        background-color: white;
        color: #0e1117;
        border: 1px solid #d1d5db;
    }

    /* Sidebar sliders */
    section[data-testid="stSidebar"] [data-baseweb="slider"] {
        padding-top: 1rem;
        padding-bottom: 1rem;
    }

    section[data-testid="stSidebar"] [data-baseweb="slider"] [role="slider"] {
        background-color: #ff4b4b;
    }

    /* Sidebar slider track */
    section[data-testid="stSidebar"] [data-baseweb="slider"] [data-testid="stTickBar"] div {
        background-color: #ff4b4b;
    }

    /* Sidebar radio buttons */
    section[data-testid="stSidebar"] [role="radiogroup"] label {
        color: #0e1117;
    }

    /* Expander styling */
    .streamlit-expanderHeader {
        font-weight: 600;
        color: #31333F;
    }

    /* Info boxes */
    .stAlert {
        border-radius: 8px;
    }

    /* Highlight classes */
    .highlight-positive {
        color: #28a745;
        font-weight: bold;
    }

    .highlight-negative {
        color: #dc3545;
        font-weight: bold;
    }

    .highlight-neutral {
        color: #6c757d;
    }
</style>
"""


# ============================================================================
# Formatting Functions
# ============================================================================


def format_currency(value: float, symbol: str = "₪", decimals: int = 0) -> str:
    """
    Format a number as Israeli Shekels (NIS).

    Args:
        value: The number to format
        symbol: Currency symbol (default: ₪)
        decimals: Number of decimal places (default: 0)

    Returns:
        Formatted currency string (e.g., "₪1,234,567")
    """
    if decimals == 0:
        return f"{symbol}{value:,.0f}"
    else:
        return f"{symbol}{value:,.{decimals}f}"


def format_percentage(value: float, decimals: int = 2) -> str:
    """
    Format a decimal as a percentage.

    Args:
        value: The decimal to format (e.g., 0.05 for 5%)
        decimals: Number of decimal places (default: 2)

    Returns:
        Formatted percentage string (e.g., "5.00%")
    """
    return f"{value * 100:.{decimals}f}%"


def format_years(years: int) -> str:
    """
    Format years with proper singular/plural.

    Args:
        years: Number of years

    Returns:
        Formatted string (e.g., "1 year" or "5 years")
    """
    return f"{years} year{'s' if years != 1 else ''}"


def format_delta(value: float, as_percentage: bool = False) -> str:
    """
    Format a delta value with +/- sign.

    Args:
        value: The delta value
        as_percentage: Whether to format as percentage

    Returns:
        Formatted delta string (e.g., "+₪50,000" or "-2.5%")
    """
    sign = "+" if value >= 0 else ""
    if as_percentage:
        return f"{sign}{format_percentage(value)}"
    else:
        return f"{sign}{format_currency(value)}"


def get_color_for_value(value: float, threshold: float = 0) -> str:
    """
    Get a color based on whether value is positive or negative.

    Args:
        value: The value to check
        threshold: Threshold for positive/negative (default: 0)

    Returns:
        Color string for use in Plotly/CSS
    """
    if value > threshold:
        return "#28a745"  # Green
    elif value < threshold:
        return "#dc3545"  # Red
    else:
        return "#6c757d"  # Gray


# ============================================================================
# Table Styling
# ============================================================================


def style_dataframe(df, currency_columns: list[str] = None, percentage_columns: list[str] = None):
    """
    Apply formatting to a pandas DataFrame for display.

    Args:
        df: DataFrame to style
        currency_columns: Columns to format as currency
        percentage_columns: Columns to format as percentage

    Returns:
        Styled DataFrame
    """
    styled = df.copy()

    if currency_columns:
        for col in currency_columns:
            if col in styled.columns:
                styled[col] = styled[col].apply(lambda x: format_currency(x))

    if percentage_columns:
        for col in percentage_columns:
            if col in styled.columns:
                styled[col] = styled[col].apply(lambda x: format_percentage(x))

    return styled


# ============================================================================
# Color Scales
# ============================================================================

# Plotly color scales for heatmaps
HEATMAP_COLORSCALE = [
    [0.0, "#d73027"],    # Red (low/bad)
    [0.25, "#fc8d59"],   # Orange
    [0.5, "#fee08b"],    # Yellow
    [0.75, "#91cf60"],   # Light green
    [1.0, "#1a9850"],    # Green (high/good)
]

# Alternative blue scale for neutral metrics
HEATMAP_BLUE_SCALE = [
    [0.0, "#f7fbff"],    # Very light blue
    [0.25, "#c6dbef"],   # Light blue
    [0.5, "#6baed6"],    # Medium blue
    [0.75, "#2171b5"],   # Dark blue
    [1.0, "#084594"],    # Very dark blue
]

# Diverging scale for comparisons
COMPARISON_COLORSCALE = [
    [0.0, "#d73027"],    # Red (worse)
    [0.5, "#ffffbf"],    # Yellow (neutral)
    [1.0, "#1a9850"],    # Green (better)
]
