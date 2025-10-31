"""Test that main agent uses quick tools directly for simple requests."""

from src.deep_agent import create_finance_deep_agent
from langchain_core.messages import HumanMessage

def test_quick_tool_usage():
    """Test that simple queries use main agent tools directly (no subagent delegation)."""

    print("\n" + "="*80)
    print("TESTING QUICK TOOLS - Main agent should handle these directly")
    print("="*80 + "\n")

    agent = create_finance_deep_agent()

    # Test 1: Simple stock price query (should use get_stock_quote directly)
    print("Test 1: 'What's the price of AAPL?'")
    print("Expected: Main agent uses get_stock_quote directly (no subagent)")
    print("-" * 80)

    state = {
        "messages": [HumanMessage(content="What's the current price of AAPL stock?")],
        "files": {}
    }

    result = agent.invoke(state)

    # Check if subagent was spawned
    messages = result.get("messages", [])
    subagent_spawned = any(
        msg.type == "ai" and hasattr(msg, "tool_calls") and
        any(tc.get("name") == "task" for tc in msg.tool_calls)
        for msg in messages
    )

    if subagent_spawned:
        print("❌ FAIL: Subagent was spawned (should use direct tool)")
    else:
        print("✅ PASS: Main agent handled directly with get_stock_quote")

    # Show response
    ai_messages = [m for m in messages if m.type == "ai" and m.content]
    if ai_messages:
        print(f"\nResponse: {ai_messages[-1].content[:200]}...")

    print("\n" + "="*80)
    print("Test complete!")
    print("="*80 + "\n")


if __name__ == "__main__":
    test_quick_tool_usage()
