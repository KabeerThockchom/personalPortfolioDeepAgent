"""Chat management service."""

import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from pathlib import Path

from api.database import (
    create_chat,
    get_chat,
    update_chat,
    delete_chat,
    list_chats,
    search_chats,
    get_chat_messages,
    delete_chat_messages,
)
from deepagents.backends.utils import create_file_data


def generate_chat_title(first_message: str, max_length: int = 50) -> str:
    """Generate a chat title from the first message."""
    if not first_message:
        return "New Chat"

    # Take first sentence or first N characters
    title = first_message.strip()

    # Remove newlines
    title = title.replace('\n', ' ')

    # Truncate to max length
    if len(title) > max_length:
        title = title[:max_length].rsplit(' ', 1)[0] + "..."

    return title or "New Chat"


def load_portfolio_files() -> Dict[str, any]:
    """Load portfolio data as initial files for agent."""
    portfolio_path = Path(__file__).parent.parent.parent / "portfolio.json"

    try:
        with open(portfolio_path, "r") as f:
            portfolio = json.load(f)

        portfolio_json = json.dumps(portfolio, indent=2)

        files = {
            "/financial_data/kabeer_thockchom_portfolio.json": create_file_data(portfolio_json),
        }

        return files
    except FileNotFoundError:
        print(f"⚠️  Portfolio file not found at {portfolio_path}")
        return {}


# ============================================================================
# Chat Operations
# ============================================================================

def create_new_chat(title: Optional[str] = None, load_portfolio: bool = True) -> Dict:
    """
    Create a new chat.

    Args:
        title: Optional chat title (auto-generated from first message if None)
        load_portfolio: Whether to load portfolio.json into agent files

    Returns:
        Chat data
    """
    chat_id = str(uuid.uuid4())
    session_id = str(uuid.uuid4())

    # Default title
    if not title:
        title = "New Chat"

    # Create chat in database
    chat = create_chat(
        chat_id=chat_id,
        title=title,
        session_id=session_id
    )

    return {
        "id": chat["id"],
        "title": chat["title"],
        "session_id": chat["session_id"],
        "created_at": chat["created_at"],
        "updated_at": chat["updated_at"],
        "message_count": 0,
        "pinned": bool(chat["pinned"]),
        "archived": bool(chat["archived"]),
        "preview": None,
        "initial_files": load_portfolio_files() if load_portfolio else {}
    }


def get_chat_data(chat_id: str) -> Optional[Dict]:
    """Get chat by ID."""
    chat = get_chat(chat_id)
    if not chat:
        return None

    return {
        "id": chat["id"],
        "title": chat["title"],
        "session_id": chat["session_id"],
        "created_at": chat["created_at"],
        "updated_at": chat["updated_at"],
        "message_count": chat.get("message_count", 0),
        "pinned": bool(chat["pinned"]),
        "archived": bool(chat["archived"]),
        "preview": chat.get("preview"),
    }


def update_chat_data(
    chat_id: str,
    title: Optional[str] = None,
    pinned: Optional[bool] = None,
    archived: Optional[bool] = None
) -> Optional[Dict]:
    """Update chat metadata."""
    chat = update_chat(
        chat_id=chat_id,
        title=title,
        pinned=pinned,
        archived=archived
    )

    if not chat:
        return None

    return {
        "id": chat["id"],
        "title": chat["title"],
        "session_id": chat["session_id"],
        "created_at": chat["created_at"],
        "updated_at": chat["updated_at"],
        "message_count": chat.get("message_count", 0),
        "pinned": bool(chat["pinned"]),
        "archived": bool(chat["archived"]),
        "preview": chat.get("preview"),
    }


def delete_chat_data(chat_id: str) -> bool:
    """Delete a chat and all its messages."""
    return delete_chat(chat_id)


def list_all_chats(
    archived: bool = False,
    limit: int = 100,
    offset: int = 0
) -> Tuple[List[Dict], int]:
    """
    List all chats with pagination.

    Returns:
        Tuple of (chats list, total count)
    """
    chats, total = list_chats(archived=archived, limit=limit, offset=offset)

    formatted_chats = []
    for chat in chats:
        formatted_chats.append({
            "id": chat["id"],
            "title": chat["title"],
            "created_at": chat["created_at"],
            "updated_at": chat["updated_at"],
            "message_count": chat.get("message_count", 0),
            "pinned": bool(chat["pinned"]),
            "archived": bool(chat["archived"]),
            "preview": chat.get("preview"),
        })

    return formatted_chats, total


def search_chats_by_query(query: str, limit: int = 50) -> List[Dict]:
    """Search chats by title or content."""
    chats = search_chats(query, limit=limit)

    formatted_chats = []
    for chat in chats:
        formatted_chats.append({
            "id": chat["id"],
            "title": chat["title"],
            "created_at": chat["created_at"],
            "updated_at": chat["updated_at"],
            "message_count": chat.get("message_count", 0),
            "pinned": bool(chat["pinned"]),
            "archived": bool(chat["archived"]),
        })

    return formatted_chats


def clear_chat_history(chat_id: str) -> int:
    """Clear all messages from a chat."""
    return delete_chat_messages(chat_id)


# ============================================================================
# Message Operations
# ============================================================================

def get_full_chat_history(chat_id: str) -> Optional[Dict]:
    """Get complete chat history with messages."""
    chat = get_chat(chat_id)
    if not chat:
        return None

    messages = get_chat_messages(chat_id)

    formatted_messages = []
    for msg in messages:
        formatted_messages.append({
            "id": msg["id"],
            "role": msg["role"],
            "content": msg["content"],
            "created_at": msg["created_at"],
            "tool_calls": msg.get("tool_calls"),
            "tool_results": msg.get("tool_results"),
            "metadata": msg.get("metadata"),
        })

    return {
        "chat_id": chat["id"],
        "title": chat["title"],
        "session_id": chat["session_id"],
        "messages": formatted_messages,
        "files": {},  # Files are in agent filesystem
        "todos": [],  # Todos are in agent state
    }
