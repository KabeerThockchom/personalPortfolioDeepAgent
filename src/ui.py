"""Rich UI components for beautiful terminal output."""

from rich import box
from rich.panel import Panel
from rich.syntax import Syntax
from src.config import console, COLORS


def render_diff_block(diff: str, title: str):
    """
    Render a diff block with syntax highlighting.

    Args:
        diff: Unified diff string
        title: Title for the panel
    """
    syntax = Syntax(diff, "diff", theme="monokai", line_numbers=False)
    panel = Panel(
        syntax,
        title=title,
        border_style=COLORS["primary"],
        box=box.ROUNDED,
        padding=(0, 1)
    )
    console.print(panel)


def render_approval_panel(tool_name: str, tool_args: dict, description: str | None = None):
    """
    Render an approval request panel.

    Args:
        tool_name: Name of the tool
        tool_args: Tool arguments dict
        description: Optional description text
    """
    # Build body
    body_lines = [
        f"[bold yellow]Tool:[/bold yellow] {tool_name}",
        "",
        "[bold yellow]Arguments:[/bold yellow]"
    ]

    for key, value in tool_args.items():
        val_str = str(value)
        if len(val_str) > 200:
            val_str = val_str[:200] + "..."
        body_lines.append(f"  [cyan]{key}:[/cyan] {val_str}")

    if description:
        body_lines.extend(["", f"[dim]{description}[/dim]"])

    panel = Panel(
        "\n".join(body_lines),
        title="[bold yellow]⚠️  Approval Required[/bold yellow]",
        border_style="yellow",
        box=box.ROUNDED,
        padding=(1, 2)
    )
    console.print(panel)


def render_file_operation(record):
    """
    Render concise file operation summary with diff.

    Args:
        record: FileOperationRecord instance
    """
    label_map = {
        "read_file": "Read",
        "write_file": "Write",
        "edit_file": "Update",
    }
    label = label_map.get(record.tool_name, record.tool_name)

    console.print(f"⏺ {label}({record.display_path})", style=f"bold {COLORS['tool']}")

    if record.status == "error":
        console.print(f"  ⎿  {record.error}", style=COLORS["error"])
        return

    if record.tool_name == "read_file":
        console.print(f"  ⎿  Read {record.metrics.lines_read} lines", style=COLORS["dim"])
    else:
        added = record.metrics.lines_added
        removed = record.metrics.lines_removed
        detail = f"  ⎿  {record.metrics.lines_written} lines (+{added} / -{removed})"
        console.print(detail, style=COLORS["dim"])

    if record.diff:
        render_diff_block(record.diff, f"Diff {record.display_path}")


def render_banner(ascii_art: str, subtitle: str | None = None):
    """
    Render ASCII art banner with optional subtitle.

    Args:
        ascii_art: ASCII art string
        subtitle: Optional subtitle text
    """
    console.print(ascii_art, style=f"bold {COLORS['primary']}")
    if subtitle:
        console.print(subtitle, style=COLORS["dim"])
    console.print()
