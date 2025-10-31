#!/usr/bin/env python3
"""
MCP Server for Web Search

Automatically generated server that wraps tools from src.tools.search_tools
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from mcp.server.fastmcp import FastMCP
from src.tools.search_tools import (
    web_search, web_search_news, web_search_financial
)

# Store tool implementations
web_search_impl = web_search
web_search_news_impl = web_search_news
web_search_financial_impl = web_search_financial

# Create MCP server
mcp = FastMCP("Web Search")


@mcp.tool()
def web_search(*args, **kwargs):
    """Wrapper for web_search from src.tools.search_tools"""
    tool_func = globals()['web_search_impl']
    if hasattr(tool_func, 'invoke'):
        return tool_func.invoke(kwargs if kwargs else {})
    else:
        return tool_func(*args, **kwargs)

@mcp.tool()
def web_search_news(*args, **kwargs):
    """Wrapper for web_search_news from src.tools.search_tools"""
    tool_func = globals()['web_search_news_impl']
    if hasattr(tool_func, 'invoke'):
        return tool_func.invoke(kwargs if kwargs else {})
    else:
        return tool_func(*args, **kwargs)

@mcp.tool()
def web_search_financial(*args, **kwargs):
    """Wrapper for web_search_financial from src.tools.search_tools"""
    tool_func = globals()['web_search_financial_impl']
    if hasattr(tool_func, 'invoke'):
        return tool_func.invoke(kwargs if kwargs else {})
    else:
        return tool_func(*args, **kwargs)


if __name__ == "__main__":
    # Run MCP server with stdio transport for local subprocess communication
    mcp.run(transport="stdio")
