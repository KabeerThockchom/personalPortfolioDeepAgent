"""File operation tracking with diffs and metrics."""

from dataclasses import dataclass, field
from pathlib import Path
import difflib


@dataclass
class FileOpMetrics:
    """Line and byte metrics for file operations."""
    lines_read: int = 0
    start_line: int | None = None
    end_line: int | None = None
    lines_written: int = 0
    lines_added: int = 0
    lines_removed: int = 0
    bytes_written: int = 0


@dataclass
class FileOperationRecord:
    """Track a single filesystem tool call."""
    tool_name: str
    display_path: str
    physical_path: Path | None
    tool_call_id: str | None
    args: dict = field(default_factory=dict)
    status: str = "pending"  # pending, success, error
    error: str | None = None
    metrics: FileOpMetrics = field(default_factory=FileOpMetrics)
    diff: str | None = None
    before_content: str | None = None
    after_content: str | None = None


def compute_unified_diff(before: str, after: str, display_path: str, max_lines: int = 800):
    """
    Compute unified diff between before/after content.

    Args:
        before: Content before change
        after: Content after change
        display_path: Path to display in diff header
        max_lines: Maximum diff lines before truncating

    Returns:
        Unified diff string or None if no changes
    """
    before_lines = before.splitlines()
    after_lines = after.splitlines()

    diff_lines = list(difflib.unified_diff(
        before_lines,
        after_lines,
        fromfile=f"{display_path} (before)",
        tofile=f"{display_path} (after)",
        lineterm="",
    ))

    if not diff_lines:
        return None

    if max_lines and len(diff_lines) > max_lines:
        truncated = diff_lines[:max_lines - 1]
        truncated.append("... (diff truncated)")
        return "\n".join(truncated)

    return "\n".join(diff_lines)


class FileOpTracker:
    """Track file operations during chat session."""

    def __init__(self, assistant_id: str | None = None):
        self.assistant_id = assistant_id
        self.active: dict[str, FileOperationRecord] = {}
        self.completed: list[FileOperationRecord] = []

    def start_operation(self, tool_name: str, args: dict, tool_call_id: str):
        """Start tracking a file operation."""
        if tool_name not in {"read_file", "write_file", "edit_file"}:
            return

        path_str = args.get("file_path") or args.get("path", "")
        path = Path(path_str)

        record = FileOperationRecord(
            tool_name=tool_name,
            display_path=path.name,
            physical_path=path.resolve() if path.exists() else path,
            tool_call_id=tool_call_id,
            args=args,
        )

        # Capture before content for write/edit
        if tool_name in {"write_file", "edit_file"} and record.physical_path.exists():
            try:
                record.before_content = record.physical_path.read_text()
            except:
                record.before_content = ""

        self.active[tool_call_id] = record

    def complete_with_message(self, tool_message):
        """
        Complete tracking when tool result arrives.

        Args:
            tool_message: ToolMessage instance

        Returns:
            FileOperationRecord or None
        """
        tool_call_id = getattr(tool_message, "tool_call_id", None)
        record = self.active.get(tool_call_id)
        if not record:
            return None

        # Check for errors
        content = tool_message.content
        status = getattr(tool_message, "status", "success")
        if status != "success" or (isinstance(content, str) and content.lower().startswith("error")):
            record.status = "error"
            record.error = str(content)
            self._finalize(record)
            return record

        record.status = "success"

        if record.tool_name == "read_file":
            record.metrics.lines_read = len(str(content).splitlines())
        else:
            # Capture after content
            try:
                record.after_content = record.physical_path.read_text()
                record.metrics.lines_written = len(record.after_content.splitlines())
                record.metrics.bytes_written = len(record.after_content.encode("utf-8"))

                # Generate diff
                record.diff = compute_unified_diff(
                    record.before_content or "",
                    record.after_content,
                    record.display_path
                )

                # Count additions/removals
                if record.diff:
                    additions = sum(1 for line in record.diff.splitlines()
                                  if line.startswith("+") and not line.startswith("+++"))
                    removals = sum(1 for line in record.diff.splitlines()
                                 if line.startswith("-") and not line.startswith("---"))
                    record.metrics.lines_added = additions
                    record.metrics.lines_removed = removals
            except:
                record.status = "error"
                record.error = "Could not read updated file content"

        self._finalize(record)
        return record

    def _finalize(self, record: FileOperationRecord):
        """Move record from active to completed."""
        self.completed.append(record)
        self.active.pop(record.tool_call_id, None)
