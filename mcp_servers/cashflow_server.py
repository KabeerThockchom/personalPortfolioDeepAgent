#!/usr/bin/env python3
"""Cash Flow Analysis Tools MCP Server"""

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
app = Server("cashflow-tools")


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available cash flow analysis tools."""
    return [
        Tool(
            name="analyze_monthly_cashflow",
            description="Analyze monthly cash flow from income and expenses",
            inputSchema={
                "type": "object",
                "properties": {
                    "income": {
                        "type": "object",
                        "description": "Dictionary of income sources with amounts",
                        "additionalProperties": {"type": "number"}
                    },
                    "expenses": {
                        "type": "object",
                        "description": "Dictionary of expense categories (can be nested)",
                        "additionalProperties": {"type": ["number", "object"]}
                    }
                },
                "required": ["income", "expenses"]
            }
        ),
        Tool(
            name="calculate_savings_rate",
            description="Calculate savings rate from income, taxes, and expenses",
            inputSchema={
                "type": "object",
                "properties": {
                    "income": {
                        "type": "object",
                        "description": "Dictionary of gross income sources",
                        "additionalProperties": {"type": "number"}
                    },
                    "taxes": {
                        "type": "object",
                        "description": "Dictionary of tax and deduction amounts",
                        "additionalProperties": {"type": "number"}
                    },
                    "expenses": {
                        "type": "object",
                        "description": "Dictionary of expense categories",
                        "additionalProperties": {"type": ["number", "object"]}
                    }
                },
                "required": ["income", "taxes", "expenses"]
            }
        ),
        Tool(
            name="categorize_expenses",
            description="Categorize and break down expenses by major categories with percentages",
            inputSchema={
                "type": "object",
                "properties": {
                    "expenses": {
                        "type": "object",
                        "description": "Nested dictionary of expense categories",
                        "additionalProperties": {"type": ["number", "object"]}
                    }
                },
                "required": ["expenses"]
            }
        ),
        Tool(
            name="project_future_cashflow",
            description="Project future cash flow with optional growth rate",
            inputSchema={
                "type": "object",
                "properties": {
                    "net_monthly_cashflow": {
                        "type": "number",
                        "description": "Current net monthly cash flow"
                    },
                    "months": {
                        "type": "integer",
                        "description": "Number of months to project"
                    },
                    "growth_rate": {
                        "type": "number",
                        "description": "Annual growth rate as decimal (default 0.0)",
                        "default": 0.0
                    }
                },
                "required": ["net_monthly_cashflow", "months"]
            }
        ),
        Tool(
            name="calculate_burn_rate",
            description="Calculate burn rate and runway (months of expenses covered)",
            inputSchema={
                "type": "object",
                "properties": {
                    "expenses": {
                        "type": "object",
                        "description": "Dictionary of expense categories",
                        "additionalProperties": {"type": ["number", "object"]}
                    },
                    "liquid_assets": {
                        "type": "number",
                        "description": "Total liquid assets available"
                    }
                },
                "required": ["expenses", "liquid_assets"]
            }
        ),
        Tool(
            name="generate_waterfall_chart",
            description="Generate waterfall chart data showing income to net cashflow",
            inputSchema={
                "type": "object",
                "properties": {
                    "income": {
                        "type": "number",
                        "description": "Total income"
                    },
                    "expenses": {
                        "type": "number",
                        "description": "Total expenses"
                    }
                },
                "required": ["income", "expenses"]
            }
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool execution."""
    try:
        result = None

        if name == "analyze_monthly_cashflow":
            result = _analyze_monthly_cashflow(
                arguments["income"],
                arguments["expenses"]
            )

        elif name == "calculate_savings_rate":
            result = _calculate_savings_rate(
                arguments["income"],
                arguments["taxes"],
                arguments["expenses"]
            )

        elif name == "categorize_expenses":
            result = _categorize_expenses(arguments["expenses"])

        elif name == "project_future_cashflow":
            result = _project_future_cashflow(
                arguments["net_monthly_cashflow"],
                arguments["months"],
                arguments.get("growth_rate", 0.0)
            )

        elif name == "calculate_burn_rate":
            result = _calculate_burn_rate(
                arguments["expenses"],
                arguments["liquid_assets"]
            )

        elif name == "generate_waterfall_chart":
            result = _generate_waterfall_chart(
                arguments["income"],
                arguments["expenses"]
            )

        else:
            raise ValueError(f"Unknown tool: {name}")

        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    except Exception as e:
        return [TextContent(type="text", text=json.dumps({
            "success": False,
            "error": str(e)
        }, indent=2))]


# Tool implementation functions (from src/tools/cashflow_tools.py)

def _sum_nested_dict(d):
    """Helper function to sum nested dictionary values."""
    total = 0
    for value in d.values():
        if isinstance(value, dict):
            total += _sum_nested_dict(value)
        else:
            total += value
    return total


def _analyze_monthly_cashflow(income: dict, expenses: dict) -> dict:
    """Analyze monthly cash flow from income and expenses."""
    # Calculate total income
    total_income = sum(income.values())

    # Calculate total expenses (flatten nested structure)
    total_expenses = _sum_nested_dict(expenses)

    # Net cash flow
    net_cashflow = total_income - total_expenses

    return {
        "total_monthly_income": round(total_income, 2),
        "total_monthly_expenses": round(total_expenses, 2),
        "net_monthly_cashflow": round(net_cashflow, 2),
        "expense_to_income_ratio": round(total_expenses / total_income * 100, 2) if total_income > 0 else 0
    }


def _calculate_savings_rate(income: dict, taxes: dict, expenses: dict) -> dict:
    """Calculate savings rate from income, taxes, and expenses."""
    # Total gross income
    gross_income = sum(income.values())

    # Total taxes and deductions
    total_taxes = sum(taxes.values())

    # Net income after taxes
    net_income = gross_income - total_taxes

    # Total expenses
    total_expenses = _sum_nested_dict(expenses)

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


def _categorize_expenses(expenses: dict) -> dict:
    """Categorize and break down expenses by major categories."""
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


def _project_future_cashflow(
    net_monthly_cashflow: float,
    months: int,
    growth_rate: float = 0.0
) -> dict:
    """Project future cash flow with optional growth rate."""
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


def _calculate_burn_rate(expenses: dict, liquid_assets: float) -> dict:
    """Calculate burn rate and runway (months of expenses covered)."""
    monthly_burn = _sum_nested_dict(expenses)

    runway_months = (liquid_assets / monthly_burn) if monthly_burn > 0 else float('inf')

    return {
        "monthly_burn_rate": round(monthly_burn, 2),
        "liquid_assets": round(liquid_assets, 2),
        "runway_months": round(runway_months, 1),
        "runway_years": round(runway_months / 12, 1)
    }


def _generate_waterfall_chart(income: float, expenses: float) -> dict:
    """Generate waterfall chart data showing income to net cashflow."""
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
