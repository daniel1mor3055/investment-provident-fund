"""Core calculation logic for Provident Fund vs Personal Investment comparison."""

from typing import Optional
import pandas as pd
import numpy as np

from .models import (
    ProvidentInputs,
    YearlyResult,
    TaxCalculation,
    AgeComparisonResult,
    ComparisonSummary,
    SensitivityPoint,
    MonthlyWithdrawalResult,
)


def calculate_future_value(
    annual_contribution: float,
    annual_return: float,
    years: int,
) -> float:
    """
    Calculate future value with annual contributions.

    Uses the future value of annuity formula:
    FV = PMT * [((1 + r)^n - 1) / r]

    Args:
        annual_contribution: Annual contribution amount
        annual_return: Annual return rate (e.g., 0.07 for 7%)
        years: Number of years

    Returns:
        Future value at the end of the period
    """
    if years <= 0:
        return 0.0
    
    if annual_return == 0:
        return annual_contribution * years
    
    # Future value of annuity (payments at end of each period)
    fv = annual_contribution * (((1 + annual_return) ** years - 1) / annual_return)
    return fv


def calculate_inflation_adjusted_contributions(
    annual_contribution: float,
    inflation_rate: float,
    years: int,
) -> float:
    """
    Calculate the inflation-adjusted value of contributions at withdrawal time.

    Each contribution is adjusted for inflation from the time it was made
    to the withdrawal date.

    Args:
        annual_contribution: Annual contribution amount
        inflation_rate: Annual inflation rate (e.g., 0.025 for 2.5%)
        years: Number of years

    Returns:
        Sum of inflation-adjusted contributions
    """
    if years <= 0:
        return 0.0
    
    # Each year's contribution is adjusted for remaining years of inflation
    # Year 1 contribution grows by inflation for (years-1) years
    # Year 2 contribution grows by inflation for (years-2) years
    # etc.
    total = 0.0
    for year in range(1, years + 1):
        years_to_grow = years - year
        adjusted = annual_contribution * ((1 + inflation_rate) ** years_to_grow)
        total += adjusted
    
    return total


def calculate_provident_tax(
    gross_balance: float,
    total_contributions: float,
    inflation_adjusted_contributions: float,
    capital_gains_tax: float,
    withdrawal_mode: str,
    age_at_withdrawal: int,
) -> TaxCalculation:
    """
    Calculate tax for Provident Fund withdrawal.

    - Lump sum: 25% tax on REAL gains (inflation-adjusted)
    - Annuity after 60: 0% tax on gains

    Args:
        gross_balance: Total balance at withdrawal
        total_contributions: Sum of nominal contributions
        inflation_adjusted_contributions: Inflation-adjusted contributions
        capital_gains_tax: Tax rate (e.g., 0.25)
        withdrawal_mode: "lump_sum" or "annuity"
        age_at_withdrawal: Age when withdrawing

    Returns:
        TaxCalculation with all details
    """
    nominal_gain = max(0, gross_balance - total_contributions)
    real_gain = max(0, gross_balance - inflation_adjusted_contributions)
    
    # Determine tax based on withdrawal mode
    if withdrawal_mode == "annuity" and age_at_withdrawal >= 60:
        # Annuity after 60: No tax on gains
        tax_amount = 0.0
    else:
        # Lump sum: 25% on real gains
        tax_amount = capital_gains_tax * real_gain
    
    net_balance = gross_balance - tax_amount
    
    return TaxCalculation(
        gross_balance=gross_balance,
        total_contributions=total_contributions,
        inflation_adjusted_contributions=inflation_adjusted_contributions,
        nominal_gain=nominal_gain,
        real_gain=real_gain,
        tax_amount=tax_amount,
        net_balance=net_balance,
    )


def calculate_personal_tax(
    gross_balance: float,
    total_contributions: float,
    capital_gains_tax: float,
) -> TaxCalculation:
    """
    Calculate tax for personal account withdrawal.

    Personal account: 25% tax on NOMINAL gains.

    Args:
        gross_balance: Total balance at withdrawal
        total_contributions: Sum of nominal contributions
        capital_gains_tax: Tax rate (e.g., 0.25)

    Returns:
        TaxCalculation with all details
    """
    nominal_gain = max(0, gross_balance - total_contributions)
    
    # Personal account: tax on nominal gains
    tax_amount = capital_gains_tax * nominal_gain
    net_balance = gross_balance - tax_amount
    
    return TaxCalculation(
        gross_balance=gross_balance,
        total_contributions=total_contributions,
        inflation_adjusted_contributions=total_contributions,  # Not relevant for personal
        nominal_gain=nominal_gain,
        real_gain=nominal_gain,  # Same as nominal for personal
        tax_amount=tax_amount,
        net_balance=net_balance,
    )


def calculate_comparison_for_starting_age(
    starting_age: int,
    inputs: ProvidentInputs,
) -> AgeComparisonResult:
    """
    Calculate comparison results for a specific starting age.

    Args:
        starting_age: Age at which investment begins
        inputs: All input parameters

    Returns:
        AgeComparisonResult with full comparison
    """
    investment_years = inputs.retirement_age - starting_age
    
    if investment_years <= 0:
        return AgeComparisonResult(
            starting_age=starting_age,
            retirement_age=inputs.retirement_age,
            investment_years=0,
            provident_gross=0,
            provident_contributions=0,
            provident_tax=0,
            provident_net=0,
            personal_gross=0,
            personal_contributions=0,
            personal_tax=0,
            personal_net=0,
            withdrawal_mode=inputs.withdrawal_mode,
        )
    
    # Use the same contribution for both accounts (apples-to-apples comparison)
    # The cap only applies in real-world limits, but for comparison we use equal amounts
    provident_contribution = inputs.annual_contribution
    personal_contribution = inputs.annual_contribution
    
    # Calculate net returns
    provident_net_return = inputs.get_provident_net_return()
    personal_net_return = inputs.get_personal_net_return()
    
    # Calculate future values
    provident_gross = calculate_future_value(
        provident_contribution, provident_net_return, investment_years
    )
    personal_gross = calculate_future_value(
        personal_contribution, personal_net_return, investment_years
    )
    
    # Calculate contributions
    provident_contributions = provident_contribution * investment_years
    personal_contributions = personal_contribution * investment_years
    
    # Calculate inflation-adjusted contributions for provident
    provident_inflation_adjusted = calculate_inflation_adjusted_contributions(
        provident_contribution, inputs.inflation_rate, investment_years
    )
    
    # Calculate taxes
    provident_tax_calc = calculate_provident_tax(
        gross_balance=provident_gross,
        total_contributions=provident_contributions,
        inflation_adjusted_contributions=provident_inflation_adjusted,
        capital_gains_tax=inputs.capital_gains_tax,
        withdrawal_mode=inputs.withdrawal_mode,
        age_at_withdrawal=inputs.retirement_age,
    )
    
    personal_tax_calc = calculate_personal_tax(
        gross_balance=personal_gross,
        total_contributions=personal_contributions,
        capital_gains_tax=inputs.capital_gains_tax,
    )
    
    return AgeComparisonResult(
        starting_age=starting_age,
        retirement_age=inputs.retirement_age,
        investment_years=investment_years,
        provident_gross=provident_gross,
        provident_contributions=provident_contributions,
        provident_tax=provident_tax_calc.tax_amount,
        provident_net=provident_tax_calc.net_balance,
        personal_gross=personal_gross,
        personal_contributions=personal_contributions,
        personal_tax=personal_tax_calc.tax_amount,
        personal_net=personal_tax_calc.net_balance,
        withdrawal_mode=inputs.withdrawal_mode,
    )


def find_crossover_age(
    inputs: ProvidentInputs,
    min_age: int = 18,
    max_age: int = 59,
) -> Optional[int]:
    """
    Find the starting age where Provident Fund becomes better than personal.

    Searches from max_age down to min_age to find the oldest age where
    Provident Fund first becomes advantageous.

    Args:
        inputs: All input parameters
        min_age: Minimum age to consider
        max_age: Maximum age to consider

    Returns:
        The crossover age, or None if Provident is never better
    """
    # Start from oldest age and work backwards
    # We want to find the LATEST age where provident is still better
    # because that tells us "from what age onwards should you use provident"
    
    crossover_age = None
    
    for age in range(min_age, max_age + 1):
        result = calculate_comparison_for_starting_age(age, inputs)
        if result.provident_wins:
            crossover_age = age
            break  # Found the first age where provident wins
    
    return crossover_age


def run_full_comparison(
    inputs: ProvidentInputs,
    min_age: int = 18,
    max_age: int = 59,
) -> ComparisonSummary:
    """
    Run a complete comparison across all starting ages.

    Args:
        inputs: All input parameters
        min_age: Minimum starting age to analyze
        max_age: Maximum starting age to analyze

    Returns:
        ComparisonSummary with results for all ages
    """
    age_results = []
    
    for age in range(min_age, max_age + 1):
        result = calculate_comparison_for_starting_age(age, inputs)
        age_results.append(result)
    
    crossover_age = find_crossover_age(inputs, min_age, max_age)
    
    return ComparisonSummary(
        inputs=inputs,
        age_results=age_results,
        crossover_age=crossover_age,
        provident_net_return=inputs.get_provident_net_return(),
        personal_net_return=inputs.get_personal_net_return(),
    )


def generate_yearly_growth(
    inputs: ProvidentInputs,
) -> list[YearlyResult]:
    """
    Generate year-by-year growth data for visualization.

    Args:
        inputs: All input parameters

    Returns:
        List of YearlyResult for each year from current age to retirement
    """
    results = []
    investment_years = inputs.get_investment_years()
    
    if investment_years <= 0:
        return results
    
    # Use the same contribution for both accounts (apples-to-apples comparison)
    provident_contribution = inputs.annual_contribution
    personal_contribution = inputs.annual_contribution

    provident_net_return = inputs.get_provident_net_return()
    personal_net_return = inputs.get_personal_net_return()

    for year in range(1, investment_years + 1):
        age = inputs.current_age + year
        
        provident_fv = calculate_future_value(
            provident_contribution, provident_net_return, year
        )
        provident_contributions = provident_contribution * year
        
        personal_fv = calculate_future_value(
            personal_contribution, personal_net_return, year
        )
        personal_contributions = personal_contribution * year
        
        results.append(YearlyResult(
            year=year,
            age=age,
            provident_fv=provident_fv,
            provident_contributions=provident_contributions,
            personal_fv=personal_fv,
            personal_contributions=personal_contributions,
        ))
    
    return results


def generate_comparison_dataframe(
    summary: ComparisonSummary,
) -> pd.DataFrame:
    """
    Generate a pandas DataFrame from comparison results.

    Args:
        summary: ComparisonSummary from run_full_comparison

    Returns:
        DataFrame with comparison data by starting age
    """
    data = []
    for result in summary.age_results:
        data.append({
            "Starting Age": result.starting_age,
            "Years to Invest": result.investment_years,
            "Provident Gross": result.provident_gross,
            "Provident Tax": result.provident_tax,
            "Provident Net": result.provident_net,
            "Personal Gross": result.personal_gross,
            "Personal Tax": result.personal_tax,
            "Personal Net": result.personal_net,
            "Difference": result.difference,
            "Difference %": result.difference_pct,
            "Winner": result.winner,
        })
    return pd.DataFrame(data)


def generate_yearly_dataframe(
    yearly_results: list[YearlyResult],
) -> pd.DataFrame:
    """
    Generate a pandas DataFrame from yearly growth results.

    Args:
        yearly_results: List of YearlyResult

    Returns:
        DataFrame with yearly growth data
    """
    data = []
    for yr in yearly_results:
        data.append({
            "Year": yr.year,
            "Age": yr.age,
            "Provident Balance": yr.provident_fv,
            "Provident Contributions": yr.provident_contributions,
            "Provident Gain": yr.provident_gain,
            "Personal Balance": yr.personal_fv,
            "Personal Contributions": yr.personal_contributions,
            "Personal Gain": yr.personal_gain,
        })
    return pd.DataFrame(data)


def generate_sensitivity_analysis(
    base_inputs: ProvidentInputs,
    return_rates: list[float] = None,
    inflation_rates: list[float] = None,
) -> list[SensitivityPoint]:
    """
    Generate sensitivity analysis data.

    Args:
        base_inputs: Base input parameters
        return_rates: List of return rates to test
        inflation_rates: List of inflation rates to test

    Returns:
        List of SensitivityPoint for each combination
    """
    if return_rates is None:
        return_rates = [0.04, 0.05, 0.06, 0.07, 0.08, 0.09, 0.10]
    
    if inflation_rates is None:
        inflation_rates = [0.01, 0.02, 0.025, 0.03, 0.04]
    
    results = []
    
    for ret in return_rates:
        for inf in inflation_rates:
            # Create modified inputs (use same return for both in sensitivity analysis)
            modified_inputs = ProvidentInputs(
                current_age=base_inputs.current_age,
                retirement_age=base_inputs.retirement_age,
                life_expectancy=base_inputs.life_expectancy,
                annual_contribution=base_inputs.annual_contribution,
                annual_cap=base_inputs.annual_cap,
                provident_expected_return=ret,
                personal_expected_return=ret,  # Same return for sensitivity analysis
                inflation_rate=inf,
                provident_mgmt_fee=base_inputs.provident_mgmt_fee,
                personal_mgmt_fee=base_inputs.personal_mgmt_fee,
                capital_gains_tax=base_inputs.capital_gains_tax,
                withdrawal_mode=base_inputs.withdrawal_mode,
            )
            
            # Find crossover
            crossover = find_crossover_age(modified_inputs)
            
            # Calculate advantage at age 30
            test_inputs = ProvidentInputs(
                current_age=30,
                retirement_age=base_inputs.retirement_age,
                life_expectancy=base_inputs.life_expectancy,
                annual_contribution=base_inputs.annual_contribution,
                annual_cap=base_inputs.annual_cap,
                provident_expected_return=ret,
                personal_expected_return=ret,
                inflation_rate=inf,
                provident_mgmt_fee=base_inputs.provident_mgmt_fee,
                personal_mgmt_fee=base_inputs.personal_mgmt_fee,
                capital_gains_tax=base_inputs.capital_gains_tax,
                withdrawal_mode=base_inputs.withdrawal_mode,
            )
            result_at_30 = calculate_comparison_for_starting_age(30, test_inputs)
            
            results.append(SensitivityPoint(
                return_rate=ret,
                inflation_rate=inf,
                crossover_age=crossover,
                provident_advantage_at_30=result_at_30.difference,
            ))
    
    return results


def generate_sensitivity_matrix(
    base_inputs: ProvidentInputs,
    return_rates: list[float] = None,
    inflation_rates: list[float] = None,
) -> pd.DataFrame:
    """
    Generate a sensitivity matrix as a DataFrame.

    Shows crossover age for different combinations of return and inflation.

    Args:
        base_inputs: Base input parameters
        return_rates: List of return rates to test
        inflation_rates: List of inflation rates to test

    Returns:
        DataFrame with return rates as rows and inflation rates as columns
    """
    if return_rates is None:
        return_rates = [0.04, 0.05, 0.06, 0.07, 0.08, 0.09, 0.10]
    
    if inflation_rates is None:
        inflation_rates = [0.01, 0.02, 0.025, 0.03, 0.04]
    
    data = []
    for ret in return_rates:
        row = {"Return": f"{ret*100:.0f}%"}
        for inf in inflation_rates:
            modified_inputs = ProvidentInputs(
                current_age=base_inputs.current_age,
                retirement_age=base_inputs.retirement_age,
                life_expectancy=base_inputs.life_expectancy,
                annual_contribution=base_inputs.annual_contribution,
                annual_cap=base_inputs.annual_cap,
                provident_expected_return=ret,
                personal_expected_return=ret,  # Same return for sensitivity matrix
                inflation_rate=inf,
                provident_mgmt_fee=base_inputs.provident_mgmt_fee,
                personal_mgmt_fee=base_inputs.personal_mgmt_fee,
                capital_gains_tax=base_inputs.capital_gains_tax,
                withdrawal_mode=base_inputs.withdrawal_mode,
            )
            crossover = find_crossover_age(modified_inputs)
            row[f"Inflation {inf*100:.1f}%"] = crossover if crossover else "Never"
        data.append(row)
    
    df = pd.DataFrame(data)
    df.set_index("Return", inplace=True)
    return df


def calculate_tax_comparison(
    inputs: ProvidentInputs,
) -> dict:
    """
    Calculate detailed tax comparison for visualization.

    Args:
        inputs: All input parameters

    Returns:
        Dictionary with tax details for both options
    """
    result = calculate_comparison_for_starting_age(inputs.current_age, inputs)
    investment_years = inputs.get_investment_years()
    
    # Use same contribution for both (apples-to-apples)
    provident_contribution = inputs.annual_contribution
    provident_contributions = provident_contribution * investment_years
    provident_inflation_adjusted = calculate_inflation_adjusted_contributions(
        provident_contribution, inputs.inflation_rate, investment_years
    )
    
    personal_contribution = inputs.annual_contribution
    personal_contributions = personal_contribution * investment_years
    
    return {
        "provident": {
            "gross": result.provident_gross,
            "contributions": provident_contributions,
            "inflation_adjusted_contributions": provident_inflation_adjusted,
            "nominal_gain": result.provident_gross - provident_contributions,
            "real_gain": result.provident_gross - provident_inflation_adjusted,
            "tax": result.provident_tax,
            "net": result.provident_net,
            "tax_type": "0% (Annuity)" if inputs.withdrawal_mode == "annuity" and inputs.retirement_age >= 60 else "25% Real Gains",
        },
        "personal": {
            "gross": result.personal_gross,
            "contributions": personal_contributions,
            "nominal_gain": result.personal_gross - personal_contributions,
            "tax": result.personal_tax,
            "net": result.personal_net,
            "tax_type": "25% Nominal Gains",
        },
    }


def calculate_monthly_withdrawal(
    balance: float,
    withdrawal_years: int,
    annual_return_during_withdrawal: float,
) -> float:
    """
    Calculate sustainable monthly withdrawal using annuity formula.
    
    This calculates how much you can withdraw monthly so that the balance
    is depleted over the specified number of years, assuming the remaining
    balance earns the specified return.
    
    Uses the PMT formula: PMT = PV * [r / (1 - (1 + r)^-n)]
    
    Args:
        balance: Total balance at start of withdrawals
        withdrawal_years: Number of years to withdraw over
        annual_return_during_withdrawal: Expected annual return during withdrawal
        
    Returns:
        Monthly withdrawal amount
    """
    if withdrawal_years <= 0 or balance <= 0:
        return 0.0
    
    # Convert to monthly rate and periods
    monthly_rate = annual_return_during_withdrawal / 12
    total_months = withdrawal_years * 12
    
    if monthly_rate == 0:
        return balance / total_months
    
    # PMT formula for annuity
    monthly_withdrawal = balance * (monthly_rate / (1 - (1 + monthly_rate) ** -total_months))
    return monthly_withdrawal


def calculate_monthly_withdrawal_comparison(
    inputs: ProvidentInputs,
) -> MonthlyWithdrawalResult:
    """
    Calculate monthly withdrawal comparison between provident fund and personal account.
    
    For provident fund annuity (קצבה): 0% tax on withdrawals after age 60
    For personal account: 25% capital gains tax on the gains portion of each withdrawal
    
    Args:
        inputs: All input parameters
        
    Returns:
        MonthlyWithdrawalResult with comparison details
    """
    # Get the comparison result at retirement
    result = calculate_comparison_for_starting_age(inputs.current_age, inputs)
    
    # Calculate withdrawal period
    withdrawal_years = inputs.life_expectancy - inputs.retirement_age
    if withdrawal_years <= 0:
        withdrawal_years = 1  # Minimum 1 year
    
    # Use a conservative return during withdrawal (lower than accumulation phase)
    # Typically 3-4% is assumed for retirement withdrawals
    withdrawal_return = 0.03  # 3% conservative return during withdrawal
    
    # Calculate gross monthly withdrawals
    provident_gross_monthly = calculate_monthly_withdrawal(
        result.provident_gross, withdrawal_years, withdrawal_return
    )
    personal_gross_monthly = calculate_monthly_withdrawal(
        result.personal_gross, withdrawal_years, withdrawal_return
    )
    
    # Provident fund annuity: 0% tax (after age 60)
    provident_net_monthly = provident_gross_monthly  # No tax on annuity
    
    # Personal account: 25% tax on gains portion
    # Calculate the gain ratio (what portion of the balance is gains vs contributions)
    if result.personal_gross > 0:
        gain_ratio = (result.personal_gross - result.personal_contributions) / result.personal_gross
    else:
        gain_ratio = 0.0
    
    # Each withdrawal is proportionally gains + principal
    # Only the gains portion is taxed at 25%
    taxable_per_month = personal_gross_monthly * gain_ratio
    tax_per_month = taxable_per_month * inputs.capital_gains_tax
    personal_net_monthly = personal_gross_monthly - tax_per_month
    
    return MonthlyWithdrawalResult(
        provident_balance=result.provident_gross,
        provident_contributions=result.provident_contributions,
        provident_gross_monthly=provident_gross_monthly,
        provident_net_monthly=provident_net_monthly,
        personal_balance=result.personal_gross,
        personal_contributions=result.personal_contributions,
        personal_gross_monthly=personal_gross_monthly,
        personal_net_monthly=personal_net_monthly,
        personal_tax_per_month=tax_per_month,
        withdrawal_years=withdrawal_years,
        withdrawal_return=withdrawal_return,
    )
