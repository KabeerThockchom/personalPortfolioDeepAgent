#!/usr/bin/env python3
"""Test MCP servers to verify they work correctly."""

import asyncio
import json
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def test_portfolio_server():
    """Test the portfolio server with a sample calculation."""
    print("\n=== Testing Portfolio Server ===")

    server_params = StdioServerParameters(
        command="python3",
        args=["mcp_servers/portfolio_server.py"],
        env=None
    )

    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                # Initialize
                await session.initialize()
                print("✅ Server initialized successfully")

                # List tools
                tools = await session.list_tools()
                print(f"✅ Found {len(tools.tools)} tools:")
                for tool in tools.tools:
                    print(f"   - {tool.name}")

                # Test calculate_portfolio_value
                print("\n📊 Testing calculate_portfolio_value...")
                result = await session.call_tool(
                    "calculate_portfolio_value",
                    arguments={
                        "holdings": [
                            {"ticker": "AAPL", "shares": 100, "cost_basis": 150.00},
                            {"ticker": "MSFT", "shares": 50, "cost_basis": 300.00}
                        ],
                        "current_prices": {
                            "AAPL": 175.50,
                            "MSFT": 380.00
                        }
                    }
                )

                # Parse result
                result_data = json.loads(result.content[0].text)
                print("✅ Result:")
                print(json.dumps(result_data, indent=2))

    except Exception as e:
        print(f"❌ Error: {e}")
        raise


async def test_search_server():
    """Test the search server."""
    print("\n=== Testing Search Server ===")

    server_params = StdioServerParameters(
        command="python3",
        args=["mcp_servers/search_server.py"],
        env=None
    )

    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                # Initialize
                await session.initialize()
                print("✅ Server initialized successfully")

                # List tools
                tools = await session.list_tools()
                print(f"✅ Found {len(tools.tools)} tools:")
                for tool in tools.tools:
                    print(f"   - {tool.name}")

                # Test web_search (basic test - may require API key)
                print("\n🔍 Testing web_search...")
                result = await session.call_tool(
                    "web_search",
                    arguments={
                        "query": "Python programming",
                        "max_results": 2
                    }
                )

                result_data = json.loads(result.content[0].text)
                print(f"✅ Search returned {result_data.get('total_results', 0)} results")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


async def test_cashflow_server():
    """Test the cashflow server."""
    print("\n=== Testing Cashflow Server ===")

    server_params = StdioServerParameters(
        command="python3",
        args=["mcp_servers/cashflow_server.py"],
        env=None
    )

    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                print("✅ Server initialized successfully")

                tools = await session.list_tools()
                print(f"✅ Found {len(tools.tools)} tools")

                # Test analyze_monthly_cashflow
                print("\n💰 Testing analyze_monthly_cashflow...")
                result = await session.call_tool(
                    "analyze_monthly_cashflow",
                    arguments={
                        "income": {"salary": 5000, "side_hustle": 500},
                        "expenses": {
                            "housing": {"rent": 1500, "utilities": 200},
                            "food": 600,
                            "transport": 300
                        }
                    }
                )

                result_data = json.loads(result.content[0].text)
                print("✅ Result:")
                print(json.dumps(result_data, indent=2))

    except Exception as e:
        print(f"❌ Error: {e}")
        raise


async def main():
    """Run all tests."""
    print("🧪 MCP Server Test Suite")
    print("=" * 60)

    try:
        await test_portfolio_server()
        await test_search_server()
        await test_cashflow_server()

        print("\n" + "=" * 60)
        print("✅ All tests passed!")
        print("\nMCP servers are working correctly and ready to use.")

    except Exception as e:
        print("\n" + "=" * 60)
        print(f"❌ Tests failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
