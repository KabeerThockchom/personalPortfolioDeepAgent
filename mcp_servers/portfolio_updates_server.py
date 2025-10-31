#!/usr/bin/env python3
"""
MCP Server for Portfolio Updates

Automatically generated server that wraps tools from src.tools.portfolio_update_tools
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from mcp.server.fastmcp import FastMCP
from src.tools.portfolio_update_tools import (
    update_investment_holding, update_cash_balance, record_expense, update_credit_card_balance, recalculate_net_worth
)

# Store tool implementations
update_investment_holding_impl = update_investment_holding
update_cash_balance_impl = update_cash_balance
record_expense_impl = record_expense
update_credit_card_balance_impl = update_credit_card_balance
recalculate_net_worth_impl = recalculate_net_worth

# Create MCP server
mcp = FastMCP("Portfolio Updates")


@mcp.tool()
def update_investment_holding(*args, **kwargs):
    """Wrapper for update_investment_holding from src.tools.portfolio_update_tools"""
    tool_func = globals()['update_investment_holding_impl']
    if hasattr(tool_func, 'invoke'):
        return tool_func.invoke(kwargs if kwargs else {})
    else:
        return tool_func(*args, **kwargs)

@mcp.tool()
def update_cash_balance(*args, **kwargs):
    """Wrapper for update_cash_balance from src.tools.portfolio_update_tools"""
    tool_func = globals()['update_cash_balance_impl']
    if hasattr(tool_func, 'invoke'):
        return tool_func.invoke(kwargs if kwargs else {})
    else:
        return tool_func(*args, **kwargs)

@mcp.tool()
def record_expense(*args, **kwargs):
    """Wrapper for record_expense from src.tools.portfolio_update_tools"""
    tool_func = globals()['record_expense_impl']
    if hasattr(tool_func, 'invoke'):
        return tool_func.invoke(kwargs if kwargs else {})
    else:
        return tool_func(*args, **kwargs)

@mcp.tool()
def update_credit_card_balance(*args, **kwargs):
    """Wrapper for update_credit_card_balance from src.tools.portfolio_update_tools"""
    tool_func = globals()['update_credit_card_balance_impl']
    if hasattr(tool_func, 'invoke'):
        return tool_func.invoke(kwargs if kwargs else {})
    else:
        return tool_func(*args, **kwargs)

@mcp.tool()
def recalculate_net_worth(*args, **kwargs):
    """Wrapper for recalculate_net_worth from src.tools.portfolio_update_tools"""
    tool_func = globals()['recalculate_net_worth_impl']
    if hasattr(tool_func, 'invoke'):
        return tool_func.invoke(kwargs if kwargs else {})
    else:
        return tool_func(*args, **kwargs)


if __name__ == "__main__":
    # Run MCP server with stdio transport for local subprocess communication
    mcp.run(transport="stdio")
