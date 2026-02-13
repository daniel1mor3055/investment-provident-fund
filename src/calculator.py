"""
Core calculation logic for Gemel Lehashkaa (Investment Provident Fund) simulation.

This module implements the financial formulas for:
- Monthly balance updates with fees and returns
- Annual contribution cap enforcement
- Real (inflation-adjusted) gain tax calculation
- Comparison between different scenarios
"""

import copy
from dataclasses import replace
from typing import Optional

import numpy as np
import pandas as pd

from .models import (
    ANNUITY_MIN_AGE,
    InvestmentInputs,
    MonthlyResult,
    SimulationResult,
    YearlyResult,
    ComparisonResult,
)


# ============================================================================
# Core Simulation
# ============================================================================


def calculate_monthly_rate(annual_rate: float) -> float:
    """
    Convert annual rate to monthly rate.

    Formula: r_m = (1 + R)^(1/12) - 1

    Args:
        annual_rate: Annual rate (e.g., 0.05 for 5%)

    Returns:
        Monthly rate
    """
    return (1 + annual_rate) ** (1 / 12) - 1


def simulate(inputs: InvestmentInputs) -> SimulationResult:
    """
    Run a complete simulation of Investment Provident Fund growth.

    Implements the formula:
        B_{t+1} = (B_t + D_t * (1 - F_d)) * (1 + r_m) * (1 - f_m)

    Where:
        - B_t: Balance at month t
        - D_t: Deposit at month t (respecting annual cap)
        - F_d: Deposit fee
        - r_m: Monthly return rate
        - f_m: Monthly AUM fee

    Tax calculation:
        - Lump sum: Tax = τ * max(B_T - Basis_real, 0)
        - Annuity after 60: Tax = 0

    Args:
        inputs: InvestmentInputs with all parameters

    Returns:
        SimulationResult with complete simulation data
    """
    # Convert annual rates to monthly
    monthly_return = calculate_monthly_rate(inputs.expected_return)
    monthly_fee = inputs.fee_aum / 12  # Simple division for AUM fee
    monthly_inflation = calculate_monthly_rate(inputs.inflation)

    # Initialize tracking variables
    balance = 0.0
    total_contributions = 0.0
    monthly_results: list[MonthlyResult] = []
    yearly_results: list[YearlyResult] = []

    # Track cap enforcement
    cap_was_binding = False
    cap_limited_amount = 0.0

    # Track yearly contributions for cap enforcement
    year_contributions = 0.0
    current_year = 1

    # Track real basis (inflation-adjusted contributions)
    # Each contribution is indexed forward to the withdrawal date
    total_months = inputs.months_of_contribution
    contribution_records: list[tuple[int, float]] = []  # (month, amount)

    for month in range(total_months):
        # Check if we're in a new year (every 12 months)
        year_of_contribution = (month // 12) + 1
        if year_of_contribution > current_year:
            # Save yearly result for previous year
            yearly_results.append(
                YearlyResult(
                    year=current_year,
                    age=inputs.start_age + current_year,
                    balance=balance,
                    contributions_ytd=year_contributions,
                    cumulative_contributions=total_contributions,
                    real_basis=_calculate_real_basis(
                        contribution_records, month, monthly_inflation
                    ),
                )
            )
            current_year = year_of_contribution
            year_contributions = 0.0

        # Calculate contribution respecting annual cap
        desired_contribution = inputs.monthly_contribution
        remaining_cap = inputs.annual_cap - year_contributions

        if remaining_cap <= 0:
            actual_contribution = 0.0
            cap_was_binding = True
            cap_limited_amount += desired_contribution
        elif desired_contribution > remaining_cap:
            actual_contribution = remaining_cap
            cap_was_binding = True
            cap_limited_amount += desired_contribution - remaining_cap
        else:
            actual_contribution = desired_contribution

        # Apply deposit fee
        net_contribution = actual_contribution * (1 - inputs.fee_deposit)

        # Update balance: add contribution, apply return, deduct AUM fee
        balance = (balance + net_contribution) * (1 + monthly_return) * (1 - monthly_fee)

        # Track contributions
        if actual_contribution > 0:
            contribution_records.append((month, actual_contribution))
        total_contributions += actual_contribution
        year_contributions += actual_contribution

        # Calculate current real basis
        current_real_basis = _calculate_real_basis(
            contribution_records, month, monthly_inflation
        )

        # Store monthly result
        monthly_results.append(
            MonthlyResult(
                month=month,
                age=inputs.start_age + (month / 12),
                balance=balance,
                contribution=actual_contribution,
                real_basis=current_real_basis,
                cumulative_contributions=total_contributions,
            )
        )

    # Add final year result
    if year_contributions > 0 or len(yearly_results) == 0:
        final_real_basis = _calculate_real_basis(
            contribution_records, total_months - 1, monthly_inflation
        )
        yearly_results.append(
            YearlyResult(
                year=current_year,
                age=inputs.withdraw_age,
                balance=balance,
                contributions_ytd=year_contributions,
                cumulative_contributions=total_contributions,
                real_basis=final_real_basis,
            )
        )

    # Calculate final real basis and tax
    real_basis = _calculate_real_basis(
        contribution_records, total_months - 1, monthly_inflation
    )
    real_gain = balance - real_basis

    # Determine tax based on withdrawal mode
    if inputs.withdrawal_mode == "annuity" and inputs.withdraw_age >= ANNUITY_MIN_AGE:
        tax_amount = 0.0
    else:
        tax_amount = inputs.capital_gains_tax * max(real_gain, 0)

    net_balance = balance - tax_amount

    return SimulationResult(
        inputs=inputs,
        monthly_results=monthly_results,
        yearly_results=yearly_results,
        gross_balance=balance,
        total_contributions=total_contributions,
        real_basis=real_basis,
        real_gain=real_gain,
        tax_amount=tax_amount,
        net_balance=net_balance,
        cap_was_binding=cap_was_binding,
        cap_limited_amount=cap_limited_amount,
    )


def _calculate_real_basis(
    contribution_records: list[tuple[int, float]],
    current_month: int,
    monthly_inflation: float,
) -> float:
    """
    Calculate the inflation-adjusted cost basis.

    Formula: Basis_real = Σ D_t * (1 + π_m)^(T - t)

    Each contribution is indexed forward from its deposit month
    to the current/withdrawal month.

    Args:
        contribution_records: List of (month, amount) tuples
        current_month: Current month number
        monthly_inflation: Monthly inflation rate

    Returns:
        Real (inflation-adjusted) cost basis
    """
    real_basis = 0.0
    for month, amount in contribution_records:
        months_elapsed = current_month - month
        # Index the contribution forward by inflation
        indexed_amount = amount * ((1 + monthly_inflation) ** months_elapsed)
        real_basis += indexed_amount
    return real_basis


# ============================================================================
# Comparison Functions
# ============================================================================


def compare_start_ages(
    base_inputs: InvestmentInputs,
    ages: Optional[list[int]] = None,
) -> ComparisonResult:
    """
    Compare simulation results for different starting ages.

    Args:
        base_inputs: Base input parameters (start_age will be overridden)
        ages: List of starting ages to compare (default: [30, 40, 50, 59])

    Returns:
        ComparisonResult with scenarios keyed by "Age {age}"
    """
    if ages is None:
        ages = [30, 40, 50, 59]

    scenarios: dict[str, SimulationResult] = {}

    for age in ages:
        if age >= base_inputs.withdraw_age:
            continue  # Skip invalid combinations

        modified_inputs = replace(base_inputs, start_age=age)
        result = simulate(modified_inputs)
        scenarios[f"Age {age}"] = result

    # Use the earliest start age as baseline
    baseline_name = f"Age {min(ages)}" if ages else ""

    return ComparisonResult(scenarios=scenarios, baseline_name=baseline_name)


def compare_withdrawal_modes(
    inputs: InvestmentInputs,
) -> dict[str, SimulationResult]:
    """
    Compare lump sum vs annuity withdrawal modes.

    Args:
        inputs: Input parameters (withdrawal_mode will be overridden)

    Returns:
        Dict with "Lump Sum" and "Annuity" results
    """
    lump_inputs = replace(inputs, withdrawal_mode="lump")
    annuity_inputs = replace(inputs, withdrawal_mode="annuity")

    return {
        "Lump Sum": simulate(lump_inputs),
        "Annuity": simulate(annuity_inputs),
    }


def compare_fees(
    base_inputs: InvestmentInputs,
    fee_levels: Optional[list[float]] = None,
) -> dict[str, SimulationResult]:
    """
    Compare simulation results for different AUM fee levels.

    Args:
        base_inputs: Base input parameters
        fee_levels: List of AUM fee rates (default: [0.004, 0.0065, 0.0105])

    Returns:
        Dict with results keyed by fee level description
    """
    if fee_levels is None:
        fee_levels = [0.004, 0.0065, 0.0105]  # Low, Medium, High (max legal)

    results: dict[str, SimulationResult] = {}

    for fee in fee_levels:
        modified_inputs = replace(base_inputs, fee_aum=fee)
        result = simulate(modified_inputs)
        results[f"{fee:.2%} AUM Fee"] = result

    return results


# ============================================================================
# Sensitivity Analysis
# ============================================================================


def generate_sensitivity_matrix(
    base_inputs: InvestmentInputs,
    param1_name: str,
    param1_values: list[float],
    param2_name: str,
    param2_values: list[float],
    output_metric: str = "net_balance",
) -> pd.DataFrame:
    """
    Generate a sensitivity matrix for two parameters.

    Args:
        base_inputs: Base input parameters
        param1_name: Name of first parameter (row axis)
        param1_values: Values to test for first parameter
        param2_name: Name of second parameter (column axis)
        param2_values: Values to test for second parameter
        output_metric: Which result metric to show ("net_balance", "tax_amount", etc.)

    Returns:
        DataFrame with param1 as index, param2 as columns, values are the metric
    """
    matrix = np.zeros((len(param1_values), len(param2_values)))

    for i, p1_val in enumerate(param1_values):
        for j, p2_val in enumerate(param2_values):
            # Create modified inputs
            modified = copy.copy(base_inputs)
            setattr(modified, param1_name, p1_val)
            setattr(modified, param2_name, p2_val)

            # Run simulation
            try:
                result = simulate(modified)
                matrix[i, j] = getattr(result, output_metric)
            except (ValueError, AttributeError):
                matrix[i, j] = np.nan

    # Create DataFrame with formatted labels
    df = pd.DataFrame(
        matrix,
        index=[_format_param_value(param1_name, v) for v in param1_values],
        columns=[_format_param_value(param2_name, v) for v in param2_values],
    )
    df.index.name = param1_name
    df.columns.name = param2_name

    return df


def _format_param_value(param_name: str, value: float) -> str:
    """Format parameter value for display."""
    if param_name in ("expected_return", "fee_aum", "fee_deposit", "inflation"):
        return f"{value:.2%}"
    elif param_name == "start_age":
        return f"Age {int(value)}"
    elif param_name == "monthly_contribution":
        return f"₪{value:,.0f}"
    else:
        return str(value)


def calculate_fee_impact(
    base_inputs: InvestmentInputs,
    fee_range: Optional[list[float]] = None,
) -> pd.DataFrame:
    """
    Calculate the impact of different fee levels on final balance.

    Args:
        base_inputs: Base input parameters
        fee_range: List of fee rates to test

    Returns:
        DataFrame with fee levels and corresponding net balances
    """
    if fee_range is None:
        fee_range = [0.003, 0.004, 0.005, 0.006, 0.007, 0.008, 0.009, 0.0105]

    data = []
    for fee in fee_range:
        modified = replace(base_inputs, fee_aum=fee)
        result = simulate(modified)
        data.append(
            {
                "AUM Fee": fee,
                "AUM Fee %": f"{fee:.2%}",
                "Gross Balance": result.gross_balance,
                "Net Balance": result.net_balance,
                "Tax Amount": result.tax_amount,
                "Fee Cost": result.total_contributions
                * (1 + base_inputs.expected_return) ** base_inputs.years_of_contribution
                - result.gross_balance,
            }
        )

    return pd.DataFrame(data)


# ============================================================================
# DataFrame Generation
# ============================================================================


def generate_yearly_dataframe(result: SimulationResult) -> pd.DataFrame:
    """
    Convert simulation result to a yearly DataFrame for display.

    Args:
        result: SimulationResult from simulation

    Returns:
        DataFrame with yearly data
    """
    data = []
    for yr in result.yearly_results:
        data.append(
            {
                "Year": yr.year,
                "Age": yr.age,
                "Contributions (Year)": yr.contributions_ytd,
                "Total Contributions": yr.cumulative_contributions,
                "Balance": yr.balance,
                "Real Basis": yr.real_basis,
            }
        )

    df = pd.DataFrame(data)
    return df


def generate_comparison_dataframe(
    comparison: ComparisonResult,
) -> pd.DataFrame:
    """
    Generate a summary DataFrame comparing multiple scenarios.

    Args:
        comparison: ComparisonResult with multiple scenarios

    Returns:
        DataFrame with summary metrics for each scenario
    """
    data = []
    for name, result in comparison.scenarios.items():
        data.append(
            {
                "Scenario": name,
                "Years": result.inputs.years_of_contribution,
                "Total Contributions": result.total_contributions,
                "Gross Balance": result.gross_balance,
                "Tax": result.tax_amount,
                "Net Balance": result.net_balance,
                "Effective Tax Rate": result.effective_tax_rate,
                "Cap Binding": result.cap_was_binding,
            }
        )

    return pd.DataFrame(data)


def generate_start_age_comparison_df(
    base_inputs: InvestmentInputs,
    ages: Optional[list[int]] = None,
) -> pd.DataFrame:
    """
    Generate a DataFrame comparing different starting ages.

    Args:
        base_inputs: Base input parameters
        ages: List of starting ages to compare

    Returns:
        DataFrame with comparison data
    """
    comparison = compare_start_ages(base_inputs, ages)
    return generate_comparison_dataframe(comparison)
