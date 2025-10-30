"""Debt management calculation tools."""

from langchain_core.tools import tool
from typing import Dict, List


@tool
def calculate_debt_payoff_timeline(
    debts: List[Dict],
    extra_monthly_payment: float = 0
) -> Dict:
    """
    Calculate debt payoff timeline with extra payments.

    Args:
        debts: List of debts with balance, rate, min_payment
        extra_monthly_payment: Extra payment to apply each month

    Returns:
        Payoff timeline and total interest
    """
    total_balance = sum(d["current_balance"] for d in debts)
    total_min_payment = sum(d["monthly_payment"] for d in debts)

    # Calculate months to payoff with extra payment
    total_monthly = total_min_payment + extra_monthly_payment

    # Simplified calculation (assumes weighted average rate)
    if total_balance > 0:
        weighted_rate = sum(d["current_balance"] * d["interest_rate"] for d in debts) / total_balance
        monthly_rate = weighted_rate / 100 / 12
    else:
        return {
            "months_to_payoff": 0,
            "total_interest_paid": 0,
            "debt_free_date": "Already debt free"
        }

    # Calculate payoff timeline
    months = 0
    remaining = total_balance
    total_interest = 0

    while remaining > 0 and months < 600:  # Cap at 50 years
        interest_charge = remaining * monthly_rate
        principal_payment = min(total_monthly - interest_charge, remaining)

        if principal_payment <= 0:
            months = 600  # Can't pay off with current payment
            break

        total_interest += interest_charge
        remaining -= principal_payment
        months += 1

    years = months / 12

    return {
        "total_debt": round(total_balance, 2),
        "total_monthly_payment": round(total_monthly, 2),
        "months_to_payoff": months,
        "years_to_payoff": round(years, 1),
        "total_interest_paid": round(total_interest, 2),
        "total_amount_paid": round(total_balance + total_interest, 2)
    }


@tool
def compare_avalanche_vs_snowball(debts: List[Dict], extra_payment: float) -> Dict:
    """
    Compare debt avalanche (highest rate first) vs snowball (lowest balance first).

    Args:
        debts: List of debts with balance, rate, min_payment, name
        extra_payment: Extra monthly payment to allocate

    Returns:
        Comparison of both strategies
    """
    # Avalanche: Sort by interest rate (highest first)
    avalanche_debts = sorted(debts, key=lambda x: x["interest_rate"], reverse=True)

    # Snowball: Sort by balance (lowest first)
    snowball_debts = sorted(debts, key=lambda x: x["current_balance"])

    def calculate_strategy(debt_order):
        debts_copy = [d.copy() for d in debt_order]
        months = 0
        total_interest = 0

        while any(d["current_balance"] > 0 for d in debts_copy) and months < 600:
            months += 1
            remaining_extra = extra_payment

            # Pay minimums on all debts and interest
            for debt in debts_copy:
                if debt["current_balance"] > 0:
                    monthly_rate = debt["interest_rate"] / 100 / 12
                    interest = debt["current_balance"] * monthly_rate
                    total_interest += interest

                    principal = min(debt["monthly_payment"], debt["current_balance"] + interest) - interest
                    debt["current_balance"] = max(0, debt["current_balance"] - principal)

            # Apply extra payment to first non-zero debt
            for debt in debts_copy:
                if debt["current_balance"] > 0 and remaining_extra > 0:
                    payment = min(remaining_extra, debt["current_balance"])
                    debt["current_balance"] -= payment
                    remaining_extra -= payment
                    break

        return months, total_interest

    avalanche_months, avalanche_interest = calculate_strategy(avalanche_debts)
    snowball_months, snowball_interest = calculate_strategy(snowball_debts)

    savings = snowball_interest - avalanche_interest
    time_savings = snowball_months - avalanche_months

    return {
        "avalanche": {
            "months": avalanche_months,
            "years": round(avalanche_months / 12, 1),
            "total_interest": round(avalanche_interest, 2),
            "strategy": "Pay highest interest rate first"
        },
        "snowball": {
            "months": snowball_months,
            "years": round(snowball_months / 12, 1),
            "total_interest": round(snowball_interest, 2),
            "strategy": "Pay lowest balance first"
        },
        "avalanche_savings": round(savings, 2),
        "avalanche_time_savings_months": time_savings,
        "recommended": "Avalanche" if savings > 0 else "Snowball"
    }


@tool
def calculate_total_interest_cost(debts: List[Dict]) -> Dict:
    """
    Calculate total lifetime interest cost of all debts at current payment rate.

    Args:
        debts: List of debts with balance, rate, monthly_payment

    Returns:
        Total interest cost breakdown
    """
    total_interest = 0
    debt_details = []

    for debt in debts:
        balance = debt["current_balance"]
        rate = debt["interest_rate"] / 100 / 12
        payment = debt["monthly_payment"]

        if payment <= balance * rate:
            # Payment doesn't cover interest - debt grows
            interest = float('inf')
            months = float('inf')
        else:
            # Calculate months to payoff
            months = 0
            remaining = balance
            interest_paid = 0

            while remaining > 0 and months < 600:
                interest_charge = remaining * rate
                principal = min(payment - interest_charge, remaining)
                interest_paid += interest_charge
                remaining -= principal
                months += 1

            interest = interest_paid

        total_interest += interest if interest != float('inf') else 0

        debt_details.append({
            "debt_name": debt.get("type", "Unknown"),
            "balance": round(balance, 2),
            "interest_rate": debt["interest_rate"],
            "interest_cost": round(interest, 2) if interest != float('inf') else "Unpayable",
            "months_to_payoff": months if months != float('inf') else "Unpayable"
        })

    return {
        "total_interest_cost": round(total_interest, 2),
        "debt_breakdown": debt_details,
        "total_debt_balance": round(sum(d["current_balance"] for d in debts), 2)
    }


@tool
def optimize_extra_payment_allocation(debts: List[Dict], extra_amount: float) -> Dict:
    """
    Determine optimal allocation of extra payment across debts (avalanche method).

    Args:
        debts: List of debts with balance, rate, monthly_payment
        extra_amount: Extra amount to allocate

    Returns:
        Recommended allocation strategy
    """
    # Sort by interest rate (highest first)
    sorted_debts = sorted(debts, key=lambda x: x["interest_rate"], reverse=True)

    allocations = []
    remaining_extra = extra_amount

    for debt in sorted_debts:
        if remaining_extra <= 0:
            allocations.append({
                "debt": debt.get("type", "Unknown"),
                "current_payment": debt["monthly_payment"],
                "extra_payment": 0,
                "total_payment": debt["monthly_payment"]
            })
        else:
            # Allocate all remaining extra to highest rate debt
            extra_for_this = min(remaining_extra, debt["current_balance"])
            allocations.append({
                "debt": debt.get("type", "Unknown"),
                "current_payment": debt["monthly_payment"],
                "extra_payment": round(extra_for_this, 2),
                "total_payment": round(debt["monthly_payment"] + extra_for_this, 2),
                "interest_rate": debt["interest_rate"]
            })
            remaining_extra -= extra_for_this

    return {
        "allocations": allocations,
        "strategy": "Avalanche (highest interest rate first)",
        "total_extra_allocated": extra_amount
    }


@tool
def calculate_debt_to_income_ratio(total_debt_payments: float, gross_monthly_income: float) -> Dict:
    """
    Calculate debt-to-income ratio.

    Args:
        total_debt_payments: Total monthly debt payments
        gross_monthly_income: Gross monthly income

    Returns:
        DTI ratio and assessment
    """
    dti_ratio = (total_debt_payments / gross_monthly_income * 100) if gross_monthly_income > 0 else 0

    # DTI assessment
    if dti_ratio <= 20:
        assessment = "Excellent"
        risk_level = "Low"
    elif dti_ratio <= 36:
        assessment = "Good"
        risk_level = "Moderate"
    elif dti_ratio <= 43:
        assessment = "Fair"
        risk_level = "Elevated"
    else:
        assessment = "Poor"
        risk_level = "High"

    return {
        "dti_ratio": round(dti_ratio, 2),
        "assessment": assessment,
        "risk_level": risk_level,
        "monthly_debt_payments": round(total_debt_payments, 2),
        "gross_monthly_income": round(gross_monthly_income, 2)
    }


@tool
def generate_payoff_chart(debts: List[Dict]) -> Dict:
    """
    Generate debt payoff waterfall chart data.

    Args:
        debts: List of debts with name, balance

    Returns:
        Chart data structure for UI rendering
    """
    labels = [d.get("type", "Unknown") for d in debts]
    values = [d["current_balance"] for d in debts]

    return {
        "chart_type": "bar",
        "title": "Debt Balances by Type",
        "data": {
            "labels": labels,
            "values": values,
            "colors": ["#d62728"] * len(debts)
        },
        "library": "plotly"
    }
