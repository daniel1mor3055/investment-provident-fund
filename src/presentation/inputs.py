"""
Streamlit sidebar input widgets for Gemel Lehashkaa analysis.

This module provides the user interface for inputting all simulation parameters.
"""

import streamlit as st

from ..models import (
    InvestmentInputs,
    ANNUAL_CAP_2026,
    MAX_FEE_AUM,
    MAX_FEE_DEPOSIT,
)


def render_sidebar_inputs() -> InvestmentInputs:
    """
    Render the sidebar input widgets and return the collected inputs.

    Returns:
        InvestmentInputs dataclass with all user-specified parameters
    """
    st.sidebar.header("📊 Simulation Parameters")

    # Age Settings
    st.sidebar.subheader("Age Settings")

    start_age = st.sidebar.slider(
        "Start Age",
        min_value=18,
        max_value=59,
        value=30,
        step=1,
        help="Age when you start contributing to the fund",
    )

    withdraw_age = st.sidebar.slider(
        "Withdrawal Age",
        min_value=start_age + 1,
        max_value=75,
        value=60,
        step=1,
        help="Age when you plan to withdraw (60+ for tax-free annuity)",
    )

    # Contribution Settings
    st.sidebar.subheader("Contributions")

    monthly_contribution = st.sidebar.number_input(
        "Monthly Contribution (₪)",
        min_value=0.0,
        max_value=10000.0,
        value=6970.0,  # ~83,641 / 12
        step=100.0,
        help="Amount to contribute each month",
    )

    annual_cap = st.sidebar.number_input(
        "Annual Cap (₪)",
        min_value=0.0,
        max_value=200000.0,
        value=float(ANNUAL_CAP_2026),
        step=1000.0,
        help=f"Annual contribution limit (2026 cap: ₪{ANNUAL_CAP_2026:,.0f})",
    )

    # Returns & Fees
    st.sidebar.subheader("Returns & Fees")

    expected_return = st.sidebar.slider(
        "Expected Annual Return (%)",
        min_value=0.0,
        max_value=15.0,
        value=5.0,
        step=0.5,
        help="Expected nominal annual return before fees",
    ) / 100

    fee_aum = st.sidebar.slider(
        "AUM Fee (%)",
        min_value=0.0,
        max_value=MAX_FEE_AUM * 100,
        value=0.65,
        step=0.05,
        help=f"Annual fee on assets (legal cap: {MAX_FEE_AUM:.2%})",
    ) / 100

    show_advanced = st.sidebar.checkbox("Show Advanced Options", value=False)

    if show_advanced:
        fee_deposit = st.sidebar.slider(
            "Deposit Fee (%)",
            min_value=0.0,
            max_value=MAX_FEE_DEPOSIT * 100,
            value=0.0,
            step=0.1,
            help=f"Fee on contributions (legal cap: {MAX_FEE_DEPOSIT:.2%})",
        ) / 100
    else:
        fee_deposit = 0.0

    # Inflation
    st.sidebar.subheader("Inflation")

    inflation = st.sidebar.slider(
        "Expected Inflation (%)",
        min_value=0.0,
        max_value=10.0,
        value=2.5,
        step=0.1,
        help="Expected annual inflation rate (for real gain tax calculation)",
    ) / 100

    # Withdrawal Mode
    st.sidebar.subheader("Withdrawal Mode")

    withdrawal_mode = st.sidebar.radio(
        "How will you withdraw?",
        options=["annuity", "lump"],
        format_func=lambda x: "Annuity (Tax-Free after 60)" if x == "annuity" else "Lump Sum (25% Tax on Real Gains)",
        help="Annuity conversion after age 60 is tax-free",
    )

    # Fee warnings
    inputs = InvestmentInputs(
        start_age=start_age,
        withdraw_age=withdraw_age,
        monthly_contribution=monthly_contribution,
        annual_cap=annual_cap,
        expected_return=expected_return,
        fee_aum=fee_aum,
        fee_deposit=fee_deposit,
        inflation=inflation,
        withdrawal_mode=withdrawal_mode,
    )

    warnings = inputs.validate_fees()
    for warning in warnings:
        st.sidebar.warning(f"⚠️ {warning}")

    # Show summary
    st.sidebar.divider()
    st.sidebar.subheader("Summary")

    years = inputs.years_of_contribution
    max_yearly = monthly_contribution * 12
    actual_yearly = min(max_yearly, annual_cap)

    st.sidebar.markdown(f"""
    - **Duration**: {years} years
    - **Yearly Target**: ₪{max_yearly:,.0f}
    - **Effective Yearly** (after cap): ₪{actual_yearly:,.0f}
    - **Net Return**: {inputs.get_net_return():.2%}
    - **Tax-Free Eligible**: {'✅ Yes' if inputs.is_annuity_eligible() else '❌ No (age < 60)'}
    """)

    return inputs


def render_comparison_sidebar() -> dict:
    """
    Render sidebar inputs for comparison mode.

    Returns:
        Dict with comparison parameters
    """
    st.sidebar.header("📊 Comparison Settings")

    compare_ages = st.sidebar.multiselect(
        "Starting Ages to Compare",
        options=[25, 30, 35, 40, 45, 50, 55, 59],
        default=[30, 40, 50, 59],
        help="Select multiple starting ages for comparison",
    )

    compare_fees = st.sidebar.multiselect(
        "Fee Levels to Compare",
        options=["0.40%", "0.55%", "0.65%", "0.80%", "1.05%"],
        default=["0.40%", "0.65%", "1.05%"],
        help="Select fee levels for sensitivity analysis",
    )

    # Convert fee strings to floats
    fee_map = {
        "0.40%": 0.004,
        "0.55%": 0.0055,
        "0.65%": 0.0065,
        "0.80%": 0.008,
        "1.05%": 0.0105,
    }
    fee_values = [fee_map[f] for f in compare_fees]

    return {
        "ages": compare_ages,
        "fees": fee_values,
    }
