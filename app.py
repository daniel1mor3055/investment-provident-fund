"""
Gemel Lehashkaa (Investment Provident Fund) Analysis Tool.

A Streamlit web application for simulating and analyzing Israeli Investment
Provident Fund savings scenarios.

Run with: streamlit run app.py
"""

import streamlit as st
import pandas as pd

from src.models import InvestmentInputs, ANNUAL_CAP_2026, ANNUITY_MIN_AGE
from src.calculator import (
    simulate,
    compare_start_ages,
    compare_withdrawal_modes,
    compare_fees,
    generate_sensitivity_matrix,
    calculate_fee_impact,
    generate_yearly_dataframe,
    generate_comparison_dataframe,
)
from src.presentation.inputs import render_sidebar_inputs
from src.presentation.styles import (
    CUSTOM_CSS,
    format_currency,
    format_percentage,
    style_dataframe,
)
from src.presentation.charts import (
    create_growth_chart,
    create_growth_area_chart,
    create_start_age_comparison_chart,
    create_start_age_bar_chart,
    create_withdrawal_mode_chart,
    create_fee_impact_chart,
    create_fee_comparison_line_chart,
    create_sensitivity_heatmap,
)

# ============================================================================
# Page Configuration
# ============================================================================

st.set_page_config(
    page_title="Gemel Lehashkaa Analysis",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Apply custom CSS
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ============================================================================
# Header
# ============================================================================

st.title("📊 Gemel Lehashkaa Analysis")
st.markdown(
    """
    **Investment Provident Fund (קופת גמל להשקעה) Simulator**

    Analyze different savings scenarios, compare starting ages, and understand
    the impact of fees and withdrawal modes on your investment.
    """
)

# ============================================================================
# Sidebar Inputs
# ============================================================================

inputs = render_sidebar_inputs()

# ============================================================================
# Run Simulation
# ============================================================================

result = simulate(inputs)

# ============================================================================
# Summary Metrics
# ============================================================================

st.header("Summary")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        label="Net Balance at Withdrawal",
        value=format_currency(result.net_balance),
        delta=f"{format_currency(result.net_balance - result.total_contributions)} gain",
    )

with col2:
    st.metric(
        label="Total Contributions",
        value=format_currency(result.total_contributions),
        delta=f"{inputs.years_of_contribution} years",
    )

with col3:
    if inputs.withdrawal_mode == "annuity" and inputs.withdraw_age >= ANNUITY_MIN_AGE:
        st.metric(
            label="Tax Saved (Annuity)",
            value=format_currency(result.tax_savings_from_annuity),
            delta="Tax-Free",
        )
    else:
        st.metric(
            label="Tax (25% Real Gains)",
            value=format_currency(result.tax_amount),
            delta=f"-{format_percentage(result.effective_tax_rate)} effective",
        )

with col4:
    gains = result.gross_balance - result.total_contributions
    gain_pct = gains / result.total_contributions if result.total_contributions > 0 else 0
    st.metric(
        label="Investment Gains",
        value=format_currency(gains),
        delta=f"+{format_percentage(gain_pct)}",
    )

# Cap warning
if result.cap_was_binding:
    st.warning(
        f"⚠️ Annual contribution cap was binding. "
        f"Could not contribute {format_currency(result.cap_limited_amount)} due to the annual limit."
    )

st.divider()

# ============================================================================
# Tabs
# ============================================================================

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📈 Growth Chart",
    "🎂 Start Age Comparison",
    "💰 Withdrawal Mode",
    "📉 Fee Impact",
    "🔬 Sensitivity Analysis",
])

# ----------------------------------------------------------------------------
# Tab 1: Growth Chart
# ----------------------------------------------------------------------------

with tab1:
    st.subheader("Investment Growth Over Time")

    chart_type = st.radio(
        "Chart Type",
        options=["Line Chart", "Area Chart"],
        horizontal=True,
    )

    if chart_type == "Line Chart":
        fig = create_growth_chart(result)
    else:
        fig = create_growth_area_chart(result)

    st.plotly_chart(fig, use_container_width=True)

    # Yearly data table
    with st.expander("📊 View Yearly Data"):
        yearly_df = generate_yearly_dataframe(result)
        styled_df = style_dataframe(
            yearly_df,
            currency_columns=["Contributions (Year)", "Total Contributions", "Balance", "Real Basis"],
        )
        st.dataframe(styled_df, use_container_width=True)

# ----------------------------------------------------------------------------
# Tab 2: Start Age Comparison
# ----------------------------------------------------------------------------

with tab2:
    st.subheader("Compare Different Starting Ages")

    st.markdown(
        """
        See how starting earlier or later affects your final balance.
        Earlier starts benefit from more years of compound growth.
        """
    )

    # Age selection
    col1, col2 = st.columns([2, 1])
    with col1:
        ages_to_compare = st.multiselect(
            "Select starting ages to compare",
            options=list(range(20, 60)),
            default=[30, 40, 50, 59],
        )

    if ages_to_compare:
        # Filter out invalid ages
        valid_ages = [a for a in ages_to_compare if a < inputs.withdraw_age]

        if valid_ages:
            comparison = compare_start_ages(inputs, valid_ages)

            # Line chart
            st.plotly_chart(
                create_start_age_comparison_chart(comparison),
                use_container_width=True,
            )

            # Bar chart
            st.plotly_chart(
                create_start_age_bar_chart(comparison),
                use_container_width=True,
            )

            # Comparison table
            with st.expander("📊 View Comparison Data"):
                comp_df = generate_comparison_dataframe(comparison)
                styled_comp_df = style_dataframe(
                    comp_df,
                    currency_columns=["Total Contributions", "Gross Balance", "Tax", "Net Balance"],
                    percentage_columns=["Effective Tax Rate"],
                )
                st.dataframe(styled_comp_df, use_container_width=True)
        else:
            st.warning("All selected ages are >= withdrawal age. Select lower ages.")

# ----------------------------------------------------------------------------
# Tab 3: Withdrawal Mode
# ----------------------------------------------------------------------------

with tab3:
    st.subheader("Lump Sum vs Annuity Comparison")

    if inputs.withdraw_age >= ANNUITY_MIN_AGE:
        st.success(
            f"✅ At age {inputs.withdraw_age}, you qualify for tax-free annuity conversion!"
        )

        # Run both scenarios
        mode_results = compare_withdrawal_modes(inputs)
        lump_result = mode_results["Lump Sum"]
        annuity_result = mode_results["Annuity"]

        # Comparison chart
        fig = create_withdrawal_mode_chart(lump_result, annuity_result)
        st.plotly_chart(fig, use_container_width=True)

        # Detailed comparison
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### 💵 Lump Sum (Taxable)")
            st.markdown(f"""
            - **Gross Balance**: {format_currency(lump_result.gross_balance)}
            - **Real Gain**: {format_currency(lump_result.real_gain)}
            - **Tax (25%)**: {format_currency(lump_result.tax_amount)}
            - **Net Balance**: {format_currency(lump_result.net_balance)}
            """)

        with col2:
            st.markdown("### 🏦 Annuity (Tax-Free)")
            st.markdown(f"""
            - **Gross Balance**: {format_currency(annuity_result.gross_balance)}
            - **Real Gain**: {format_currency(annuity_result.real_gain)}
            - **Tax**: {format_currency(0)} (Exempt!)
            - **Net Balance**: {format_currency(annuity_result.net_balance)}
            """)

        tax_savings = lump_result.tax_amount
        st.info(f"💡 **Tax Savings with Annuity: {format_currency(tax_savings)}**")

    else:
        st.warning(
            f"⚠️ At withdrawal age {inputs.withdraw_age}, you do not qualify for "
            f"tax-free annuity (requires age ≥ {ANNUITY_MIN_AGE})."
        )
        st.markdown(
            """
            **Lump sum withdrawal will be taxed at 25% on real (inflation-adjusted) gains.**

            Consider setting withdrawal age to 60 or later to qualify for the tax benefit.
            """
        )

# ----------------------------------------------------------------------------
# Tab 4: Fee Impact
# ----------------------------------------------------------------------------

with tab4:
    st.subheader("Impact of Management Fees")

    st.markdown(
        """
        Management fees compound over time and can significantly reduce your final balance.
        Compare different fee levels to understand the long-term impact.
        """
    )

    # Fee comparison
    fee_results = compare_fees(inputs)

    # Line chart showing growth under different fees
    st.plotly_chart(
        create_fee_comparison_line_chart(fee_results),
        use_container_width=True,
    )

    # Fee impact table
    fee_df = calculate_fee_impact(inputs)
    st.plotly_chart(
        create_fee_impact_chart(fee_df),
        use_container_width=True,
    )

    with st.expander("📊 View Fee Impact Data"):
        styled_fee_df = style_dataframe(
            fee_df,
            currency_columns=["Gross Balance", "Net Balance", "Tax Amount", "Fee Cost"],
        )
        st.dataframe(styled_fee_df, use_container_width=True)

    # Key insight
    if len(fee_df) >= 2:
        low_fee_net = fee_df.iloc[0]["Net Balance"]
        high_fee_net = fee_df.iloc[-1]["Net Balance"]
        fee_cost = low_fee_net - high_fee_net
        st.info(
            f"💡 The difference between the lowest and highest fee is **{format_currency(fee_cost)}** "
            f"over {inputs.years_of_contribution} years!"
        )

# ----------------------------------------------------------------------------
# Tab 5: Sensitivity Analysis
# ----------------------------------------------------------------------------

with tab5:
    st.subheader("Sensitivity Analysis")

    st.markdown(
        """
        Explore how different combinations of parameters affect your final balance.
        """
    )

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Return vs Fee")

        return_values = [0.03, 0.04, 0.05, 0.06, 0.07, 0.08]
        fee_values = [0.004, 0.0055, 0.0065, 0.008, 0.0105]

        return_fee_matrix = generate_sensitivity_matrix(
            inputs,
            param1_name="expected_return",
            param1_values=return_values,
            param2_name="fee_aum",
            param2_values=fee_values,
            output_metric="net_balance",
        )

        fig = create_sensitivity_heatmap(
            return_fee_matrix,
            title="Net Balance: Return vs Fee",
            value_format="currency",
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("#### Return vs Start Age")

        start_age_values = [30, 35, 40, 45, 50, 55]
        valid_start_ages = [a for a in start_age_values if a < inputs.withdraw_age]

        if valid_start_ages:
            return_age_matrix = generate_sensitivity_matrix(
                inputs,
                param1_name="expected_return",
                param1_values=return_values,
                param2_name="start_age",
                param2_values=valid_start_ages,
                output_metric="net_balance",
            )

            fig = create_sensitivity_heatmap(
                return_age_matrix,
                title="Net Balance: Return vs Start Age",
                value_format="currency",
            )
            st.plotly_chart(fig, use_container_width=True)

# ============================================================================
# Assumptions & Model Details
# ============================================================================

with st.expander("ℹ️ Model Assumptions & Details"):
    st.markdown(f"""
    ### Input Parameters
    - **Start Age**: {inputs.start_age}
    - **Withdrawal Age**: {inputs.withdraw_age}
    - **Monthly Contribution**: {format_currency(inputs.monthly_contribution)}
    - **Annual Cap**: {format_currency(inputs.annual_cap)}
    - **Expected Return**: {format_percentage(inputs.expected_return)}
    - **AUM Fee**: {format_percentage(inputs.fee_aum)}
    - **Deposit Fee**: {format_percentage(inputs.fee_deposit)}
    - **Inflation**: {format_percentage(inputs.inflation)}
    - **Withdrawal Mode**: {inputs.withdrawal_mode.title()}

    ### Model Assumptions
    1. **Contributions**: Monthly contributions at the start of each month
    2. **Annual Cap**: Enforced per calendar year (resets each January)
    3. **Returns**: Applied monthly using compound formula
    4. **Fees**: AUM fee deducted monthly, deposit fee at contribution time
    5. **Tax Calculation**:
       - Lump sum: 25% on real (inflation-adjusted) gains
       - Annuity after 60: 0% tax on gains (recognized annuity)
    6. **Inflation**: Used to calculate real gains for tax purposes

    ### Legal Caps (Israel 2026)
    - Annual contribution cap: **{format_currency(ANNUAL_CAP_2026)}**
    - Maximum AUM fee: **1.05%**
    - Maximum deposit fee: **4%**
    - Maximum annuity fee: **0.6%**
    - Minimum age for tax-free annuity: **{ANNUITY_MIN_AGE}**

    ### Data Sources
    - Based on Amendment No. 15 to the Supervision of Financial Services (Provident Funds) Law
    - Tax rates per Israeli Tax Authority guidelines
    """)

# ============================================================================
# Footer
# ============================================================================

st.divider()
st.markdown(
    """
    <div style="text-align: center; color: #888; font-size: 12px;">
        This tool is for educational purposes only. Consult a licensed financial advisor for personal advice.
    </div>
    """,
    unsafe_allow_html=True,
)
