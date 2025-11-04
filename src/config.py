"""Centralized configuration for Personal Finance Deep Agent."""

import os
from pathlib import Path
from rich.console import Console
from dotenv import load_dotenv

load_dotenv()

# Rich console instance (shared across app)
# highlight=False prevents auto-highlighting of code-like text
console = Console(highlight=False)

# Color scheme (emerald green theme, consistent with deepagents-cli)
COLORS = {
    "primary": "#10b981",    # Emerald green
    "dim": "#6b7280",        # Gray
    "user": "#ffffff",       # White
    "agent": "#10b981",      # Emerald green
    "thinking": "#34d399",   # Light green
    "tool": "#fbbf24",       # Amber
    "error": "#ef4444",      # Red
    "success": "#10b981",    # Green
    "warning": "#f59e0b",    # Orange
}

# ASCII art banner
FINANCE_AGENT_ASCII = """
 ███████╗ ██╗ ███╗   ██╗  █████╗  ███╗   ██╗  ██████╗ ███████╗
 ██╔════╝ ██║ ████╗  ██║ ██╔══██╗ ████╗  ██║ ██╔════╝ ██╔════╝
 █████╗   ██║ ██╔██╗ ██║ ███████║ ██╔██╗ ██║ ██║      █████╗
 ██╔══╝   ██║ ██║╚██╗██║ ██╔══██║ ██║╚██╗██║ ██║      ██╔══╝
 ██║      ██║ ██║ ╚████║ ██║  ██║ ██║ ╚████║ ╚██████╗ ███████╗
 ╚═╝      ╚═╝ ╚═╝  ╚═══╝ ╚═╝  ╚═╝ ╚═╝  ╚═══╝  ╚═════╝ ╚══════╝

  █████╗   ██████╗  ███████╗ ███╗   ██╗ ████████╗
 ██╔══██╗ ██╔════╝  ██╔════╝ ████╗  ██║ ╚══██╔══╝
 ███████║ ██║  ███╗ █████╗   ██╔██╗ ██║    ██║
 ██╔══██║ ██║   ██║ ██╔══╝   ██║╚██╗██║    ██║
 ██║  ██║ ╚██████╔╝ ███████╗ ██║ ╚████║    ██║
 ╚═╝  ╚═╝  ╚═════╝  ╚══════╝ ╚═╝  ╚═══╝    ╚═╝
"""

# Dollar sign ASCII art
DOLLAR_ASCII = """
      ██████╗
     ██╔════╝
     ███████╗
     ╚════██║
     ███████║
     ╚══════╝
        ██║
        ╚═╝
"""

# Money bag ASCII art
MONEYBAG_ASCII = """
      ▄▄▄▄▄
    ▄█▀   ▀█▄
   ██  $$$  ██
   ██ $$$$$ ██
   ██  $$$  ██
    ██     ██
     ███████
    ▄███████▄
   ███████████
  █████████████
  █████████████
   ███████████
    █████████
"""

# Stock market chart ASCII art
STOCK_CHART_ASCII = """
    ╔═══════════════════════════╗
    ║    📈 MARKET OVERVIEW     ║
    ║                           ║
    ║     ┌─────────────┐       ║
    ║  +5%│         ╱   │       ║
    ║     │       ╱     │       ║
    ║   0%│   ╱╲ ╱      │       ║
    ║     │  ╱  ╲       │       ║
    ║  -5%│╱            │       ║
    ║     └─────────────┘       ║
    ║  MON TUE WED THU FRI      ║
    ╚═══════════════════════════╝
"""

# Interactive commands registry
COMMANDS = {
    "clear": "Clear screen and reset conversation",
    "help": "Show help information",
    "tokens": "Show token usage for current session",
    "quit": "Exit the CLI",
    "exit": "Exit the CLI",
}

# Common bash commands for autocomplete
COMMON_BASH_COMMANDS = {
    "ls": "List directory contents",
    "cd": "Change directory",
    "pwd": "Print working directory",
    "cat": "Display file contents",
    "grep": "Search text patterns",
    "find": "Find files",
    "git status": "Show git status",
    "git diff": "Show git diff",
    "git log": "Show git history",
    "python": "Run Python",
    "pytest": "Run tests",
    "pip install": "Install package",
    "npm install": "Install npm packages",
}

# Display settings
MAX_ARG_LENGTH = 150  # Max length for argument display
MAX_CONVERSATION_TURNS = 5  # Keep last N turns
CONTEXT_WARNING_THRESHOLD = 150000  # Token warning threshold

# File operation settings
MAX_DIFF_LINES = 800  # Maximum diff lines to display before truncating

# Agent configuration
AGENT_CONFIG = {
    "recursion_limit": 1000,
}

# Session state
class SessionState:
    """Mutable session state for auto-approve and other runtime settings."""

    def __init__(self, auto_approve: bool = False):
        self.auto_approve = auto_approve

    def toggle_auto_approve(self) -> bool:
        """Toggle auto-approve mode and return new state."""
        self.auto_approve = not self.auto_approve
        return self.auto_approve
