"""
Gemel Lehashkaa (Investment Provident Fund) Analysis Tool.

A comprehensive simulation and analysis tool for Israeli Investment Provident Funds.
"""

from .models import (
    InvestmentInputs,
    SimulationResult,
    YearlyResult,
    MonthlyResult,
    ComparisonResult,
    ANNUAL_CAP_2026,
    MAX_FEE_AUM,
    MAX_FEE_DEPOSIT,
    MAX_FEE_ANNUITY,
    CAPITAL_GAINS_TAX,
    ANNUITY_MIN_AGE,
)

from .calculator import (
    simulate,
    compare_start_ages,
    compare_withdrawal_modes,
    compare_fees,
    generate_sensitivity_matrix,
    calculate_fee_impact,
    generate_yearly_dataframe,
    generate_comparison_dataframe,
)

__all__ = [
    # Models
    "InvestmentInputs",
    "SimulationResult",
    "YearlyResult",
    "MonthlyResult",
    "ComparisonResult",
    # Constants
    "ANNUAL_CAP_2026",
    "MAX_FEE_AUM",
    "MAX_FEE_DEPOSIT",
    "MAX_FEE_ANNUITY",
    "CAPITAL_GAINS_TAX",
    "ANNUITY_MIN_AGE",
    # Calculator functions
    "simulate",
    "compare_start_ages",
    "compare_withdrawal_modes",
    "compare_fees",
    "generate_sensitivity_matrix",
    "calculate_fee_impact",
    "generate_yearly_dataframe",
    "generate_comparison_dataframe",
]
