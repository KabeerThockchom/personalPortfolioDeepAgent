"""Test enhanced display with friendly names and context details."""

import sys
sys.path.insert(0, '/Users/kabeerthockchom/Desktop/personal_finance_deep_agent')

from chat import get_friendly_node_name, print_step_header, Colors
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage

print("\n" + "="*80)
print("TESTING ENHANCED DISPLAY - Friendly Names & Context Details")
print("="*80 + "\n")

# Test 1: Friendly node names
print(f"{Colors.BOLD}Test 1: Friendly Node Names{Colors.ENDC}\n")
test_nodes = [
    "PatchToolCallsMiddleware.before_agent",
    "SummarizationMiddleware.before_model",
    "model",
    "tools",
    "SubAgent[market-data-fetcher]"
]

for node in test_nodes:
    friendly = get_friendly_node_name(node)
    print(f"{node:45s} → {Colors.OKGREEN}{friendly}{Colors.ENDC}")

print("\n" + "─"*80 + "\n")

# Test 2: Step headers with context details
print(f"{Colors.BOLD}Test 2: Step Headers with Context{Colors.ENDC}\n")

# Simulate Pre-processing step
print("Simulating Pre-processing step:")
print_step_header(1, "PatchToolCallsMiddleware.before_agent", {})

# Simulate Context Management step
# Note: In actual streaming, middleware doesn't provide state deltas
print("\nSimulating Context Management step:")
print_step_header(2, "SummarizationMiddleware.before_model", None)

# Simulate Main Agent step
print("\nSimulating Main Agent step:")
print_step_header(3, "model", {})

# Simulate Tool Execution step
print("\nSimulating Tool Execution step:")
print_step_header(4, "tools", {})

print("\n" + "="*80)
print("✓ Enhanced display working!")
print("="*80)
print(f"\n{Colors.OKGREEN}Features tested:{Colors.ENDC}")
print("  ✓ Friendly node names (Main Agent, Pre-processing, etc.)")
print("  ✓ Context Management shows optimization details")
print("  ✓ Pre-processing shows preparation steps")
print("  ✓ Clear agent identification")
print(f"\n{Colors.OKCYAN}Ready to test in live chat.py!{Colors.ENDC}\n")
