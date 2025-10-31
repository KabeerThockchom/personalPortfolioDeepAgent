#!/usr/bin/env python3
"""
Script to create all MCP servers from existing tool modules.

This script automatically generates MCP server files for all tool categories
by importing the tools from the existing src/tools/ modules and wrapping them
in FastMCP servers.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import all tools
from src.tools import debt_tools, tax_tools, risk_tools, search_tools, portfolio_update_tools

def create_mcp_server_from_module(module, server_name, description):
    """
    Create an MCP server file from a tool module.

    Args:
        module: The Python module containing the tools
        server_name: Name for the MCP server
        description: Description of what the server does
    """
    # Get all tool functions from the module
    tools = []
    for attr_name in dir(module):
        attr = getattr(module, attr_name)
        if callable(attr) and hasattr(attr, '__wrapped__'):  # LangChain tools have __wrapped__
            tools.append(attr_name)

    # Create server file
    server_filename = f"{server_name.lower().replace(' ', '_')}_server.py"
    server_path = os.path.join(os.path.dirname(__file__), server_filename)

    # Generate server code
    code = f'''#!/usr/bin/env python3
"""
MCP Server for {server_name}

{description}
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from mcp.server.fastmcp import FastMCP
from {module.__name__} import (
    {', '.join(tools)}
)

# Create MCP server
mcp = FastMCP("{server_name}")

# Register all tools
'''

    for tool_name in tools:
        code += f'''
@mcp.tool()
def {tool_name}_mcp(*args, **kwargs):
    """Proxy to {module.__name__}.{tool_name}"""
    return {tool_name}.invoke(kwargs)

'''

    code += '''
if __name__ == "__main__":
    # Run MCP server with stdio transport for local subprocess communication
    mcp.run(transport="stdio")
'''

    with open(server_path, 'w') as f:
        f.write(code)

    # Make executable
    os.chmod(server_path, 0o755)

    print(f"Created MCP server: {server_filename}")
    return server_path


if __name__ == "__main__":
    servers = [
        (debt_tools, "Debt Management", "Exposes debt management calculation tools as MCP tools."),
        (tax_tools, "Tax Optimization", "Exposes tax optimization calculation tools as MCP tools."),
        (risk_tools, "Risk Assessment", "Exposes risk assessment calculation tools as MCP tools."),
        (search_tools, "Web Search", "Exposes Tavily web search tools as MCP tools."),
        (portfolio_update_tools, "Portfolio Updates", "Exposes portfolio persistence tools as MCP tools."),
    ]

    for module, name, desc in servers:
        create_mcp_server_from_module(module, name, desc)

    print("\nAll MCP servers created successfully!")
