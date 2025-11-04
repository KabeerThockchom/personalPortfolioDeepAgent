"""Interactive chat interface for the Personal Finance Deep Agent."""

import asyncio
import json
import sys
import textwrap
import uuid
from pathlib import Path
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage
from deepagents.backends.utils import create_file_data
from langgraph.types import Command, Overwrite
from rich.markdown import Markdown

from src.deep_agent import create_finance_deep_agent
from src.config import console, COLORS, FINANCE_AGENT_ASCII, DOLLAR_ASCII, MONEYBAG_ASCII, STOCK_CHART_ASCII, MAX_CONVERSATION_TURNS, CONTEXT_WARNING_THRESHOLD, SessionState
from src.input_handler import create_prompt_session, parse_file_mentions
from src.token_tracker import TokenTracker
from src.token_utils import calculate_baseline_tokens
from src.commands import handle_command, execute_bash_command
from src.tool_display import format_tool_display
from src.file_ops_tracker import FileOpTracker
from src.ui import render_approval_panel, render_file_operation, render_banner

load_dotenv()

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
    """Print welcome banner with Rich."""
    render_banner(FINANCE_AGENT_ASCII)

    # Display financial ASCII art in a row (without boxes)
    from rich.columns import Columns

    console.print(Columns([DOLLAR_ASCII, MONEYBAG_ASCII, STOCK_CHART_ASCII], equal=True, expand=True))
    console.print()

    console.print(f"[{COLORS['agent']}]Welcome! I'm your personal financial assistant with REAL-TIME market data![/{COLORS['agent']}]")
    console.print("\n[bold]I can help you with:[/bold]")
    console.print("  • Portfolio analysis with real Yahoo Finance prices", style=COLORS["dim"])
    console.print("  • Company research (analyst ratings, news, ESG scores)", style=COLORS["dim"])
    console.print("  • Retirement planning and projections", style=COLORS["dim"])
    console.print("  • Cash flow and budgeting analysis", style=COLORS["dim"])
    console.print("  • Debt management strategies", style=COLORS["dim"])
    console.print("  • Tax optimization opportunities", style=COLORS["dim"])
    console.print("  • Risk assessment and insurance gaps", style=COLORS["dim"])
    console.print(f"\n[bold {COLORS['warning']}]Commands:[/bold {COLORS['warning']}]")
    console.print("  • /help - Show all commands and features", style=COLORS["dim"])
    console.print("  • /clear - Clear conversation history", style=COLORS["dim"])
    console.print("  • /quit - Exit the CLI", style=COLORS["dim"])
    console.print(f"\n[bold {COLORS['success']}]✨ Smart Features:[/bold {COLORS['success']}]")
    console.print(f"  • Human-in-the-loop: I'll ask permission before portfolio changes", style=COLORS["dim"])
    console.print(f"  • Auto-pruning: Keeps last {MAX_CONVERSATION_TURNS} turns to prevent context bloat", style=COLORS["dim"])
    console.print(f"  • Large API responses auto-saved to /financial_data/", style=COLORS["dim"])
    console.print(f"  • @file mentions: Type @ to autocomplete and inject file content", style=COLORS["dim"])
    console.print(f"  • Alt+Enter for multiline, Ctrl+E for external editor", style=COLORS["dim"])
    console.print(f"\n[{COLORS['success']}]Tip: I work best when you load portfolio data first![/{COLORS['success']}]\n")

def print_thinking():
    """Print thinking indicator."""
    console.print(f"[{COLORS['thinking']}]💭 Thinking...[/{COLORS['thinking']}]")

def print_agent_response(text):
    """Print agent response with markdown formatting."""
    console.print(f"\n[bold {COLORS['agent']}]🤖 Assistant:[/bold {COLORS['agent']}]\n")
    # Render as markdown for proper formatting (bold, tables, lists, headers, etc.)
    console.print(Markdown(text))
    console.print()

def print_error(text):
    """Print error message."""
    console.print(f"\n[{COLORS['error']}]❌ Error: {text}[/{COLORS['error']}]\n")

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
    console.print(f"\n[bold]━━━ Step {step_num}: {friendly_name} ━━━[/bold]")

    # For middleware steps, show what they're doing
    if node_name == "SummarizationMiddleware.before_model":
        # Note: Middleware steps in stream_mode="updates" don't provide state deltas,
        # only full state modifications. We can't see the actual messages here.
        console.print(f"[{COLORS['dim']}]   Optimizing conversation context for the model[/{COLORS['dim']}]")
        console.print(f"[{COLORS['dim']}]   • Checking message history size[/{COLORS['dim']}]")
        console.print(f"[{COLORS['dim']}]   • Preparing context window[/{COLORS['dim']}]")

    elif node_name == "PatchToolCallsMiddleware.before_agent":
        # Show what pre-processing is doing
        console.print(f"[{COLORS['dim']}]   Preparing request for agent execution[/{COLORS['dim']}]")

def format_value(value, max_length=10000):
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
        if len(value) > 20:
            preview = value[:20]
            return f"{preview}... ({len(value)} items total)"
        value_str = str(value)
    else:
        value_str = str(value)

    if len(value_str) > max_length:
        return value_str[:max_length] + "... (truncated)"
    return value_str

def print_tool_call(tool_name, args, indent=""):
    """Print tool call details with full arguments."""
    # Use the smart formatter from tool_display module
    display_str = format_tool_display(tool_name, args)

    if tool_name == "task":
        # Subagent spawn - special formatting
        subagent_type = args.get("subagent_type", "unknown")
        description = args.get("description", "")
        console.print(f"{indent}[bold {COLORS['warning']}]🚀 SPAWNING SUBAGENT: {subagent_type}[/bold {COLORS['warning']}]")
        if description:
            # Show full description with proper wrapping
            wrapped = textwrap.fill(description, width=90, initial_indent=f"{indent}   📋 ", subsequent_indent=f"{indent}      ")
            console.print(f"[{COLORS['warning']}]{wrapped}[/{COLORS['warning']}]")
        return  # Early return for task tool

    # For all other tools, use simple formatted display
    icon = "🔧"
    if tool_name in ("read_file", "write_file", "edit_file", "ls"):
        icon = "📁"
    elif tool_name.startswith("get_") or tool_name.startswith("web_search"):
        icon = "🔍"
    elif tool_name == "write_todos":
        icon = "📋"

    console.print(f"{indent}[{COLORS['tool']}]{icon} {display_str}[/{COLORS['tool']}]")

def print_tool_result(result, indent=""):
    """Print tool result with smart formatting and full data display."""
    # Try to parse as JSON first
    if isinstance(result, str):
        try:
            parsed = json.loads(result)
            result = parsed
        except:
            pass

    if isinstance(result, dict):
        # Show success status if present
        if "success" in result:
            success = result.get("success", False)
            status_icon = "✓" if success else "✗"
            status_text = "SUCCESS" if success else "FAILED"
            color = COLORS["success"] if success else COLORS["error"]
            console.print(f"{indent}[{color}]   {status_icon} {status_text}[/{color}]")

        # Show error prominently
        if "error" in result and result["error"]:
            console.print(f"{indent}[{COLORS['error']}]   ❌ Error: {result['error']}[/{COLORS['error']}]")
            return

        # Extract and display key information based on structure
        symbol = result.get("symbol", "")

        # Stock Quote Data
        if "price" in result or "regularMarketPrice" in result:
            price = result.get("price") or result.get("regularMarketPrice")
            change = result.get("change") or result.get("regularMarketChange")
            change_pct = result.get("change_percent") or result.get("regularMarketChangePercent")
            volume = result.get("volume") or result.get("regularMarketVolume")
            market_cap = result.get("market_cap") or result.get("marketCap")

            console.print(f"{indent}[{COLORS['success']}]   📊 Stock Quote:[/{COLORS['success']}]")
            if symbol:
                console.print(f"{indent}[{COLORS['agent']}]      • Symbol: {symbol}[/{COLORS['agent']}]")
            if price:
                price_str = f"${price:,.2f}" if isinstance(price, (int, float)) else price
                console.print(f"{indent}[{COLORS['agent']}]      • Price: {price_str}[/{COLORS['agent']}]")
            if change is not None:
                change_color = COLORS["success"] if (isinstance(change, (int, float)) and change >= 0) else COLORS["error"]
                change_str = f"{change:+,.2f}" if isinstance(change, (int, float)) else change
                pct_str = f" ({change_pct:+.2f}%)" if change_pct is not None else ""
                console.print(f"{indent}[{change_color}]      • Change: {change_str}{pct_str}[/{change_color}]")
            if volume:
                vol_str = f"{volume:,.0f}" if isinstance(volume, (int, float)) else volume
                console.print(f"{indent}[{COLORS['agent']}]      • Volume: {vol_str}[/{COLORS['agent']}]")
            if market_cap:
                mcap_str = f"${market_cap:,.0f}" if isinstance(market_cap, (int, float)) else market_cap
                console.print(f"{indent}[{COLORS['agent']}]      • Market Cap: {mcap_str}[/{COLORS['agent']}]")

        # Financial Metrics
        if "key_metrics" in result and result["key_metrics"]:
            console.print(f"{indent}[{COLORS['success']}]   💰 Key Metrics:[/{COLORS['success']}]")
            metrics = result["key_metrics"]
            for key, value in metrics.items():
                if value is not None:
                    # Format numbers nicely
                    if isinstance(value, float):
                        if abs(value) >= 1e9:
                            value_str = f"${value/1e9:.2f}B"
                        elif abs(value) >= 1e6:
                            value_str = f"${value/1e6:.2f}M"
                        elif abs(value) > 100:
                            value_str = f"${value:,.2f}"
                        else:
                            value_str = f"{value:.2f}"
                    else:
                        value_str = str(value)
                    console.print(f"{indent}[{COLORS['agent']}]      • {key}: {value_str}[/{COLORS['agent']}]")

        # Summary text
        if "summary" in result:
            summary = result["summary"]
            console.print(f"{indent}[{COLORS['success']}]   📋 Summary:[/{COLORS['success']}]")
            lines = summary.split('\n') if isinstance(summary, str) else [str(summary)]
            for line in lines[:30]:  # Show up to 30 lines
                if line.strip():
                    console.print(f"{indent}[{COLORS['agent']}]      {line}[/{COLORS['agent']}]")

        # File path if saved
        if "file_path" in result:
            console.print(f"{indent}[{COLORS['dim']}]   💾 Full data saved: {result['file_path']}[/{COLORS['dim']}]")

        # Data field - show structured view
        if "data" in result:
            data = result["data"]
            # If data wasn't already displayed above, show it
            if not any(k in result for k in ["price", "regularMarketPrice", "key_metrics", "summary"]):
                console.print(f"{indent}[{COLORS['success']}]   📦 Data:[/{COLORS['success']}]")
                if isinstance(data, dict):
                    for key, value in list(data.items())[:20]:  # Show first 20 fields
                        if isinstance(value, (dict, list)) and len(str(value)) > 100:
                            console.print(f"{indent}[{COLORS['agent']}]      • {key}: {type(value).__name__} ({len(value)} items)[/{COLORS['agent']}]")
                        else:
                            value_str = str(value)[:200]
                            console.print(f"{indent}[{COLORS['agent']}]      • {key}: {value_str}[/{COLORS['agent']}]")
                elif isinstance(data, list):
                    console.print(f"{indent}[{COLORS['agent']}]      List with {len(data)} items[/{COLORS['agent']}]")
                    for i, item in enumerate(data[:10], 1):
                        item_str = str(item)[:200]
                        console.print(f"{indent}[{COLORS['agent']}]      {i}. {item_str}[/{COLORS['agent']}]")
                else:
                    console.print(f"{indent}[{COLORS['agent']}]      {str(data)[:500]}[/{COLORS['agent']}]")

        # If no special fields found, show all top-level keys
        displayed_keys = {"success", "error", "symbol", "price", "regularMarketPrice", "change",
                         "change_percent", "volume", "market_cap", "key_metrics", "summary",
                         "file_path", "data"}
        remaining = {k: v for k, v in result.items() if k not in displayed_keys and v is not None}
        if remaining:
            console.print(f"{indent}[{COLORS['success']}]   ℹ️  Additional Fields:[/{COLORS['success']}]")
            for key, value in list(remaining.items())[:15]:
                if isinstance(value, (dict, list)) and len(str(value)) > 100:
                    console.print(f"{indent}[{COLORS['agent']}]      • {key}: {type(value).__name__} ({len(value)} items)[/{COLORS['agent']}]")
                else:
                    value_str = str(value)[:300]
                    console.print(f"{indent}[{COLORS['agent']}]      • {key}: {value_str}[/{COLORS['agent']}]")

    elif isinstance(result, list):
        # Show list length and detailed preview
        console.print(f"{indent}[{COLORS['success']}]   📊 Result: List with {len(result)} items[/{COLORS['success']}]")
        for i, item in enumerate(result[:15], 1):  # Show first 15 items
            if isinstance(item, dict):
                # For dict items, show key fields
                item_preview = ", ".join(f"{k}={v}" for k, v in list(item.items())[:3])
                console.print(f"{indent}[{COLORS['agent']}]     {i}. {{{item_preview}...}}[/{COLORS['agent']}]")
            else:
                item_str = str(item)[:300]
                console.print(f"{indent}[{COLORS['agent']}]     {i}. {item_str}[/{COLORS['agent']}]")
        if len(result) > 15:
            console.print(f"{indent}[{COLORS['dim']}]     ... and {len(result)-15} more items[/{COLORS['dim']}]")

    else:
        # Plain string or other type - show in full
        result_str = str(result)
        if len(result_str) > 5000:
            # Show first 5000 chars
            lines = result_str[:5000].split('\n')
            console.print(f"{indent}[{COLORS['agent']}]   ✓ Result:[/{COLORS['agent']}]")
            for line in lines[:100]:  # Show up to 100 lines
                console.print(f"{indent}[{COLORS['agent']}]     {line}[/{COLORS['agent']}]")
            console.print(f"{indent}[{COLORS['dim']}]     ... (truncated, {len(result_str):,} chars total)[/{COLORS['dim']}]")
        else:
            # Show full result
            lines = result_str.split('\n')
            if len(lines) > 1:
                console.print(f"{indent}[{COLORS['agent']}]   ✓ Result:[/{COLORS['agent']}]")
                for line in lines:
                    console.print(f"{indent}[{COLORS['agent']}]     {line}[/{COLORS['agent']}]")
            else:
                console.print(f"{indent}[{COLORS['agent']}]   ✓ Result: {result_str}[/{COLORS['agent']}]")

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

        console.print(f"[{COLORS['success']}]✓ Loaded portfolio for: {portfolio['client']['name']}[/{COLORS['success']}]")
        console.print(f"[{COLORS['dim']}]📊 Agent will fetch REAL prices from Yahoo Finance API[/{COLORS['dim']}]")
        return files
    except FileNotFoundError:
        console.print(f"[{COLORS['warning']}]⚠️  Example portfolio file not found. Continuing without portfolio data.[/{COLORS['warning']}]")
        return {}

def show_help():
    """Show help information."""
    from src.commands import show_interactive_help
    show_interactive_help()

def print_approval_request(action_request, review_config):
    """Display an approval request for a tool call."""
    tool_name = action_request.get("name", "unknown")
    tool_args = action_request.get("args", {})
    allowed_decisions = review_config.get("allowed_decisions", ["approve", "reject"])

    console.print(f"\n[bold {COLORS['warning']}]⚠️  APPROVAL REQUIRED[/bold {COLORS['warning']}]")
    console.print(f"[{COLORS['warning']}]{'━' * 60}[/{COLORS['warning']}]")
    console.print(f"[bold]Tool:[/bold] {tool_name}")
    console.print(f"[bold]Arguments:[/bold]")

    # Format arguments nicely
    for key, value in tool_args.items():
        # Use textwrap for better formatting of long descriptions
        if isinstance(value, str) and len(value) > 100:
            wrapped = textwrap.fill(value, width=90, initial_indent="  ", subsequent_indent="  ")
            console.print(f"  [{COLORS['dim']}]{key}:[/{COLORS['dim']}]")
            console.print(f"[{COLORS['dim']}]{wrapped}[/{COLORS['dim']}]")
        else:
            formatted_value = format_value(value, max_length=5000)
            if '\n' in formatted_value:
                console.print(f"  [{COLORS['dim']}]{key}:[/{COLORS['dim']}]")
                for line in formatted_value.split('\n'):
                    console.print(f"    [{COLORS['dim']}]{line}[/{COLORS['dim']}]")
            else:
                console.print(f"  [{COLORS['dim']}]{key}: {formatted_value}[/{COLORS['dim']}]")

    console.print(f"[{COLORS['warning']}]{'━' * 60}[/{COLORS['warning']}]")

    # Show description if available
    description = action_request.get("description")
    if description:
        console.print(f"[{COLORS['dim']}]Description: {description}[/{COLORS['dim']}]\n")

    return allowed_decisions

async def get_user_decision(allowed_decisions):
    """Get user's decision on whether to approve/reject/edit a tool call (async)."""
    # Map decision types to user-friendly prompts
    decision_map = {
        "approve": "y",
        "reject": "n",
        "edit": "e"
    }

    # Build prompt based on allowed decisions - use plain text for input() since it doesn't support Rich markup
    prompt_parts = []
    if "approve" in allowed_decisions:
        prompt_parts.append("[y]es")
    if "reject" in allowed_decisions:
        prompt_parts.append("[n]o")
    if "edit" in allowed_decisions:
        prompt_parts.append("[e]dit")

    prompt = f"Approve? ({'/'.join(prompt_parts)}): "

    while True:
        try:
            # Run input() in thread pool to avoid blocking
            user_input = await asyncio.to_thread(input, prompt)
            user_input = user_input.strip().lower()

            if user_input in ['y', 'yes'] and "approve" in allowed_decisions:
                return {"type": "approve"}
            elif user_input in ['n', 'no'] and "reject" in allowed_decisions:
                return {"type": "reject"}
            elif user_input in ['e', 'edit'] and "edit" in allowed_decisions:
                console.print(f"[{COLORS['warning']}]Edit functionality coming soon. Rejecting for now.[/{COLORS['warning']}]")
                return {"type": "reject"}
            else:
                console.print(f"[{COLORS['error']}]Invalid choice. Please try again.[/{COLORS['error']}]")
        except (KeyboardInterrupt, EOFError):
            console.print(f"\n[{COLORS['warning']}]Defaulting to reject[/{COLORS['warning']}]")
            return {"type": "reject"}

async def run_chat():
    """Run the interactive chat loop (async)."""

    print_banner()

    # Load example portfolio
    print("📂 Loading example portfolio...")
    initial_files = load_portfolio()

    # Generate thread ID for checkpointing and local file storage
    thread_id = str(uuid.uuid4())

    # Create agent with session_id for local filesystem
    console.print(f"\n🏗️  Creating deep agent (session: {thread_id[:8]}...)...")
    agent = create_finance_deep_agent(session_id=thread_id)
    console.print(f"[{COLORS['success']}]✓ Agent ready with 8 specialized subagents (ASYNC MODE)[/{COLORS['success']}]")
    console.print(f"[{COLORS['success']}]✓ Files will be saved to: sessions/{thread_id}/[/{COLORS['success']}]")
    console.print(f"[{COLORS['success']}]  - market-data-fetcher (NEW: Yahoo Finance API)[/{COLORS['success']}]")
    console.print(f"[{COLORS['success']}]  - research-analyst (NEW: Company research)[/{COLORS['success']}]")
    console.print(f"[{COLORS['success']}]  - portfolio, cashflow, goals, debt, tax, risk analyzers[/{COLORS['success']}]\n")

    # Initialize session state
    session_state = SessionState(auto_approve=False)

    # Initialize token tracker
    token_tracker = TokenTracker()
    # Note: Baseline token calculation would require model access, skip for now
    # Can be added later if model is accessible

    # Initialize prompt session with advanced features
    prompt_session = create_prompt_session(session_state)

    # Initialize conversation state
    conversation_messages = []
    files = initial_files.copy()
    # thread_id already generated above for agent creation

    # Main chat loop
    while True:
        # Get user input with advanced features (async to avoid blocking)
        try:
            user_input = await prompt_session.prompt_async()
            user_input = user_input.strip()
        except (KeyboardInterrupt, EOFError):
            console.print(f"\n\n[{COLORS['warning']}]👋 Goodbye![/{COLORS['warning']}]\n")
            break

        # Handle empty input
        if not user_input:
            continue

        # Handle slash commands
        if user_input.startswith("/"):
            result = handle_command(user_input, agent, token_tracker, session_state)
            if result == "exit":
                console.print(f"\n[{COLORS['success']}]👋 Goodbye![/{COLORS['success']}]\n")
                break
            if result:
                continue  # Command handled

        # Handle bash commands
        if user_input.startswith("!"):
            execute_bash_command(user_input)
            continue

        # Handle old-style quit keywords
        if user_input.lower() in ['quit', 'exit', 'q']:
            console.print(f"\n[{COLORS['warning']}]👋 Goodbye![/{COLORS['warning']}]\n")
            break

        # Parse file mentions and inject content
        prompt_text, mentioned_files = parse_file_mentions(user_input)
        if mentioned_files:
            console.print(f"[{COLORS['dim']}]📎 Injecting {len(mentioned_files)} file(s)[/{COLORS['dim']}]")
            # Inject file contents
            context_parts = [prompt_text, "\n\n## Referenced Files\n"]
            for file_path in mentioned_files:
                try:
                    content = file_path.read_text()
                    context_parts.append(f"\n### {file_path.name}\n```\n{content}\n```")
                except Exception as e:
                    console.print(f"[{COLORS['warning']}]Warning: Could not read {file_path.name}: {e}[/{COLORS['warning']}]")
            final_input = "\n".join(context_parts)
        else:
            final_input = prompt_text

        # Add user message to conversation
        conversation_messages.append(HumanMessage(content=final_input))

        # Prune conversation history to prevent context bloat
        original_count = len(conversation_messages)
        pruned_messages = prune_conversation_history(conversation_messages)

        # Check if pruning occurred and notify user
        if len(pruned_messages) < original_count:
            pruned_count = original_count - len(pruned_messages)
            console.print(f"[{COLORS['warning']}]📊 Context Management: Pruned {pruned_count} older messages (keeping last {MAX_CONVERSATION_TURNS} turns)[/{COLORS['warning']}]")

        # Estimate token count and warn if high
        estimated_tokens = estimate_token_count(pruned_messages)
        if estimated_tokens > CONTEXT_WARNING_THRESHOLD:
            console.print(f"[{COLORS['warning']}]⚠️  High context size: ~{estimated_tokens:,} tokens (may affect performance)[/{COLORS['warning']}]")

        # Add context summary if messages were pruned
        context_summary = create_context_summary(pruned_messages, original_count)
        messages_to_send = pruned_messages[:]
        if context_summary:
            messages_to_send.insert(0, context_summary)

        # Prepare state and config
        state = {
            "messages": messages_to_send,  # Pass pruned conversation history
            "files": files.copy()
        }
        config = {
            "configurable": {
                "thread_id": thread_id
            }
        }

        # Execute agent with live progress
        print_thinking()
        step_count = 0
        new_messages = []
        has_interrupted = False
        collected_interrupts = []

        try:
            console.print(f"[{COLORS['dim']}]{'─' * 80}[/{COLORS['dim']}]")

            async for chunk in agent.astream(state, config=config, stream_mode="updates"):
                step_count += 1

                for node_name, state_update in chunk.items():
                    # Check for interrupts FIRST (before any processing)
                    if node_name == "__interrupt__":
                        has_interrupted = True
                        # state_update can be a tuple, list, or single Interrupt object
                        if isinstance(state_update, (tuple, list)):
                            # Unpack tuple/list of Interrupt objects
                            collected_interrupts.extend(state_update)
                        else:
                            # Single Interrupt object
                            collected_interrupts.append(state_update)
                        # Don't process interrupt as a normal node
                        continue

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
                        console.print(f"\n[bold {COLORS['dim']}]  ╭─── Subagent: {subagent_name} ───╮[/bold {COLORS['dim']}]")
                    else:
                        print_step_header(step_count, node_name, state_update)

                    if state_update is None:
                        continue

                    # Show messages and tool calls
                    if "messages" in state_update:
                        # Handle Overwrite wrapper from LangGraph
                        messages = state_update["messages"]
                        if isinstance(messages, Overwrite):
                            messages = messages.value

                        # Ensure messages is iterable
                        if not isinstance(messages, (list, tuple)):
                            messages = [messages]

                        for msg in messages:
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
                                console.print(f"{indent}[{COLORS['success']}]  [{tool_name}] returned:[/{COLORS['success']}]")
                                print_tool_result(msg.content, indent=indent)

                    # Show file updates (only if content actually changed)
                    if "files" in state_update and state_update["files"]:
                        new_files = state_update["files"]
                        # Handle Overwrite wrapper
                        if isinstance(new_files, Overwrite):
                            new_files = new_files.value
                        if new_files:
                            # Detect actual changes (new files or modified content)
                            changed_files = {}
                            for path, new_data in new_files.items():
                                if path not in files or files[path] != new_data:
                                    changed_files[path] = new_data

                            # Update files dict
                            files.update(new_files)

                            # Only show message if files actually changed
                            if changed_files:
                                console.print(f"{indent}[{COLORS['agent']}]📁 Files updated: {len(changed_files)} file(s)[/{COLORS['agent']}]")
                                for path in list(changed_files.keys())[:3]:  # Show first 3
                                    console.print(f"{indent}[{COLORS['agent']}]   - {path}[/{COLORS['agent']}]")

                    # Show todos
                    if "todos" in state_update and state_update["todos"]:
                        todos = state_update["todos"]
                        # Handle Overwrite wrapper
                        if isinstance(todos, Overwrite):
                            todos = todos.value
                        if todos:
                            console.print(f"{indent}[{COLORS['warning']}]📋 TODO LIST:[/{COLORS['warning']}]")
                            for todo in todos[:5]:  # Show first 5
                                status = todo.get("status", "unknown")
                                content = todo.get("content", "")
                                emoji = "✓" if status == "completed" else "⏳" if status == "in_progress" else "○"
                                console.print(f"{indent}[{COLORS['warning']}]   {emoji} [{status}] {content}[/{COLORS['warning']}]")

                    # Close subagent box
                    if is_subagent:
                        console.print(f"[{COLORS['dim']}]  ╰{'─' * 50}╯[/{COLORS['dim']}]")

            # Handle interrupts if any occurred
            if has_interrupted and collected_interrupts:
                console.print(f"\n[{COLORS['warning']}]{'━' * 80}[/{COLORS['warning']}]")
                console.print(f"[bold {COLORS['warning']}]🛑 Agent Paused - Approval Required[/bold {COLORS['warning']}]")
                console.print(f"[{COLORS['warning']}]{'━' * 80}[/{COLORS['warning']}]\n")

                # Extract action requests from interrupts
                # Based on LangChain docs: result["__interrupt__"][0].value contains the data
                all_action_requests = []
                all_review_configs = []

                for interrupt in collected_interrupts:
                    # Interrupt objects have a .value attribute containing the dict
                    if hasattr(interrupt, 'value'):
                        interrupt_data = interrupt.value
                    elif isinstance(interrupt, dict):
                        # Fallback if it's already a dict
                        interrupt_data = interrupt
                    else:
                        continue

                    # Extract action_requests and review_configs from interrupt_data
                    if isinstance(interrupt_data, dict):
                        action_requests = interrupt_data.get("action_requests", [])
                        review_configs = interrupt_data.get("review_configs", [])

                        all_action_requests.extend(action_requests)
                        all_review_configs.extend(review_configs)

                # Create a map from tool name to review config
                config_map = {cfg.get("action_name", ""): cfg for cfg in all_review_configs if cfg.get("action_name")}

                # If no action requests found, something went wrong
                if not all_action_requests:
                    console.print(f"[{COLORS['error']}]⚠️  No action requests found. Continuing...[/{COLORS['error']}]")
                    continue  # Skip to next iteration

                # Collect decisions for each action
                decisions = []
                for i, action_request in enumerate(all_action_requests, 1):
                    tool_name = action_request.get("name", "unknown")
                    review_config = config_map.get(tool_name, {"allowed_decisions": ["approve", "reject"]})

                    console.print(f"[bold]Request {i} of {len(all_action_requests)}:[/bold]")
                    allowed_decisions = print_approval_request(action_request, review_config)
                    decision = await get_user_decision(allowed_decisions)
                    decisions.append(decision)

                    if decision["type"] == "approve":
                        console.print(f"[{COLORS['success']}]✓ Approved[/{COLORS['success']}]\n")
                    else:
                        console.print(f"[{COLORS['error']}]✗ Rejected[/{COLORS['error']}]\n")

                # Resume execution with decisions
                console.print(f"[{COLORS['dim']}]{'─' * 80}[/{COLORS['dim']}]")
                console.print(f"[bold]🔄 Resuming agent execution...[/bold]\n")

                # Use Command to resume with decisions
                resume_state = Command(resume={"decisions": decisions})

                # Stream the resumed execution (async)
                async for chunk in agent.astream(resume_state, config=config, stream_mode="updates"):
                    step_count += 1

                    for node_name, state_update in chunk.items():
                        # Same processing as before
                        is_subagent = node_name.startswith("SubAgent[") or "SubAgent" in node_name
                        subagent_name = ""
                        if is_subagent:
                            if "[" in node_name and "]" in node_name:
                                subagent_name = node_name.split("[")[1].split("]")[0]

                        indent = "  " if is_subagent else ""

                        if is_subagent:
                            console.print(f"\n[bold {COLORS['dim']}]  ╭─── Subagent: {subagent_name} ───╮[/bold {COLORS['dim']}]")
                        else:
                            print_step_header(step_count, node_name, state_update)

                        if state_update is None:
                            continue

                        if "messages" in state_update:
                            for msg in state_update["messages"]:
                                new_messages.append(msg)

                                if msg.type == "ai" and hasattr(msg, "tool_calls") and msg.tool_calls:
                                    for tool_call in msg.tool_calls:
                                        tool_name = tool_call.get("name", "unknown")
                                        tool_args = tool_call.get("args", {})
                                        print_tool_call(tool_name, tool_args, indent=indent)

                                elif msg.type == "tool":
                                    tool_name = getattr(msg, 'name', 'unknown')
                                    console.print(f"{indent}[{COLORS['success']}]  [{tool_name}] returned:[/{COLORS['success']}]")
                                    print_tool_result(msg.content, indent=indent)

                        if "files" in state_update and state_update["files"]:
                            new_files = state_update["files"]
                            # Detect actual changes (new files or modified content)
                            changed_files = {}
                            for path, new_data in new_files.items():
                                if path not in files or files[path] != new_data:
                                    changed_files[path] = new_data

                            # Update files dict
                            files.update(new_files)

                            # Only show message if files actually changed
                            if changed_files:
                                console.print(f"{indent}[{COLORS['agent']}]📁 Files updated: {len(changed_files)} file(s)[/{COLORS['agent']}]")
                                for path in list(changed_files.keys())[:3]:
                                    console.print(f"{indent}[{COLORS['agent']}]   - {path}[/{COLORS['agent']}]")

                        if "todos" in state_update and state_update["todos"]:
                            todos = state_update["todos"]
                            console.print(f"{indent}[{COLORS['warning']}]📋 TODO LIST:[/{COLORS['warning']}]")
                            for todo in todos[:5]:
                                status = todo.get("status", "unknown")
                                content = todo.get("content", "")
                                emoji = "✓" if status == "completed" else "⏳" if status == "in_progress" else "○"
                                console.print(f"{indent}[{COLORS['warning']}]   {emoji} [{status}] {content}[/{COLORS['warning']}]")

                        if is_subagent:
                            console.print(f"[{COLORS['dim']}]  ╰{'─' * 50}╯[/{COLORS['dim']}]")

            # Add only new AI messages to conversation history
            for msg in new_messages:
                if msg.type == "ai" and msg not in conversation_messages:
                    conversation_messages.append(msg)

            # Separator before final response
            console.print(f"\n[{COLORS['dim']}]{'─' * 80}[/{COLORS['dim']}]")
            console.print(f"[bold {COLORS['success']}]✓ Execution complete[/bold {COLORS['success']}]\n")

            # Get final response
            ai_messages = [m for m in conversation_messages if m.type == "ai"]
            if ai_messages:
                final_response = ai_messages[-1].content
                print_agent_response(final_response)
            else:
                print_error("No response generated")

        except KeyboardInterrupt:
            console.print(f"\n\n[{COLORS['warning']}]⚠️  Interrupted. Type 'quit' to exit or continue chatting.[/{COLORS['warning']}]\n")
            # Remove the last user message since we interrupted
            conversation_messages.pop()

        except Exception as e:
            print_error(f"{e}")
            console.print(f"[{COLORS['warning']}]💡 Try rephrasing your question or type 'help' for guidance[/{COLORS['warning']}]")
            # Remove the last user message on error
            conversation_messages.pop()

if __name__ == "__main__":
    try:
        # Run async chat loop
        asyncio.run(run_chat())
    except Exception as e:
        console.print(f"\n[{COLORS['error']}]Fatal error: {e}[/{COLORS['error']}]\n")
        sys.exit(1)
