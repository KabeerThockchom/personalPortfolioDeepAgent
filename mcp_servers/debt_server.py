#!/usr/bin/env python3
"""Debt Management Tools MCP Server"""

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
app = Server("debt-tools")


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available debt management tools."""
    return [
        Tool(
            name="calculate_debt_payoff_timeline",
            description="Calculate debt payoff timeline with extra payments",
            inputSchema={
                "type": "object",
                "properties": {
                    "debts": {
                        "type": "array",
                        "description": "List of debts with current_balance, interest_rate, monthly_payment",
                        "items": {
                            "type": "object",
                            "properties": {
                                "current_balance": {"type": "number"},
                                "interest_rate": {"type": "number", "description": "Annual interest rate as percentage (e.g., 18.5)"},
                                "monthly_payment": {"type": "number"},
                                "type": {"type": "string"}
                            },
                            "required": ["current_balance", "interest_rate", "monthly_payment"]
                        }
                    },
                    "extra_monthly_payment": {
                        "type": "number",
                        "description": "Extra payment to apply each month",
                        "default": 0
                    }
                },
                "required": ["debts"]
            }
        ),
        Tool(
            name="compare_avalanche_vs_snowball",
            description="Compare debt avalanche (highest rate first) vs snowball (lowest balance first) strategies",
            inputSchema={
                "type": "object",
                "properties": {
                    "debts": {
                        "type": "array",
                        "description": "List of debts with current_balance, interest_rate, monthly_payment, type",
                        "items": {
                            "type": "object",
                            "properties": {
                                "current_balance": {"type": "number"},
                                "interest_rate": {"type": "number"},
                                "monthly_payment": {"type": "number"},
                                "type": {"type": "string"}
                            },
                            "required": ["current_balance", "interest_rate", "monthly_payment"]
                        }
                    },
                    "extra_payment": {
                        "type": "number",
                        "description": "Extra monthly payment to allocate"
                    }
                },
                "required": ["debts", "extra_payment"]
            }
        ),
        Tool(
            name="calculate_total_interest_cost",
            description="Calculate total lifetime interest cost of all debts at current payment rate",
            inputSchema={
                "type": "object",
                "properties": {
                    "debts": {
                        "type": "array",
                        "description": "List of debts with current_balance, interest_rate, monthly_payment",
                        "items": {
                            "type": "object",
                            "properties": {
                                "current_balance": {"type": "number"},
                                "interest_rate": {"type": "number"},
                                "monthly_payment": {"type": "number"},
                                "type": {"type": "string"}
                            },
                            "required": ["current_balance", "interest_rate", "monthly_payment"]
                        }
                    }
                },
                "required": ["debts"]
            }
        ),
        Tool(
            name="optimize_extra_payment_allocation",
            description="Determine optimal allocation of extra payment across debts (avalanche method)",
            inputSchema={
                "type": "object",
                "properties": {
                    "debts": {
                        "type": "array",
                        "description": "List of debts with current_balance, interest_rate, monthly_payment",
                        "items": {
                            "type": "object",
                            "properties": {
                                "current_balance": {"type": "number"},
                                "interest_rate": {"type": "number"},
                                "monthly_payment": {"type": "number"},
                                "type": {"type": "string"}
                            },
                            "required": ["current_balance", "interest_rate", "monthly_payment"]
                        }
                    },
                    "extra_amount": {
                        "type": "number",
                        "description": "Extra amount to allocate"
                    }
                },
                "required": ["debts", "extra_amount"]
            }
        ),
        Tool(
            name="calculate_debt_to_income_ratio",
            description="Calculate debt-to-income ratio and assessment",
            inputSchema={
                "type": "object",
                "properties": {
                    "total_debt_payments": {
                        "type": "number",
                        "description": "Total monthly debt payments"
                    },
                    "gross_monthly_income": {
                        "type": "number",
                        "description": "Gross monthly income"
                    }
                },
                "required": ["total_debt_payments", "gross_monthly_income"]
            }
        ),
        Tool(
            name="generate_payoff_chart",
            description="Generate debt payoff waterfall chart data",
            inputSchema={
                "type": "object",
                "properties": {
                    "debts": {
                        "type": "array",
                        "description": "List of debts with current_balance and type",
                        "items": {
                            "type": "object",
                            "properties": {
                                "current_balance": {"type": "number"},
                                "type": {"type": "string"}
                            },
                            "required": ["current_balance"]
                        }
                    }
                },
                "required": ["debts"]
            }
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool execution."""
    try:
        result = None

        if name == "calculate_debt_payoff_timeline":
            result = _calculate_debt_payoff_timeline(
                arguments["debts"],
                arguments.get("extra_monthly_payment", 0)
            )

        elif name == "compare_avalanche_vs_snowball":
            result = _compare_avalanche_vs_snowball(
                arguments["debts"],
                arguments["extra_payment"]
            )

        elif name == "calculate_total_interest_cost":
            result = _calculate_total_interest_cost(arguments["debts"])

        elif name == "optimize_extra_payment_allocation":
            result = _optimize_extra_payment_allocation(
                arguments["debts"],
                arguments["extra_amount"]
            )

        elif name == "calculate_debt_to_income_ratio":
            result = _calculate_debt_to_income_ratio(
                arguments["total_debt_payments"],
                arguments["gross_monthly_income"]
            )

        elif name == "generate_payoff_chart":
            result = _generate_payoff_chart(arguments["debts"])

        else:
            raise ValueError(f"Unknown tool: {name}")

        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    except Exception as e:
        return [TextContent(type="text", text=json.dumps({
            "success": False,
            "error": str(e)
        }, indent=2))]


# Tool implementation functions (from src/tools/debt_tools.py)

def _calculate_debt_payoff_timeline(debts: list, extra_monthly_payment: float = 0) -> dict:
    """Calculate debt payoff timeline with extra payments."""
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


def _compare_avalanche_vs_snowball(debts: list, extra_payment: float) -> dict:
    """Compare debt avalanche (highest rate first) vs snowball (lowest balance first)."""
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


def _calculate_total_interest_cost(debts: list) -> dict:
    """Calculate total lifetime interest cost of all debts at current payment rate."""
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


def _optimize_extra_payment_allocation(debts: list, extra_amount: float) -> dict:
    """Determine optimal allocation of extra payment across debts (avalanche method)."""
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


def _calculate_debt_to_income_ratio(total_debt_payments: float, gross_monthly_income: float) -> dict:
    """Calculate debt-to-income ratio."""
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


def _generate_payoff_chart(debts: list) -> dict:
    """Generate debt payoff waterfall chart data."""
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
