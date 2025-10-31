"""Test stream_mode='debug' to see subagent tool calls."""

from src.deep_agent import create_finance_deep_agent
from langchain_core.messages import HumanMessage


def test_debug_mode():
    """Test if debug mode shows subagent tool calls."""

    agent = create_finance_deep_agent()

    state = {
        "messages": [HumanMessage(content="Get the current price of AAPL")],
        "files": {}
    }

    print("\n" + "="*80)
    print("TESTING stream_mode='debug'")
    print("="*80 + "\n")

    step_count = 0

    for chunk in agent.stream(state, stream_mode="debug"):
        step_count += 1

        print(f"\n{'─'*80}")
        print(f"DEBUG CHUNK #{step_count}")
        print(f"{'─'*80}")

        # Debug mode returns different structure
        print(f"Chunk type: {type(chunk)}")
        print(f"Chunk keys: {chunk.keys() if isinstance(chunk, dict) else 'N/A'}")

        if isinstance(chunk, dict):
            for key, value in chunk.items():
                print(f"\n{key}:")
                print(f"  Type: {type(value)}")

                # Show first 200 chars of value
                value_str = str(value)[:200]
                print(f"  Value: {value_str}...")

    print(f"\n{'='*80}")
    print(f"TOTAL DEBUG CHUNKS: {step_count}")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    test_debug_mode()
