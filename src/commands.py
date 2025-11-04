"""Slash command handlers for interactive CLI."""

import subprocess
from pathlib import Path
from langgraph.checkpoint.memory import MemorySaver
from src.config import console, COLORS, COMMANDS


def handle_command(command: str, agent, token_tracker, session_state) -> str | bool:
    """
    Handle slash commands.

    Args:
        command: The command string (with or without /)
        agent: The agent instance
        token_tracker: TokenTracker instance
        session_state: SessionState instance

    Returns:
        'exit' to exit program
        True if handled
        False to pass to agent
    """
    cmd = command.lower().strip().lstrip("/")

    if cmd in ["quit", "exit", "q"]:
        return "exit"

    if cmd == "clear":
        # Reset agent conversation state (new checkpointer = fresh start)
        agent.checkpointer = MemorySaver()

        # Reset token tracking
        token_tracker.reset()

        # Clear screen
        console.clear()
        from chat import print_banner  # Import here to avoid circular import
        print_banner()
        console.print("Fresh start! Screen cleared and conversation reset.", style=COLORS["success"])
        console.print()
        return True

    if cmd == "help":
        show_interactive_help()
        return True

    if cmd == "tokens":
        token_tracker.display_session()
        return True

    console.print(f"[{COLORS['warning']}]Unknown command: /{cmd}[/{COLORS['warning']}]")
    console.print(f"[{COLORS['dim']}]Type /help for available commands.[/{COLORS['dim']}]")
    return True


def show_interactive_help():
    """Show available commands and features."""
    console.print()
    console.print("[bold]Interactive Commands:[/bold]", style=COLORS["primary"])
    console.print()

    for cmd, desc in COMMANDS.items():
        console.print(f"  /{cmd:<12} {desc}", style=COLORS["dim"])

    console.print()
    console.print("[bold]Editing Features:[/bold]", style=COLORS["primary"])
    console.print("  Enter           Submit your message", style=COLORS["dim"])
    console.print("  Alt+Enter       Insert newline (Option+Enter on Mac, or ESC then Enter)",
                 style=COLORS["dim"])
    console.print("  Ctrl+E          Open in external editor (nano by default)", style=COLORS["dim"])
    console.print("  Ctrl+T          Toggle auto-approve mode", style=COLORS["dim"])
    console.print("  Arrow keys      Navigate input", style=COLORS["dim"])
    console.print("  Ctrl+C          Cancel input or interrupt agent mid-work", style=COLORS["dim"])
    console.print()

    console.print("[bold]Special Features:[/bold]", style=COLORS["primary"])
    console.print("  @filename       Type @ to auto-complete files and inject content",
                 style=COLORS["dim"])
    console.print("  /command        Type / to see available commands", style=COLORS["dim"])
    console.print("  !command        Type ! to run bash commands (e.g., !ls, !git status)",
                 style=COLORS["dim"])
    console.print()


def execute_bash_command(command: str) -> bool:
    """
    Execute !commands directly from chat.

    Args:
        command: Command string starting with !

    Returns:
        True (command handled)
    """
    cmd = command.strip().lstrip("!")
    if not cmd:
        return True

    try:
        console.print(f"[{COLORS['dim']}]$ {cmd}[/{COLORS['dim']}]")
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30,
            cwd=Path.cwd()
        )

        if result.stdout:
            console.print(result.stdout, style=COLORS["dim"], markup=False)
        if result.stderr:
            console.print(result.stderr, style=COLORS["error"], markup=False)

        return True
    except subprocess.TimeoutExpired:
        console.print(f"[{COLORS['error']}]Command timed out[/{COLORS['error']}]")
        return True
    except Exception as e:
        console.print(f"[{COLORS['error']}]Error: {e}[/{COLORS['error']}]")
        return True
