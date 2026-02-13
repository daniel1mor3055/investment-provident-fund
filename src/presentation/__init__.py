"""Presentation layer for the Gemel Lehashkaa analysis app."""

from .inputs import render_sidebar_inputs
from .charts import (
    create_growth_chart,
    create_start_age_comparison_chart,
    create_withdrawal_mode_chart,
    create_fee_impact_chart,
    create_sensitivity_heatmap,
)
from .styles import format_currency, format_percentage, CUSTOM_CSS

__all__ = [
    "render_sidebar_inputs",
    "create_growth_chart",
    "create_start_age_comparison_chart",
    "create_withdrawal_mode_chart",
    "create_fee_impact_chart",
    "create_sensitivity_heatmap",
    "format_currency",
    "format_percentage",
    "CUSTOM_CSS",
]
