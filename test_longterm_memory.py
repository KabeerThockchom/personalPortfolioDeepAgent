"""Test long-term memory functionality."""

from src.deep_agent import create_finance_deep_agent
from langchain_core.messages import HumanMessage
from langgraph.store.memory import InMemoryStore


def test_longterm_memory():
    """Test that /memories/ paths persist across threads."""

    # Create agent with explicit store
    store = InMemoryStore()
    agent = create_finance_deep_agent(store=store)

    print("✓ Agent created with InMemoryStore")

    # Thread 1: Write to /memories/
    print("\n--- Thread 1: Writing to /memories/ ---")
    state1 = {
        "messages": [
            HumanMessage(content="Write 'Hello from thread 1' to /memories/test.txt")
        ],
        "files": {}
    }

    result1 = agent.invoke(state1, config={"configurable": {"thread_id": "thread-1"}})

    if "files" in result1:
        print(f"Files in thread 1: {list(result1['files'].keys())}")

    # Thread 2: Try to read from /memories/
    print("\n--- Thread 2: Reading from /memories/ ---")
    state2 = {
        "messages": [
            HumanMessage(content="Read /memories/test.txt and tell me what it says")
        ],
        "files": {}
    }

    result2 = agent.invoke(state2, config={"configurable": {"thread_id": "thread-2"}})

    # Check if file persists
    if "files" in result2:
        print(f"Files in thread 2: {list(result2['files'].keys())}")

    # Get final response
    ai_messages = [m for m in result2["messages"] if m.type == "ai"]
    if ai_messages:
        print(f"\nAgent response: {ai_messages[-1].content[:200]}")

    # Check store directly
    print("\n--- Checking Store directly ---")
    print(f"Store type: {type(store)}")

    # Try to list items in store
    try:
        # InMemoryStore has a data attribute
        if hasattr(store, 'data'):
            print(f"Store data keys: {list(store.data.keys())}")
            print(f"Store contents: {store.data}")
    except Exception as e:
        print(f"Could not inspect store: {e}")

    print("\n✓ Long-term memory test complete")


if __name__ == "__main__":
    test_longterm_memory()
