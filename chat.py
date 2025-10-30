"""Interactive chat interface for the Personal Finance Deep Agent."""

import json
import sys
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage
from deepagents.backends.utils import create_file_data

from src.deep_agent import create_finance_deep_agent

# Colors for terminal output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

load_dotenv()

# Configuration
MAX_CONVERSATION_TURNS = 5  # Keep last N turns (each turn = 1 user + 1 AI message)
CONTEXT_WARNING_THRESHOLD = 150000  # Warn if context exceeds this many tokens (rough estimate)

def estimate_token_count(messages):
    """
    Rough estimate of token count for messages.
    Actual tokenization varies, but this gives us a ballpark figure.
    Uses ~4 characters per token as a rough heuristic.
    """
    total_chars = 0
    for msg in messages:
        content = msg.content if hasattr(msg, 'content') else str(msg)
        total_chars += len(content)
    return total_chars // 4

def prune_conversation_history(messages, max_turns=MAX_CONVERSATION_TURNS):
    """
    Prune conversation history to keep only recent turns.

    Args:
        messages: List of conversation messages
        max_turns: Maximum number of conversation turns to keep

    Returns:
        Pruned list of messages
    """
    if not messages:
        return messages

    # Group messages into turns (pairs of user + AI messages)
    turns = []
    current_turn = []

    for msg in messages:
        if msg.type in ["human", "ai"]:
            current_turn.append(msg)
            # Complete turn when we see an AI message
            if msg.type == "ai" and current_turn:
                turns.append(current_turn)
                current_turn = []
        else:
            # Tool messages belong to the current turn
            if current_turn:
                current_turn.append(msg)

    # Add incomplete turn if exists
    if current_turn:
        turns.append(current_turn)

    # Keep only last N turns
    if len(turns) <= max_turns:
        return messages

    # Flatten recent turns back into messages
    recent_turns = turns[-max_turns:]
    pruned_messages = []
    for turn in recent_turns:
        pruned_messages.extend(turn)

    return pruned_messages

def create_context_summary(pruned_messages, original_count):
    """
    Create a summary message when context has been pruned.

    Args:
        pruned_messages: The pruned message list
        original_count: Number of messages before pruning

    Returns:
        Summary message to add at the start
    """
    pruned_count = original_count - len(pruned_messages)
    if pruned_count > 0:
        summary_text = f"""[Context Management: Removed {pruned_count} older messages to prevent context bloat.
Keeping last {MAX_CONVERSATION_TURNS} conversation turns.]"""
        return SystemMessage(content=summary_text)
    return None

def print_banner():
    """Print welcome banner."""
    print(f"\n{Colors.BOLD}{Colors.HEADER}{'='*80}")
    print("🤖 PERSONAL FINANCE DEEP AGENT - Interactive Chat")
    print(f"{'='*80}{Colors.ENDC}\n")
    print(f"{Colors.OKCYAN}Welcome! I'm your personal financial assistant with REAL-TIME market data!")
    print("I can help you with:")
    print("  • Portfolio analysis with real Yahoo Finance prices")
    print("  • Company research (analyst ratings, news, ESG scores)")
    print("  • Retirement planning and projections")
    print("  • Cash flow and budgeting analysis")
    print("  • Debt management strategies")
    print("  • Tax optimization opportunities")
    print("  • Risk assessment and insurance gaps")
    print(f"\n{Colors.WARNING}Commands:{Colors.ENDC}")
    print("  • Type 'quit', 'exit', or 'q' to end the session")
    print("  • Type 'clear' to clear conversation history")
    print("  • Type 'help' for assistance")
    print(f"\n{Colors.OKGREEN}✨ Smart Features:{Colors.ENDC}")
    print(f"  • Auto-pruning: Keeps last {MAX_CONVERSATION_TURNS} turns to prevent context bloat")
    print(f"  • Large API responses auto-saved to /financial_data/")
    print(f"\n{Colors.OKGREEN}Tip: I work best when you load portfolio data first!{Colors.ENDC}\n")

def print_thinking():
    """Print thinking indicator."""
    print(f"{Colors.OKCYAN}💭 Thinking...{Colors.ENDC}")

def print_agent_response(text):
    """Print agent response."""
    print(f"\n{Colors.BOLD}{Colors.OKBLUE}🤖 Assistant:{Colors.ENDC}\n")
    print(text)
    print()

def print_error(text):
    """Print error message."""
    print(f"\n{Colors.FAIL}❌ Error: {text}{Colors.ENDC}\n")

def print_step_header(step_num, node_name):
    """Print step header."""
    print(f"\n{Colors.BOLD}━━━ Step {step_num}: {node_name} ━━━{Colors.ENDC}")

def print_tool_call(tool_name, args):
    """Print tool call details."""
    if tool_name == "task":
        # Subagent spawn
        subagent_type = args.get("subagent_type", "unknown")
        description = args.get("description", "")[:100]
        print(f"{Colors.WARNING}{Colors.BOLD}🚀 SPAWNING SUBAGENT: {subagent_type}{Colors.ENDC}")
        print(f"{Colors.WARNING}   Description: {description}...{Colors.ENDC}")
    elif tool_name == "write_file":
        path = args.get("file_path", "?")
        print(f"{Colors.OKBLUE}📝 Writing file: {path}{Colors.ENDC}")
    elif tool_name == "edit_file":
        path = args.get("file_path", "?")
        print(f"{Colors.OKBLUE}✏️  Editing file: {path}{Colors.ENDC}")
    elif tool_name == "read_file":
        path = args.get("file_path", "?")
        print(f"{Colors.OKCYAN}📖 Reading file: {path}{Colors.ENDC}")
    elif tool_name == "ls":
        path = args.get("path", "/")
        print(f"{Colors.OKCYAN}📂 Listing directory: {path}{Colors.ENDC}")
    elif tool_name == "write_todos":
        todos = args.get("todos", [])
        print(f"{Colors.WARNING}📋 Planning {len(todos)} tasks{Colors.ENDC}")
    elif tool_name.startswith("get_") and ("stock" in tool_name or "quote" in tool_name or "search" in tool_name):
        # Yahoo Finance tools
        symbol = args.get("symbol", args.get("query", ""))
        if symbol:
            print(f"{Colors.OKGREEN}📊 Yahoo Finance API: {tool_name} ({symbol}){Colors.ENDC}")
        else:
            print(f"{Colors.OKGREEN}📊 Yahoo Finance API: {tool_name}{Colors.ENDC}")
    else:
        # Regular tool
        print(f"{Colors.OKGREEN}🔧 Tool: {tool_name}{Colors.ENDC}")
        # Show args preview for calculation tools
        if args:
            args_preview = str(args)[:100]
            print(f"{Colors.OKGREEN}   Args: {args_preview}...{Colors.ENDC}")

def print_tool_result(result):
    """Print tool result preview."""
    result_str = str(result)[:200]
    print(f"{Colors.OKBLUE}   ✓ Result: {result_str}...{Colors.ENDC}")

def load_portfolio():
    """Load the example portfolio from file."""
    try:
        with open("portfolio.json", "r") as f:
            portfolio = json.load(f)

        # NOTE: With Yahoo Finance API integration, the agent will use the
        # market-data-fetcher subagent to fetch real-time prices automatically.
        # No need to provide mock prices anymore!
        #
        # For backwards compatibility or testing without API, you can uncomment:
        # current_prices = {}
        # for account_name, account_data in portfolio.get("investment_accounts", {}).items():
        #     for holding in account_data.get("holdings", []):
        #         ticker = holding["ticker"]
        #         cost_basis = holding.get("cost_basis", 100)
        #         current_prices[ticker] = cost_basis * 1.10  # Mock 10% gain
        # prices_json = json.dumps(current_prices, indent=2)

        # Create files
        portfolio_json = json.dumps(portfolio, indent=2)

        files = {
            "/financial_data/kabeer_thockchom_portfolio.json": create_file_data(portfolio_json),
            # Agent will create current_prices.json using real Yahoo Finance data
            # Uncomment line below to use mock prices instead:
            # "/financial_data/current_prices.json": create_file_data(prices_json),
        }

        print(f"{Colors.OKGREEN}✓ Loaded portfolio for: {portfolio['client']['name']}{Colors.ENDC}")
        print(f"{Colors.OKCYAN}📊 Agent will fetch REAL prices from Yahoo Finance API{Colors.ENDC}")
        return files
    except FileNotFoundError:
        print(f"{Colors.WARNING}⚠️  Example portfolio file not found. Continuing without portfolio data.{Colors.ENDC}")
        return {}

def show_help():
    """Show help information."""
    print(f"\n{Colors.BOLD}📚 Help{Colors.ENDC}\n")
    print("Ask me questions about your finances. Examples:")
    print(f"\n{Colors.BOLD}Portfolio Analysis (with real Yahoo Finance data!):{Colors.ENDC}")
    print(f"  {Colors.OKCYAN}• Calculate my portfolio value with current prices{Colors.ENDC}")
    print(f"  {Colors.OKCYAN}• Analyze my portfolio performance{Colors.ENDC}")
    print(f"  {Colors.OKCYAN}• How am I doing on retirement?{Colors.ENDC}")
    print(f"\n{Colors.BOLD}Stock Research:{Colors.ENDC}")
    print(f"  {Colors.OKCYAN}• Research Apple stock (AAPL){Colors.ENDC}")
    print(f"  {Colors.OKCYAN}• What do analysts say about Tesla?{Colors.ENDC}")
    print(f"  {Colors.OKCYAN}• Get ESG scores for Microsoft{Colors.ENDC}")
    print(f"\n{Colors.BOLD}Other Analysis:{Colors.ENDC}")
    print(f"  {Colors.OKCYAN}• Analyze my monthly cash flow{Colors.ENDC}")
    print(f"  {Colors.OKCYAN}• What are my tax optimization opportunities?{Colors.ENDC}")
    print(f"  {Colors.OKCYAN}• Run a stress test on my portfolio{Colors.ENDC}")
    print(f"\n{Colors.WARNING}Commands:{Colors.ENDC}")
    print("  • quit, exit, q - End session")
    print("  • clear - Clear conversation history")
    print("  • help - Show this help message\n")

def run_chat():
    """Run the interactive chat loop."""

    print_banner()

    # Load example portfolio
    print("📂 Loading example portfolio...")
    initial_files = load_portfolio()

    # Create agent
    print("\n🏗️  Creating deep agent...")
    agent = create_finance_deep_agent()
    print(f"{Colors.OKGREEN}✓ Agent ready with 8 specialized subagents{Colors.ENDC}")
    print(f"{Colors.OKGREEN}  - market-data-fetcher (NEW: Yahoo Finance API){Colors.ENDC}")
    print(f"{Colors.OKGREEN}  - research-analyst (NEW: Company research){Colors.ENDC}")
    print(f"{Colors.OKGREEN}  - portfolio, cashflow, goals, debt, tax, risk analyzers{Colors.ENDC}\n")

    # Initialize conversation state
    conversation_messages = []
    files = initial_files.copy()

    # Main chat loop
    while True:
        # Get user input
        try:
            user_input = input(f"{Colors.BOLD}You: {Colors.ENDC}").strip()
        except (KeyboardInterrupt, EOFError):
            print(f"\n\n{Colors.WARNING}👋 Goodbye!{Colors.ENDC}\n")
            break

        # Handle empty input
        if not user_input:
            continue

        # Handle commands
        if user_input.lower() in ['quit', 'exit', 'q']:
            print(f"\n{Colors.WARNING}👋 Goodbye!{Colors.ENDC}\n")
            break

        if user_input.lower() == 'clear':
            conversation_messages = []
            files = initial_files.copy()
            print(f"\n{Colors.OKGREEN}✓ Conversation history cleared{Colors.ENDC}\n")
            continue

        if user_input.lower() == 'help':
            show_help()
            continue

        # Add user message to conversation
        conversation_messages.append(HumanMessage(content=user_input))

        # Prune conversation history to prevent context bloat
        original_count = len(conversation_messages)
        pruned_messages = prune_conversation_history(conversation_messages)

        # Check if pruning occurred and notify user
        if len(pruned_messages) < original_count:
            pruned_count = original_count - len(pruned_messages)
            print(f"{Colors.WARNING}📊 Context Management: Pruned {pruned_count} older messages (keeping last {MAX_CONVERSATION_TURNS} turns){Colors.ENDC}")

        # Estimate token count and warn if high
        estimated_tokens = estimate_token_count(pruned_messages)
        if estimated_tokens > CONTEXT_WARNING_THRESHOLD:
            print(f"{Colors.WARNING}⚠️  High context size: ~{estimated_tokens:,} tokens (may affect performance){Colors.ENDC}")

        # Add context summary if messages were pruned
        context_summary = create_context_summary(pruned_messages, original_count)
        messages_to_send = pruned_messages[:]
        if context_summary:
            messages_to_send.insert(0, context_summary)

        # Prepare state
        state = {
            "messages": messages_to_send,  # Pass pruned conversation history
            "files": files.copy()
        }

        # Execute agent with live progress
        print_thinking()
        step_count = 0
        new_messages = []

        try:
            print(f"{Colors.OKCYAN}{'─' * 80}{Colors.ENDC}")

            for chunk in agent.stream(state, stream_mode="updates"):
                step_count += 1

                for node_name, state_update in chunk.items():
                    # Print step header
                    print_step_header(step_count, node_name)

                    if state_update is None:
                        continue

                    # Show messages and tool calls
                    if "messages" in state_update:
                        for msg in state_update["messages"]:
                            new_messages.append(msg)

                            # Show tool calls from AI
                            if msg.type == "ai" and hasattr(msg, "tool_calls") and msg.tool_calls:
                                for tool_call in msg.tool_calls:
                                    tool_name = tool_call.get("name", "unknown")
                                    tool_args = tool_call.get("args", {})
                                    print_tool_call(tool_name, tool_args)

                            # Show tool results
                            elif msg.type == "tool":
                                print_tool_result(msg.content)

                    # Show file updates
                    if "files" in state_update and state_update["files"]:
                        new_files = state_update["files"]
                        files.update(new_files)
                        print(f"{Colors.OKBLUE}📁 Files updated: {len(new_files)} file(s){Colors.ENDC}")
                        for path in list(new_files.keys())[:3]:  # Show first 3
                            print(f"{Colors.OKBLUE}   - {path}{Colors.ENDC}")

                    # Show todos
                    if "todos" in state_update and state_update["todos"]:
                        todos = state_update["todos"]
                        print(f"{Colors.WARNING}📋 TODO LIST:{Colors.ENDC}")
                        for todo in todos[:5]:  # Show first 5
                            status = todo.get("status", "unknown")
                            content = todo.get("content", "")
                            emoji = "✓" if status == "completed" else "⏳" if status == "in_progress" else "○"
                            print(f"{Colors.WARNING}   {emoji} [{status}] {content}{Colors.ENDC}")

            # Add only new AI messages to conversation history
            for msg in new_messages:
                if msg.type == "ai" and msg not in conversation_messages:
                    conversation_messages.append(msg)

            # Separator before final response
            print(f"\n{Colors.OKCYAN}{'─' * 80}{Colors.ENDC}")
            print(f"{Colors.BOLD}{Colors.OKGREEN}✓ Execution complete{Colors.ENDC}\n")

            # Get final response
            ai_messages = [m for m in conversation_messages if m.type == "ai"]
            if ai_messages:
                final_response = ai_messages[-1].content
                print_agent_response(final_response)
            else:
                print_error("No response generated")

        except KeyboardInterrupt:
            print(f"\n\n{Colors.WARNING}⚠️  Interrupted. Type 'quit' to exit or continue chatting.{Colors.ENDC}\n")
            # Remove the last user message since we interrupted
            conversation_messages.pop()

        except Exception as e:
            print_error(f"{e}")
            print(f"{Colors.WARNING}💡 Try rephrasing your question or type 'help' for guidance{Colors.ENDC}")
            # Remove the last user message on error
            conversation_messages.pop()

if __name__ == "__main__":
    try:
        run_chat()
    except Exception as e:
        print(f"\n{Colors.FAIL}Fatal error: {e}{Colors.ENDC}\n")
        sys.exit(1)
