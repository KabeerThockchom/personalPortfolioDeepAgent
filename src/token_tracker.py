"""Token usage tracking across conversation sessions."""

from src.config import console, COLORS


class TokenTracker:
    """Track token usage across conversation."""

    def __init__(self):
        self.baseline_context = 0  # System + agent.md + tools
        self.current_context = 0   # Total including messages
        self.last_output = 0

    def set_baseline(self, tokens: int):
        """Set baseline context token count."""
        self.baseline_context = tokens
        self.current_context = tokens

    def reset(self):
        """Reset to baseline (for /clear command)."""
        self.current_context = self.baseline_context
        self.last_output = 0

    def add(self, input_tokens: int, output_tokens: int):
        """
        Add tokens from API response.

        Args:
            input_tokens: Total input tokens (includes full context)
            output_tokens: Generated output tokens
        """
        self.current_context = input_tokens  # input_tokens IS current context
        self.last_output = output_tokens

    def display_last(self):
        """Display context size after this turn."""
        if self.last_output and self.last_output >= 1000:
            console.print(f"  Generated: {self.last_output:,} tokens", style=COLORS["dim"])
        if self.current_context:
            console.print(f"  Current context: {self.current_context:,} tokens", style=COLORS["dim"])

    def display_session(self):
        """Display full session token usage (for /tokens command)."""
        console.print()
        console.print("[bold]Token Usage:[/bold]", style=COLORS["primary"])

        has_conversation = self.current_context > self.baseline_context

        if self.baseline_context > 0:
            console.print(
                f"  Baseline: {self.baseline_context:,} tokens [dim](system + agent.md)[/dim]",
                style=COLORS["dim"]
            )

            if not has_conversation:
                console.print(
                    "  [dim]Note: Tool definitions (~5k tokens) included after first message[/dim]"
                )

        if has_conversation:
            tools_and_conversation = self.current_context - self.baseline_context
            console.print(
                f"  Tools + conversation: {tools_and_conversation:,} tokens",
                style=COLORS["dim"]
            )

        console.print(f"  Total: {self.current_context:,} tokens", style=f"bold {COLORS['dim']}")
        console.print()
