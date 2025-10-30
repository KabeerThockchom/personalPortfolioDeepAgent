#!/usr/bin/env python3
"""Portfolio Analysis Tools MCP Server"""

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
app = Server("portfolio-tools")


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available portfolio analysis tools."""
    return [
        Tool(
            name="calculate_portfolio_value",
            description="Calculate total portfolio value across all holdings with current prices",
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
                            "required": ["ticker", "shares"]
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
            name="calculate_asset_allocation",
            description="Calculate asset allocation breakdown by asset class",
            inputSchema={
                "type": "object",
                "properties": {
                    "holdings": {
                        "type": "array",
                        "description": "List of holdings with ticker, shares, asset_class",
                        "items": {
                            "type": "object",
                            "properties": {
                                "ticker": {"type": "string"},
                                "shares": {"type": "number"},
                                "asset_class": {"type": "string"},
                                "cost_basis": {"type": "number"}
                            },
                            "required": ["ticker", "shares"]
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
            name="calculate_concentration_risk",
            description="Analyze concentration risk - largest positions as % of portfolio",
            inputSchema={
                "type": "object",
                "properties": {
                    "holdings": {
                        "type": "array",
                        "description": "List of holdings with ticker, shares",
                        "items": {
                            "type": "object",
                            "properties": {
                                "ticker": {"type": "string"},
                                "shares": {"type": "number"},
                                "cost_basis": {"type": "number"}
                            },
                            "required": ["ticker", "shares"]
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
            name="calculate_sharpe_ratio",
            description="Calculate Sharpe ratio for a portfolio",
            inputSchema={
                "type": "object",
                "properties": {
                    "returns": {
                        "type": "array",
                        "description": "List of periodic returns",
                        "items": {"type": "number"}
                    },
                    "risk_free_rate": {
                        "type": "number",
                        "description": "Annual risk-free rate (default 0.04)",
                        "default": 0.04
                    }
                },
                "required": ["returns"]
            }
        ),
        Tool(
            name="check_rebalancing_needs",
            description="Check if portfolio needs rebalancing based on drift from target",
            inputSchema={
                "type": "object",
                "properties": {
                    "current_allocation": {
                        "type": "object",
                        "description": "Current allocation percentages by asset class",
                        "additionalProperties": {"type": "number"}
                    },
                    "target_allocation": {
                        "type": "object",
                        "description": "Target allocation percentages by asset class",
                        "additionalProperties": {"type": "number"}
                    },
                    "threshold": {
                        "type": "number",
                        "description": "Drift threshold in percentage points (default 5.0)",
                        "default": 5.0
                    }
                },
                "required": ["current_allocation", "target_allocation"]
            }
        ),
        Tool(
            name="generate_allocation_chart",
            description="Generate pie chart data for asset allocation",
            inputSchema={
                "type": "object",
                "properties": {
                    "allocation": {
                        "type": "object",
                        "description": "Dictionary of asset_class -> percentage",
                        "additionalProperties": {"type": "number"}
                    }
                },
                "required": ["allocation"]
            }
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool execution."""

    if name == "calculate_portfolio_value":
        result = _calculate_portfolio_value(
            arguments["holdings"],
            arguments["current_prices"]
        )
        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    elif name == "calculate_asset_allocation":
        result = _calculate_asset_allocation(
            arguments["holdings"],
            arguments["current_prices"]
        )
        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    elif name == "calculate_concentration_risk":
        result = _calculate_concentration_risk(
            arguments["holdings"],
            arguments["current_prices"]
        )
        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    elif name == "calculate_sharpe_ratio":
        result = _calculate_sharpe_ratio(
            arguments["returns"],
            arguments.get("risk_free_rate", 0.04)
        )
        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    elif name == "check_rebalancing_needs":
        result = _check_rebalancing_needs(
            arguments["current_allocation"],
            arguments["target_allocation"],
            arguments.get("threshold", 5.0)
        )
        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    elif name == "generate_allocation_chart":
        result = _generate_allocation_chart(arguments["allocation"])
        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    else:
        raise ValueError(f"Unknown tool: {name}")


# Tool implementation functions (from src/tools/portfolio_tools.py)

def _calculate_portfolio_value(holdings: list, current_prices: dict) -> dict:
    """Calculate total portfolio value across all holdings."""
    total_value = 0
    total_cost_basis = 0

    for holding in holdings:
        ticker = holding["ticker"]
        shares = holding["shares"]
        cost_basis = holding.get("cost_basis", 100)

        current_price = current_prices.get(ticker, cost_basis)
        position_value = shares * current_price
        position_cost = shares * cost_basis

        total_value += position_value
        total_cost_basis += position_cost

    total_gain_loss = total_value - total_cost_basis
    total_return_pct = (total_gain_loss / total_cost_basis * 100) if total_cost_basis > 0 else 0

    return {
        "total_value": round(total_value, 2),
        "total_cost_basis": round(total_cost_basis, 2),
        "total_gain_loss": round(total_gain_loss, 2),
        "total_return_pct": round(total_return_pct, 2)
    }


def _calculate_asset_allocation(holdings: list, current_prices: dict) -> dict:
    """Calculate asset allocation breakdown by asset class."""
    allocation = {}
    total_value = 0

    for holding in holdings:
        ticker = holding["ticker"]
        shares = holding["shares"]
        asset_class = holding.get("asset_class", "Unknown")
        cost_basis = holding.get("cost_basis", 0)

        current_price = current_prices.get(ticker, cost_basis if cost_basis > 0 else 100)
        position_value = shares * current_price

        allocation[asset_class] = allocation.get(asset_class, 0) + position_value
        total_value += position_value

    # Convert to percentages
    allocation_pct = {
        asset_class: round(value / total_value * 100, 2) if total_value > 0 else 0
        for asset_class, value in allocation.items()
    }

    return {
        "allocation_by_class": allocation_pct,
        "allocation_dollars": {k: round(v, 2) for k, v in allocation.items()},
        "total_portfolio_value": round(total_value, 2)
    }


def _calculate_concentration_risk(holdings: list, current_prices: dict) -> dict:
    """Analyze concentration risk - largest positions as % of portfolio."""
    positions = []
    total_value = 0

    for holding in holdings:
        ticker = holding["ticker"]
        shares = holding["shares"]
        cost_basis = holding.get("cost_basis", 100)

        current_price = current_prices.get(ticker, cost_basis)
        position_value = shares * current_price

        positions.append({
            "ticker": ticker,
            "value": position_value,
            "shares": shares
        })
        total_value += position_value

    # Sort by value descending
    positions.sort(key=lambda x: x["value"], reverse=True)

    # Calculate percentages
    top_positions = []
    for pos in positions[:10]:  # Top 10
        pct = (pos["value"] / total_value * 100) if total_value > 0 else 0
        top_positions.append({
            "ticker": pos["ticker"],
            "value": round(pos["value"], 2),
            "percentage": round(pct, 2)
        })

    # Calculate top 5 concentration
    top_5_value = sum(pos["value"] for pos in positions[:5])
    top_5_pct = (top_5_value / total_value * 100) if total_value > 0 else 0

    return {
        "top_positions": top_positions,
        "top_5_concentration_pct": round(top_5_pct, 2),
        "total_positions": len(positions),
        "largest_position_pct": top_positions[0]["percentage"] if top_positions else 0
    }


def _calculate_sharpe_ratio(returns: list, risk_free_rate: float = 0.04) -> float:
    """Calculate Sharpe ratio for a portfolio."""
    if not returns or len(returns) < 2:
        return 0.0

    returns_array = np.array(returns)

    # Annualized return and volatility
    avg_return = np.mean(returns_array)
    std_dev = np.std(returns_array, ddof=1)

    if std_dev == 0:
        return 0.0

    # Annualize (assuming monthly returns)
    annualized_return = avg_return * 12
    annualized_volatility = std_dev * np.sqrt(12)

    sharpe = (annualized_return - risk_free_rate) / annualized_volatility

    return round(sharpe, 2)


def _check_rebalancing_needs(
    current_allocation: dict,
    target_allocation: dict,
    threshold: float = 5.0
) -> dict:
    """Check if portfolio needs rebalancing based on drift from target."""
    needs_rebalancing = False
    drifts = {}
    recommendations = []

    for asset_class, target_pct in target_allocation.items():
        current_pct = current_allocation.get(asset_class, 0)
        drift = current_pct - target_pct
        drifts[asset_class] = round(drift, 2)

        if abs(drift) > threshold:
            needs_rebalancing = True
            action = "Reduce" if drift > 0 else "Increase"
            recommendations.append({
                "asset_class": asset_class,
                "action": action,
                "current_pct": current_pct,
                "target_pct": target_pct,
                "drift": round(drift, 2)
            })

    return {
        "needs_rebalancing": needs_rebalancing,
        "drifts": drifts,
        "recommendations": recommendations,
        "threshold_used": threshold
    }


def _generate_allocation_chart(allocation: dict) -> dict:
    """Generate pie chart data for asset allocation."""
    colors = {
        "US Equity": "#1f77b4",
        "International Equity": "#ff7f0e",
        "Bonds": "#2ca02c",
        "Real Estate": "#d62728",
        "Crypto": "#9467bd",
        "Target Date Fund": "#8c564b",
        "Unknown": "#7f7f7f"
    }

    labels = list(allocation.keys())
    values = list(allocation.values())
    chart_colors = [colors.get(label, "#cccccc") for label in labels]

    return {
        "chart_type": "pie",
        "title": "Portfolio Asset Allocation",
        "data": {
            "labels": labels,
            "values": values,
            "colors": chart_colors
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
