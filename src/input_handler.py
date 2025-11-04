"""Advanced input handling with autocomplete, file mentions, and multiline support."""

import re
from pathlib import Path
from typing import Iterable
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import Completer, Completion, PathCompleter, WordCompleter, merge_completers
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.document import Document

from src.config import COMMANDS, COMMON_BASH_COMMANDS, COLORS


class FilePathCompleter(Completer):
    """Autocomplete file paths when user types @filename."""

    def __init__(self):
        self.path_completer = PathCompleter(
            only_directories=False,
            expanduser=True,
            file_filter=lambda path: True,  # Accept all files
        )

    def get_completions(self, document: Document, complete_event):
        text = document.text_before_cursor

        # Look for @ followed by a path
        match = re.search(r"@((?:[^\s@]|(?<=\\)\s)*)$", text)
        if not match:
            return

        # Get the path after @
        path_str = match.group(1)
        clean_path = path_str.replace("\\ ", " ")

        # Create a new document with just the path for PathCompleter
        path_doc = Document(clean_path, len(clean_path))

        # Get completions from PathCompleter
        for completion in self.path_completer.get_completions(path_doc, complete_event):
            # Modify the completion to work with our @ prefix
            yield Completion(
                completion.text,
                start_position=completion.start_position - len(path_str),
                display=completion.display,
                display_meta=completion.display_meta,
            )


class CommandCompleter(Completer):
    """Autocomplete /commands."""

    def __init__(self):
        self.commands = COMMANDS

    def get_completions(self, document: Document, complete_event):
        text = document.text_before_cursor

        # Only complete if line starts with /
        if not text.lstrip().startswith("/"):
            return

        # Get the command part after /
        match = re.search(r"/(\w*)$", text)
        if not match:
            return

        prefix = match.group(1).lower()

        # Offer completions
        for cmd, desc in self.commands.items():
            if cmd.startswith(prefix):
                yield Completion(
                    cmd,
                    start_position=-len(prefix),
                    display=f"/{cmd}",
                    display_meta=desc,
                )


class BashCompleter(Completer):
    """Autocomplete !bash commands."""

    def __init__(self):
        self.commands = COMMON_BASH_COMMANDS

    def get_completions(self, document: Document, complete_event):
        text = document.text_before_cursor

        # Only complete if line starts with !
        if not text.lstrip().startswith("!"):
            return

        # Get the command part after !
        match = re.search(r"!([\w\s]*)$", text)
        if not match:
            return

        prefix = match.group(1).lower()

        # Offer completions
        for cmd, desc in self.commands.items():
            if cmd.startswith(prefix):
                yield Completion(
                    cmd,
                    start_position=-len(prefix),
                    display=f"!{cmd}",
                    display_meta=desc,
                )


def parse_file_mentions(text: str) -> tuple[str, list[Path]]:
    """
    Parse @file mentions and return (original_text, list_of_file_paths).

    Does NOT inject content here - that's done in chat.py.
    Just extracts the file paths for later processing.

    Args:
        text: User input text with potential @file mentions

    Returns:
        Tuple of (original_text, list of Path objects)
    """
    pattern = r"@((?:[^\s@]|(?<=\\)\s)+)"
    matches = re.findall(pattern, text)

    files = []
    for match in matches:
        # Clean up escaped spaces
        clean_path = match.replace("\\ ", " ")
        path = Path(clean_path).expanduser()

        # Make absolute
        if not path.is_absolute():
            path = Path.cwd() / path

        try:
            path = path.resolve()
            if path.exists() and path.is_file():
                files.append(path)
        except Exception:
            # Invalid path, skip it
            pass

    return text, files


def get_bottom_toolbar(session_state):
    """Create a bottom toolbar showing auto-approve status."""
    def toolbar():
        if session_state.auto_approve:
            return HTML('<style fg="#10b981">auto-accept ON (CTRL+T to toggle)</style>')
        return HTML('<style fg="#f59e0b">manual accept (CTRL+T to toggle)</style>')
    return toolbar


def create_prompt_session(session_state) -> PromptSession:
    """
    Create a PromptSession with all advanced features:
    - File path autocomplete (@filename)
    - Command autocomplete (/commands)
    - Bash command autocomplete (!commands)
    - Multiline input (Alt+Enter for newline, Enter to submit)
    - External editor (Ctrl+E)
    - Auto-approve toggle (Ctrl+T)
    - Bottom toolbar showing status

    Args:
        session_state: SessionState instance for auto-approve tracking

    Returns:
        Configured PromptSession
    """
    kb = KeyBindings()

    # Ctrl+T to toggle auto-approve
    @kb.add("c-t")
    def toggle_auto_approve(event):
        """Toggle auto-approve mode."""
        new_state = session_state.toggle_auto_approve()
        # Update the app to show new toolbar
        event.app.invalidate()

    # Enter to submit (unless completing)
    @kb.add("enter")
    def submit_or_complete(event):
        """Submit input or apply completion."""
        buffer = event.current_buffer

        # If completing, apply the completion
        if buffer.complete_state:
            current = buffer.complete_state.current_completion
            if not current and buffer.complete_state.completions:
                # Move to first completion
                buffer.complete_next()
                buffer.apply_completion(buffer.complete_state.current_completion)
            elif current:
                buffer.apply_completion(current)
        # Otherwise, submit if not empty
        elif buffer.text.strip():
            buffer.validate_and_handle()

    # Alt+Enter for newlines
    @kb.add("escape", "enter")
    def insert_newline(event):
        """Insert a newline character."""
        event.current_buffer.insert_text("\n")

    # Ctrl+E for external editor
    @kb.add("c-e")
    def open_editor(event):
        """Open in external editor (nano by default)."""
        event.current_buffer.open_in_editor()

    # Create merged completer
    completer = merge_completers([
        CommandCompleter(),
        BashCompleter(),
        FilePathCompleter(),
    ])

    return PromptSession(
        message=HTML(f'<style fg="{COLORS["primary"]}">></style> '),
        multiline=True,
        key_bindings=kb,
        completer=completer,
        complete_while_typing=True,
        enable_open_in_editor=True,
        bottom_toolbar=get_bottom_toolbar(session_state),
    )
