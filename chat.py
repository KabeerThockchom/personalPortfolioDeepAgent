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
    print(f"  • Live tool execution display with inputs and outputs")
    print(f"  • Subagent tool calls shown with indentation and context")
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

def get_friendly_node_name(node_name):
    """Convert technical node names to user-friendly names."""
    # Map technical names to user-friendly names
    name_map = {
        "PatchToolCallsMiddleware.before_agent": "Pre-processing",
        "SummarizationMiddleware.before_model": "Context Management",
        "model": "🤖 Main Agent",
        "tools": "Tool Execution",
    }

    return name_map.get(node_name, node_name)

def print_step_header(step_num, node_name, state_update=None):
    """Print step header with friendly names."""
    friendly_name = get_friendly_node_name(node_name)
    print(f"\n{Colors.BOLD}━━━ Step {step_num}: {friendly_name} ━━━{Colors.ENDC}")

    # For middleware steps, show what they're doing
    if node_name == "SummarizationMiddleware.before_model":
        # Note: Middleware steps in stream_mode="updates" don't provide state deltas,
        # only full state modifications. We can't see the actual messages here.
        print(f"{Colors.OKCYAN}   Optimizing conversation context for the model{Colors.ENDC}")
        print(f"{Colors.OKCYAN}   • Checking message history size{Colors.ENDC}")
        print(f"{Colors.OKCYAN}   • Preparing context window{Colors.ENDC}")

    elif node_name == "PatchToolCallsMiddleware.before_agent":
        # Show what pre-processing is doing
        print(f"{Colors.OKCYAN}   Preparing request for agent execution{Colors.ENDC}")

def format_value(value, max_length=500):
    """Format a value for display with smart truncation."""
    if isinstance(value, dict):
        # Pretty print dicts as JSON
        try:
            formatted = json.dumps(value, indent=2)
            if len(formatted) > max_length:
                # Show first part with ellipsis
                return formatted[:max_length] + "\n    ... (truncated)"
            return formatted
        except:
            value_str = str(value)
    elif isinstance(value, list):
        # Show list length and first few items
        if len(value) > 5:
            preview = value[:5]
            return f"{preview}... ({len(value)} items total)"
        value_str = str(value)
    else:
        value_str = str(value)

    if len(value_str) > max_length:
        return value_str[:max_length] + "... (truncated)"
    return value_str

def print_tool_call(tool_name, args, indent=""):
    """Print tool call details with full arguments."""
    if tool_name == "task":
        # Subagent spawn
        subagent_type = args.get("subagent_type", "unknown")
        description = args.get("description", "")
        print(f"{indent}{Colors.WARNING}{Colors.BOLD}🚀 SPAWNING SUBAGENT: {subagent_type}{Colors.ENDC}")
        if description:
            # Show full description with wrapping
            lines = [description[i:i+80] for i in range(0, len(description), 80)]
            for line in lines:
                print(f"{indent}{Colors.WARNING}   Description: {line}{Colors.ENDC}")
    elif tool_name == "write_file":
        path = args.get("file_path", "?")
        content = args.get("content", "")
        content_preview = content[:150] if content else "(empty)"
        print(f"{indent}{Colors.OKBLUE}📝 Writing file: {path}{Colors.ENDC}")
        print(f"{indent}{Colors.OKBLUE}   Content preview: {content_preview}...{Colors.ENDC}")
    elif tool_name == "edit_file":
        path = args.get("file_path", "?")
        old_string = args.get("old_string", "")[:100]
        new_string = args.get("new_string", "")[:100]
        print(f"{indent}{Colors.OKBLUE}✏️  Editing file: {path}{Colors.ENDC}")
        print(f"{indent}{Colors.OKBLUE}   Old: {old_string}...{Colors.ENDC}")
        print(f"{indent}{Colors.OKBLUE}   New: {new_string}...{Colors.ENDC}")
    elif tool_name == "read_file":
        path = args.get("file_path", "?")
        print(f"{indent}{Colors.OKCYAN}📖 Reading file: {path}{Colors.ENDC}")
    elif tool_name == "ls":
        path = args.get("path", "/")
        print(f"{indent}{Colors.OKCYAN}📂 Listing directory: {path}{Colors.ENDC}")
    elif tool_name == "write_todos":
        todos = args.get("todos", [])
        print(f"{indent}{Colors.WARNING}📋 Planning {len(todos)} tasks{Colors.ENDC}")
        for i, todo in enumerate(todos[:3], 1):  # Show first 3
            content = todo.get("content", "")
            print(f"{indent}{Colors.WARNING}   {i}. {content}{Colors.ENDC}")
        if len(todos) > 3:
            print(f"{indent}{Colors.WARNING}   ... and {len(todos)-3} more{Colors.ENDC}")
    elif tool_name.startswith("get_") and ("stock" in tool_name or "quote" in tool_name or "search" in tool_name):
        # Yahoo Finance tools
        symbol = args.get("symbol", args.get("symbols", args.get("query", "")))
        print(f"{indent}{Colors.OKGREEN}📊 Yahoo Finance API: {tool_name}{Colors.ENDC}")
        if symbol:
            print(f"{indent}{Colors.OKGREEN}   Symbol(s): {symbol}{Colors.ENDC}")
        # Show other relevant args
        for key, value in args.items():
            if key not in ["symbol", "symbols", "query"] and value:
                print(f"{indent}{Colors.OKGREEN}   {key}: {value}{Colors.ENDC}")
    elif tool_name.startswith("web_search"):
        # Web search tools
        query = args.get("query", "")
        print(f"{indent}{Colors.OKGREEN}🔍 Web Search: {tool_name}{Colors.ENDC}")
        print(f"{indent}{Colors.OKGREEN}   Query: {query}{Colors.ENDC}")
        if "max_results" in args:
            print(f"{indent}{Colors.OKGREEN}   Max results: {args['max_results']}{Colors.ENDC}")
    else:
        # Regular tool - show all args
        print(f"{indent}{Colors.OKGREEN}🔧 Tool: {tool_name}{Colors.ENDC}")
        if args:
            # Show formatted arguments
            for key, value in args.items():
                formatted_value = format_value(value, max_length=300)
                # Handle multiline values
                if '\n' in formatted_value:
                    print(f"{indent}{Colors.OKGREEN}   {key}:{Colors.ENDC}")
                    for line in formatted_value.split('\n'):
                        print(f"{indent}{Colors.OKGREEN}     {line}{Colors.ENDC}")
                else:
                    print(f"{indent}{Colors.OKGREEN}   {key}: {formatted_value}{Colors.ENDC}")

def print_tool_result(result, indent=""):
    """Print tool result with smart formatting."""
    # Try to parse as JSON first
    if isinstance(result, str):
        try:
            # Try to parse as JSON
            parsed = json.loads(result)
            result = parsed
        except:
            pass

    if isinstance(result, dict):
        # Show key metrics from dict results
        print(f"{indent}{Colors.OKBLUE}   ✓ Result:{Colors.ENDC}")

        # Special handling for common result structures
        if "success" in result:
            success = result.get("success", False)
            status = "✓ SUCCESS" if success else "✗ FAILED"
            color = Colors.OKGREEN if success else Colors.FAIL
            print(f"{indent}{color}     Status: {status}{Colors.ENDC}")

        if "symbol" in result:
            print(f"{indent}{Colors.OKBLUE}     Symbol: {result['symbol']}{Colors.ENDC}")

        if "error" in result and result["error"]:
            print(f"{indent}{Colors.FAIL}     Error: {result['error']}{Colors.ENDC}")

        # Show summary if available
        if "summary" in result:
            summary = result["summary"]
            # Print summary with line wrapping
            lines = summary.split('\n') if isinstance(summary, str) else [str(summary)]
            for line in lines[:10]:  # First 10 lines
                print(f"{indent}{Colors.OKBLUE}     {line}{Colors.ENDC}")
            if len(lines) > 10:
                print(f"{indent}{Colors.OKBLUE}     ... ({len(lines)-10} more lines){Colors.ENDC}")

        # Show key metrics
        if "key_metrics" in result and result["key_metrics"]:
            print(f"{indent}{Colors.OKBLUE}     Key Metrics:{Colors.ENDC}")
            metrics = result["key_metrics"]
            for key, value in list(metrics.items())[:5]:  # First 5 metrics
                print(f"{indent}{Colors.OKBLUE}       • {key}: {value}{Colors.ENDC}")

        # Show file path if saved
        if "file_path" in result:
            print(f"{indent}{Colors.OKBLUE}     Saved to: {result['file_path']}{Colors.ENDC}")

        # Show data preview if it's a large response
        if "data" in result and not ("summary" in result or "key_metrics" in result):
            data_str = str(result["data"])[:200]
            print(f"{indent}{Colors.OKBLUE}     Data preview: {data_str}...{Colors.ENDC}")

    elif isinstance(result, list):
        # Show list length and preview
        print(f"{indent}{Colors.OKBLUE}   ✓ Result: List with {len(result)} items{Colors.ENDC}")
        for i, item in enumerate(result[:3], 1):  # Show first 3
            item_str = str(item)[:100]
            print(f"{indent}{Colors.OKBLUE}     {i}. {item_str}{Colors.ENDC}")
        if len(result) > 3:
            print(f"{indent}{Colors.OKBLUE}     ... and {len(result)-3} more items{Colors.ENDC}")

    else:
        # Plain string or other type
        result_str = str(result)
        if len(result_str) > 500:
            # Show first 500 chars
            lines = result_str[:500].split('\n')
            print(f"{indent}{Colors.OKBLUE}   ✓ Result:{Colors.ENDC}")
            for line in lines[:10]:
                print(f"{indent}{Colors.OKBLUE}     {line}{Colors.ENDC}")
            print(f"{indent}{Colors.OKBLUE}     ... (truncated, {len(result_str)} chars total){Colors.ENDC}")
        else:
            # Show full result
            lines = result_str.split('\n')
            if len(lines) > 1:
                print(f"{indent}{Colors.OKBLUE}   ✓ Result:{Colors.ENDC}")
                for line in lines:
                    print(f"{indent}{Colors.OKBLUE}     {line}{Colors.ENDC}")
            else:
                print(f"{indent}{Colors.OKBLUE}   ✓ Result: {result_str}{Colors.ENDC}")

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
                    # Detect if this is a subagent node
                    is_subagent = node_name.startswith("SubAgent[") or "SubAgent" in node_name
                    subagent_name = ""
                    if is_subagent:
                        # Extract subagent name from node like "SubAgent[market-data-fetcher]"
                        if "[" in node_name and "]" in node_name:
                            subagent_name = node_name.split("[")[1].split("]")[0]

                    # Determine indentation based on context
                    indent = "  " if is_subagent else ""

                    # Print step header
                    if is_subagent:
                        print(f"\n{Colors.BOLD}{Colors.OKCYAN}  ╭─── Subagent: {subagent_name} ───╮{Colors.ENDC}")
                    else:
                        print_step_header(step_count, node_name, state_update)

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
                                    print_tool_call(tool_name, tool_args, indent=indent)

                            # Show tool results
                            elif msg.type == "tool":
                                # Get tool name from the tool call name attribute
                                tool_name = getattr(msg, 'name', 'unknown')
                                print(f"{indent}{Colors.OKGREEN}  [{tool_name}] returned:{Colors.ENDC}")
                                print_tool_result(msg.content, indent=indent)

                    # Show file updates
                    if "files" in state_update and state_update["files"]:
                        new_files = state_update["files"]
                        files.update(new_files)
                        print(f"{indent}{Colors.OKBLUE}📁 Files updated: {len(new_files)} file(s){Colors.ENDC}")
                        for path in list(new_files.keys())[:3]:  # Show first 3
                            print(f"{indent}{Colors.OKBLUE}   - {path}{Colors.ENDC}")

                    # Show todos
                    if "todos" in state_update and state_update["todos"]:
                        todos = state_update["todos"]
                        print(f"{indent}{Colors.WARNING}📋 TODO LIST:{Colors.ENDC}")
                        for todo in todos[:5]:  # Show first 5
                            status = todo.get("status", "unknown")
                            content = todo.get("content", "")
                            emoji = "✓" if status == "completed" else "⏳" if status == "in_progress" else "○"
                            print(f"{indent}{Colors.WARNING}   {emoji} [{status}] {content}{Colors.ENDC}")

                    # Close subagent box
                    if is_subagent:
                        print(f"{Colors.OKCYAN}  ╰{'─' * 50}╯{Colors.ENDC}")

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
