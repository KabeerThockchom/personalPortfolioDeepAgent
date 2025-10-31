#!/usr/bin/env python3
"""
MCP Server for Risk Assessment

Automatically generated server that wraps tools from src.tools.risk_tools
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from mcp.server.fastmcp import FastMCP
from src.tools.risk_tools import (
    calculate_emergency_fund_adequacy, analyze_insurance_gaps, calculate_portfolio_volatility, run_stress_test_scenarios, calculate_value_at_risk, analyze_concentration_risk, generate_risk_dashboard
)

# Store tool implementations
calculate_emergency_fund_adequacy_impl = calculate_emergency_fund_adequacy
analyze_insurance_gaps_impl = analyze_insurance_gaps
calculate_portfolio_volatility_impl = calculate_portfolio_volatility
run_stress_test_scenarios_impl = run_stress_test_scenarios
calculate_value_at_risk_impl = calculate_value_at_risk
analyze_concentration_risk_impl = analyze_concentration_risk
generate_risk_dashboard_impl = generate_risk_dashboard

# Create MCP server
mcp = FastMCP("Risk Assessment")


@mcp.tool()
def calculate_emergency_fund_adequacy(*args, **kwargs):
    """Wrapper for calculate_emergency_fund_adequacy from src.tools.risk_tools"""
    tool_func = globals()['calculate_emergency_fund_adequacy_impl']
    if hasattr(tool_func, 'invoke'):
        return tool_func.invoke(kwargs if kwargs else {})
    else:
        return tool_func(*args, **kwargs)

@mcp.tool()
def analyze_insurance_gaps(*args, **kwargs):
    """Wrapper for analyze_insurance_gaps from src.tools.risk_tools"""
    tool_func = globals()['analyze_insurance_gaps_impl']
    if hasattr(tool_func, 'invoke'):
        return tool_func.invoke(kwargs if kwargs else {})
    else:
        return tool_func(*args, **kwargs)

@mcp.tool()
def calculate_portfolio_volatility(*args, **kwargs):
    """Wrapper for calculate_portfolio_volatility from src.tools.risk_tools"""
    tool_func = globals()['calculate_portfolio_volatility_impl']
    if hasattr(tool_func, 'invoke'):
        return tool_func.invoke(kwargs if kwargs else {})
    else:
        return tool_func(*args, **kwargs)

@mcp.tool()
def run_stress_test_scenarios(*args, **kwargs):
    """Wrapper for run_stress_test_scenarios from src.tools.risk_tools"""
    tool_func = globals()['run_stress_test_scenarios_impl']
    if hasattr(tool_func, 'invoke'):
        return tool_func.invoke(kwargs if kwargs else {})
    else:
        return tool_func(*args, **kwargs)

@mcp.tool()
def calculate_value_at_risk(*args, **kwargs):
    """Wrapper for calculate_value_at_risk from src.tools.risk_tools"""
    tool_func = globals()['calculate_value_at_risk_impl']
    if hasattr(tool_func, 'invoke'):
        return tool_func.invoke(kwargs if kwargs else {})
    else:
        return tool_func(*args, **kwargs)

@mcp.tool()
def analyze_concentration_risk(*args, **kwargs):
    """Wrapper for analyze_concentration_risk from src.tools.risk_tools"""
    tool_func = globals()['analyze_concentration_risk_impl']
    if hasattr(tool_func, 'invoke'):
        return tool_func.invoke(kwargs if kwargs else {})
    else:
        return tool_func(*args, **kwargs)

@mcp.tool()
def generate_risk_dashboard(*args, **kwargs):
    """Wrapper for generate_risk_dashboard from src.tools.risk_tools"""
    tool_func = globals()['generate_risk_dashboard_impl']
    if hasattr(tool_func, 'invoke'):
        return tool_func.invoke(kwargs if kwargs else {})
    else:
        return tool_func(*args, **kwargs)


if __name__ == "__main__":
    # Run MCP server with stdio transport for local subprocess communication
    mcp.run(transport="stdio")
