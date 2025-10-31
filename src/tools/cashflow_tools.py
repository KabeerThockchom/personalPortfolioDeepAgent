from src.utils.tool_logger import logged_tool

"""Cash flow analysis calculation tools."""

from langchain_core.tools import tool
from typing import Dict, List


@tool
@logged_tool
def analyze_monthly_cashflow(income: Dict, expenses: Dict) -> Dict:
    """
    Analyze monthly cash flow from income and expenses.

    Args:
        income: Dictionary of income sources
        expenses: Dictionary of expense categories (nested)

    Returns:
        Cash flow analysis with net monthly flow
    """
    # Calculate total income
    total_income = sum(income.values())

    # Calculate total expenses (flatten nested structure)
    def sum_nested_dict(d):
        total = 0
        for value in d.values():
            if isinstance(value, dict):
                total += sum_nested_dict(value)
            else:
                total += value
        return total

    total_expenses = sum_nested_dict(expenses)

    # Net cash flow
    net_cashflow = total_income - total_expenses

    return {
        "total_monthly_income": round(total_income, 2),
        "total_monthly_expenses": round(total_expenses, 2),
        "net_monthly_cashflow": round(net_cashflow, 2),
        "expense_to_income_ratio": round(total_expenses / total_income * 100, 2) if total_income > 0 else 0
    }


@tool
@logged_tool
def calculate_savings_rate(income: Dict, taxes: Dict, expenses: Dict) -> Dict:
    """
    Calculate savings rate from income, taxes, and expenses.

    Args:
        income: Dictionary of gross income sources
        taxes: Dictionary of tax and deduction amounts
        expenses: Dictionary of expense categories

    Returns:
        Savings rate percentage and details
    """
    # Total gross income
    gross_income = sum(income.values())

    # Total taxes and deductions
    total_taxes = sum(taxes.values())

    # Net income after taxes
    net_income = gross_income - total_taxes

    # Total expenses
    def sum_nested_dict(d):
        total = 0
        for value in d.values():
            if isinstance(value, dict):
                total += sum_nested_dict(value)
            else:
                total += value
        return total

    total_expenses = sum_nested_dict(expenses)

    # Monthly savings
    monthly_savings = net_income - total_expenses

    # Savings rate (as % of gross income)
    savings_rate_gross = (monthly_savings / gross_income * 100) if gross_income > 0 else 0

    # Savings rate (as % of net income)
    savings_rate_net = (monthly_savings / net_income * 100) if net_income > 0 else 0

    return {
        "gross_income": round(gross_income, 2),
        "total_taxes": round(total_taxes, 2),
        "net_income": round(net_income, 2),
        "total_expenses": round(total_expenses, 2),
        "monthly_savings": round(monthly_savings, 2),
        "savings_rate_of_gross": round(savings_rate_gross, 2),
        "savings_rate_of_net": round(savings_rate_net, 2),
        "annual_savings": round(monthly_savings * 12, 2)
    }


@tool
@logged_tool
def categorize_expenses(expenses: Dict) -> Dict:
    """
    Categorize and break down expenses by major categories.

    Args:
        expenses: Nested dictionary of expense categories

    Returns:
        Flattened expense breakdown with percentages
    """
    # Flatten expense categories
    category_totals = {}

    for category, items in expenses.items():
        if isinstance(items, dict):
            category_total = sum(items.values())
            category_totals[category] = category_total
        else:
            category_totals[category] = items

    total_expenses = sum(category_totals.values())

    # Calculate percentages
    category_breakdown = []
    for category, amount in sorted(category_totals.items(), key=lambda x: x[1], reverse=True):
        pct = (amount / total_expenses * 100) if total_expenses > 0 else 0
        category_breakdown.append({
            "category": category,
            "amount": round(amount, 2),
            "percentage": round(pct, 2)
        })

    return {
        "total_expenses": round(total_expenses, 2),
        "category_breakdown": category_breakdown,
        "top_3_categories": category_breakdown[:3]
    }


@tool
@logged_tool
def project_future_cashflow(
    net_monthly_cashflow: float,
    months: int,
    growth_rate: float = 0.0
) -> Dict:
    """
    Project future cash flow with optional growth rate.

    Args:
        net_monthly_cashflow: Current net monthly cash flow
        months: Number of months to project
        growth_rate: Annual growth rate (default 0%)

    Returns:
        Cash flow projections
    """
    monthly_growth_rate = growth_rate / 12 / 100

    projections = []
    cumulative = 0

    for month in range(1, months + 1):
        # Apply growth
        adjusted_cashflow = net_monthly_cashflow * ((1 + monthly_growth_rate) ** month)
        cumulative += adjusted_cashflow

        projections.append({
            "month": month,
            "monthly_cashflow": round(adjusted_cashflow, 2),
            "cumulative": round(cumulative, 2)
        })

    return {
        "projections": projections,
        "final_cumulative": round(cumulative, 2),
        "months_projected": months,
        "growth_rate_used": growth_rate
    }


@tool
@logged_tool
def calculate_burn_rate(expenses: Dict, liquid_assets: float) -> Dict:
    """
    Calculate burn rate and runway (months of expenses covered).

    Args:
        expenses: Dictionary of expense categories
        liquid_assets: Total liquid assets available

    Returns:
        Burn rate analysis with runway
    """
    def sum_nested_dict(d):
        total = 0
        for value in d.values():
            if isinstance(value, dict):
                total += sum_nested_dict(value)
            else:
                total += value
        return total

    monthly_burn = sum_nested_dict(expenses)

    runway_months = (liquid_assets / monthly_burn) if monthly_burn > 0 else float('inf')

    return {
        "monthly_burn_rate": round(monthly_burn, 2),
        "liquid_assets": round(liquid_assets, 2),
        "runway_months": round(runway_months, 1),
        "runway_years": round(runway_months / 12, 1)
    }


@tool
@logged_tool
def generate_waterfall_chart(income: float, expenses: float) -> Dict:
    """
    Generate waterfall chart data showing income to net cashflow.

    Args:
        income: Total income
        expenses: Total expenses

    Returns:
        Chart data structure for UI rendering
    """
    net = income - expenses

    return {
        "chart_type": "waterfall",
        "title": "Monthly Cash Flow Waterfall",
        "data": {
            "categories": ["Income", "Expenses", "Net Savings"],
            "values": [income, -expenses, net],
            "colors": ["#2ca02c", "#d62728", "#1f77b4"]
        },
        "library": "plotly"
    }
