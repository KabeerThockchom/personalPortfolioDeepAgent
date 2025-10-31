from src.utils.tool_logger import logged_tool

"""Goal planning and retirement calculation tools."""

from langchain_core.tools import tool
import numpy as np
from typing import Dict, List


@tool
@logged_tool
def calculate_retirement_gap(
    current_savings: float,
    desired_annual_income: float,
    years_until_retirement: int,
    expected_return: float = 0.07,
    inflation_rate: float = 0.03,
    retirement_years: int = 30
) -> Dict:
    """
    Calculate retirement savings gap and required contributions.

    Args:
        current_savings: Current retirement savings total
        desired_annual_income: Desired annual income in retirement (today's dollars)
        years_until_retirement: Years until retirement
        expected_return: Expected annual return (default 7%)
        inflation_rate: Expected inflation rate (default 3%)
        retirement_years: Years in retirement (default 30)

    Returns:
        Retirement gap analysis with required savings
    """
    # Adjust desired income for inflation
    future_income_needed = desired_annual_income * ((1 + inflation_rate) ** years_until_retirement)

    # Calculate corpus needed (using 4% withdrawal rule, adjusted)
    withdrawal_rate = 0.04
    corpus_needed = future_income_needed / withdrawal_rate

    # Project current savings to retirement
    future_value_current = current_savings * ((1 + expected_return) ** years_until_retirement)

    # Gap
    gap = corpus_needed - future_value_current

    # Required monthly contribution to close gap
    months = years_until_retirement * 12
    monthly_return = expected_return / 12

    if gap > 0 and months > 0 and monthly_return > 0:
        # Future value of annuity formula solved for payment
        required_monthly = (gap * monthly_return) / (((1 + monthly_return) ** months) - 1)
    else:
        required_monthly = 0

    return {
        "current_savings": round(current_savings, 2),
        "corpus_needed": round(corpus_needed, 2),
        "projected_savings_at_retirement": round(future_value_current, 2),
        "gap": round(gap, 2),
        "required_monthly_contribution": round(required_monthly, 2),
        "on_track": gap <= 0,
        "years_until_retirement": years_until_retirement
    }


@tool
@logged_tool
def run_monte_carlo_simulation(
    current_savings: float,
    monthly_contribution: float,
    years: int,
    expected_return: float = 0.07,
    volatility: float = 0.15,
    simulations: int = 1000
) -> Dict:
    """
    Run Monte Carlo simulation for retirement projections.

    Args:
        current_savings: Current savings balance
        monthly_contribution: Monthly contribution amount
        years: Number of years to simulate
        expected_return: Expected annual return (default 7%)
        volatility: Annual volatility/std dev (default 15%)
        simulations: Number of simulations (default 1000)

    Returns:
        Monte Carlo results with percentiles
    """
    np.random.seed(42)  # For reproducibility

    months = years * 12
    monthly_return = expected_return / 12
    monthly_volatility = volatility / np.sqrt(12)

    final_balances = []

    for _ in range(simulations):
        balance = current_savings

        for month in range(months):
            # Random return for this month
            monthly_rate = np.random.normal(monthly_return, monthly_volatility)

            # Apply return and add contribution
            balance = balance * (1 + monthly_rate) + monthly_contribution

        final_balances.append(balance)

    final_balances = np.array(final_balances)

    return {
        "median": round(np.median(final_balances), 2),
        "mean": round(np.mean(final_balances), 2),
        "percentile_10": round(np.percentile(final_balances, 10), 2),
        "percentile_25": round(np.percentile(final_balances, 25), 2),
        "percentile_75": round(np.percentile(final_balances, 75), 2),
        "percentile_90": round(np.percentile(final_balances, 90), 2),
        "best_case": round(np.max(final_balances), 2),
        "worst_case": round(np.min(final_balances), 2),
        "simulations_run": simulations,
        "success_rate": round(np.sum(final_balances >= current_savings) / simulations * 100, 2)
    }


@tool
@logged_tool
def calculate_required_savings_rate(
    current_age: int,
    retirement_age: int,
    current_savings: float,
    target_corpus: float,
    current_income: float,
    expected_return: float = 0.07
) -> Dict:
    """
    Calculate required savings rate to reach retirement goal.

    Args:
        current_age: Current age
        retirement_age: Target retirement age
        current_savings: Current retirement savings
        target_corpus: Target retirement corpus
        current_income: Current annual income
        expected_return: Expected annual return (default 7%)

    Returns:
        Required savings rate as percentage of income
    """
    years = retirement_age - current_age
    months = years * 12
    monthly_return = expected_return / 12

    # Future value of current savings
    fv_current = current_savings * ((1 + expected_return) ** years)

    # Additional amount needed
    additional_needed = target_corpus - fv_current

    if additional_needed <= 0:
        return {
            "required_monthly_savings": 0,
            "required_savings_rate_pct": 0,
            "currently_on_track": True,
            "surplus": round(abs(additional_needed), 2)
        }

    # Calculate required monthly payment
    if monthly_return > 0:
        required_monthly = (additional_needed * monthly_return) / (((1 + monthly_return) ** months) - 1)
    else:
        required_monthly = additional_needed / months

    # As percentage of income
    monthly_income = current_income / 12
    savings_rate_pct = (required_monthly / monthly_income * 100) if monthly_income > 0 else 0

    return {
        "required_monthly_savings": round(required_monthly, 2),
        "required_annual_savings": round(required_monthly * 12, 2),
        "required_savings_rate_pct": round(savings_rate_pct, 2),
        "currently_on_track": False,
        "years_to_goal": years
    }


@tool
@logged_tool
def calculate_fire_number(
    annual_expenses: float,
    withdrawal_rate: float = 0.04,
    safety_margin: float = 1.25
) -> Dict:
    """
    Calculate FIRE (Financial Independence Retire Early) number.

    Args:
        annual_expenses: Annual expenses to cover
        withdrawal_rate: Safe withdrawal rate (default 4%)
        safety_margin: Safety margin multiplier (default 1.25 = 25% buffer)

    Returns:
        FIRE number and related metrics
    """
    base_fire_number = annual_expenses / withdrawal_rate
    safe_fire_number = base_fire_number * safety_margin

    # "Fat FIRE" (more comfortable)
    fat_fire = annual_expenses * 1.5 / withdrawal_rate

    # "Lean FIRE" (minimal expenses)
    lean_fire = annual_expenses * 0.7 / withdrawal_rate

    return {
        "annual_expenses": round(annual_expenses, 2),
        "base_fire_number": round(base_fire_number, 2),
        "safe_fire_number": round(safe_fire_number, 2),
        "lean_fire_number": round(lean_fire, 2),
        "fat_fire_number": round(fat_fire, 2),
        "withdrawal_rate_used": withdrawal_rate
    }


@tool
@logged_tool
def project_college_funding(
    current_savings: float,
    target_amount: float,
    years_until_needed: int,
    monthly_contribution: float,
    expected_return: float = 0.06
) -> Dict:
    """
    Project college funding goal achievement.

    Args:
        current_savings: Current 529/college savings
        target_amount: Target amount needed
        years_until_needed: Years until college starts
        monthly_contribution: Monthly contribution
        expected_return: Expected annual return (default 6%)

    Returns:
        College funding projection
    """
    months = years_until_needed * 12
    monthly_return = expected_return / 12

    # Future value of current savings
    fv_current = current_savings * ((1 + expected_return) ** years_until_needed)

    # Future value of monthly contributions (annuity)
    if monthly_return > 0:
        fv_contributions = monthly_contribution * ((((1 + monthly_return) ** months) - 1) / monthly_return)
    else:
        fv_contributions = monthly_contribution * months

    # Total projected
    total_projected = fv_current + fv_contributions

    # Gap
    gap = target_amount - total_projected

    # Progress percentage
    progress_pct = (total_projected / target_amount * 100) if target_amount > 0 else 0

    return {
        "current_savings": round(current_savings, 2),
        "target_amount": round(target_amount, 2),
        "projected_balance": round(total_projected, 2),
        "gap": round(gap, 2),
        "on_track": gap <= 0,
        "progress_percentage": round(progress_pct, 2),
        "years_until_needed": years_until_needed,
        "monthly_contribution": round(monthly_contribution, 2)
    }


@tool
@logged_tool
def generate_monte_carlo_chart(percentiles: Dict[str, float], years: int) -> Dict:
    """
    Generate Monte Carlo fan chart data.

    Args:
        percentiles: Dictionary with p10, p25, p50, p75, p90 values
        years: Number of years projected

    Returns:
        Chart data structure for UI rendering
    """
    return {
        "chart_type": "fan",
        "title": f"Retirement Projection - {years} Year Monte Carlo Simulation",
        "data": {
            "years": years,
            "percentiles": percentiles,
            "confidence_intervals": [
                {"level": "10th-90th", "range": [percentiles.get("percentile_10", 0), percentiles.get("percentile_90", 0)]},
                {"level": "25th-75th", "range": [percentiles.get("percentile_25", 0), percentiles.get("percentile_75", 0)]},
                {"level": "50th (Median)", "value": percentiles.get("median", 0)}
            ]
        },
        "library": "plotly"
    }
