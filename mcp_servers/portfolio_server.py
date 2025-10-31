#!/usr/bin/env python3
"""
MCP Server for Portfolio Analysis Tools

Exposes portfolio calculation tools as MCP tools.
Includes: portfolio valuation, asset allocation, concentration risk,
Sharpe ratio, rebalancing checks, and allocation charts.
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from mcp.server.fastmcp import FastMCP
from typing import Dict, List
import numpy as np

# Create MCP server
mcp = FastMCP("Portfolio Analysis")

@mcp.tool()
def calculate_portfolio_value(holdings: List[Dict], current_prices: Dict[str, float]) -> Dict:
    """
    Calculate total portfolio value across all holdings.

    Args:
        holdings: List of holdings with ticker, shares, cost_basis
        current_prices: Dictionary of ticker -> current price

    Returns:
        Dictionary with total value, total cost basis, total gain/loss
    """
    total_value = 0
    total_cost_basis = 0

    for holding in holdings:
        ticker = holding["ticker"]
        shares = holding["shares"]
        cost_basis = holding.get("cost_basis", 100)  # Default to 100 if missing

        current_price = current_prices.get(ticker, cost_basis)  # Fallback to cost basis

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


@mcp.tool()
def calculate_asset_allocation(holdings: List[Dict], current_prices: Dict[str, float]) -> Dict:
    """
    Calculate asset allocation breakdown by asset class.

    Args:
        holdings: List of holdings with ticker, shares, asset_class
        current_prices: Dictionary of ticker -> current price

    Returns:
        Dictionary with allocation percentages by asset class
    """
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


@mcp.tool()
def calculate_concentration_risk(holdings: List[Dict], current_prices: Dict[str, float]) -> Dict:
    """
    Analyze concentration risk - largest positions as % of portfolio.

    Args:
        holdings: List of holdings with ticker, shares
        current_prices: Dictionary of ticker -> current price

    Returns:
        Dictionary with top positions and concentration metrics
    """
    positions = []
    total_value = 0

    for holding in holdings:
        ticker = holding["ticker"]
        shares = holding["shares"]
        cost_basis = holding.get("cost_basis", 100)  # Default to 100 if missing

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


@mcp.tool()
def calculate_sharpe_ratio(returns: List[float], risk_free_rate: float = 0.04) -> float:
    """
    Calculate Sharpe ratio for a portfolio.

    Args:
        returns: List of periodic returns
        risk_free_rate: Annual risk-free rate (default 4%)

    Returns:
        Sharpe ratio
    """
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


@mcp.tool()
def check_rebalancing_needs(
    current_allocation: Dict[str, float],
    target_allocation: Dict[str, float],
    threshold: float = 5.0
) -> Dict:
    """
    Check if portfolio needs rebalancing based on drift from target.

    Args:
        current_allocation: Current allocation percentages by asset class
        target_allocation: Target allocation percentages by asset class
        threshold: Drift threshold in percentage points (default 5%)

    Returns:
        Dictionary with rebalancing recommendations
    """
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


@mcp.tool()
def generate_allocation_chart(allocation: Dict[str, float]) -> Dict:
    """
    Generate pie chart data for asset allocation.

    Args:
        allocation: Dictionary of asset_class -> percentage

    Returns:
        Chart data structure for UI rendering
    """
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


if __name__ == "__main__":
    # Run MCP server with stdio transport for local subprocess communication
    mcp.run(transport="stdio")
