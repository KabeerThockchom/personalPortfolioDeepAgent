#!/usr/bin/env python3
"""Tax Optimization Tools MCP Server"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path to import tools
sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
import json

# Initialize MCP server
app = Server("tax-tools")


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available tax optimization tools."""
    return [
        Tool(
            name="calculate_effective_tax_rate",
            description="Calculate effective tax rate based on gross income and total taxes paid",
            inputSchema={
                "type": "object",
                "properties": {
                    "gross_income": {
                        "type": "number",
                        "description": "Total gross income"
                    },
                    "total_taxes_paid": {
                        "type": "number",
                        "description": "Total taxes paid (federal + state)"
                    }
                },
                "required": ["gross_income", "total_taxes_paid"]
            }
        ),
        Tool(
            name="identify_tax_loss_harvesting_opportunities",
            description="Identify positions with unrealized losses for tax loss harvesting",
            inputSchema={
                "type": "object",
                "properties": {
                    "holdings": {
                        "type": "array",
                        "description": "List of holdings with ticker, shares, cost_basis",
                        "items": {
                            "type": "object",
                            "properties": {
                                "ticker": {"type": "string"},
                                "shares": {"type": "number"},
                                "cost_basis": {"type": "number"}
                            },
                            "required": ["ticker", "shares", "cost_basis"]
                        }
                    },
                    "current_prices": {
                        "type": "object",
                        "description": "Dictionary of ticker -> current price",
                        "additionalProperties": {"type": "number"}
                    }
                },
                "required": ["holdings", "current_prices"]
            }
        ),
        Tool(
            name="analyze_roth_conversion_opportunity",
            description="Analyze Roth IRA conversion opportunity and tax implications",
            inputSchema={
                "type": "object",
                "properties": {
                    "current_income": {
                        "type": "number",
                        "description": "Current annual income"
                    },
                    "marginal_tax_bracket": {
                        "type": "number",
                        "description": "Current marginal tax bracket (as decimal, e.g., 0.24 for 24%)"
                    },
                    "traditional_ira_balance": {
                        "type": "number",
                        "description": "Traditional IRA balance"
                    },
                    "conversion_amount": {
                        "type": "number",
                        "description": "Amount considering for conversion"
                    }
                },
                "required": ["current_income", "marginal_tax_bracket", "traditional_ira_balance", "conversion_amount"]
            }
        ),
        Tool(
            name="optimize_withdrawal_sequence",
            description="Determine optimal withdrawal sequence from different account types for tax efficiency",
            inputSchema={
                "type": "object",
                "properties": {
                    "taxable_balance": {
                        "type": "number",
                        "description": "Balance in taxable accounts"
                    },
                    "tax_deferred_balance": {
                        "type": "number",
                        "description": "Balance in tax-deferred accounts (401k, traditional IRA)"
                    },
                    "tax_free_balance": {
                        "type": "number",
                        "description": "Balance in tax-free accounts (Roth IRA)"
                    },
                    "annual_need": {
                        "type": "number",
                        "description": "Annual withdrawal needed"
                    }
                },
                "required": ["taxable_balance", "tax_deferred_balance", "tax_free_balance", "annual_need"]
            }
        ),
        Tool(
            name="calculate_capital_gains_tax",
            description="Calculate capital gains tax on a sale",
            inputSchema={
                "type": "object",
                "properties": {
                    "cost_basis": {
                        "type": "number",
                        "description": "Original cost basis"
                    },
                    "sale_price": {
                        "type": "number",
                        "description": "Sale price"
                    },
                    "holding_period_years": {
                        "type": "number",
                        "description": "Years held (< 1 = short-term, >= 1 = long-term)"
                    },
                    "income_level": {
                        "type": "string",
                        "description": "Income level for rate determination",
                        "enum": ["low", "medium", "high"],
                        "default": "high"
                    }
                },
                "required": ["cost_basis", "sale_price", "holding_period_years"]
            }
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool execution."""
    try:
        result = None

        if name == "calculate_effective_tax_rate":
            result = _calculate_effective_tax_rate(
                arguments["gross_income"],
                arguments["total_taxes_paid"]
            )

        elif name == "identify_tax_loss_harvesting_opportunities":
            result = _identify_tax_loss_harvesting_opportunities(
                arguments["holdings"],
                arguments["current_prices"]
            )

        elif name == "analyze_roth_conversion_opportunity":
            result = _analyze_roth_conversion_opportunity(
                arguments["current_income"],
                arguments["marginal_tax_bracket"],
                arguments["traditional_ira_balance"],
                arguments["conversion_amount"]
            )

        elif name == "optimize_withdrawal_sequence":
            result = _optimize_withdrawal_sequence(
                arguments["taxable_balance"],
                arguments["tax_deferred_balance"],
                arguments["tax_free_balance"],
                arguments["annual_need"]
            )

        elif name == "calculate_capital_gains_tax":
            result = _calculate_capital_gains_tax(
                arguments["cost_basis"],
                arguments["sale_price"],
                arguments["holding_period_years"],
                arguments.get("income_level", "high")
            )

        else:
            raise ValueError(f"Unknown tool: {name}")

        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    except Exception as e:
        return [TextContent(type="text", text=json.dumps({
            "success": False,
            "error": str(e)
        }, indent=2))]


# Tool implementation functions (from src/tools/tax_tools.py)

def _calculate_effective_tax_rate(gross_income: float, total_taxes_paid: float) -> dict:
    """Calculate effective tax rate."""
    effective_rate = (total_taxes_paid / gross_income * 100) if gross_income > 0 else 0

    return {
        "gross_income": round(gross_income, 2),
        "total_taxes_paid": round(total_taxes_paid, 2),
        "effective_tax_rate": round(effective_rate, 2),
        "after_tax_income": round(gross_income - total_taxes_paid, 2)
    }


def _identify_tax_loss_harvesting_opportunities(holdings: list, current_prices: dict) -> dict:
    """Identify positions with unrealized losses for tax loss harvesting."""
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


def _analyze_roth_conversion_opportunity(
    current_income: float,
    marginal_tax_bracket: float,
    traditional_ira_balance: float,
    conversion_amount: float
) -> dict:
    """Analyze Roth IRA conversion opportunity."""
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


def _optimize_withdrawal_sequence(
    taxable_balance: float,
    tax_deferred_balance: float,
    tax_free_balance: float,
    annual_need: float
) -> dict:
    """Determine optimal withdrawal sequence from different account types."""
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


def _calculate_capital_gains_tax(
    cost_basis: float,
    sale_price: float,
    holding_period_years: float,
    income_level: str = "high"
) -> dict:
    """Calculate capital gains tax on a sale."""
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


async def main():
    """Run the MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
