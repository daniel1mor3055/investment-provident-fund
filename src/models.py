"""Data models for Provident Fund vs Personal Investment comparison."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class ProvidentInputs:
    """Input parameters for the investment comparison."""

    current_age: int  # Current age of the investor
    retirement_age: int  # Target withdrawal age (typically 60 for annuity benefit)
    life_expectancy: int  # Expected age at death (for withdrawal calculations)
    annual_contribution: float  # Annual contribution amount in NIS
    annual_cap: float  # Annual contribution cap (83,641 for 2026)
    provident_expected_return: float  # Expected annual return for provident fund (e.g., 0.07 for 7%)
    personal_expected_return: float  # Expected annual return for personal account (e.g., 0.08 for 8%)
    inflation_rate: float  # Annual inflation rate for real gains calculation
    provident_mgmt_fee: float  # Annual management fee for provident fund (e.g., 0.006 for 0.6%)
    personal_mgmt_fee: float  # Annual management fee for personal account (e.g., 0.001 for 0.1%)
    capital_gains_tax: float  # Capital gains tax rate (e.g., 0.25 for 25%)
    withdrawal_mode: str  # "lump_sum" or "annuity"

    def get_provident_net_return(self) -> float:
        """Calculate the net return for Provident Fund after management fees."""
        # Net return = (1 + gross) * (1 - fee) - 1
        return (1 + self.provident_expected_return) * (1 - self.provident_mgmt_fee) - 1

    def get_personal_net_return(self) -> float:
        """Calculate the net return for personal account after management fees."""
        return (1 + self.personal_expected_return) * (1 - self.personal_mgmt_fee) - 1

    def get_investment_years(self) -> int:
        """Calculate the number of years from current age to retirement."""
        return max(0, self.retirement_age - self.current_age)

    def get_effective_contribution(self) -> float:
        """Get the effective annual contribution respecting the cap."""
        return min(self.annual_contribution, self.annual_cap)


@dataclass
class YearlyResult:
    """Results for a single year in the comparison."""

    year: int  # Year number (1, 2, 3, ...)
    age: int  # Age at this year
    provident_fv: float  # Future value in Provident Fund (gross)
    provident_contributions: float  # Total contributions to date
    personal_fv: float  # Future value in personal account (gross)
    personal_contributions: float  # Total contributions to date

    @property
    def provident_gain(self) -> float:
        """Nominal gain in Provident Fund."""
        return self.provident_fv - self.provident_contributions

    @property
    def personal_gain(self) -> float:
        """Nominal gain in personal account."""
        return self.personal_fv - self.personal_contributions


@dataclass
class TaxCalculation:
    """Tax calculation details for a withdrawal."""

    gross_balance: float  # Balance before tax
    total_contributions: float  # Sum of all contributions
    inflation_adjusted_contributions: float  # Contributions adjusted for inflation
    nominal_gain: float  # gross_balance - total_contributions
    real_gain: float  # gross_balance - inflation_adjusted_contributions
    tax_amount: float  # Tax to be paid
    net_balance: float  # Balance after tax

    @property
    def effective_tax_rate(self) -> float:
        """Calculate the effective tax rate on the gross balance."""
        if self.gross_balance == 0:
            return 0.0
        return self.tax_amount / self.gross_balance


@dataclass
class AgeComparisonResult:
    """Comparison result for a specific starting age."""

    starting_age: int  # Age at which investment started
    retirement_age: int  # Target withdrawal age
    investment_years: int  # Number of years invested
    
    # Provident Fund results
    provident_gross: float  # Gross balance at retirement
    provident_contributions: float  # Total contributions
    provident_tax: float  # Tax paid (0 for annuity, 25% real for lump sum)
    provident_net: float  # Net balance after tax
    
    # Personal account results
    personal_gross: float  # Gross balance at retirement
    personal_contributions: float  # Total contributions
    personal_tax: float  # Tax paid (25% on nominal gains)
    personal_net: float  # Net balance after tax
    
    # Comparison
    withdrawal_mode: str  # "lump_sum" or "annuity"

    @property
    def difference(self) -> float:
        """Net difference (provident - personal). Positive = Provident wins."""
        return self.provident_net - self.personal_net

    @property
    def difference_pct(self) -> float:
        """Percentage difference relative to personal account."""
        if self.personal_net == 0:
            return 0.0
        return (self.provident_net - self.personal_net) / self.personal_net * 100

    @property
    def winner(self) -> str:
        """Which option wins."""
        if self.difference > 0:
            return "Provident Fund"
        elif self.difference < 0:
            return "Personal Account"
        else:
            return "Tie"

    @property
    def provident_wins(self) -> bool:
        """True if Provident Fund has higher net value."""
        return self.difference > 0


@dataclass
class ComparisonSummary:
    """Summary of the full comparison across all ages."""

    inputs: ProvidentInputs
    age_results: list[AgeComparisonResult]  # Results for each starting age
    crossover_age: Optional[int]  # Age where Provident becomes better (None if never)
    provident_net_return: float  # Calculated net return for Provident Fund
    personal_net_return: float  # Calculated net return for personal account

    @property
    def current_age_result(self) -> Optional[AgeComparisonResult]:
        """Get the result for the user's current age."""
        for result in self.age_results:
            if result.starting_age == self.inputs.current_age:
                return result
        return None

    @property
    def winner_at_current_age(self) -> str:
        """Which option wins at the user's current age."""
        result = self.current_age_result
        if result:
            return result.winner
        return "Unknown"

    @property
    def has_crossover(self) -> bool:
        """Whether there is a crossover point."""
        return self.crossover_age is not None


@dataclass
class SensitivityPoint:
    """A single point in sensitivity analysis."""

    return_rate: float
    inflation_rate: float
    crossover_age: Optional[int]
    provident_advantage_at_30: float  # Difference if starting at age 30


@dataclass
class MonthlyWithdrawalResult:
    """Results for monthly withdrawal (קצבה) comparison."""

    # Provident Fund (annuity mode - 0% tax)
    provident_balance: float  # Total balance at retirement
    provident_contributions: float  # Total contributions
    provident_gross_monthly: float  # Monthly withdrawal before any considerations
    provident_net_monthly: float  # Net monthly withdrawal (same as gross for annuity)
    
    # Personal Account (25% tax on gains portion)
    personal_balance: float  # Total balance at retirement
    personal_contributions: float  # Total contributions
    personal_gross_monthly: float  # Monthly withdrawal before tax
    personal_net_monthly: float  # Net monthly withdrawal after tax on gains
    personal_tax_per_month: float  # Tax paid per month
    
    # Comparison
    withdrawal_years: int  # Number of years in retirement
    withdrawal_return: float  # Expected return during withdrawal period

    @property
    def monthly_difference(self) -> float:
        """Net monthly difference (provident - personal). Positive = Provident wins."""
        return self.provident_net_monthly - self.personal_net_monthly

    @property
    def monthly_difference_pct(self) -> float:
        """Percentage difference in monthly withdrawal."""
        if self.personal_net_monthly == 0:
            return 0.0
        return (self.provident_net_monthly - self.personal_net_monthly) / self.personal_net_monthly * 100

    @property
    def personal_gain_ratio(self) -> float:
        """Ratio of gains to total balance in personal account."""
        if self.personal_balance == 0:
            return 0.0
        return (self.personal_balance - self.personal_contributions) / self.personal_balance

    @property
    def lifetime_tax_savings(self) -> float:
        """Total tax saved over retirement by using provident fund annuity."""
        return self.personal_tax_per_month * 12 * self.withdrawal_years
