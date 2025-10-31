"""
Parse LangGraph stream chunks into frontend-friendly events.
"""
import time
from typing import Any, Dict, List, Iterator, AsyncIterator
from langchain_core.messages import AIMessage, ToolMessage

from api.models import (
    AgentEvent,
    ThinkingEvent,
    ToolCallEvent,
    ToolResultEvent,
    FileUpdateEvent,
    TodoUpdateEvent,
    MessageEvent,
    SubagentSpawnEvent,
    SubagentCompleteEvent,
    CompleteEvent,
)


class EventParser:
    """Parse LangGraph stream chunks into structured events."""

    def __init__(self):
        self.active_subagents: Dict[str, str] = {}  # subagent_name -> node_name
        self.completed_subagents: set = set()

    def parse_chunk(self, chunk: Dict[str, Any]) -> List[AgentEvent]:
        """
        Parse a single LangGraph stream chunk into events.

        Chunk format: {node_name: state_update}
        State update contains: messages, files, todos, etc.
        """
        events = []

        # Some frameworks may yield None or non-dict values between updates
        if not isinstance(chunk, dict):
            return events

        for node_name, state_update in chunk.items():
            # Some stream chunks may emit None or non-dict values; skip safely
            if not isinstance(state_update, dict):
                continue
            # Emit thinking event for this node
            events.append(ThinkingEvent(
                node=node_name,
                timestamp=time.time()
            ))

            # Check if this is a subagent node
            if node_name.startswith("task:"):
                subagent_name = node_name.split(":", 1)[1]
                if subagent_name not in self.active_subagents:
                    # Subagent just spawned (first time seeing this node)
                    self.active_subagents[subagent_name] = node_name

            # Parse messages for tool calls and results
            messages = state_update.get("messages") or []
            for msg in messages:
                    events.extend(self._parse_message(msg, node_name))

            # Parse file updates
            files = state_update.get("files")
            if isinstance(files, dict):
                file_paths = list(files.keys())
                if file_paths:
                    events.append(FileUpdateEvent(
                        paths=file_paths,
                        timestamp=time.time()
                    ))

            # Parse TODO updates
            todos = state_update.get("todos")
            if isinstance(todos, list):
                events.append(TodoUpdateEvent(
                    todos=todos,
                    timestamp=time.time()
                ))

        return events

    def _parse_message(self, msg: Any, node_name: str) -> List[AgentEvent]:
        """Parse a LangChain message into events."""
        events = []

        # AIMessage with tool calls
        if isinstance(msg, AIMessage):
            # Extract tool calls
            if hasattr(msg, "tool_calls") and msg.tool_calls:
                for tool_call in msg.tool_calls:
                    tool_name = tool_call.get("name", "")
                    tool_args = tool_call.get("args", {})
                    tool_call_id = tool_call.get("id", "")

                    # Check if this is a subagent spawn
                    is_subagent = tool_name == "task"
                    subagent_name = None

                    if is_subagent:
                        subagent_name = tool_args.get("subagent_type", "")
                        description = tool_args.get("description", "")

                        # Emit subagent spawn event
                        events.append(SubagentSpawnEvent(
                            name=subagent_name,
                            description=description,
                            status="spawning",
                            timestamp=time.time()
                        ))

                    # Emit tool call event
                    events.append(ToolCallEvent(
                        tool_name=tool_name,
                        args=tool_args,
                        tool_call_id=tool_call_id,
                        is_subagent_spawn=is_subagent,
                        subagent_name=subagent_name,
                        timestamp=time.time()
                    ))

            # Extract content (if final message without tool calls)
            if msg.content and not (hasattr(msg, "tool_calls") and msg.tool_calls):
                events.append(MessageEvent(
                    content=msg.content,
                    timestamp=time.time()
                ))

        # ToolMessage with results
        elif isinstance(msg, ToolMessage):
            tool_name = getattr(msg, "name", "unknown")
            content = msg.content if isinstance(msg.content, str) else str(msg.content)
            tool_call_id = getattr(msg, "tool_call_id", "")

            # Truncate large results
            if len(content) > 1000:
                content = content[:1000] + f"... ({len(content)} characters total)"

            events.append(ToolResultEvent(
                tool_name=tool_name,
                result=content,
                tool_call_id=tool_call_id,
                timestamp=time.time()
            ))

        return events

    def finalize(self) -> List[AgentEvent]:
        """
        Generate final events (e.g., mark subagents as complete).
        Call this after stream ends.
        """
        events = []

        # Mark all active subagents as completed
        for subagent_name in self.active_subagents:
            if subagent_name not in self.completed_subagents:
                events.append(SubagentCompleteEvent(
                    name=subagent_name,
                    timestamp=time.time()
                ))
                self.completed_subagents.add(subagent_name)

        # Emit completion event
        events.append(CompleteEvent(timestamp=time.time()))

        return events


def parse_stream_to_events(stream: Iterator[Dict[str, Any]]) -> Iterator[AgentEvent]:
    """
    Parse LangGraph stream into events (synchronous version).

    Args:
        stream: Iterator of LangGraph chunks

    Yields:
        AgentEvent objects
    """
    parser = EventParser()

    try:
        for chunk in stream:
            events = parser.parse_chunk(chunk)
            for event in events:
                yield event
    finally:
        # Emit final events
        final_events = parser.finalize()
        for event in final_events:
            yield event


# Note: Async parsing is now handled directly in agent_service.py
# using per-session parser instances to avoid concurrency issues
