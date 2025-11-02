"""Database setup and models for chat storage."""

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

# Database file location
DB_PATH = Path(__file__).parent.parent / "chat_history.db"


def init_db():
    """Initialize the database with required tables."""
    with get_db() as conn:
        cursor = conn.cursor()

        # Chats table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chats (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                pinned BOOLEAN DEFAULT FALSE,
                archived BOOLEAN DEFAULT FALSE,
                session_id TEXT,
                metadata TEXT
            )
        """)

        # Messages table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id TEXT PRIMARY KEY,
                chat_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                tool_calls TEXT,
                tool_results TEXT,
                metadata TEXT,
                FOREIGN KEY (chat_id) REFERENCES chats(id) ON DELETE CASCADE
            )
        """)

        # Create indexes for better query performance
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_messages_chat_id
            ON messages(chat_id)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_chats_updated_at
            ON chats(updated_at DESC)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_chats_archived
            ON chats(archived)
        """)

        conn.commit()


@contextmanager
def get_db():
    """Get database connection context manager."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row  # Access columns by name
    try:
        yield conn
    finally:
        conn.close()


# ============================================================================
# Chat Operations
# ============================================================================

def create_chat(chat_id: str, title: str, session_id: str) -> Dict[str, Any]:
    """Create a new chat."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO chats (id, title, session_id)
            VALUES (?, ?, ?)
        """, (chat_id, title, session_id))
        conn.commit()

        return get_chat(chat_id)


def get_chat(chat_id: str) -> Optional[Dict[str, Any]]:
    """Get a chat by ID."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT c.*,
                   COUNT(m.id) as message_count,
                   (SELECT content FROM messages
                    WHERE chat_id = c.id
                    ORDER BY created_at DESC
                    LIMIT 1) as preview
            FROM chats c
            LEFT JOIN messages m ON c.id = m.chat_id
            WHERE c.id = ?
            GROUP BY c.id
        """, (chat_id,))

        row = cursor.fetchone()
        if not row:
            return None

        return dict(row)


def update_chat(chat_id: str, **kwargs) -> Optional[Dict[str, Any]]:
    """Update a chat."""
    allowed_fields = ["title", "pinned", "archived"]
    updates = {k: v for k, v in kwargs.items() if k in allowed_fields and v is not None}

    if not updates:
        return get_chat(chat_id)

    # Add updated_at
    updates["updated_at"] = datetime.now().isoformat()

    set_clause = ", ".join(f"{k} = ?" for k in updates.keys())
    values = list(updates.values()) + [chat_id]

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(f"""
            UPDATE chats
            SET {set_clause}
            WHERE id = ?
        """, values)
        conn.commit()

    return get_chat(chat_id)


def delete_chat(chat_id: str) -> bool:
    """Delete a chat and all its messages."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM chats WHERE id = ?", (chat_id,))
        conn.commit()
        return cursor.rowcount > 0


def list_chats(
    archived: bool = False,
    limit: int = 100,
    offset: int = 0
) -> tuple[List[Dict[str, Any]], int]:
    """List all chats with pagination."""
    with get_db() as conn:
        cursor = conn.cursor()

        # Get total count
        cursor.execute("""
            SELECT COUNT(*) FROM chats WHERE archived = ?
        """, (archived,))
        total = cursor.fetchone()[0]

        # Get chats
        cursor.execute("""
            SELECT c.*,
                   COUNT(m.id) as message_count,
                   (SELECT content FROM messages
                    WHERE chat_id = c.id
                    ORDER BY created_at DESC
                    LIMIT 1) as preview
            FROM chats c
            LEFT JOIN messages m ON c.id = m.chat_id
            WHERE c.archived = ?
            GROUP BY c.id
            ORDER BY c.pinned DESC, c.updated_at DESC
            LIMIT ? OFFSET ?
        """, (archived, limit, offset))

        chats = [dict(row) for row in cursor.fetchall()]

        return chats, total


def search_chats(query: str, limit: int = 50) -> List[Dict[str, Any]]:
    """Search chats by title or message content."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT DISTINCT c.*,
                   COUNT(m.id) as message_count
            FROM chats c
            LEFT JOIN messages m ON c.id = m.chat_id
            WHERE c.title LIKE ? OR m.content LIKE ?
            GROUP BY c.id
            ORDER BY c.updated_at DESC
            LIMIT ?
        """, (f"%{query}%", f"%{query}%", limit))

        return [dict(row) for row in cursor.fetchall()]


# ============================================================================
# Message Operations
# ============================================================================

def add_message(
    message_id: str,
    chat_id: str,
    role: str,
    content: str,
    tool_calls: Optional[List[Dict]] = None,
    tool_results: Optional[List[Dict]] = None,
    metadata: Optional[Dict] = None
) -> Dict[str, Any]:
    """Add a message to a chat."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO messages (id, chat_id, role, content, tool_calls, tool_results, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            message_id,
            chat_id,
            role,
            content,
            json.dumps(tool_calls) if tool_calls else None,
            json.dumps(tool_results) if tool_results else None,
            json.dumps(metadata) if metadata else None
        ))

        # Update chat's updated_at
        cursor.execute("""
            UPDATE chats SET updated_at = CURRENT_TIMESTAMP WHERE id = ?
        """, (chat_id,))

        conn.commit()

        return get_message(message_id)


def get_message(message_id: str) -> Optional[Dict[str, Any]]:
    """Get a message by ID."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM messages WHERE id = ?
        """, (message_id,))

        row = cursor.fetchone()
        if not row:
            return None

        msg = dict(row)

        # Parse JSON fields
        if msg.get("tool_calls"):
            msg["tool_calls"] = json.loads(msg["tool_calls"])
        if msg.get("tool_results"):
            msg["tool_results"] = json.loads(msg["tool_results"])
        if msg.get("metadata"):
            msg["metadata"] = json.loads(msg["metadata"])

        return msg


def get_chat_messages(chat_id: str) -> List[Dict[str, Any]]:
    """Get all messages for a chat."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM messages
            WHERE chat_id = ?
            ORDER BY created_at ASC
        """, (chat_id,))

        messages = []
        for row in cursor.fetchall():
            msg = dict(row)

            # Parse JSON fields
            if msg.get("tool_calls"):
                msg["tool_calls"] = json.loads(msg["tool_calls"])
            if msg.get("tool_results"):
                msg["tool_results"] = json.loads(msg["tool_results"])
            if msg.get("metadata"):
                msg["metadata"] = json.loads(msg["metadata"])

            messages.append(msg)

        return messages


def delete_message(message_id: str) -> bool:
    """Delete a message."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM messages WHERE id = ?", (message_id,))
        conn.commit()
        return cursor.rowcount > 0


def delete_chat_messages(chat_id: str) -> int:
    """Delete all messages for a chat."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM messages WHERE chat_id = ?", (chat_id,))
        conn.commit()
        return cursor.rowcount


# Initialize database on import
init_db()
