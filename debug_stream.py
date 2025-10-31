"""Debug script to see all stream chunks from DeepAgents."""

import json
from src.deep_agent import create_finance_deep_agent
from langchain_core.messages import HumanMessage
from deepagents.backends.utils import create_file_data


def debug_agent_stream():
    """Debug the agent stream to see all chunks."""

    # Create agent
    agent = create_finance_deep_agent()

    # Simple test query
    state = {
        "messages": [HumanMessage(content="What's the current price of AAPL?")],
        "files": {}
    }

    print("\n" + "="*80)
    print("DEBUGGING AGENT STREAM - ALL CHUNKS")
    print("="*80 + "\n")

    step_count = 0

    for chunk in agent.stream(state, stream_mode="updates"):
        step_count += 1

        print(f"\n{'─'*80}")
        print(f"CHUNK #{step_count}")
        print(f"{'─'*80}")

        for node_name, state_update in chunk.items():
            print(f"\nNode: {node_name}")
            print(f"Type: {type(state_update)}")

            if state_update is None:
                print("  [None]")
                continue

            # Show what keys are in the update
            if isinstance(state_update, dict):
                print(f"Keys: {list(state_update.keys())}")

                # Show messages
                if "messages" in state_update:
                    messages = state_update["messages"]
                    # Handle Overwrite objects
                    if hasattr(messages, '__iter__') and not isinstance(messages, str):
                        try:
                            messages_list = list(messages)
                            print(f"\nMessages ({len(messages_list)}):")
                            for i, msg in enumerate(messages_list):
                                print(f"  {i+1}. Type: {msg.type}")

                                if msg.type == "ai":
                                    if hasattr(msg, "tool_calls") and msg.tool_calls:
                                        print(f"     Tool calls: {len(msg.tool_calls)}")
                                        for tc in msg.tool_calls:
                                            print(f"       - {tc.get('name', 'unknown')}")
                                            print(f"         Args: {list(tc.get('args', {}).keys())}")
                                    if hasattr(msg, "content") and msg.content:
                                        content_preview = str(msg.content)[:100]
                                        print(f"     Content: {content_preview}...")

                                elif msg.type == "tool":
                                    tool_name = getattr(msg, 'name', 'unknown')
                                    print(f"     Tool name: {tool_name}")
                                    content_preview = str(msg.content)[:200]
                                    print(f"     Content: {content_preview}...")

                                elif msg.type == "human":
                                    content_preview = str(msg.content)[:100]
                                    print(f"     Content: {content_preview}...")
                        except Exception as e:
                            print(f"\nMessages: Error iterating - {e}")
                            print(f"Messages type: {type(messages)}")

                # Show files
                if "files" in state_update and state_update["files"]:
                    print(f"\nFiles: {list(state_update['files'].keys())}")

                # Show todos
                if "todos" in state_update and state_update["todos"]:
                    print(f"\nTodos: {len(state_update['todos'])}")
                    for todo in state_update["todos"][:3]:
                        print(f"  - [{todo.get('status')}] {todo.get('content', '')[:60]}")

            else:
                print(f"State update: {state_update}")

    print("\n" + "="*80)
    print(f"TOTAL CHUNKS: {step_count}")
    print("="*80 + "\n")


if __name__ == "__main__":
    debug_agent_stream()
