#!/usr/bin/env python3
"""
MCP Server for Debt Management

Automatically generated server that wraps tools from src.tools.debt_tools
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from mcp.server.fastmcp import FastMCP
from src.tools.debt_tools import (
    calculate_debt_payoff_timeline, compare_avalanche_vs_snowball, calculate_total_interest_cost, optimize_extra_payment_allocation, calculate_debt_to_income_ratio, generate_payoff_chart
)

# Store tool implementations
calculate_debt_payoff_timeline_impl = calculate_debt_payoff_timeline
compare_avalanche_vs_snowball_impl = compare_avalanche_vs_snowball
calculate_total_interest_cost_impl = calculate_total_interest_cost
optimize_extra_payment_allocation_impl = optimize_extra_payment_allocation
calculate_debt_to_income_ratio_impl = calculate_debt_to_income_ratio
generate_payoff_chart_impl = generate_payoff_chart

# Create MCP server
mcp = FastMCP("Debt Management")


@mcp.tool()
def calculate_debt_payoff_timeline(*args, **kwargs):
    """Wrapper for calculate_debt_payoff_timeline from src.tools.debt_tools"""
    tool_func = globals()['calculate_debt_payoff_timeline_impl']
    if hasattr(tool_func, 'invoke'):
        return tool_func.invoke(kwargs if kwargs else {})
    else:
        return tool_func(*args, **kwargs)

@mcp.tool()
def compare_avalanche_vs_snowball(*args, **kwargs):
    """Wrapper for compare_avalanche_vs_snowball from src.tools.debt_tools"""
    tool_func = globals()['compare_avalanche_vs_snowball_impl']
    if hasattr(tool_func, 'invoke'):
        return tool_func.invoke(kwargs if kwargs else {})
    else:
        return tool_func(*args, **kwargs)

@mcp.tool()
def calculate_total_interest_cost(*args, **kwargs):
    """Wrapper for calculate_total_interest_cost from src.tools.debt_tools"""
    tool_func = globals()['calculate_total_interest_cost_impl']
    if hasattr(tool_func, 'invoke'):
        return tool_func.invoke(kwargs if kwargs else {})
    else:
        return tool_func(*args, **kwargs)

@mcp.tool()
def optimize_extra_payment_allocation(*args, **kwargs):
    """Wrapper for optimize_extra_payment_allocation from src.tools.debt_tools"""
    tool_func = globals()['optimize_extra_payment_allocation_impl']
    if hasattr(tool_func, 'invoke'):
        return tool_func.invoke(kwargs if kwargs else {})
    else:
        return tool_func(*args, **kwargs)

@mcp.tool()
def calculate_debt_to_income_ratio(*args, **kwargs):
    """Wrapper for calculate_debt_to_income_ratio from src.tools.debt_tools"""
    tool_func = globals()['calculate_debt_to_income_ratio_impl']
    if hasattr(tool_func, 'invoke'):
        return tool_func.invoke(kwargs if kwargs else {})
    else:
        return tool_func(*args, **kwargs)

@mcp.tool()
def generate_payoff_chart(*args, **kwargs):
    """Wrapper for generate_payoff_chart from src.tools.debt_tools"""
    tool_func = globals()['generate_payoff_chart_impl']
    if hasattr(tool_func, 'invoke'):
        return tool_func.invoke(kwargs if kwargs else {})
    else:
        return tool_func(*args, **kwargs)


if __name__ == "__main__":
    # Run MCP server with stdio transport for local subprocess communication
    mcp.run(transport="stdio")
