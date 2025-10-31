"""
In-memory session management for chat conversations.
"""
import uuid
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage


@dataclass
class Session:
    """Chat session data."""
    session_id: str
    messages: List[BaseMessage] = field(default_factory=list)
    files: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)
    thread_id: str = None  # Thread ID for LangGraph checkpointing (matches session_id)
    pending_interrupts: Optional[List[Any]] = field(default_factory=list)  # Pending approval requests

    def __post_init__(self):
        """Initialize thread_id to match session_id if not provided."""
        if self.thread_id is None:
            self.thread_id = self.session_id

    def update_activity(self):
        """Update last activity timestamp."""
        self.last_activity = datetime.now()

    def add_message(self, message: BaseMessage):
        """Add a message to the session."""
        self.messages.append(message)
        self.update_activity()

    def prune_history(self, max_turns: int = 5):
        """
        Prune conversation history to last N turns.

        A turn is one user message + one AI response.
        This prevents context from growing too large.
        """
        if len(self.messages) <= max_turns * 2:
            return

        # Keep only last N turns (N user + N AI messages)
        # Find the cutoff point
        user_messages = [i for i, msg in enumerate(self.messages) if isinstance(msg, HumanMessage)]

        if len(user_messages) > max_turns:
            # Keep from the (len - max_turns)th user message onwards
            cutoff_index = user_messages[len(user_messages) - max_turns]
            self.messages = self.messages[cutoff_index:]

    def get_state(self) -> Dict[str, Any]:
        """Get current session state for agent."""
        return {
            "messages": self.messages,
            "files": self.files
        }

    def get_config(self) -> Dict[str, Any]:
        """Get LangGraph config with thread_id for checkpointing."""
        return {
            "configurable": {
                "thread_id": self.thread_id
            }
        }

    def update_files(self, new_files: Dict[str, Any]):
        """Merge new files into session files."""
        self.files.update(new_files)


class SessionManager:
    """Manage chat sessions in memory."""

    def __init__(self, session_timeout_hours: int = 24):
        self.sessions: Dict[str, Session] = {}
        self.session_timeout = timedelta(hours=session_timeout_hours)

    def create_session(self) -> str:
        """Create a new session and return its ID."""
        session_id = str(uuid.uuid4())
        new_session = Session(session_id=session_id)
        # Seed known files so tools like glob/ls can discover them
        try:
            import os
            portfolio_path = "portfolio.json"
            if os.path.exists(portfolio_path):
                with open(portfolio_path, "r") as f:
                    content = f.read()
                # Map to the agent-visible path
                new_session.files["/financial_data/portfolio.json"] = {
                    "content": content,
                }
        except Exception:
            # Best-effort seeding; continue even if it fails
            pass
        self.sessions[session_id] = new_session
        return session_id

    def get_session(self, session_id: Optional[str] = None) -> Session:
        """
        Get a session by ID, or create a new one if ID is None or not found.

        Also cleans up expired sessions.
        """
        # Clean up expired sessions
        self._cleanup_expired_sessions()

        # If no session ID provided, create new session
        if not session_id:
            new_id = self.create_session()
            return self.sessions[new_id]

        # If session exists, return it
        if session_id in self.sessions:
            session = self.sessions[session_id]
            session.update_activity()
            return session

        # Session not found, create new one with the provided ID
        self.sessions[session_id] = Session(session_id=session_id)
        return self.sessions[session_id]

    def clear_session(self, session_id: str) -> bool:
        """Clear a session's conversation history."""
        if session_id in self.sessions:
            session = self.sessions[session_id]
            session.messages = []
            session.files = {}
            session.pending_interrupts = []
            session.update_activity()
            return True
        return False

    def delete_session(self, session_id: str) -> bool:
        """Delete a session entirely."""
        if session_id in self.sessions:
            del self.sessions[session_id]
            return True
        return False

    def _cleanup_expired_sessions(self):
        """Remove sessions that haven't been active within the timeout period."""
        now = datetime.now()
        expired = [
            sid for sid, session in self.sessions.items()
            if now - session.last_activity > self.session_timeout
        ]
        for sid in expired:
            del self.sessions[sid]

    def get_all_sessions(self) -> List[Dict[str, Any]]:
        """Get metadata for all active sessions."""
        self._cleanup_expired_sessions()
        return [
            {
                "session_id": session.session_id,
                "message_count": len(session.messages),
                "created_at": session.created_at.isoformat(),
                "last_activity": session.last_activity.isoformat()
            }
            for session in self.sessions.values()
        ]


# Global session manager instance
session_manager = SessionManager()
