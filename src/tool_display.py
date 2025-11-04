"""Tool-specific display formatting for cleaner output."""

from pathlib import Path


def abbreviate_path(path_str: str, max_length: int = 60) -> str:
    """
    Show basename or relative path for readability.

    Args:
        path_str: Full path string
        max_length: Maximum length before using basename only

    Returns:
        Abbreviated path string
    """
    try:
        path = Path(path_str)
        if len(path.parts) == 1:
            return path_str

        # Try relative path
        try:
            rel_path = path.relative_to(Path.cwd())
            rel_str = str(rel_path)
            if len(rel_str) < len(path_str) and len(rel_str) <= max_length:
                return rel_str
        except:
            pass

        # Use absolute if reasonable
        if len(path_str) <= max_length:
            return path_str

        # Otherwise basename only
        return path.name
    except:
        return path_str[:max_length]


def format_tool_display(tool_name: str, tool_args: dict) -> str:
    """
    Format tool calls with tool-specific smart formatting.

    Shows only relevant arguments in a readable format.

    Args:
        tool_name: Name of the tool being called
        tool_args: Dictionary of tool arguments

    Returns:
        Formatted string like "read_file(portfolio.json)"
    """
    # File operations: show path only
    if tool_name in ("read_file", "write_file", "edit_file"):
        path_value = tool_args.get("file_path") or tool_args.get("path")
        if path_value:
            path = abbreviate_path(str(path_value))
            return f"{tool_name}({path})"

    # Web search: show query
    elif tool_name in ("web_search", "web_search_news", "web_search_financial"):
        if "query" in tool_args:
            query = str(tool_args["query"])[:100]
            return f'{tool_name}("{query}")'

    # Grep: show pattern
    elif tool_name == "grep":
        if "pattern" in tool_args:
            pattern = str(tool_args["pattern"])[:70]
            return f'{tool_name}("{pattern}")'

    # ls: show directory
    elif tool_name == "ls":
        if tool_args.get("path"):
            path = abbreviate_path(str(tool_args["path"]))
            return f"{tool_name}({path})"
        return f"{tool_name}()"

    # Glob: show pattern
    elif tool_name == "glob":
        if "pattern" in tool_args:
            pattern = str(tool_args["pattern"])[:80]
            return f'{tool_name}("{pattern}")'

    # Task: show description
    elif tool_name == "task":
        if "description" in tool_args:
            desc = str(tool_args["description"])[:100]
            subagent_type = tool_args.get("subagent_type", "")
            if subagent_type:
                return f'{tool_name}({subagent_type}: "{desc}")'
            return f'{tool_name}("{desc}")'

    # Todos: show count
    elif tool_name == "write_todos":
        if "todos" in tool_args and isinstance(tool_args["todos"], list):
            count = len(tool_args["todos"])
            return f"{tool_name}({count} items)"

    # Stock quotes
    elif tool_name in ("get_stock_quote", "get_multiple_quotes"):
        symbols = tool_args.get("symbol") or tool_args.get("symbols", [])
        if isinstance(symbols, list):
            symbols_str = ", ".join(str(s) for s in symbols[:5])
            if len(symbols) > 5:
                symbols_str += f", ...({len(symbols)} total)"
            return f"{tool_name}([{symbols_str}])"
        return f"{tool_name}({symbols})"

    # Fallback: generic formatting
    if not tool_args:
        return f"{tool_name}()"

    # Show first few relevant args
    args_parts = []
    for k, v in list(tool_args.items())[:3]:
        val_str = str(v)[:50]
        if len(str(v)) > 50:
            val_str += "..."
        args_parts.append(f"{k}={val_str}")

    args_str = ", ".join(args_parts)
    if len(tool_args) > 3:
        args_str += ", ..."

    return f"{tool_name}({args_str})"
