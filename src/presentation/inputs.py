"""Streamlit input components for the sidebar."""

import streamlit as st
from ..models import ProvidentInputs


# Constants for 2026
DEFAULT_ANNUAL_CAP = 83641  # NIS for 2026
DEFAULT_CONTRIBUTION = 83641  # Max out by default


def render_sidebar_inputs() -> ProvidentInputs:
    """
    Render all input controls in the sidebar and return the collected inputs.

    Returns:
        ProvidentInputs dataclass with all user inputs
    """
    st.sidebar.header("Investment Parameters")

    # Age settings
    st.sidebar.subheader("Age Settings")
    
    current_age = st.sidebar.slider(
        "Your Current Age",
        min_value=18,
        max_value=59,
        value=30,
        help="Your current age. This determines how many years until retirement.",
    )

    retirement_age = st.sidebar.slider(
        "Target Retirement Age",
        min_value=60,
        max_value=70,
        value=60,
        help="Age at which you plan to withdraw. Must be 60+ for annuity tax benefit.",
    )

    life_expectancy = st.sidebar.slider(
        "Life Expectancy",
        min_value=70,
        max_value=100,
        value=85,
        help="Expected lifespan. Used to calculate monthly withdrawal amounts (קצבה).",
    )

    # Contribution settings
    st.sidebar.subheader("Contributions")

    annual_contribution = st.sidebar.number_input(
        "Annual Contribution (₪)",
        min_value=0,
        max_value=500_000,
        value=DEFAULT_CONTRIBUTION,
        step=1_000,
        help="Your annual contribution. Will be capped at the legal limit for Provident Fund.",
    )

    annual_cap = st.sidebar.number_input(
        "Provident Fund Annual Cap (₪)",
        min_value=0,
        max_value=200_000,
        value=DEFAULT_ANNUAL_CAP,
        step=1_000,
        help="Legal annual contribution limit for Provident Fund (83,641 for 2026).",
    )

    # Show effective contribution
    effective_contrib = min(annual_contribution, annual_cap)
    if annual_contribution > annual_cap:
        st.sidebar.warning(
            f"Provident Fund capped at ₪{annual_cap:,}. "
            f"Personal account: ₪{annual_contribution:,}"
        )

    # Provident Fund Return Assumptions
    st.sidebar.subheader("Provident Fund Returns")

    provident_expected_return = st.sidebar.slider(
        "Expected Return (%)",
        min_value=3.0,
        max_value=12.0,
        value=7.0,
        step=0.5,
        help="Expected annual return for Provident Fund before fees.",
        key="provident_return",
    ) / 100

    provident_mgmt_fee = st.sidebar.slider(
        "Management Fee (%)",
        min_value=0.0,
        max_value=1.05,
        value=0.60,
        step=0.05,
        help="Annual management fee for Provident Fund (max 1.05% by law).",
    ) / 100

    # Show provident net return
    provident_net = (1 + provident_expected_return) * (1 - provident_mgmt_fee) - 1
    st.sidebar.info(f"**Net Return After Fees:** {provident_net*100:.2f}%")

    # Personal Account Return Assumptions
    st.sidebar.subheader("Personal Account Returns")

    personal_expected_return = st.sidebar.slider(
        "Expected Return (%)",
        min_value=3.0,
        max_value=15.0,
        value=8.0,
        step=0.5,
        help="Expected annual return for personal account (e.g., S&P 500 ETF).",
        key="personal_return",
    ) / 100

    personal_mgmt_fee = st.sidebar.slider(
        "Personal Account Fee (%)",
        min_value=0.0,
        max_value=1.0,
        value=0.10,
        step=0.05,
        help="Annual fee for personal account (ETFs typically 0.03%-0.20%).",
    ) / 100

    # Show personal net return
    personal_net = (1 + personal_expected_return) * (1 - personal_mgmt_fee) - 1
    st.sidebar.info(f"**Net Return After Fees:** {personal_net*100:.2f}%")

    # Inflation
    st.sidebar.subheader("Inflation")

    inflation_rate = st.sidebar.slider(
        "Inflation Rate (%)",
        min_value=0.0,
        max_value=5.0,
        value=2.5,
        step=0.5,
        help="Annual inflation rate. Used to calculate real gains for Provident Fund lump sum tax.",
    ) / 100

    # Tax settings
    st.sidebar.subheader("Tax Settings")

    capital_gains_tax = st.sidebar.slider(
        "Capital Gains Tax (%)",
        min_value=0.0,
        max_value=35.0,
        value=25.0,
        step=1.0,
        help="Capital gains tax rate (25% standard in Israel).",
    ) / 100

    # Withdrawal mode
    st.sidebar.subheader("Withdrawal Strategy")

    withdrawal_mode = st.sidebar.radio(
        "Provident Fund Withdrawal Mode",
        options=["annuity", "lump_sum"],
        index=0,
        format_func=lambda x: {
            "annuity": "Annuity (0% tax after 60)",
            "lump_sum": "Lump Sum (25% on real gains)",
        }[x],
        help="How you plan to withdraw from Provident Fund. Annuity after 60 = 0% tax on gains.",
    )

    # Show tax implication
    if withdrawal_mode == "annuity" and retirement_age >= 60:
        st.sidebar.success("**Tax Benefit Active:** 0% capital gains tax on Provident Fund")
    elif withdrawal_mode == "lump_sum":
        st.sidebar.warning("**Tax applies:** 25% on real (inflation-adjusted) gains")

    return ProvidentInputs(
        current_age=current_age,
        retirement_age=retirement_age,
        life_expectancy=life_expectancy,
        annual_contribution=float(annual_contribution),
        annual_cap=float(annual_cap),
        provident_expected_return=provident_expected_return,
        personal_expected_return=personal_expected_return,
        inflation_rate=inflation_rate,
        provident_mgmt_fee=provident_mgmt_fee,
        personal_mgmt_fee=personal_mgmt_fee,
        capital_gains_tax=capital_gains_tax,
        withdrawal_mode=withdrawal_mode,
    )


def render_quick_scenarios() -> None:
    """Render quick scenario buttons in the sidebar."""
    st.sidebar.subheader("Quick Scenarios")
    st.sidebar.markdown(
        """
        **Common scenarios:**
        - **Young investor (30):** Long horizon, maximize annuity benefit
        - **Mid-career (45):** Balance between options
        - **Near retirement (55):** Short horizon, limited benefit
        """
    )


def render_info_box() -> None:
    """Render information box about the comparison."""
    st.sidebar.divider()
    st.sidebar.markdown(
        """
        ### Key Points
        
        **Provident Fund (קופת גמל להשקעה):**
        - Annual cap: ~₪83,641 (2026)
        - Lump sum: 25% tax on **real** gains
        - Annuity after 60: **0%** tax
        
        **Personal Account:**
        - No contribution limit
        - 25% tax on **nominal** gains
        - Lower management fees (ETFs)
        """
    )
