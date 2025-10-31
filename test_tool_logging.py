"""Test that tool logging works for subagent tool calls."""

from src.deep_agent import create_finance_deep_agent
from langchain_core.messages import HumanMessage


def test_tool_logging():
    """Test that subagent tool calls are logged."""

    print("\n" + "="*80)
    print("TESTING TOOL LOGGING - Subagent tool calls should be visible!")
    print("="*80 + "\n")

    agent = create_finance_deep_agent()

    state = {
        "messages": [HumanMessage(content="Get the current price of AAPL")],
        "files": {}
    }

    print("🚀 Running agent... Watch for tool logs!\n")
    print("─" * 80)

    result = agent.invoke(state)

    print("─" * 80)
    print("\n✓ Agent execution complete")

    # Show final response
    ai_messages = [m for m in result["messages"] if m.type == "ai"]
    if ai_messages:
        print(f"\n📝 Final response: {ai_messages[-1].content[:200]}...")

    print("\n" + "="*80)
    print("If you saw tool logs like '🔧 [get_stock_quote]' above, it worked!")
    print("="*80 + "\n")


if __name__ == "__main__":
    test_tool_logging()
