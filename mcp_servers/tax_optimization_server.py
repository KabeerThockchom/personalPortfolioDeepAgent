#!/usr/bin/env python3
"""
MCP Server for Tax Optimization

Automatically generated server that wraps tools from src.tools.tax_tools
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from mcp.server.fastmcp import FastMCP
from src.tools.tax_tools import (
    calculate_effective_tax_rate, identify_tax_loss_harvesting_opportunities, analyze_roth_conversion_opportunity, optimize_withdrawal_sequence, calculate_capital_gains_tax
)

# Store tool implementations
calculate_effective_tax_rate_impl = calculate_effective_tax_rate
identify_tax_loss_harvesting_opportunities_impl = identify_tax_loss_harvesting_opportunities
analyze_roth_conversion_opportunity_impl = analyze_roth_conversion_opportunity
optimize_withdrawal_sequence_impl = optimize_withdrawal_sequence
calculate_capital_gains_tax_impl = calculate_capital_gains_tax

# Create MCP server
mcp = FastMCP("Tax Optimization")


@mcp.tool()
def calculate_effective_tax_rate(*args, **kwargs):
    """Wrapper for calculate_effective_tax_rate from src.tools.tax_tools"""
    tool_func = globals()['calculate_effective_tax_rate_impl']
    if hasattr(tool_func, 'invoke'):
        return tool_func.invoke(kwargs if kwargs else {})
    else:
        return tool_func(*args, **kwargs)

@mcp.tool()
def identify_tax_loss_harvesting_opportunities(*args, **kwargs):
    """Wrapper for identify_tax_loss_harvesting_opportunities from src.tools.tax_tools"""
    tool_func = globals()['identify_tax_loss_harvesting_opportunities_impl']
    if hasattr(tool_func, 'invoke'):
        return tool_func.invoke(kwargs if kwargs else {})
    else:
        return tool_func(*args, **kwargs)

@mcp.tool()
def analyze_roth_conversion_opportunity(*args, **kwargs):
    """Wrapper for analyze_roth_conversion_opportunity from src.tools.tax_tools"""
    tool_func = globals()['analyze_roth_conversion_opportunity_impl']
    if hasattr(tool_func, 'invoke'):
        return tool_func.invoke(kwargs if kwargs else {})
    else:
        return tool_func(*args, **kwargs)

@mcp.tool()
def optimize_withdrawal_sequence(*args, **kwargs):
    """Wrapper for optimize_withdrawal_sequence from src.tools.tax_tools"""
    tool_func = globals()['optimize_withdrawal_sequence_impl']
    if hasattr(tool_func, 'invoke'):
        return tool_func.invoke(kwargs if kwargs else {})
    else:
        return tool_func(*args, **kwargs)

@mcp.tool()
def calculate_capital_gains_tax(*args, **kwargs):
    """Wrapper for calculate_capital_gains_tax from src.tools.tax_tools"""
    tool_func = globals()['calculate_capital_gains_tax_impl']
    if hasattr(tool_func, 'invoke'):
        return tool_func.invoke(kwargs if kwargs else {})
    else:
        return tool_func(*args, **kwargs)


if __name__ == "__main__":
    # Run MCP server with stdio transport for local subprocess communication
    mcp.run(transport="stdio")
