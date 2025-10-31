"""Test enhanced display of tool calls and results."""

import sys
import json

# Add project root to path
sys.path.insert(0, '/Users/kabeerthockchom/Desktop/personal_finance_deep_agent')

from chat import (
    print_tool_call,
    print_tool_result,
    format_value,
    Colors
)


def test_enhanced_display():
    """Test the enhanced tool call and result display."""

    print(f"\n{Colors.HEADER}{'='*80}")
    print("Testing Enhanced Tool Display")
    print(f"{'='*80}{Colors.ENDC}\n")

    # Test 1: Simple tool call
    print(f"\n{Colors.BOLD}Test 1: Simple tool call (read_file){Colors.ENDC}")
    print_tool_call("read_file", {"file_path": "/financial_data/portfolio.json"})

    # Test 2: Tool call with complex args (Yahoo Finance)
    print(f"\n{Colors.BOLD}Test 2: Yahoo Finance tool call{Colors.ENDC}")
    print_tool_call("get_stock_quote", {
        "symbol": "AAPL",
        "region": "US",
        "lang": "en-US"
    })

    # Test 3: Subagent spawn
    print(f"\n{Colors.BOLD}Test 3: Subagent spawn{Colors.ENDC}")
    print_tool_call("task", {
        "subagent_type": "market-data-fetcher",
        "description": "Fetch real-time quotes for AAPL, MSFT, and GOOGL to calculate current portfolio value"
    })

    # Test 4: Tool call with indentation (simulating subagent)
    print(f"\n{Colors.BOLD}Test 4: Subagent tool call (indented){Colors.ENDC}")
    print_tool_call("get_multiple_quotes", {
        "symbols": ["AAPL", "MSFT", "GOOGL"],
        "region": "US"
    }, indent="  ")

    # Test 5: Simple string result
    print(f"\n{Colors.BOLD}Test 5: Simple string result{Colors.ENDC}")
    print_tool_result("File contents loaded successfully")

    # Test 6: Dict result with success/error
    print(f"\n{Colors.BOLD}Test 6: Dict result (success){Colors.ENDC}")
    print_tool_result({
        "success": True,
        "symbol": "AAPL",
        "summary": "📊 Stock Quote for AAPL\n\nPrice: $150.25 (+2.50, +1.69%)\nMarket Cap: $2.4T\nP/E Ratio: 28.5\nDividend Yield: 0.52%",
        "key_metrics": {
            "price": 150.25,
            "change": 2.50,
            "changePercent": 1.69,
            "marketCap": "2.4T"
        },
        "file_path": "/financial_data/AAPL_quote.json"
    })

    # Test 7: Dict result (error)
    print(f"\n{Colors.BOLD}Test 7: Dict result (error){Colors.ENDC}")
    print_tool_result({
        "success": False,
        "symbol": "INVALID",
        "error": "Symbol not found"
    })

    # Test 8: List result
    print(f"\n{Colors.BOLD}Test 8: List result{Colors.ENDC}")
    print_tool_result([
        {"ticker": "AAPL", "price": 150.25},
        {"ticker": "MSFT", "price": 330.15},
        {"ticker": "GOOGL", "price": 140.50},
        {"ticker": "NVDA", "price": 495.75},
        {"ticker": "TSLA", "price": 245.80}
    ])

    # Test 9: Long text result
    print(f"\n{Colors.BOLD}Test 9: Long text result{Colors.ENDC}")
    long_text = "This is a very long result that contains many lines of text. " * 20
    print_tool_result(long_text)

    # Test 10: Tool result with indentation (subagent)
    print(f"\n{Colors.BOLD}Test 10: Subagent tool result (indented){Colors.ENDC}")
    print_tool_result({
        "success": True,
        "summary": "✓ Fetched quotes for 3 symbols\n\nAAPL: $150.25 (+1.69%)\nMSFT: $330.15 (-0.36%)\nGOOGL: $140.50 (+0.82%)",
        "key_metrics": {
            "symbols_fetched": 3,
            "total_market_cap": "$5.2T"
        }
    }, indent="  ")

    # Test 11: format_value function
    print(f"\n{Colors.BOLD}Test 11: format_value with dict{Colors.ENDC}")
    test_dict = {
        "portfolio_value": 125000,
        "holdings": ["AAPL", "MSFT", "GOOGL"],
        "allocation": {"stocks": 0.7, "bonds": 0.3}
    }
    formatted = format_value(test_dict)
    print(f"{Colors.OKBLUE}{formatted}{Colors.ENDC}")

    print(f"\n{Colors.OKGREEN}{'='*80}")
    print("✓ All display tests completed successfully!")
    print(f"{'='*80}{Colors.ENDC}\n")


if __name__ == "__main__":
    test_enhanced_display()
