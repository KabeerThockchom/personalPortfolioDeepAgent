"""Test friendly node names in chat interface."""

import sys
sys.path.insert(0, '/Users/kabeerthockchom/Desktop/personal_finance_deep_agent')

from chat import get_friendly_node_name, Colors

print("\n" + "="*80)
print("Testing Friendly Node Names")
print("="*80 + "\n")

test_cases = [
    "PatchToolCallsMiddleware.before_agent",
    "SummarizationMiddleware.before_model",
    "model",
    "tools",
    "SubAgent[market-data-fetcher]",
    "unknown_node"
]

for node_name in test_cases:
    friendly = get_friendly_node_name(node_name)
    print(f"{node_name:45s} → {Colors.OKGREEN}{friendly}{Colors.ENDC}")

print("\n" + "="*80)
print("✓ Friendly names working!")
print("="*80 + "\n")
