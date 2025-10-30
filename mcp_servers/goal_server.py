#!/usr/bin/env python3
"""Goal Planning and Retirement Tools MCP Server"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path to import tools
sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
import json
import numpy as np

# Initialize MCP server
app = Server("goal-tools")


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available goal planning and retirement tools."""
    return [
        Tool(
            name="calculate_retirement_gap",
            description="Calculate retirement savings gap and required contributions",
            inputSchema={
                "type": "object",
                "properties": {
                    "current_savings": {
                        "type": "number",
                        "description": "Current retirement savings total"
                    },
                    "desired_annual_income": {
                        "type": "number",
                        "description": "Desired annual income in retirement (today's dollars)"
                    },
                    "years_until_retirement": {
                        "type": "integer",
                        "description": "Years until retirement"
                    },
                    "expected_return": {
                        "type": "number",
                        "description": "Expected annual return as decimal (default 0.07)",
                        "default": 0.07
                    },
                    "inflation_rate": {
                        "type": "number",
                        "description": "Expected inflation rate as decimal (default 0.03)",
                        "default": 0.03
                    },
                    "retirement_years": {
                        "type": "integer",
                        "description": "Years in retirement (default 30)",
                        "default": 30
                    }
                },
                "required": ["current_savings", "desired_annual_income", "years_until_retirement"]
            }
        ),
        Tool(
            name="run_monte_carlo_simulation",
            description="Run Monte Carlo simulation for retirement projections with volatility",
            inputSchema={
                "type": "object",
                "properties": {
                    "current_savings": {
                        "type": "number",
                        "description": "Current savings balance"
                    },
                    "monthly_contribution": {
                        "type": "number",
                        "description": "Monthly contribution amount"
                    },
                    "years": {
                        "type": "integer",
                        "description": "Number of years to simulate"
                    },
                    "expected_return": {
                        "type": "number",
                        "description": "Expected annual return as decimal (default 0.07)",
                        "default": 0.07
                    },
                    "volatility": {
                        "type": "number",
                        "description": "Annual volatility/std dev as decimal (default 0.15)",
                        "default": 0.15
                    },
                    "simulations": {
                        "type": "integer",
                        "description": "Number of simulations to run (default 1000)",
                        "default": 1000
                    }
                },
                "required": ["current_savings", "monthly_contribution", "years"]
            }
        ),
        Tool(
            name="calculate_required_savings_rate",
            description="Calculate required savings rate to reach retirement goal",
            inputSchema={
                "type": "object",
                "properties": {
                    "current_age": {
                        "type": "integer",
                        "description": "Current age"
                    },
                    "retirement_age": {
                        "type": "integer",
                        "description": "Target retirement age"
                    },
                    "current_savings": {
                        "type": "number",
                        "description": "Current retirement savings"
                    },
                    "target_corpus": {
                        "type": "number",
                        "description": "Target retirement corpus"
                    },
                    "current_income": {
                        "type": "number",
                        "description": "Current annual income"
                    },
                    "expected_return": {
                        "type": "number",
                        "description": "Expected annual return as decimal (default 0.07)",
                        "default": 0.07
                    }
                },
                "required": ["current_age", "retirement_age", "current_savings", "target_corpus", "current_income"]
            }
        ),
        Tool(
            name="calculate_fire_number",
            description="Calculate FIRE (Financial Independence Retire Early) number",
            inputSchema={
                "type": "object",
                "properties": {
                    "annual_expenses": {
                        "type": "number",
                        "description": "Annual expenses to cover"
                    },
                    "withdrawal_rate": {
                        "type": "number",
                        "description": "Safe withdrawal rate as decimal (default 0.04)",
                        "default": 0.04
                    },
                    "safety_margin": {
                        "type": "number",
                        "description": "Safety margin multiplier (default 1.25 = 25% buffer)",
                        "default": 1.25
                    }
                },
                "required": ["annual_expenses"]
            }
        ),
        Tool(
            name="project_college_funding",
            description="Project college funding goal achievement",
            inputSchema={
                "type": "object",
                "properties": {
                    "current_savings": {
                        "type": "number",
                        "description": "Current 529/college savings"
                    },
                    "target_amount": {
                        "type": "number",
                        "description": "Target amount needed"
                    },
                    "years_until_needed": {
                        "type": "integer",
                        "description": "Years until college starts"
                    },
                    "monthly_contribution": {
                        "type": "number",
                        "description": "Monthly contribution"
                    },
                    "expected_return": {
                        "type": "number",
                        "description": "Expected annual return as decimal (default 0.06)",
                        "default": 0.06
                    }
                },
                "required": ["current_savings", "target_amount", "years_until_needed", "monthly_contribution"]
            }
        ),
        Tool(
            name="generate_monte_carlo_chart",
            description="Generate Monte Carlo fan chart data for visualization",
            inputSchema={
                "type": "object",
                "properties": {
                    "percentiles": {
                        "type": "object",
                        "description": "Dictionary with percentile_10, percentile_25, median, percentile_75, percentile_90 values",
                        "additionalProperties": {"type": "number"}
                    },
                    "years": {
                        "type": "integer",
                        "description": "Number of years projected"
                    }
                },
                "required": ["percentiles", "years"]
            }
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool execution."""
    try:
        result = None

        if name == "calculate_retirement_gap":
            result = _calculate_retirement_gap(
                arguments["current_savings"],
                arguments["desired_annual_income"],
                arguments["years_until_retirement"],
                arguments.get("expected_return", 0.07),
                arguments.get("inflation_rate", 0.03),
                arguments.get("retirement_years", 30)
            )

        elif name == "run_monte_carlo_simulation":
            result = _run_monte_carlo_simulation(
                arguments["current_savings"],
                arguments["monthly_contribution"],
                arguments["years"],
                arguments.get("expected_return", 0.07),
                arguments.get("volatility", 0.15),
                arguments.get("simulations", 1000)
            )

        elif name == "calculate_required_savings_rate":
            result = _calculate_required_savings_rate(
                arguments["current_age"],
                arguments["retirement_age"],
                arguments["current_savings"],
                arguments["target_corpus"],
                arguments["current_income"],
                arguments.get("expected_return", 0.07)
            )

        elif name == "calculate_fire_number":
            result = _calculate_fire_number(
                arguments["annual_expenses"],
                arguments.get("withdrawal_rate", 0.04),
                arguments.get("safety_margin", 1.25)
            )

        elif name == "project_college_funding":
            result = _project_college_funding(
                arguments["current_savings"],
                arguments["target_amount"],
                arguments["years_until_needed"],
                arguments["monthly_contribution"],
                arguments.get("expected_return", 0.06)
            )

        elif name == "generate_monte_carlo_chart":
            result = _generate_monte_carlo_chart(
                arguments["percentiles"],
                arguments["years"]
            )

        else:
            raise ValueError(f"Unknown tool: {name}")

        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    except Exception as e:
        return [TextContent(type="text", text=json.dumps({
            "success": False,
            "error": str(e)
        }, indent=2))]


# Tool implementation functions (from src/tools/goal_tools.py)

def _calculate_retirement_gap(
    current_savings: float,
    desired_annual_income: float,
    years_until_retirement: int,
    expected_return: float = 0.07,
    inflation_rate: float = 0.03,
    retirement_years: int = 30
) -> dict:
    """Calculate retirement savings gap and required contributions."""
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


def _run_monte_carlo_simulation(
    current_savings: float,
    monthly_contribution: float,
    years: int,
    expected_return: float = 0.07,
    volatility: float = 0.15,
    simulations: int = 1000
) -> dict:
    """Run Monte Carlo simulation for retirement projections."""
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


def _calculate_required_savings_rate(
    current_age: int,
    retirement_age: int,
    current_savings: float,
    target_corpus: float,
    current_income: float,
    expected_return: float = 0.07
) -> dict:
    """Calculate required savings rate to reach retirement goal."""
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


def _calculate_fire_number(
    annual_expenses: float,
    withdrawal_rate: float = 0.04,
    safety_margin: float = 1.25
) -> dict:
    """Calculate FIRE (Financial Independence Retire Early) number."""
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


def _project_college_funding(
    current_savings: float,
    target_amount: float,
    years_until_needed: int,
    monthly_contribution: float,
    expected_return: float = 0.06
) -> dict:
    """Project college funding goal achievement."""
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


def _generate_monte_carlo_chart(percentiles: dict, years: int) -> dict:
    """Generate Monte Carlo fan chart data."""
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
