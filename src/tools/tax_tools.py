"""Tax optimization calculation tools."""

from langchain_core.tools import tool
from typing import Dict, List


@tool
def calculate_effective_tax_rate(
    gross_income: float,
    total_taxes_paid: float
) -> Dict:
    """
    Calculate effective tax rate.

    Args:
        gross_income: Total gross income
        total_taxes_paid: Total taxes paid (federal + state)

    Returns:
        Effective tax rate
    """
    effective_rate = (total_taxes_paid / gross_income * 100) if gross_income > 0 else 0

    return {
        "gross_income": round(gross_income, 2),
        "total_taxes_paid": round(total_taxes_paid, 2),
        "effective_tax_rate": round(effective_rate, 2),
        "after_tax_income": round(gross_income - total_taxes_paid, 2)
    }


@tool
def identify_tax_loss_harvesting_opportunities(
    holdings: List[Dict],
    current_prices: Dict[str, float]
) -> Dict:
    """
    Identify positions with unrealized losses for tax loss harvesting.

    Args:
        holdings: List of holdings with ticker, shares, cost_basis
        current_prices: Dictionary of ticker -> current price

    Returns:
        Tax loss harvesting opportunities
    """
    opportunities = []
    total_harvestable_loss = 0

    for holding in holdings:
        ticker = holding["ticker"]
        shares = holding["shares"]
        cost_basis = holding.get("cost_basis", 100)  # Default to 100 if missing
        current_price = current_prices.get(ticker, cost_basis)

        position_cost = shares * cost_basis
        position_value = shares * current_price
        unrealized_loss = position_value - position_cost

        if unrealized_loss < 0:  # Has a loss
            opportunities.append({
                "ticker": ticker,
                "shares": shares,
                "cost_basis": cost_basis,
                "current_price": current_price,
                "unrealized_loss": round(unrealized_loss, 2),
                "loss_percentage": round((unrealized_loss / position_cost * 100), 2)
            })
            total_harvestable_loss += abs(unrealized_loss)

    # Sort by largest loss first
    opportunities.sort(key=lambda x: x["unrealized_loss"])

    # Estimate tax benefit (assume 20% long-term cap gains rate)
    estimated_tax_benefit = total_harvestable_loss * 0.20

    return {
        "opportunities": opportunities,
        "total_harvestable_loss": round(total_harvestable_loss, 2),
        "estimated_tax_benefit": round(estimated_tax_benefit, 2),
        "count": len(opportunities)
    }


@tool
def analyze_roth_conversion_opportunity(
    current_income: float,
    marginal_tax_bracket: float,
    traditional_ira_balance: float,
    conversion_amount: float
) -> Dict:
    """
    Analyze Roth IRA conversion opportunity.

    Args:
        current_income: Current annual income
        marginal_tax_bracket: Current marginal tax bracket (as decimal, e.g., 0.24)
        traditional_ira_balance: Traditional IRA balance
        conversion_amount: Amount considering for conversion

    Returns:
        Roth conversion analysis
    """
    # Tax on conversion
    conversion_tax = conversion_amount * marginal_tax_bracket

    # Remaining in traditional IRA
    remaining_traditional = traditional_ira_balance - conversion_amount

    return {
        "conversion_amount": round(conversion_amount, 2),
        "immediate_tax_cost": round(conversion_tax, 2),
        "marginal_rate_used": round(marginal_tax_bracket * 100, 2),
        "remaining_traditional_ira": round(remaining_traditional, 2),
        "recommendation": "Consider converting in lower income years" if current_income > 150000 else "Good opportunity"
    }


@tool
def optimize_withdrawal_sequence(
    taxable_balance: float,
    tax_deferred_balance: float,
    tax_free_balance: float,
    annual_need: float
) -> Dict:
    """
    Determine optimal withdrawal sequence from different account types.

    Args:
        taxable_balance: Balance in taxable accounts
        tax_deferred_balance: Balance in tax-deferred (401k, trad IRA)
        tax_free_balance: Balance in tax-free (Roth IRA)
        annual_need: Annual withdrawal needed

    Returns:
        Optimal withdrawal strategy
    """
    # Optimal sequence: Taxable -> Tax-deferred -> Tax-free
    strategy = []

    remaining_need = annual_need

    # Step 1: Taxable accounts first
    if taxable_balance > 0 and remaining_need > 0:
        from_taxable = min(taxable_balance, remaining_need)
        strategy.append({
            "account_type": "Taxable",
            "amount": round(from_taxable, 2),
            "reason": "Pay capital gains, preserve tax-advantaged growth"
        })
        remaining_need -= from_taxable

    # Step 2: Tax-deferred accounts
    if tax_deferred_balance > 0 and remaining_need > 0:
        from_tax_deferred = min(tax_deferred_balance, remaining_need)
        strategy.append({
            "account_type": "Tax-Deferred (401k/IRA)",
            "amount": round(from_tax_deferred, 2),
            "reason": "Taxed as ordinary income, fulfill RMD requirements"
        })
        remaining_need -= from_tax_deferred

    # Step 3: Tax-free accounts (last resort)
    if tax_free_balance > 0 and remaining_need > 0:
        from_tax_free = min(tax_free_balance, remaining_need)
        strategy.append({
            "account_type": "Tax-Free (Roth)",
            "amount": round(from_tax_free, 2),
            "reason": "Preserve tax-free growth as long as possible"
        })
        remaining_need -= from_tax_free

    return {
        "annual_need": round(annual_need, 2),
        "withdrawal_sequence": strategy,
        "total_withdrawn": round(annual_need - remaining_need, 2),
        "shortfall": round(remaining_need, 2) if remaining_need > 0 else 0
    }


@tool
def calculate_capital_gains_tax(
    cost_basis: float,
    sale_price: float,
    holding_period_years: float,
    income_level: str = "high"
) -> Dict:
    """
    Calculate capital gains tax on a sale.

    Args:
        cost_basis: Original cost basis
        sale_price: Sale price
        holding_period_years: Years held (< 1 = short-term, >= 1 = long-term)
        income_level: Income level (low, medium, high) for rate determination

    Returns:
        Capital gains tax calculation
    """
    gain = sale_price - cost_basis

    if gain <= 0:
        return {
            "capital_gain": round(gain, 2),
            "tax_owed": 0,
            "net_proceeds": round(sale_price, 2),
            "holding_period": "Loss - no tax"
        }

    # Determine tax rate
    if holding_period_years >= 1:
        # Long-term capital gains
        if income_level == "low":
            rate = 0.0
        elif income_level == "medium":
            rate = 0.15
        else:  # high
            rate = 0.20
        holding_type = "Long-term"
    else:
        # Short-term (taxed as ordinary income)
        if income_level == "low":
            rate = 0.22
        elif income_level == "medium":
            rate = 0.24
        else:  # high
            rate = 0.32
        holding_type = "Short-term"

    tax_owed = gain * rate
    net_proceeds = sale_price - tax_owed

    return {
        "cost_basis": round(cost_basis, 2),
        "sale_price": round(sale_price, 2),
        "capital_gain": round(gain, 2),
        "holding_period": holding_type,
        "tax_rate": round(rate * 100, 2),
        "tax_owed": round(tax_owed, 2),
        "net_proceeds": round(net_proceeds, 2)
    }
