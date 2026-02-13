"""Visualization components using Plotly for Provident Fund comparison."""

import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from typing import Optional

from ..models import ComparisonSummary, YearlyResult, AgeComparisonResult, MonthlyWithdrawalResult
from ..calculator import (
    generate_sensitivity_analysis,
    calculate_tax_comparison,
)


# Color palette
PROVIDENT_COLOR = "#38ef7d"  # Green
PERSONAL_COLOR = "#ff6a00"  # Orange
CROSSOVER_COLOR = "#8E54E9"  # Purple
TAX_COLOR = "#dc3545"  # Red


def create_age_crossover_chart(summary: ComparisonSummary) -> go.Figure:
    """
    Create a chart showing net value at retirement for each starting age.

    X-axis: Starting age
    Y-axis: Net value at retirement
    Two lines: Provident Fund vs Personal Account
    Highlights crossover point if exists.

    Args:
        summary: ComparisonSummary from run_full_comparison

    Returns:
        Plotly Figure object
    """
    ages = [r.starting_age for r in summary.age_results]
    provident_nets = [r.provident_net for r in summary.age_results]
    personal_nets = [r.personal_net for r in summary.age_results]

    fig = go.Figure()

    # Provident Fund line
    fig.add_trace(
        go.Scatter(
            x=ages,
            y=provident_nets,
            mode="lines+markers",
            name="Provident Fund",
            line=dict(color=PROVIDENT_COLOR, width=3),
            marker=dict(size=6),
            hovertemplate="Start Age: %{x}<br>Net Value: ₪%{y:,.0f}<extra>Provident Fund</extra>",
        )
    )

    # Personal Account line
    fig.add_trace(
        go.Scatter(
            x=ages,
            y=personal_nets,
            mode="lines+markers",
            name="Personal Account",
            line=dict(color=PERSONAL_COLOR, width=3),
            marker=dict(size=6),
            hovertemplate="Start Age: %{x}<br>Net Value: ₪%{y:,.0f}<extra>Personal Account</extra>",
        )
    )

    # Mark crossover point if it exists
    if summary.crossover_age:
        # Find the result for crossover age
        crossover_result = None
        for r in summary.age_results:
            if r.starting_age == summary.crossover_age:
                crossover_result = r
                break
        
        if crossover_result:
            fig.add_trace(
                go.Scatter(
                    x=[summary.crossover_age],
                    y=[crossover_result.provident_net],
                    mode="markers+text",
                    name="Crossover Point",
                    marker=dict(color=CROSSOVER_COLOR, size=15, symbol="star"),
                    text=[f"Age {summary.crossover_age}"],
                    textposition="top center",
                    hovertemplate=f"Crossover Age: {summary.crossover_age}<br>Value: ₪%{{y:,.0f}}<extra></extra>",
                )
            )

    # Add vertical line at user's current age
    fig.add_vline(
        x=summary.inputs.current_age,
        line_dash="dash",
        line_color="gray",
        annotation_text=f"Your Age ({summary.inputs.current_age})",
        annotation_position="top",
    )

    fig.update_layout(
        title=f"Net Value at Age {summary.inputs.retirement_age} by Starting Age",
        xaxis_title="Starting Age",
        yaxis_title="Net Value at Retirement (₪)",
        hovermode="x unified",
        legend=dict(yanchor="top", y=0.99, xanchor="right", x=0.99),
        template="plotly_white",
        height=500,
    )

    fig.update_yaxes(tickformat=",")
    fig.update_xaxes(dtick=5)

    return fig


def create_difference_by_age_chart(summary: ComparisonSummary) -> go.Figure:
    """
    Create a bar chart showing the difference (Provident - Personal) by starting age.

    Positive = Provident wins, Negative = Personal wins

    Args:
        summary: ComparisonSummary from run_full_comparison

    Returns:
        Plotly Figure object
    """
    ages = [r.starting_age for r in summary.age_results]
    differences = [r.difference for r in summary.age_results]
    colors = [PROVIDENT_COLOR if d > 0 else PERSONAL_COLOR for d in differences]

    fig = go.Figure(
        go.Bar(
            x=ages,
            y=differences,
            marker_color=colors,
            hovertemplate="Start Age: %{x}<br>Difference: ₪%{y:,.0f}<extra></extra>",
        )
    )

    # Add zero line
    fig.add_hline(y=0, line_dash="dash", line_color="gray")

    # Mark crossover point
    if summary.crossover_age:
        fig.add_vline(
            x=summary.crossover_age,
            line_dash="dot",
            line_color=CROSSOVER_COLOR,
            annotation_text=f"Crossover (Age {summary.crossover_age})",
            annotation_position="top",
        )

    fig.update_layout(
        title="Advantage by Starting Age (Provident - Personal)",
        xaxis_title="Starting Age",
        yaxis_title="Difference (₪)",
        template="plotly_white",
        height=400,
        showlegend=False,
    )

    # Add annotation
    fig.add_annotation(
        x=0.5,
        y=1.05,
        xref="paper",
        yref="paper",
        text="Green = Provident Wins | Orange = Personal Wins",
        showarrow=False,
        font=dict(size=12),
    )

    fig.update_xaxes(dtick=5)

    return fig


def create_growth_comparison_chart(yearly_results: list[YearlyResult]) -> go.Figure:
    """
    Create a line chart comparing growth trajectories over time.

    Args:
        yearly_results: List of YearlyResult from generate_yearly_growth

    Returns:
        Plotly Figure object
    """
    if not yearly_results:
        # Return empty figure
        fig = go.Figure()
        fig.add_annotation(
            text="No data to display",
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            showarrow=False,
        )
        return fig

    years = [yr.year for yr in yearly_results]
    ages = [yr.age for yr in yearly_results]
    provident_values = [yr.provident_fv for yr in yearly_results]
    personal_values = [yr.personal_fv for yr in yearly_results]

    fig = go.Figure()

    # Provident Fund line
    fig.add_trace(
        go.Scatter(
            x=years,
            y=provident_values,
            mode="lines+markers",
            name="Provident Fund (Gross)",
            line=dict(color=PROVIDENT_COLOR, width=3),
            marker=dict(size=6),
            customdata=ages,
            hovertemplate="Year %{x} (Age %{customdata})<br>Value: ₪%{y:,.0f}<extra>Provident</extra>",
        )
    )

    # Personal Account line
    fig.add_trace(
        go.Scatter(
            x=years,
            y=personal_values,
            mode="lines+markers",
            name="Personal Account (Gross)",
            line=dict(color=PERSONAL_COLOR, width=3),
            marker=dict(size=6),
            customdata=ages,
            hovertemplate="Year %{x} (Age %{customdata})<br>Value: ₪%{y:,.0f}<extra>Personal</extra>",
        )
    )

    fig.update_layout(
        title="Investment Growth Over Time (Gross Values)",
        xaxis_title="Years Invested",
        yaxis_title="Value (₪)",
        hovermode="x unified",
        legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01),
        template="plotly_white",
        height=450,
    )

    fig.update_yaxes(tickformat=",")

    return fig


def create_tax_comparison_chart(tax_data: dict) -> go.Figure:
    """
    Create a bar chart comparing tax impact between options.

    Args:
        tax_data: Dictionary from calculate_tax_comparison

    Returns:
        Plotly Figure object
    """
    categories = ["Provident Fund", "Personal Account"]
    
    contributions = [
        tax_data["provident"]["contributions"],
        tax_data["personal"]["contributions"],
    ]
    gains = [
        tax_data["provident"]["nominal_gain"],
        tax_data["personal"]["nominal_gain"],
    ]
    taxes = [
        tax_data["provident"]["tax"],
        tax_data["personal"]["tax"],
    ]

    fig = go.Figure()

    # Contributions (base)
    fig.add_trace(
        go.Bar(
            name="Contributions",
            x=categories,
            y=contributions,
            marker_color="#3498db",
            hovertemplate="%{x}<br>Contributions: ₪%{y:,.0f}<extra></extra>",
        )
    )

    # Net Gains (after tax)
    net_gains = [g - t for g, t in zip(gains, taxes)]
    fig.add_trace(
        go.Bar(
            name="Net Gains (After Tax)",
            x=categories,
            y=net_gains,
            marker_color="#2ecc71",
            hovertemplate="%{x}<br>Net Gains: ₪%{y:,.0f}<extra></extra>",
        )
    )

    # Tax
    fig.add_trace(
        go.Bar(
            name="Tax Paid",
            x=categories,
            y=taxes,
            marker_color=TAX_COLOR,
            hovertemplate="%{x}<br>Tax: ₪%{y:,.0f}<extra></extra>",
        )
    )

    fig.update_layout(
        title="Breakdown: Contributions, Gains, and Tax",
        barmode="stack",
        yaxis_title="Amount (₪)",
        template="plotly_white",
        height=450,
        legend=dict(yanchor="top", y=0.99, xanchor="right", x=0.99),
    )

    fig.update_yaxes(tickformat=",")

    return fig


def create_tax_savings_chart(tax_data: dict) -> go.Figure:
    """
    Create a waterfall chart showing tax savings with Provident Fund.

    Args:
        tax_data: Dictionary from calculate_tax_comparison

    Returns:
        Plotly Figure object
    """
    provident_tax = tax_data["provident"]["tax"]
    personal_tax = tax_data["personal"]["tax"]
    savings = personal_tax - provident_tax

    fig = go.Figure(
        go.Waterfall(
            orientation="v",
            measure=["absolute", "relative", "total"],
            x=["Personal Account Tax", "Tax Savings", "Provident Fund Tax"],
            y=[personal_tax, -savings, 0],
            text=[
                f"₪{personal_tax:,.0f}",
                f"-₪{savings:,.0f}",
                f"₪{provident_tax:,.0f}",
            ],
            textposition="outside",
            connector={"line": {"color": "rgb(63, 63, 63)"}},
            decreasing={"marker": {"color": "#2ecc71"}},
            increasing={"marker": {"color": TAX_COLOR}},
            totals={"marker": {"color": PROVIDENT_COLOR}},
        )
    )

    fig.update_layout(
        title="Tax Savings with Provident Fund",
        yaxis_title="Tax Amount (₪)",
        template="plotly_white",
        height=400,
        showlegend=False,
    )

    fig.update_yaxes(tickformat=",")

    return fig


def create_sensitivity_heatmap(
    summary: ComparisonSummary,
    return_rates: Optional[list[float]] = None,
    inflation_rates: Optional[list[float]] = None,
) -> go.Figure:
    """
    Create a heatmap showing crossover age for different parameter combinations.

    Args:
        summary: ComparisonSummary with base inputs
        return_rates: List of return rates to test
        inflation_rates: List of inflation rates to test

    Returns:
        Plotly Figure object
    """
    if return_rates is None:
        return_rates = [0.04, 0.05, 0.06, 0.07, 0.08, 0.09, 0.10]
    
    if inflation_rates is None:
        inflation_rates = [0.01, 0.02, 0.025, 0.03, 0.04]

    # Generate sensitivity data
    sensitivity_data = generate_sensitivity_analysis(
        summary.inputs, return_rates, inflation_rates
    )

    # Build matrix
    matrix = []
    for ret in return_rates:
        row = []
        for inf in inflation_rates:
            # Find matching point
            for point in sensitivity_data:
                if point.return_rate == ret and point.inflation_rate == inf:
                    row.append(point.crossover_age if point.crossover_age else 60)
                    break
        matrix.append(row)

    # Create heatmap
    fig = go.Figure(
        go.Heatmap(
            z=matrix,
            x=[f"{inf*100:.1f}%" for inf in inflation_rates],
            y=[f"{ret*100:.0f}%" for ret in return_rates],
            colorscale="RdYlGn",  # Green = low age (good), Red = high age
            colorbar=dict(title="Crossover Age"),
            hovertemplate="Return: %{y}<br>Inflation: %{x}<br>Crossover Age: %{z}<extra></extra>",
        )
    )

    # Add text annotations
    for i, ret in enumerate(return_rates):
        for j, inf in enumerate(inflation_rates):
            val = matrix[i][j]
            text = str(val) if val < 60 else "Never"
            fig.add_annotation(
                x=j,
                y=i,
                text=text,
                showarrow=False,
                font=dict(color="white" if val > 40 else "black", size=11),
            )

    fig.update_layout(
        title=f"Crossover Age Sensitivity (Withdrawal: {summary.inputs.withdrawal_mode.replace('_', ' ').title()})",
        xaxis_title="Inflation Rate",
        yaxis_title="Expected Return",
        template="plotly_white",
        height=450,
    )

    return fig


def create_advantage_heatmap(
    summary: ComparisonSummary,
    return_rates: Optional[list[float]] = None,
    inflation_rates: Optional[list[float]] = None,
) -> go.Figure:
    """
    Create a heatmap showing Provident Fund advantage for different parameters.

    Args:
        summary: ComparisonSummary with base inputs
        return_rates: List of return rates to test
        inflation_rates: List of inflation rates to test

    Returns:
        Plotly Figure object
    """
    if return_rates is None:
        return_rates = [0.04, 0.05, 0.06, 0.07, 0.08, 0.09, 0.10]
    
    if inflation_rates is None:
        inflation_rates = [0.01, 0.02, 0.025, 0.03, 0.04]

    # Generate sensitivity data
    sensitivity_data = generate_sensitivity_analysis(
        summary.inputs, return_rates, inflation_rates
    )

    # Build matrix of advantages at age 30
    matrix = []
    for ret in return_rates:
        row = []
        for inf in inflation_rates:
            for point in sensitivity_data:
                if point.return_rate == ret and point.inflation_rate == inf:
                    row.append(point.provident_advantage_at_30)
                    break
        matrix.append(row)

    # Create heatmap
    fig = go.Figure(
        go.Heatmap(
            z=matrix,
            x=[f"{inf*100:.1f}%" for inf in inflation_rates],
            y=[f"{ret*100:.0f}%" for ret in return_rates],
            colorscale="RdYlGn",
            colorbar=dict(title="Advantage (₪)"),
            hovertemplate="Return: %{y}<br>Inflation: %{x}<br>Advantage: ₪%{z:,.0f}<extra></extra>",
        )
    )

    fig.update_layout(
        title="Provident Fund Advantage if Starting at Age 30",
        xaxis_title="Inflation Rate",
        yaxis_title="Expected Return",
        template="plotly_white",
        height=450,
    )

    return fig


def create_monthly_withdrawal_chart(
    withdrawal_result: MonthlyWithdrawalResult,
) -> go.Figure:
    """
    Create a bar chart comparing monthly withdrawals from both account types.
    
    Shows gross vs net monthly withdrawal for personal account to highlight
    the tax impact.
    
    Args:
        withdrawal_result: MonthlyWithdrawalResult from calculate_monthly_withdrawal_comparison
        
    Returns:
        Plotly Figure object
    """
    fig = go.Figure()
    
    # Provident Fund - Net monthly (same as gross for annuity)
    fig.add_trace(
        go.Bar(
            name="Provident Fund (0% Tax)",
            x=["Provident Fund"],
            y=[withdrawal_result.provident_net_monthly],
            marker_color=PROVIDENT_COLOR,
            text=[f"₪{withdrawal_result.provident_net_monthly:,.0f}"],
            textposition="outside",
            hovertemplate="Provident Fund<br>Net Monthly: ₪%{y:,.0f}<br>Tax: 0%<extra></extra>",
        )
    )
    
    # Personal Account - Show stacked: Net + Tax
    fig.add_trace(
        go.Bar(
            name="Personal Account (Net)",
            x=["Personal Account"],
            y=[withdrawal_result.personal_net_monthly],
            marker_color=PERSONAL_COLOR,
            text=[f"₪{withdrawal_result.personal_net_monthly:,.0f}"],
            textposition="inside",
            hovertemplate="Personal Account<br>Net Monthly: ₪%{y:,.0f}<extra></extra>",
        )
    )
    
    # Personal Account Tax portion
    fig.add_trace(
        go.Bar(
            name="Tax on Personal Account",
            x=["Personal Account"],
            y=[withdrawal_result.personal_tax_per_month],
            marker_color=TAX_COLOR,
            text=[f"Tax: ₪{withdrawal_result.personal_tax_per_month:,.0f}"],
            textposition="inside",
            hovertemplate="Personal Account<br>Monthly Tax: ₪%{y:,.0f}<extra></extra>",
        )
    )
    
    fig.update_layout(
        title="Monthly Withdrawal Comparison (קצבה)",
        yaxis_title="Monthly Amount (₪)",
        barmode="stack",
        template="plotly_white",
        height=400,
        showlegend=True,
        legend=dict(yanchor="top", y=0.99, xanchor="right", x=0.99),
    )
    
    fig.update_yaxes(tickformat=",")
    
    # Add annotation showing the difference
    difference = withdrawal_result.monthly_difference
    if difference > 0:
        annotation_text = f"Provident Fund advantage: ₪{difference:,.0f}/month"
    else:
        annotation_text = f"Personal Account advantage: ₪{-difference:,.0f}/month"
    
    fig.add_annotation(
        x=0.5,
        y=-0.15,
        xref="paper",
        yref="paper",
        text=annotation_text,
        showarrow=False,
        font=dict(size=14, color=PROVIDENT_COLOR if difference > 0 else PERSONAL_COLOR),
    )
    
    return fig


def create_monthly_withdrawal_breakdown_chart(
    withdrawal_result: MonthlyWithdrawalResult,
) -> go.Figure:
    """
    Create a detailed breakdown chart showing the components of each withdrawal.
    
    Args:
        withdrawal_result: MonthlyWithdrawalResult from calculate_monthly_withdrawal_comparison
        
    Returns:
        Plotly Figure object
    """
    categories = ["Provident Fund", "Personal Account"]
    
    # Calculate principal portion per month for each
    if withdrawal_result.provident_balance > 0:
        provident_principal_ratio = withdrawal_result.provident_contributions / withdrawal_result.provident_balance
    else:
        provident_principal_ratio = 0
    
    if withdrawal_result.personal_balance > 0:
        personal_principal_ratio = withdrawal_result.personal_contributions / withdrawal_result.personal_balance
    else:
        personal_principal_ratio = 0
    
    provident_principal_monthly = withdrawal_result.provident_gross_monthly * provident_principal_ratio
    provident_gains_monthly = withdrawal_result.provident_gross_monthly - provident_principal_monthly
    
    personal_principal_monthly = withdrawal_result.personal_gross_monthly * personal_principal_ratio
    personal_gains_monthly = withdrawal_result.personal_gross_monthly - personal_principal_monthly
    personal_gains_after_tax = personal_gains_monthly - withdrawal_result.personal_tax_per_month
    
    fig = go.Figure()
    
    # Principal portion (tax-free in both)
    fig.add_trace(
        go.Bar(
            name="Principal (Tax-Free)",
            x=categories,
            y=[provident_principal_monthly, personal_principal_monthly],
            marker_color="#3498db",
            hovertemplate="%{x}<br>Principal: ₪%{y:,.0f}/month<extra></extra>",
        )
    )
    
    # Gains portion (tax-free for provident, taxed for personal)
    fig.add_trace(
        go.Bar(
            name="Gains (Net)",
            x=categories,
            y=[provident_gains_monthly, personal_gains_after_tax],
            marker_color="#2ecc71",
            hovertemplate="%{x}<br>Net Gains: ₪%{y:,.0f}/month<extra></extra>",
        )
    )
    
    # Tax (only for personal)
    fig.add_trace(
        go.Bar(
            name="Tax (25% on Gains)",
            x=categories,
            y=[0, withdrawal_result.personal_tax_per_month],
            marker_color=TAX_COLOR,
            hovertemplate="%{x}<br>Tax: ₪%{y:,.0f}/month<extra></extra>",
        )
    )
    
    fig.update_layout(
        title="Monthly Withdrawal Breakdown",
        yaxis_title="Amount per Month (₪)",
        barmode="stack",
        template="plotly_white",
        height=400,
        legend=dict(yanchor="top", y=0.99, xanchor="right", x=0.99),
    )
    
    fig.update_yaxes(tickformat=",")
    
    return fig


def create_withdrawal_mode_comparison(
    summary_lump: ComparisonSummary,
    summary_annuity: ComparisonSummary,
) -> go.Figure:
    """
    Create a chart comparing lump sum vs annuity withdrawal modes.

    Args:
        summary_lump: ComparisonSummary with lump_sum withdrawal
        summary_annuity: ComparisonSummary with annuity withdrawal

    Returns:
        Plotly Figure object
    """
    ages = [r.starting_age for r in summary_annuity.age_results]
    
    annuity_diffs = [r.difference for r in summary_annuity.age_results]
    lump_diffs = [r.difference for r in summary_lump.age_results]

    fig = go.Figure()

    # Annuity mode differences
    fig.add_trace(
        go.Scatter(
            x=ages,
            y=annuity_diffs,
            mode="lines+markers",
            name="Annuity (0% Tax after 60)",
            line=dict(color=PROVIDENT_COLOR, width=3),
            marker=dict(size=6),
            hovertemplate="Start Age: %{x}<br>Advantage: ₪%{y:,.0f}<extra>Annuity</extra>",
        )
    )

    # Lump sum mode differences
    fig.add_trace(
        go.Scatter(
            x=ages,
            y=lump_diffs,
            mode="lines+markers",
            name="Lump Sum (25% Real Gains Tax)",
            line=dict(color=PERSONAL_COLOR, width=3, dash="dash"),
            marker=dict(size=6),
            hovertemplate="Start Age: %{x}<br>Advantage: ₪%{y:,.0f}<extra>Lump Sum</extra>",
        )
    )

    # Add zero line
    fig.add_hline(y=0, line_dash="dash", line_color="gray")

    fig.update_layout(
        title="Provident Fund Advantage: Annuity vs Lump Sum Withdrawal",
        xaxis_title="Starting Age",
        yaxis_title="Provident Fund Advantage (₪)",
        hovermode="x unified",
        legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01),
        template="plotly_white",
        height=450,
    )

    fig.update_yaxes(tickformat=",")
    fig.update_xaxes(dtick=5)

    # Add annotation
    fig.add_annotation(
        x=0.5,
        y=-0.12,
        xref="paper",
        yref="paper",
        text="Above zero = Provident Fund wins | Below zero = Personal Account wins",
        showarrow=False,
        font=dict(size=11),
    )

    return fig
