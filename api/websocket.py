"""WebSocket connection manager for real-time agent streaming."""

import asyncio
import json
from typing import Dict, Set
from fastapi import WebSocket
from datetime import datetime


class ConnectionManager:
    """Manages WebSocket connections for real-time streaming."""

    def __init__(self):
        # Map of chat_id -> set of WebSocket connections
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        # Map of connection -> chat_id for cleanup
        self.connection_to_chat: Dict[WebSocket, str] = {}

    async def connect(self, websocket: WebSocket, chat_id: str):
        """Accept a new WebSocket connection."""
        await websocket.accept()

        if chat_id not in self.active_connections:
            self.active_connections[chat_id] = set()

        self.active_connections[chat_id].add(websocket)
        self.connection_to_chat[websocket] = chat_id

        print(f"✓ WebSocket connected for chat {chat_id[:8]}... (total: {len(self.active_connections[chat_id])})")

    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection."""
        chat_id = self.connection_to_chat.get(websocket)
        if chat_id and chat_id in self.active_connections:
            self.active_connections[chat_id].discard(websocket)

            if not self.active_connections[chat_id]:
                del self.active_connections[chat_id]

            print(f"✗ WebSocket disconnected for chat {chat_id[:8]}...")

        self.connection_to_chat.pop(websocket, None)

    async def send_to_chat(self, chat_id: str, message: dict):
        """Send a message to all connections for a specific chat."""
        if chat_id not in self.active_connections:
            return

        # Add timestamp if not present
        if "timestamp" not in message:
            message["timestamp"] = datetime.now().isoformat()

        # Convert to JSON
        json_message = json.dumps(message, default=str)

        # Send to all connections for this chat
        disconnected = set()
        for connection in self.active_connections[chat_id]:
            try:
                await connection.send_text(json_message)
            except Exception as e:
                print(f"Error sending to WebSocket: {e}")
                disconnected.add(connection)

        # Clean up disconnected clients
        for connection in disconnected:
            self.disconnect(connection)

    async def broadcast_to_chat(self, chat_id: str, event_type: str, data: dict):
        """Broadcast an event to all connections for a chat."""
        event = {
            "type": event_type,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
        await self.send_to_chat(chat_id, event)

    def get_connection_count(self, chat_id: str) -> int:
        """Get the number of active connections for a chat."""
        return len(self.active_connections.get(chat_id, set()))

    def is_chat_connected(self, chat_id: str) -> bool:
        """Check if any connections exist for a chat."""
        return chat_id in self.active_connections and len(self.active_connections[chat_id]) > 0


# Global connection manager instance
manager = ConnectionManager()


# ============================================================================
# Event Helpers
# ============================================================================

async def send_start_event(chat_id: str, message_id: str):
    """Send execution start event."""
    await manager.broadcast_to_chat(chat_id, "start", {
        "chat_id": chat_id,
        "message_id": message_id
    })


async def send_step_event(
    chat_id: str,
    step_number: int,
    node_name: str,
    friendly_name: str,
    is_subagent: bool = False,
    subagent_name: str = None
):
    """Send agent step event."""
    await manager.broadcast_to_chat(chat_id, "step", {
        "step_number": step_number,
        "node_name": node_name,
        "friendly_name": friendly_name,
        "is_subagent": is_subagent,
        "subagent_name": subagent_name
    })


async def send_tool_call_event(
    chat_id: str,
    tool_call_id: str,
    name: str,
    args: dict,
    is_subagent: bool = False
):
    """Send tool call event."""
    await manager.broadcast_to_chat(chat_id, "tool_call", {
        "tool_call_id": tool_call_id,
        "name": name,
        "args": args,
        "is_subagent": is_subagent
    })


async def send_tool_result_event(
    chat_id: str,
    tool_call_id: str,
    name: str,
    result: any,
    success: bool = True,
    error: str = None,
    is_subagent: bool = False
):
    """Send tool result event."""
    await manager.broadcast_to_chat(chat_id, "tool_result", {
        "tool_call_id": tool_call_id,
        "name": name,
        "result": result,
        "success": success,
        "error": error,
        "is_subagent": is_subagent
    })


async def send_message_event(chat_id: str, message: dict):
    """Send message update event."""
    await manager.broadcast_to_chat(chat_id, "message", {
        "message": message
    })


async def send_todo_update_event(chat_id: str, todos: list):
    """Send todo list update event."""
    await manager.broadcast_to_chat(chat_id, "todo_update", {
        "todos": todos
    })


async def send_file_update_event(chat_id: str, files: list):
    """Send file update event."""
    await manager.broadcast_to_chat(chat_id, "file_update", {
        "files": files
    })


async def send_approval_request_event(chat_id: str, requests: list):
    """Send approval request event."""
    await manager.broadcast_to_chat(chat_id, "approval_request", {
        "requests": requests
    })


async def send_complete_event(chat_id: str, message: dict):
    """Send execution complete event."""
    await manager.broadcast_to_chat(chat_id, "complete", {
        "message": message
    })


async def send_error_event(chat_id: str, error: str, details: str = None):
    """Send error event."""
    await manager.broadcast_to_chat(chat_id, "error", {
        "error": error,
        "details": details
    })
