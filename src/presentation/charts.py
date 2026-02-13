"""
Plotly visualizations for Gemel Lehashkaa analysis.

This module provides interactive charts for:
- Balance growth over time
- Start age comparisons
- Withdrawal mode comparisons
- Fee impact analysis
- Sensitivity heatmaps
"""

import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd

from ..models import SimulationResult, ComparisonResult
from .styles import (
    format_currency,
    format_percentage,
    HEATMAP_COLORSCALE,
    HEATMAP_BLUE_SCALE,
)


# ============================================================================
# Growth Charts
# ============================================================================


def create_growth_chart(result: SimulationResult) -> go.Figure:
    """
    Create a line chart showing balance growth over time.

    Args:
        result: SimulationResult from simulation

    Returns:
        Plotly Figure with balance growth chart
    """
    # Prepare data from yearly results
    years = [yr.year for yr in result.yearly_results]
    ages = [yr.age for yr in result.yearly_results]
    balances = [yr.balance for yr in result.yearly_results]
    contributions = [yr.cumulative_contributions for yr in result.yearly_results]

    fig = go.Figure()

    # Balance line
    fig.add_trace(
        go.Scatter(
            x=ages,
            y=balances,
            mode="lines+markers",
            name="Balance",
            line=dict(color="#2E86AB", width=3),
            marker=dict(size=6),
            hovertemplate="Age %{x}<br>Balance: ₪%{y:,.0f}<extra></extra>",
        )
    )

    # Contributions line
    fig.add_trace(
        go.Scatter(
            x=ages,
            y=contributions,
            mode="lines",
            name="Total Contributions",
            line=dict(color="#A23B72", width=2, dash="dash"),
            hovertemplate="Age %{x}<br>Contributions: ₪%{y:,.0f}<extra></extra>",
        )
    )

    # Add age 60 marker if applicable
    if result.inputs.withdraw_age >= 60:
        fig.add_vline(
            x=60,
            line_dash="dot",
            line_color="green",
            annotation_text="Tax-Free Annuity Eligible",
            annotation_position="top",
        )

    fig.update_layout(
        title="Investment Growth Over Time",
        xaxis_title="Age",
        yaxis_title="Amount (₪)",
        yaxis_tickformat=",",
        hovermode="x unified",
        legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01),
        template="plotly_white",
    )

    return fig


def create_growth_area_chart(result: SimulationResult) -> go.Figure:
    """
    Create a stacked area chart showing contributions vs growth.

    Args:
        result: SimulationResult from simulation

    Returns:
        Plotly Figure with stacked area chart
    """
    years = [yr.year for yr in result.yearly_results]
    ages = [yr.age for yr in result.yearly_results]
    contributions = [yr.cumulative_contributions for yr in result.yearly_results]
    gains = [yr.balance - yr.cumulative_contributions for yr in result.yearly_results]

    fig = go.Figure()

    # Contributions (bottom layer)
    fig.add_trace(
        go.Scatter(
            x=ages,
            y=contributions,
            fill="tozeroy",
            name="Contributions",
            line=dict(color="#A23B72"),
            fillcolor="rgba(162, 59, 114, 0.5)",
            hovertemplate="Age %{x}<br>Contributions: ₪%{y:,.0f}<extra></extra>",
        )
    )

    # Investment gains (top layer)
    balances = [c + g for c, g in zip(contributions, gains)]
    fig.add_trace(
        go.Scatter(
            x=ages,
            y=balances,
            fill="tonexty",
            name="Investment Gains",
            line=dict(color="#2E86AB"),
            fillcolor="rgba(46, 134, 171, 0.5)",
            hovertemplate="Age %{x}<br>Total: ₪%{y:,.0f}<extra></extra>",
        )
    )

    fig.update_layout(
        title="Contributions vs Investment Gains",
        xaxis_title="Age",
        yaxis_title="Amount (₪)",
        yaxis_tickformat=",",
        hovermode="x unified",
        legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01),
        template="plotly_white",
    )

    return fig


# ============================================================================
# Comparison Charts
# ============================================================================


def create_start_age_comparison_chart(comparison: ComparisonResult) -> go.Figure:
    """
    Create a multi-line chart comparing different starting ages.

    Args:
        comparison: ComparisonResult with multiple scenarios

    Returns:
        Plotly Figure with comparison chart
    """
    fig = go.Figure()

    colors = ["#2E86AB", "#A23B72", "#F18F01", "#C73E1D", "#3B1F2B"]

    for i, (name, result) in enumerate(comparison.scenarios.items()):
        ages = [yr.age for yr in result.yearly_results]
        balances = [yr.balance for yr in result.yearly_results]

        color = colors[i % len(colors)]

        fig.add_trace(
            go.Scatter(
                x=ages,
                y=balances,
                mode="lines+markers",
                name=name,
                line=dict(color=color, width=2),
                marker=dict(size=5),
                hovertemplate=f"{name}<br>Age %{{x}}<br>Balance: ₪%{{y:,.0f}}<extra></extra>",
            )
        )

    fig.update_layout(
        title="Balance Comparison by Starting Age",
        xaxis_title="Age",
        yaxis_title="Balance (₪)",
        yaxis_tickformat=",",
        hovermode="x unified",
        legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01),
        template="plotly_white",
    )

    return fig


def create_start_age_bar_chart(comparison: ComparisonResult) -> go.Figure:
    """
    Create a bar chart comparing final balances for different starting ages.

    Args:
        comparison: ComparisonResult with multiple scenarios

    Returns:
        Plotly Figure with bar chart
    """
    names = list(comparison.scenarios.keys())
    gross_balances = [r.gross_balance for r in comparison.scenarios.values()]
    net_balances = [r.net_balance for r in comparison.scenarios.values()]
    contributions = [r.total_contributions for r in comparison.scenarios.values()]

    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            x=names,
            y=contributions,
            name="Total Contributions",
            marker_color="#A23B72",
            hovertemplate="%{x}<br>Contributions: ₪%{y:,.0f}<extra></extra>",
        )
    )

    fig.add_trace(
        go.Bar(
            x=names,
            y=net_balances,
            name="Net Balance (After Tax)",
            marker_color="#2E86AB",
            hovertemplate="%{x}<br>Net Balance: ₪%{y:,.0f}<extra></extra>",
        )
    )

    fig.update_layout(
        title="Final Balance Comparison by Starting Age",
        xaxis_title="Starting Age",
        yaxis_title="Amount (₪)",
        yaxis_tickformat=",",
        barmode="group",
        legend=dict(yanchor="top", y=0.99, xanchor="right", x=0.99),
        template="plotly_white",
    )

    return fig


def create_withdrawal_mode_chart(
    lump_result: SimulationResult, annuity_result: SimulationResult
) -> go.Figure:
    """
    Create a comparison chart for lump sum vs annuity withdrawal modes.

    Args:
        lump_result: SimulationResult for lump sum withdrawal
        annuity_result: SimulationResult for annuity withdrawal

    Returns:
        Plotly Figure with side-by-side bar chart
    """
    categories = ["Gross Balance", "Tax", "Net Balance"]

    lump_values = [
        lump_result.gross_balance,
        lump_result.tax_amount,
        lump_result.net_balance,
    ]

    annuity_values = [
        annuity_result.gross_balance,
        annuity_result.tax_amount,
        annuity_result.net_balance,
    ]

    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            x=categories,
            y=lump_values,
            name="Lump Sum (25% Tax)",
            marker_color="#C73E1D",
            hovertemplate="%{x}: ₪%{y:,.0f}<extra></extra>",
        )
    )

    fig.add_trace(
        go.Bar(
            x=categories,
            y=annuity_values,
            name="Annuity (Tax-Free)",
            marker_color="#2E86AB",
            hovertemplate="%{x}: ₪%{y:,.0f}<extra></extra>",
        )
    )

    # Add tax savings annotation
    tax_savings = lump_result.tax_amount - annuity_result.tax_amount
    fig.add_annotation(
        x="Net Balance",
        y=annuity_result.net_balance,
        text=f"Tax Savings: {format_currency(tax_savings)}",
        showarrow=True,
        arrowhead=2,
        arrowcolor="#28a745",
        font=dict(color="#28a745", size=12),
        ax=50,
        ay=-40,
    )

    fig.update_layout(
        title="Lump Sum vs Annuity Comparison",
        xaxis_title="",
        yaxis_title="Amount (₪)",
        yaxis_tickformat=",",
        barmode="group",
        legend=dict(yanchor="top", y=0.99, xanchor="right", x=0.99),
        template="plotly_white",
    )

    return fig


# ============================================================================
# Fee Impact Charts
# ============================================================================


def create_fee_impact_chart(fee_df: pd.DataFrame) -> go.Figure:
    """
    Create a chart showing the impact of different fee levels.

    Args:
        fee_df: DataFrame with fee levels and balances

    Returns:
        Plotly Figure with fee impact chart
    """
    fig = make_subplots(
        rows=1,
        cols=2,
        subplot_titles=("Net Balance by Fee Level", "Cost of Fees"),
        horizontal_spacing=0.12,
    )

    # Net balance by fee
    fig.add_trace(
        go.Bar(
            x=fee_df["AUM Fee %"],
            y=fee_df["Net Balance"],
            name="Net Balance",
            marker_color="#2E86AB",
            hovertemplate="Fee: %{x}<br>Net Balance: ₪%{y:,.0f}<extra></extra>",
        ),
        row=1,
        col=1,
    )

    # Fee cost (difference from lowest fee)
    if "Fee Cost" in fee_df.columns:
        fig.add_trace(
            go.Bar(
                x=fee_df["AUM Fee %"],
                y=fee_df["Fee Cost"],
                name="Fee Drag",
                marker_color="#C73E1D",
                hovertemplate="Fee: %{x}<br>Fee Cost: ₪%{y:,.0f}<extra></extra>",
            ),
            row=1,
            col=2,
        )

    fig.update_layout(
        title="Impact of Management Fees",
        showlegend=False,
        template="plotly_white",
    )

    fig.update_yaxes(tickformat=",", row=1, col=1)
    fig.update_yaxes(tickformat=",", row=1, col=2)

    return fig


def create_fee_comparison_line_chart(
    results: dict[str, SimulationResult]
) -> go.Figure:
    """
    Create a line chart comparing growth under different fee levels.

    Args:
        results: Dict mapping fee level names to SimulationResult

    Returns:
        Plotly Figure with multi-line comparison
    """
    fig = go.Figure()

    colors = ["#28a745", "#ffc107", "#dc3545"]  # Green, Yellow, Red

    for i, (name, result) in enumerate(results.items()):
        ages = [yr.age for yr in result.yearly_results]
        balances = [yr.balance for yr in result.yearly_results]

        color = colors[i % len(colors)]

        fig.add_trace(
            go.Scatter(
                x=ages,
                y=balances,
                mode="lines",
                name=name,
                line=dict(color=color, width=2),
                hovertemplate=f"{name}<br>Age %{{x}}<br>Balance: ₪%{{y:,.0f}}<extra></extra>",
            )
        )

    fig.update_layout(
        title="Balance Growth by Fee Level",
        xaxis_title="Age",
        yaxis_title="Balance (₪)",
        yaxis_tickformat=",",
        hovermode="x unified",
        legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01),
        template="plotly_white",
    )

    return fig


# ============================================================================
# Sensitivity Analysis Charts
# ============================================================================


def create_sensitivity_heatmap(
    matrix_df: pd.DataFrame,
    title: str = "Sensitivity Analysis",
    value_format: str = "currency",
) -> go.Figure:
    """
    Create a heatmap for sensitivity analysis.

    Args:
        matrix_df: DataFrame with sensitivity matrix
        title: Chart title
        value_format: How to format values ("currency" or "percentage")

    Returns:
        Plotly Figure with heatmap
    """
    # Format hover text
    if value_format == "currency":
        text = matrix_df.applymap(lambda x: f"₪{x:,.0f}")
        colorscale = HEATMAP_BLUE_SCALE
    else:
        text = matrix_df.applymap(lambda x: f"{x:.2%}")
        colorscale = HEATMAP_COLORSCALE

    fig = go.Figure(
        data=go.Heatmap(
            z=matrix_df.values,
            x=matrix_df.columns.tolist(),
            y=matrix_df.index.tolist(),
            text=text.values,
            texttemplate="%{text}",
            textfont={"size": 10},
            colorscale=colorscale,
            hovertemplate=(
                f"{matrix_df.columns.name}: %{{x}}<br>"
                f"{matrix_df.index.name}: %{{y}}<br>"
                "Value: %{text}<extra></extra>"
            ),
        )
    )

    fig.update_layout(
        title=title,
        xaxis_title=matrix_df.columns.name,
        yaxis_title=matrix_df.index.name,
        template="plotly_white",
    )

    return fig


def create_return_vs_fee_heatmap(
    base_inputs,
    return_values: list[float],
    fee_values: list[float],
) -> go.Figure:
    """
    Create a heatmap showing net balance for different return/fee combinations.

    Args:
        base_inputs: Base InvestmentInputs
        return_values: List of return rates to test
        fee_values: List of fee rates to test

    Returns:
        Plotly Figure with heatmap
    """
    from ..calculator import generate_sensitivity_matrix

    matrix_df = generate_sensitivity_matrix(
        base_inputs,
        param1_name="expected_return",
        param1_values=return_values,
        param2_name="fee_aum",
        param2_values=fee_values,
        output_metric="net_balance",
    )

    return create_sensitivity_heatmap(
        matrix_df,
        title="Net Balance: Return vs Fee Sensitivity",
        value_format="currency",
    )


# ============================================================================
# Summary Charts
# ============================================================================


def create_summary_metrics_chart(result: SimulationResult) -> go.Figure:
    """
    Create a summary chart with key metrics as indicators.

    Args:
        result: SimulationResult from simulation

    Returns:
        Plotly Figure with indicator gauges
    """
    fig = make_subplots(
        rows=1,
        cols=4,
        specs=[[{"type": "indicator"}] * 4],
        subplot_titles=[
            "Net Balance",
            "Total Contributions",
            "Investment Gains",
            "Tax Paid/Saved",
        ],
    )

    gains = result.gross_balance - result.total_contributions

    # Net Balance
    fig.add_trace(
        go.Indicator(
            mode="number",
            value=result.net_balance,
            number={"prefix": "₪", "valueformat": ",.0f"},
        ),
        row=1,
        col=1,
    )

    # Contributions
    fig.add_trace(
        go.Indicator(
            mode="number",
            value=result.total_contributions,
            number={"prefix": "₪", "valueformat": ",.0f"},
        ),
        row=1,
        col=2,
    )

    # Gains
    fig.add_trace(
        go.Indicator(
            mode="number",
            value=gains,
            number={"prefix": "₪", "valueformat": ",.0f"},
        ),
        row=1,
        col=3,
    )

    # Tax
    tax_label = "Tax Paid" if result.tax_amount > 0 else "Tax Saved"
    tax_value = result.tax_amount if result.tax_amount > 0 else result.tax_savings_from_annuity
    fig.add_trace(
        go.Indicator(
            mode="number",
            value=tax_value,
            number={"prefix": "₪", "valueformat": ",.0f"},
        ),
        row=1,
        col=4,
    )

    fig.update_layout(
        height=200,
        template="plotly_white",
    )

    return fig
