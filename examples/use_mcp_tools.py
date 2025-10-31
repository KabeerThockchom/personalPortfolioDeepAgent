#!/usr/bin/env python3
"""
Example: Using MCP Tools with Personal Finance Deep Agent

This script demonstrates how to use the MCP servers to access
financial analysis tools through the Model Context Protocol.
"""

import sys
import os
import asyncio

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.mcp_tools_loader import (
    get_all_mcp_tools_sync,
    get_mcp_tools_by_category_sync,
    get_tools_for_subagent
)


def example_1_load_all_tools():
    """Example 1: Load all tools from all MCP servers"""
    print("=" * 60)
    print("Example 1: Loading ALL MCP tools")
    print("=" * 60)

    tools = get_all_mcp_tools_sync()

    print(f"\n✅ Loaded {len(tools)} tools from all MCP servers")
    print("\nSample tools:")
    for tool in tools[:10]:
        print(f"  - {tool.name}: {tool.description[:60]}...")


def example_2_load_specific_categories():
    """Example 2: Load tools from specific categories"""
    print("\n" + "=" * 60)
    print("Example 2: Loading tools from specific categories")
    print("=" * 60)

    # Load only portfolio and market data tools
    categories = ['portfolio', 'market']
    tools = get_mcp_tools_by_category_sync(categories)

    print(f"\n✅ Loaded {len(tools)} tools from categories: {categories}")
    print("\nTools loaded:")
    for tool in tools:
        print(f"  - {tool.name}")


def example_3_load_subagent_tools():
    """Example 3: Load tools for a specific subagent"""
    print("\n" + "=" * 60)
    print("Example 3: Loading tools for subagent")
    print("=" * 60)

    subagent_name = "portfolio-analyzer"
    tools = get_tools_for_subagent(subagent_name)

    print(f"\n✅ Loaded {len(tools)} tools for subagent: {subagent_name}")
    print("\nTools for portfolio-analyzer:")
    for tool in tools:
        print(f"  - {tool.name}")


async def example_4_use_tool_async():
    """Example 4: Actually invoke an MCP tool"""
    print("\n" + "=" * 60)
    print("Example 4: Invoking an MCP tool")
    print("=" * 60)

    from langchain_mcp_adapters.client import MultiServerMCPClient
    from src.mcp_tools_loader import load_mcp_config

    # Load config and create client
    config = load_mcp_config()

    # Filter to just portfolio server
    portfolio_config = {"portfolio": config["portfolio"]}
    client = MultiServerMCPClient(portfolio_config)

    # Get tools
    tools = await client.get_tools()
    print(f"\n✅ Connected to portfolio MCP server")
    print(f"Available tools: {[t.name for t in tools]}")

    # Find the calculate_portfolio_value tool
    calc_tool = next((t for t in tools if "portfolio_value" in t.name), None)

    if calc_tool:
        print(f"\nInvoking tool: {calc_tool.name}")

        # Example data
        holdings = [
            {"ticker": "AAPL", "shares": 10, "cost_basis": 150},
            {"ticker": "GOOGL", "shares": 5, "cost_basis": 2800}
        ]
        current_prices = {
            "AAPL": 180.50,
            "GOOGL": 3100.00
        }

        # Invoke the tool
        result = calc_tool.invoke({
            "holdings": holdings,
            "current_prices": current_prices
        })

        print("\n📊 Result:")
        print(result)
    else:
        print("\n⚠️ calculate_portfolio_value tool not found")


def example_5_use_with_langchain_agent():
    """Example 5: Use MCP tools with a LangChain agent"""
    print("\n" + "=" * 60)
    print("Example 5: Using MCP tools with LangChain agent")
    print("=" * 60)

    print("\nExample code (requires ANTHROPIC_API_KEY):")
    print("""
from langchain_anthropic import ChatAnthropic
from langchain.agents import create_agent
from src.mcp_tools_loader import get_mcp_tools_by_category_sync

# Load MCP tools
tools = get_mcp_tools_by_category_sync(['portfolio', 'market'])

# Create model
model = ChatAnthropic(model="claude-sonnet-4-5")

# Create agent with MCP tools
agent = create_agent(model, tools)

# Run agent
response = await agent.ainvoke({
    "messages": [{
        "role": "user",
        "content": "What's the current price of AAPL and MSFT?"
    }]
})

print(response)
    """)


def main():
    """Run all examples"""
    print("\n" + "=" * 60)
    print("MCP TOOLS USAGE EXAMPLES")
    print("Personal Finance Deep Agent")
    print("=" * 60)

    # Example 1: Load all tools
    try:
        example_1_load_all_tools()
    except Exception as e:
        print(f"\n❌ Example 1 failed: {e}")

    # Example 2: Load specific categories
    try:
        example_2_load_specific_categories()
    except Exception as e:
        print(f"\n❌ Example 2 failed: {e}")

    # Example 3: Load subagent tools
    try:
        example_3_load_subagent_tools()
    except Exception as e:
        print(f"\n❌ Example 3 failed: {e}")

    # Example 4: Use tool async (requires async context)
    try:
        print("\n" + "=" * 60)
        print("Example 4: Invoking MCP tool (async)")
        print("=" * 60)
        asyncio.run(example_4_use_tool_async())
    except Exception as e:
        print(f"\n❌ Example 4 failed: {e}")
        import traceback
        traceback.print_exc()

    # Example 5: Code example for LangChain integration
    example_5_use_with_langchain_agent()

    print("\n" + "=" * 60)
    print("Examples completed!")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
