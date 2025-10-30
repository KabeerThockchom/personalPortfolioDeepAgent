"""
Example: Testing Parallel Subagent Execution

This demonstrates the updated system's ability to spawn multiple subagents
in parallel for independent tasks.
"""

import os
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage

from src.deep_agent import create_finance_deep_agent

load_dotenv()


def test_parallel_stock_comparison():
    """
    Test parallel execution by asking the agent to compare multiple stocks.

    Expected behavior:
    - Agent should spawn multiple market-data-fetcher subagents in PARALLEL
    - All stock data should be fetched simultaneously
    - Much faster than sequential execution
    """

    print("=" * 80)
    print("EXAMPLE: Parallel Subagent Execution - Stock Comparison")
    print("=" * 80)

    # Create agent
    print("\nCreating finance deep agent with parallel execution capabilities...")
    agent = create_finance_deep_agent()

    # Query that benefits from parallel execution
    query = """
    Compare these 4 stocks: NVDA, AAPL, MSFT, and GOOGL.

    For each stock, I need:
    - Current price
    - P/E ratio
    - Market cap
    - 52-week high/low

    Present the comparison in a table format.

    NOTE: These are independent lookups - you should fetch all 4 stocks
    in PARALLEL using multiple market-data-fetcher subagent calls in the
    same response for maximum speed.
    """

    print(f"\nQuery: {query}")
    print("\n" + "=" * 80)
    print("EXECUTION (watch for parallel task calls):")
    print("=" * 80)

    state = {
        "messages": [HumanMessage(content=query)],
        "files": {}
    }

    # Track execution
    step_count = 0
    parallel_steps = []

    try:
        for chunk in agent.stream(state, stream_mode="updates"):
            step_count += 1
            for node_name, updates in chunk.items():
                print(f"\n[Step {step_count}] {node_name}")

                # Try to detect task calls (best effort)
                if updates:
                    print(f"  Update type: {type(updates)}")

        print("\n" + "=" * 80)
        print("COMPLETION")
        print("=" * 80)

        print("\n✅ Test completed!")
        print(f"Total steps: {step_count}")

        print("\n💡 TIP: Check the execution logs above.")
        print("   - If you see 4 task calls in ONE step → Parallel execution ✅")
        print("   - If you see 4 separate steps with 1 task each → Sequential ❌")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


def test_comprehensive_financial_analysis():
    """
    Test parallel execution with comprehensive financial analysis.

    Expected behavior:
    - Agent should spawn portfolio-analyzer, cashflow-analyzer, and risk-assessor
      in PARALLEL since they're independent analyses
    """

    print("\n\n" + "=" * 80)
    print("EXAMPLE: Parallel Comprehensive Analysis")
    print("=" * 80)

    agent = create_finance_deep_agent()

    query = """
    Give me a complete financial health assessment.

    Analyze:
    1. My investment portfolio performance
    2. My monthly cash flow
    3. My risk exposure (emergency fund, insurance)

    These are independent analyses that don't depend on each other,
    so run them in PARALLEL for speed.
    """

    print(f"\nQuery: {query}")
    print("\n" + "=" * 80)
    print("EXECUTION:")
    print("=" * 80)

    state = {
        "messages": [HumanMessage(content=query)],
        "files": {}
    }

    try:
        for chunk in agent.stream(state, stream_mode="updates"):
            for node_name, updates in chunk.items():
                print(f"  {node_name}")

        print("\n✅ Analysis complete!")

    except Exception as e:
        print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("PARALLEL SUBAGENT EXECUTION TESTS")
    print("=" * 80)
    print("\nThese examples demonstrate the updated system's ability to:")
    print("  1. Detect when tasks are independent")
    print("  2. Spawn multiple subagents in the SAME response")
    print("  3. Execute them in parallel (via LangGraph supersteps)")
    print("  4. Synthesize results from all parallel executions")

    print("\n" + "=" * 80)

    # Run tests
    try:
        test_parallel_stock_comparison()
        # Uncomment to run second test:
        # test_comprehensive_financial_analysis()

    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "=" * 80)
    print("TESTS COMPLETE")
    print("=" * 80)
