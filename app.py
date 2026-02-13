"""
Provident Fund (Kupat Gemel Lehashka'a) vs Personal Investment Comparison Tool

A Streamlit application to compare the financial outcomes of investing in an
Israeli Provident Fund versus a personal investment account, with focus on
determining the optimal starting age for Provident Fund investment.
"""

import streamlit as st
import pandas as pd

from src.models import ProvidentInputs
from src.calculator import (
    run_full_comparison,
    generate_yearly_growth,
    generate_comparison_dataframe,
    generate_yearly_dataframe,
    generate_sensitivity_matrix,
    calculate_tax_comparison,
    calculate_comparison_for_starting_age,
    calculate_monthly_withdrawal_comparison,
)
from src.presentation.inputs import render_sidebar_inputs, render_info_box
from src.presentation.charts import (
    create_age_crossover_chart,
    create_difference_by_age_chart,
    create_growth_comparison_chart,
    create_tax_comparison_chart,
    create_tax_savings_chart,
    create_sensitivity_heatmap,
    create_withdrawal_mode_comparison,
    create_monthly_withdrawal_chart,
    create_monthly_withdrawal_breakdown_chart,
)
from src.presentation.styles import CUSTOM_CSS, format_currency, format_percentage

# Page configuration
st.set_page_config(
    page_title="Provident Fund vs Personal Investment",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Apply custom CSS
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# Title and introduction
st.title("Provident Fund vs Personal Investment")
st.markdown(
    """
Compare the long-term financial outcomes of two investment strategies:

**Option A: Provident Fund (קופת גמל להשקעה)**
- Annual contribution cap (~₪83,641 in 2026)
- **Annuity after age 60: 0% tax on gains**
- Lump sum: 25% tax on real (inflation-adjusted) gains

**Option B: Personal Investment Account**
- No contribution limit
- 25% tax on nominal gains at sale
- Typically lower management fees (ETFs)

**Key Question:** At what age should you start investing in a Provident Fund to maximize the annuity tax benefit?
"""
)

# Render sidebar inputs
inputs = render_sidebar_inputs()
render_info_box()

# Run comparison
summary = run_full_comparison(inputs)
yearly_growth = generate_yearly_growth(inputs)
tax_data = calculate_tax_comparison(inputs)

# Also run with lump sum for comparison
lump_sum_inputs = ProvidentInputs(
    current_age=inputs.current_age,
    retirement_age=inputs.retirement_age,
    life_expectancy=inputs.life_expectancy,
    annual_contribution=inputs.annual_contribution,
    annual_cap=inputs.annual_cap,
    provident_expected_return=inputs.provident_expected_return,
    personal_expected_return=inputs.personal_expected_return,
    inflation_rate=inputs.inflation_rate,
    provident_mgmt_fee=inputs.provident_mgmt_fee,
    personal_mgmt_fee=inputs.personal_mgmt_fee,
    capital_gains_tax=inputs.capital_gains_tax,
    withdrawal_mode="lump_sum",
)
summary_lump = run_full_comparison(lump_sum_inputs)

annuity_inputs = ProvidentInputs(
    current_age=inputs.current_age,
    retirement_age=inputs.retirement_age,
    life_expectancy=inputs.life_expectancy,
    annual_contribution=inputs.annual_contribution,
    annual_cap=inputs.annual_cap,
    provident_expected_return=inputs.provident_expected_return,
    personal_expected_return=inputs.personal_expected_return,
    inflation_rate=inputs.inflation_rate,
    provident_mgmt_fee=inputs.provident_mgmt_fee,
    personal_mgmt_fee=inputs.personal_mgmt_fee,
    capital_gains_tax=inputs.capital_gains_tax,
    withdrawal_mode="annuity",
)
summary_annuity = run_full_comparison(annuity_inputs)

# Calculate monthly withdrawal comparison
monthly_withdrawal = calculate_monthly_withdrawal_comparison(inputs)

# Summary Metrics Row
st.header("Summary")

col1, col2, col3, col4 = st.columns(4)

current_result = summary.current_age_result

with col1:
    if summary.crossover_age:
        crossover_text = f"Age {summary.crossover_age}"
        crossover_help = f"Starting at age {summary.crossover_age} or earlier, Provident Fund beats Personal Account"
    else:
        crossover_text = "Never"
        crossover_help = "Provident Fund never beats Personal Account with current assumptions"
    
    st.metric(
        label="Crossover Age",
        value=crossover_text,
        help=crossover_help,
    )

with col2:
    if current_result:
        st.metric(
            label=f"Provident Fund at {inputs.retirement_age}",
            value=format_currency(current_result.provident_net),
            delta=f"{format_percentage(summary.provident_net_return)} net",
            help=f"Net value after tax if starting at age {inputs.current_age}",
        )
    else:
        st.metric(label="Provident Fund", value="N/A")

with col3:
    if current_result:
        st.metric(
            label=f"Personal Account at {inputs.retirement_age}",
            value=format_currency(current_result.personal_net),
            delta=f"{format_percentage(summary.personal_net_return)} net",
            help=f"Net value after tax if starting at age {inputs.current_age}",
        )
    else:
        st.metric(label="Personal Account", value="N/A")

with col4:
    if current_result:
        diff_sign = "+" if current_result.difference > 0 else ""
        st.metric(
            label=f"Winner (Starting Age {inputs.current_age})",
            value=current_result.winner,
            delta=f"{diff_sign}{format_currency(current_result.difference)}",
            delta_color="normal" if current_result.difference >= 0 else "inverse",
        )
    else:
        st.metric(label="Winner", value="N/A")

# Key insight box
if current_result:
    if current_result.provident_wins:
        st.success(
            f"**Starting at age {inputs.current_age}:** Provident Fund wins by "
            f"**{format_currency(current_result.difference)}** "
            f"({current_result.difference_pct:+.1f}%) at retirement."
        )
    else:
        st.warning(
            f"**Starting at age {inputs.current_age}:** Personal Account wins by "
            f"**{format_currency(abs(current_result.difference))}** "
            f"({abs(current_result.difference_pct):.1f}%) at retirement."
        )

st.divider()

# Main comparison chart
st.header("Analysis by Starting Age")

st.markdown(
    """
This chart shows the **net value at retirement** for each possible starting age.
The crossover point indicates when Provident Fund becomes advantageous.
"""
)

age_crossover_chart = create_age_crossover_chart(summary)
st.plotly_chart(age_crossover_chart, use_container_width=True)

# Two columns: Difference chart and growth chart
col_left, col_right = st.columns([1, 1])

with col_left:
    st.subheader("Advantage by Starting Age")
    diff_chart = create_difference_by_age_chart(summary)
    st.plotly_chart(diff_chart, use_container_width=True)

with col_right:
    st.subheader("Growth Over Time (Your Age)")
    growth_chart = create_growth_comparison_chart(yearly_growth)
    st.plotly_chart(growth_chart, use_container_width=True)

st.divider()

# Tax Analysis
st.header("Tax Impact Analysis")

st.markdown(
    f"""
**Your scenario** (starting at age {inputs.current_age}, withdrawing at age {inputs.retirement_age}):

- **Provident Fund:** {tax_data['provident']['tax_type']}
- **Personal Account:** {tax_data['personal']['tax_type']}
"""
)

col_tax1, col_tax2 = st.columns([1, 1])

with col_tax1:
    tax_chart = create_tax_comparison_chart(tax_data)
    st.plotly_chart(tax_chart, use_container_width=True)

with col_tax2:
    savings_chart = create_tax_savings_chart(tax_data)
    st.plotly_chart(savings_chart, use_container_width=True)

# Tax details expander
with st.expander("View Detailed Tax Calculation", expanded=False):
    tax_col1, tax_col2 = st.columns(2)
    
    with tax_col1:
        st.markdown("#### Provident Fund")
        st.markdown(f"""
        - **Gross Balance:** {format_currency(tax_data['provident']['gross'])}
        - **Total Contributions:** {format_currency(tax_data['provident']['contributions'])}
        - **Inflation-Adjusted Basis:** {format_currency(tax_data['provident']['inflation_adjusted_contributions'])}
        - **Nominal Gain:** {format_currency(tax_data['provident']['nominal_gain'])}
        - **Real Gain:** {format_currency(tax_data['provident']['real_gain'])}
        - **Tax ({tax_data['provident']['tax_type']}):** {format_currency(tax_data['provident']['tax'])}
        - **Net Balance:** {format_currency(tax_data['provident']['net'])}
        """)
    
    with tax_col2:
        st.markdown("#### Personal Account")
        st.markdown(f"""
        - **Gross Balance:** {format_currency(tax_data['personal']['gross'])}
        - **Total Contributions:** {format_currency(tax_data['personal']['contributions'])}
        - **Nominal Gain:** {format_currency(tax_data['personal']['nominal_gain'])}
        - **Tax ({tax_data['personal']['tax_type']}):** {format_currency(tax_data['personal']['tax'])}
        - **Net Balance:** {format_currency(tax_data['personal']['net'])}
        """)

st.divider()

# Withdrawal Mode Comparison
st.header("Withdrawal Mode Comparison")

st.markdown(
    """
Compare the impact of choosing **Annuity** (0% tax after 60) vs **Lump Sum** (25% real gains tax).
"""
)

withdrawal_chart = create_withdrawal_mode_comparison(summary_lump, summary_annuity)
st.plotly_chart(withdrawal_chart, use_container_width=True)

st.divider()

# Monthly Withdrawal Comparison (קצבה)
st.header("Monthly Withdrawal Comparison (קצבה)")

st.markdown(
    f"""
Compare the **monthly income** (קצבה) you would receive from each account during retirement.

**Assumptions:**
- Retirement at age {inputs.retirement_age}, life expectancy age {inputs.life_expectancy}
- Withdrawal period: **{monthly_withdrawal.withdrawal_years} years**
- Conservative 3% return during withdrawal phase
- **Provident Fund:** 0% tax on monthly withdrawals (annuity after 60)
- **Personal Account:** 25% tax on the gains portion of each withdrawal
"""
)

# Summary metrics for monthly withdrawal
col_w1, col_w2, col_w3, col_w4 = st.columns(4)

with col_w1:
    st.metric(
        label="Provident Monthly (Net)",
        value=format_currency(monthly_withdrawal.provident_net_monthly),
        help="Monthly withdrawal from Provident Fund with 0% tax on gains",
    )

with col_w2:
    st.metric(
        label="Personal Monthly (Net)",
        value=format_currency(monthly_withdrawal.personal_net_monthly),
        delta=f"-{format_currency(monthly_withdrawal.personal_tax_per_month)} tax/mo",
        delta_color="inverse",
        help="Monthly withdrawal from Personal Account after 25% tax on gains",
    )

with col_w3:
    diff = monthly_withdrawal.monthly_difference
    st.metric(
        label="Monthly Advantage",
        value=format_currency(abs(diff)),
        delta="Provident" if diff > 0 else "Personal",
        delta_color="normal" if diff > 0 else "inverse",
        help="Extra monthly income from the winning option",
    )

with col_w4:
    st.metric(
        label="Lifetime Tax Savings",
        value=format_currency(monthly_withdrawal.lifetime_tax_savings),
        help=f"Total tax saved over {monthly_withdrawal.withdrawal_years} years by using Provident Fund annuity",
    )

# Monthly withdrawal insight box
if monthly_withdrawal.monthly_difference > 0:
    st.success(
        f"**Provident Fund provides ₪{monthly_withdrawal.monthly_difference:,.0f} more per month** "
        f"({monthly_withdrawal.monthly_difference_pct:+.1f}%) compared to Personal Account. "
        f"Over {monthly_withdrawal.withdrawal_years} years of retirement, this saves "
        f"**{format_currency(monthly_withdrawal.lifetime_tax_savings)}** in taxes."
    )
else:
    st.warning(
        f"**Personal Account provides ₪{abs(monthly_withdrawal.monthly_difference):,.0f} more per month** "
        f"compared to Provident Fund."
    )

# Monthly withdrawal charts
col_mw1, col_mw2 = st.columns([1, 1])

with col_mw1:
    monthly_chart = create_monthly_withdrawal_chart(monthly_withdrawal)
    st.plotly_chart(monthly_chart, use_container_width=True)

with col_mw2:
    breakdown_chart = create_monthly_withdrawal_breakdown_chart(monthly_withdrawal)
    st.plotly_chart(breakdown_chart, use_container_width=True)

# Detailed monthly withdrawal breakdown
with st.expander("View Monthly Withdrawal Details", expanded=False):
    detail_col1, detail_col2 = st.columns(2)
    
    with detail_col1:
        st.markdown("#### Provident Fund (קצבה)")
        st.markdown(f"""
        - **Balance at Retirement:** {format_currency(monthly_withdrawal.provident_balance)}
        - **Total Contributions:** {format_currency(monthly_withdrawal.provident_contributions)}
        - **Gains:** {format_currency(monthly_withdrawal.provident_balance - monthly_withdrawal.provident_contributions)}
        - **Gross Monthly Withdrawal:** {format_currency(monthly_withdrawal.provident_gross_monthly)}
        - **Tax per Month:** ₪0 (0% annuity tax)
        - **Net Monthly Withdrawal:** {format_currency(monthly_withdrawal.provident_net_monthly)}
        """)
    
    with detail_col2:
        st.markdown("#### Personal Account (קצבה)")
        gain_ratio = monthly_withdrawal.personal_gain_ratio * 100
        st.markdown(f"""
        - **Balance at Retirement:** {format_currency(monthly_withdrawal.personal_balance)}
        - **Total Contributions:** {format_currency(monthly_withdrawal.personal_contributions)}
        - **Gains:** {format_currency(monthly_withdrawal.personal_balance - monthly_withdrawal.personal_contributions)}
        - **Gains Portion:** {gain_ratio:.1f}% of each withdrawal
        - **Gross Monthly Withdrawal:** {format_currency(monthly_withdrawal.personal_gross_monthly)}
        - **Tax per Month (25% on gains):** {format_currency(monthly_withdrawal.personal_tax_per_month)}
        - **Net Monthly Withdrawal:** {format_currency(monthly_withdrawal.personal_net_monthly)}
        """)

st.divider()

# Sensitivity Analysis
st.header("Sensitivity Analysis")

tab1, tab2, tab3 = st.tabs(["Crossover Heatmap", "Comparison Table", "Data Export"])

with tab1:
    st.markdown(
        """
    This heatmap shows the **crossover age** for different combinations of
    **expected return** and **inflation rate**.
    
    - **Green (lower age):** Provident Fund becomes beneficial earlier
    - **Red (higher age):** Need to start younger for Provident Fund to win
    - **"Never":** Personal Account always wins
    """
    )

    heatmap = create_sensitivity_heatmap(summary)
    st.plotly_chart(heatmap, use_container_width=True)

with tab2:
    st.subheader("Comparison by Starting Age")
    
    df = generate_comparison_dataframe(summary)
    
    # Format currency columns
    currency_cols = ["Provident Gross", "Provident Tax", "Provident Net",
                     "Personal Gross", "Personal Tax", "Personal Net", "Difference"]
    for col in currency_cols:
        df[col] = df[col].apply(lambda x: f"₪{x:,.0f}")
    
    df["Difference %"] = df["Difference %"].apply(lambda x: f"{x:+.1f}%")
    
    # Highlight current age row
    def highlight_current_age(row):
        if row["Starting Age"] == inputs.current_age:
            return ["background-color: #d97706; color: white; font-weight: bold"] * len(row)
        return [""] * len(row)
    
    styled_df = df.style.apply(highlight_current_age, axis=1)
    st.dataframe(styled_df, use_container_width=True, height=400)

with tab3:
    st.subheader("Export Data")
    
    # Age comparison data
    st.markdown("**Age Comparison Data**")
    comparison_df = generate_comparison_dataframe(summary)
    csv_comparison = comparison_df.to_csv(index=False)
    st.download_button(
        label="Download Age Comparison CSV",
        data=csv_comparison,
        file_name="provident_vs_personal_comparison.csv",
        mime="text/csv",
    )
    
    # Yearly growth data
    if yearly_growth:
        st.markdown("**Yearly Growth Data**")
        yearly_df = generate_yearly_dataframe(yearly_growth)
        csv_yearly = yearly_df.to_csv(index=False)
        st.download_button(
            label="Download Yearly Growth CSV",
            data=csv_yearly,
            file_name="yearly_growth.csv",
            mime="text/csv",
        )

st.divider()

# Key Assumptions
st.header("Key Assumptions")

with st.expander("Click to view the assumptions used in this analysis", expanded=False):
    st.markdown(
        f"""
    ### Your Inputs
    - **Current Age:** {inputs.current_age}
    - **Retirement Age:** {inputs.retirement_age}
    - **Life Expectancy:** {inputs.life_expectancy}
    - **Investment Horizon:** {inputs.get_investment_years()} years
    - **Withdrawal Period:** {inputs.life_expectancy - inputs.retirement_age} years
    - **Annual Contribution:** {format_currency(inputs.annual_contribution)} (same for both accounts)
    - **Provident Fund Expected Return:** {format_percentage(inputs.provident_expected_return)}
    - **Personal Account Expected Return:** {format_percentage(inputs.personal_expected_return)}
    - **Inflation Rate:** {format_percentage(inputs.inflation_rate)}
    - **Provident Fund Fee:** {format_percentage(inputs.provident_mgmt_fee)}
    - **Personal Account Fee:** {format_percentage(inputs.personal_mgmt_fee)}
    - **Capital Gains Tax:** {format_percentage(inputs.capital_gains_tax)}
    - **Withdrawal Mode:** {inputs.withdrawal_mode.replace('_', ' ').title()}

    ### Net Returns After Fees
    - **Provident Fund Net Return:** {format_percentage(summary.provident_net_return)}
    - **Personal Account Net Return:** {format_percentage(summary.personal_net_return)}

    ### Model Assumptions
    1. **Equal contributions** to both accounts for fair comparison
    2. **Contributions are made annually** at the end of each year
    3. **Returns are constant** at the specified rates (can differ between accounts)
    4. **Inflation is constant** at the specified rate
    5. **Provident Fund annuity after 60** provides 0% capital gains tax
    6. **Provident Fund lump sum** is taxed at 25% on real (inflation-adjusted) gains
    7. **Personal account withdrawals** are taxed at 25% on the gains portion
    8. **Management fees** are deducted from returns annually
    9. **Conservative 3% return** assumed during withdrawal phase

    ### Important Notes
    - The **annuity tax benefit** (0% after age 60) is the primary driver of Provident Fund advantage
    - **Monthly withdrawal comparison** shows the actual income difference in retirement
    - **Real gains taxation** (Provident) vs **nominal gains taxation** (Personal) favors Provident in high-inflation scenarios
    - Results are sensitive to return and inflation assumptions
    """
    )

# Footer
st.sidebar.divider()
st.sidebar.markdown(
    """
### About This Tool
This tool compares Israeli Provident Fund (קופת גמל להשקעה) 
with a personal investment account to help determine the optimal
investment strategy based on your age and circumstances.

**Data Sources:**
- Annual cap: 83,641 NIS (2026)
- Tax rates: Israeli tax law
"""
)
