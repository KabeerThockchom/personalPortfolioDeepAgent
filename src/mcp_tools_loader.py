"""
MCP Tools Loader

Loads tools from MCP servers using langchain-mcp-adapters.
Provides a unified interface for agents to access tools from all MCP servers.
"""

import json
import os
import asyncio
from typing import Dict, List
from langchain_mcp_adapters.client import MultiServerMCPClient


# Get absolute path to project root
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
MCP_CONFIG_PATH = os.path.join(PROJECT_ROOT, 'mcp_config.json')


def load_mcp_config() -> Dict:
    """Load MCP server configuration from mcp_config.json"""
    if not os.path.exists(MCP_CONFIG_PATH):
        raise FileNotFoundError(f"MCP config file not found: {MCP_CONFIG_PATH}")

    with open(MCP_CONFIG_PATH, 'r') as f:
        config = json.load(f)

    # Convert paths to absolute paths
    for server_name, server_config in config['mcpServers'].items():
        if 'args' in server_config and len(server_config['args']) > 0:
            # Make paths absolute
            script_path = server_config['args'][0]
            if not os.path.isabs(script_path):
                server_config['args'][0] = os.path.join(PROJECT_ROOT, script_path)

    return config['mcpServers']


async def get_all_mcp_tools():
    """
    Get all tools from all MCP servers.

    Returns:
        List of tool objects that can be used with LangChain agents
    """
    config = load_mcp_config()

    # Create MultiServerMCPClient
    client = MultiServerMCPClient(config)

    # Get all tools from all servers
    tools = await client.get_tools()

    return tools


async def get_mcp_tools_by_category(categories: List[str]):
    """
    Get tools from specific MCP server categories.

    Args:
        categories: List of server names (e.g., ['portfolio', 'market', 'search'])

    Returns:
        List of tool objects from specified servers
    """
    full_config = load_mcp_config()

    # Filter config to only requested categories
    filtered_config = {
        name: config
        for name, config in full_config.items()
        if name in categories
    }

    if not filtered_config:
        raise ValueError(f"No matching MCP servers found for categories: {categories}")

    # Create MultiServerMCPClient with filtered config
    client = MultiServerMCPClient(filtered_config)

    # Get tools from specified servers
    tools = await client.get_tools()

    return tools


def get_all_mcp_tools_sync():
    """Synchronous wrapper for get_all_mcp_tools()"""
    return asyncio.run(get_all_mcp_tools())


def get_mcp_tools_by_category_sync(categories: List[str]):
    """Synchronous wrapper for get_mcp_tools_by_category()"""
    return asyncio.run(get_mcp_tools_by_category(categories))


# Category mappings for subagents
SUBAGENT_TOOL_CATEGORIES = {
    "market-data-fetcher": ["market", "search"],
    "research-analyst": ["market", "search"],
    "portfolio-analyzer": ["portfolio", "market"],
    "cashflow-analyzer": ["cashflow", "portfolio_updates"],
    "goal-planner": ["goal", "portfolio"],
    "debt-manager": ["debt", "portfolio"],
    "tax-optimizer": ["tax", "portfolio", "market"],
    "risk-assessor": ["risk", "portfolio", "market"],
}


def get_tools_for_subagent(subagent_name: str):
    """
    Get the appropriate MCP tools for a specific subagent.

    Args:
        subagent_name: Name of the subagent (e.g., "market-data-fetcher")

    Returns:
        List of tools for this subagent
    """
    if subagent_name not in SUBAGENT_TOOL_CATEGORIES:
        raise ValueError(f"Unknown subagent: {subagent_name}")

    categories = SUBAGENT_TOOL_CATEGORIES[subagent_name]
    return get_mcp_tools_by_category_sync(categories)


if __name__ == "__main__":
    # Test loading tools
    print("Testing MCP tools loader...\n")

    # Load config
    config = load_mcp_config()
    print(f"Found {len(config)} MCP servers:")
    for name, server_config in config.items():
        print(f"  - {name}: {server_config.get('description', 'No description')}")

    print("\n✅ MCP configuration loaded successfully!")

    # Note: Can't test async functions in __main__ without proper event loop
    print("\nTo test tool loading, use:")
    print("  tools = get_all_mcp_tools_sync()")
    print("  tools = get_mcp_tools_by_category_sync(['portfolio', 'market'])")
