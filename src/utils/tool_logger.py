"""Tool call logging decorator for visibility into subagent execution."""

import json
import os
from functools import wraps
from typing import Any, Callable


# Colors for terminal output (matching chat.py)
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


# Global flag to enable/disable logging
TOOL_LOGGING_ENABLED = os.getenv('TOOL_LOGGING', 'true').lower() in ('true', '1', 'yes')


def format_value(value: Any, max_length: int = 300) -> str:
    """Format a value for display with smart truncation."""
    if isinstance(value, dict):
        try:
            formatted = json.dumps(value, indent=2)
            if len(formatted) > max_length:
                return formatted[:max_length] + "\n    ... (truncated)"
            return formatted
        except:
            value_str = str(value)
    elif isinstance(value, list):
        if len(value) > 5:
            preview = value[:5]
            return f"{preview}... ({len(value)} items total)"
        value_str = str(value)
    else:
        value_str = str(value)

    if len(value_str) > max_length:
        return value_str[:max_length] + "... (truncated)"
    return value_str


def log_tool_call(tool_name: str, args: dict, indent: str = "    "):
    """Log a tool call with its arguments."""
    if not TOOL_LOGGING_ENABLED:
        return

    # Special formatting for different tool types
    if tool_name.startswith("get_") and ("stock" in tool_name or "quote" in tool_name):
        # Yahoo Finance tools
        symbol = args.get("symbol", args.get("symbols", args.get("query", "")))
        print(f"{indent}{Colors.OKGREEN}🔧 [{tool_name}]{Colors.ENDC}")
        if symbol:
            print(f"{indent}{Colors.OKGREEN}   Symbol(s): {symbol}{Colors.ENDC}")
        # Show other relevant args
        for key, value in args.items():
            if key not in ["symbol", "symbols", "query", "region", "lang"] and value:
                print(f"{indent}{Colors.OKGREEN}   {key}: {value}{Colors.ENDC}")
    elif tool_name.startswith("web_search"):
        query = args.get("query", "")
        print(f"{indent}{Colors.OKGREEN}🔧 [{tool_name}]{Colors.ENDC}")
        print(f"{indent}{Colors.OKGREEN}   Query: {query}{Colors.ENDC}")
    elif tool_name.startswith("calculate_") or tool_name.startswith("analyze_"):
        # Calculation/analysis tools
        print(f"{indent}{Colors.OKGREEN}🔧 [{tool_name}]{Colors.ENDC}")
        for key, value in list(args.items())[:3]:  # Show first 3 args
            formatted_value = format_value(value, max_length=100)
            if '\n' not in formatted_value:
                print(f"{indent}{Colors.OKGREEN}   {key}: {formatted_value}{Colors.ENDC}")
    else:
        # Generic tool
        print(f"{indent}{Colors.OKGREEN}🔧 [{tool_name}]{Colors.ENDC}")
        if args and len(args) <= 3:  # Show all args if few
            for key, value in args.items():
                formatted_value = format_value(value, max_length=100)
                print(f"{indent}{Colors.OKGREEN}   {key}: {formatted_value}{Colors.ENDC}")


def log_tool_result(tool_name: str, result: Any, indent: str = "    "):
    """Log a tool result with smart formatting."""
    if not TOOL_LOGGING_ENABLED:
        return

    # Parse JSON if string
    if isinstance(result, str):
        try:
            parsed = json.loads(result)
            result = parsed
        except:
            pass

    print(f"{indent}{Colors.OKBLUE}   ✓ [{tool_name}] returned:{Colors.ENDC}")

    if isinstance(result, dict):
        # Show success/error status
        if "success" in result:
            success = result.get("success", False)
            status = "✓ SUCCESS" if success else "✗ FAILED"
            color = Colors.OKGREEN if success else Colors.FAIL
            print(f"{indent}{color}     Status: {status}{Colors.ENDC}")

        if "symbol" in result:
            print(f"{indent}{Colors.OKBLUE}     Symbol: {result['symbol']}{Colors.ENDC}")

        if "error" in result and result["error"]:
            print(f"{indent}{Colors.FAIL}     Error: {result['error']}{Colors.ENDC}")

        # Show summary if available (first 3 lines)
        if "summary" in result:
            summary = result["summary"]
            lines = summary.split('\n') if isinstance(summary, str) else [str(summary)]
            for line in lines[:3]:
                print(f"{indent}{Colors.OKBLUE}     {line}{Colors.ENDC}")
            if len(lines) > 3:
                print(f"{indent}{Colors.OKBLUE}     ... ({len(lines)-3} more lines){Colors.ENDC}")

        # Show key metrics (first 3)
        if "key_metrics" in result and result["key_metrics"]:
            metrics = result["key_metrics"]
            for key, value in list(metrics.items())[:3]:
                print(f"{indent}{Colors.OKBLUE}       • {key}: {value}{Colors.ENDC}")

    elif isinstance(result, list):
        print(f"{indent}{Colors.OKBLUE}     List with {len(result)} items{Colors.ENDC}")
        for i, item in enumerate(result[:2], 1):
            item_str = str(item)[:80]
            print(f"{indent}{Colors.OKBLUE}       {i}. {item_str}{Colors.ENDC}")

    else:
        # String or other type
        result_str = str(result)
        if len(result_str) > 200:
            lines = result_str[:200].split('\n')[:3]
            for line in lines:
                print(f"{indent}{Colors.OKBLUE}     {line}{Colors.ENDC}")
            print(f"{indent}{Colors.OKBLUE}     ... (truncated){Colors.ENDC}")
        else:
            lines = result_str.split('\n')
            for line in lines[:3]:
                print(f"{indent}{Colors.OKBLUE}     {line}{Colors.ENDC}")


def logged_tool(func: Callable) -> Callable:
    """
    Decorator to log tool calls and results.

    Usage:
        @tool
        @logged_tool
        def my_tool(arg1: str, arg2: int) -> dict:
            return {"result": "success"}

    Note: Apply this AFTER the @tool decorator
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        tool_name = func.__name__

        # Log the call
        log_tool_call(tool_name, kwargs)

        # Execute the function
        try:
            result = func(*args, **kwargs)

            # Log the result
            log_tool_result(tool_name, result)

            return result

        except Exception as e:
            # Log the error
            if TOOL_LOGGING_ENABLED:
                print(f"    {Colors.FAIL}   ✗ [{tool_name}] EXCEPTION: {str(e)}{Colors.ENDC}")
            raise

    return wrapper


# Alternative: Class-based decorator for async support
class LoggedTool:
    """
    Class-based decorator for logging tool calls (supports both sync and async).

    Usage:
        @tool
        @LoggedTool()
        def my_tool(arg1: str) -> dict:
            return {"result": "success"}
    """

    def __init__(self, indent: str = "    "):
        self.indent = indent

    def __call__(self, func: Callable) -> Callable:
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            tool_name = func.__name__
            log_tool_call(tool_name, kwargs, self.indent)

            try:
                result = func(*args, **kwargs)
                log_tool_result(tool_name, result, self.indent)
                return result
            except Exception as e:
                if TOOL_LOGGING_ENABLED:
                    print(f"{self.indent}{Colors.FAIL}   ✗ [{tool_name}] EXCEPTION: {str(e)}{Colors.ENDC}")
                raise

        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            tool_name = func.__name__
            log_tool_call(tool_name, kwargs, self.indent)

            try:
                result = await func(*args, **kwargs)
                log_tool_result(tool_name, result, self.indent)
                return result
            except Exception as e:
                if TOOL_LOGGING_ENABLED:
                    print(f"{self.indent}{Colors.FAIL}   ✗ [{tool_name}] EXCEPTION: {str(e)}{Colors.ENDC}")
                raise

        # Return appropriate wrapper based on function type
        if hasattr(func, '__wrapped__'):
            # Already wrapped by @tool decorator
            import inspect
            if inspect.iscoroutinefunction(func.__wrapped__):
                return async_wrapper

        import inspect
        if inspect.iscoroutinefunction(func):
            return async_wrapper

        return sync_wrapper
