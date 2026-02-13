"""
Data models for Gemel Lehashkaa (Investment Provident Fund) analysis.

These models define the input parameters and output results for simulating
investment scenarios in Israeli Investment Provident Funds.
"""

from dataclasses import dataclass, field
from typing import Literal


# ============================================================================
# Constants (from Israeli regulations)
# ============================================================================

ANNUAL_CAP_2026 = 83_641  # NIS - annual contribution cap for 2026
MAX_FEE_AUM = 0.0105  # 1.05% - maximum annual AUM fee
MAX_FEE_DEPOSIT = 0.04  # 4% - maximum deposit fee
MAX_FEE_ANNUITY = 0.006  # 0.6% - maximum fee for annuity recipients
CAPITAL_GAINS_TAX = 0.25  # 25% on real (inflation-adjusted) gains
ANNUITY_MIN_AGE = 60  # Minimum age for tax-free annuity conversion


# ============================================================================
# Input Models
# ============================================================================


@dataclass
class InvestmentInputs:
    """
    Input parameters for Investment Provident Fund simulation.

    Attributes:
        start_age: Age when contributions begin (e.g., 30, 40, 50)
        withdraw_age: Target withdrawal age (typically 60 for annuity benefit)
        monthly_contribution: Monthly contribution amount in NIS
        annual_cap: Annual contribution cap in NIS (default: 83,641 for 2026)
        expected_return: Expected annual nominal return (e.g., 0.05 for 5%)
        fee_aum: Annual AUM (assets under management) fee (e.g., 0.0065 for 0.65%)
        fee_deposit: Fee on deposits (e.g., 0.0 for 0%, often waived)
        inflation: Expected annual inflation rate (e.g., 0.025 for 2.5%)
        capital_gains_tax: Tax rate on real gains for lump sum (default: 0.25)
        withdrawal_mode: "lump" for lump sum or "annuity" for tax-free annuity
    """

    start_age: int
    withdraw_age: int
    monthly_contribution: float
    annual_cap: float = ANNUAL_CAP_2026
    expected_return: float = 0.05  # 5% default
    fee_aum: float = 0.0065  # 0.65% default (market average)
    fee_deposit: float = 0.0  # Often 0% in practice
    inflation: float = 0.025  # 2.5% default
    capital_gains_tax: float = CAPITAL_GAINS_TAX
    withdrawal_mode: Literal["lump", "annuity"] = "annuity"

    def __post_init__(self):
        """Validate inputs after initialization."""
        if self.start_age >= self.withdraw_age:
            raise ValueError("start_age must be less than withdraw_age")
        if self.start_age < 0:
            raise ValueError("start_age must be non-negative")
        if self.monthly_contribution < 0:
            raise ValueError("monthly_contribution must be non-negative")
        if self.annual_cap < 0:
            raise ValueError("annual_cap must be non-negative")

    @property
    def years_of_contribution(self) -> int:
        """Calculate the number of years of contributions."""
        return self.withdraw_age - self.start_age

    @property
    def months_of_contribution(self) -> int:
        """Calculate the number of months of contributions."""
        return self.years_of_contribution * 12

    def get_net_return(self) -> float:
        """
        Calculate net annual return after AUM fees.

        Returns:
            Net annual return rate
        """
        # Approximate: (1 + R) * (1 - fee) - 1
        return (1 + self.expected_return) * (1 - self.fee_aum) - 1

    def validate_fees(self) -> list[str]:
        """
        Validate that fees don't exceed legal caps.

        Returns:
            List of warning messages (empty if all valid)
        """
        warnings = []
        if self.fee_aum > MAX_FEE_AUM:
            warnings.append(
                f"AUM fee ({self.fee_aum:.2%}) exceeds legal cap ({MAX_FEE_AUM:.2%})"
            )
        if self.fee_deposit > MAX_FEE_DEPOSIT:
            warnings.append(
                f"Deposit fee ({self.fee_deposit:.2%}) exceeds legal cap ({MAX_FEE_DEPOSIT:.2%})"
            )
        return warnings

    def is_annuity_eligible(self) -> bool:
        """Check if withdrawal age qualifies for tax-free annuity."""
        return self.withdraw_age >= ANNUITY_MIN_AGE


# ============================================================================
# Result Models
# ============================================================================


@dataclass
class MonthlyResult:
    """
    Result for a single month in the simulation.

    Attributes:
        month: Month number (0-indexed from start)
        age: Age at this month (float for precision)
        balance: Account balance at end of month
        contribution: Contribution made this month
        real_basis: Inflation-adjusted basis up to this month
        cumulative_contributions: Total contributions to date
    """

    month: int
    age: float
    balance: float
    contribution: float
    real_basis: float
    cumulative_contributions: float


@dataclass
class YearlyResult:
    """
    Aggregated result for a single year in the simulation.

    Attributes:
        year: Year number (1-indexed)
        age: Age at end of year
        balance: Account balance at end of year
        contributions_ytd: Contributions made during this year
        cumulative_contributions: Total contributions to date
        real_basis: Inflation-adjusted basis at end of year
    """

    year: int
    age: int
    balance: float
    contributions_ytd: float
    cumulative_contributions: float
    real_basis: float


@dataclass
class SimulationResult:
    """
    Complete result of a provident fund simulation.

    Attributes:
        inputs: The input parameters used for simulation
        monthly_results: List of monthly results
        yearly_results: List of yearly aggregated results
        gross_balance: Final balance before tax
        total_contributions: Sum of all contributions made
        real_basis: Inflation-adjusted cost basis at withdrawal
        real_gain: Gain after adjusting for inflation
        tax_amount: Tax due on withdrawal (0 for annuity after 60)
        net_balance: Final balance after tax
        cap_was_binding: True if annual cap limited contributions
        cap_limited_amount: Total amount that couldn't be contributed due to cap
    """

    inputs: InvestmentInputs
    monthly_results: list[MonthlyResult] = field(default_factory=list)
    yearly_results: list[YearlyResult] = field(default_factory=list)
    gross_balance: float = 0.0
    total_contributions: float = 0.0
    real_basis: float = 0.0
    real_gain: float = 0.0
    tax_amount: float = 0.0
    net_balance: float = 0.0
    cap_was_binding: bool = False
    cap_limited_amount: float = 0.0

    @property
    def effective_tax_rate(self) -> float:
        """Calculate effective tax rate on total gains."""
        nominal_gain = self.gross_balance - self.total_contributions
        if nominal_gain <= 0:
            return 0.0
        return self.tax_amount / nominal_gain

    @property
    def tax_savings_from_annuity(self) -> float:
        """
        Calculate how much tax would be saved by choosing annuity over lump sum.

        Only relevant if withdrawal_mode is 'annuity' and age >= 60.
        """
        if self.inputs.withdrawal_mode == "annuity" and self.inputs.is_annuity_eligible():
            # Tax that would have been paid with lump sum
            potential_tax = self.inputs.capital_gains_tax * max(self.real_gain, 0)
            return potential_tax
        return 0.0


@dataclass
class ComparisonResult:
    """
    Result comparing multiple scenarios (e.g., different start ages).

    Attributes:
        scenarios: Dict mapping scenario name to SimulationResult
        baseline_name: Name of the baseline scenario for comparison
    """

    scenarios: dict[str, SimulationResult] = field(default_factory=dict)
    baseline_name: str = ""

    def get_differences(self) -> dict[str, float]:
        """
        Calculate difference in net balance vs baseline for each scenario.

        Returns:
            Dict mapping scenario name to difference from baseline
        """
        if not self.baseline_name or self.baseline_name not in self.scenarios:
            return {}

        baseline_net = self.scenarios[self.baseline_name].net_balance
        return {
            name: result.net_balance - baseline_net
            for name, result in self.scenarios.items()
        }
