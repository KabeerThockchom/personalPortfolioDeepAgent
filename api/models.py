"""Pydantic models for API requests and responses."""

from datetime import datetime
from typing import Any, Dict, List, Optional, Literal
from pydantic import BaseModel, Field


# ============================================================================
# Chat Models
# ============================================================================

class ChatCreate(BaseModel):
    """Request to create a new chat."""
    title: Optional[str] = None
    load_portfolio: bool = True


class ChatUpdate(BaseModel):
    """Request to update a chat."""
    title: Optional[str] = None
    pinned: Optional[bool] = None
    archived: Optional[bool] = None


class ChatResponse(BaseModel):
    """Chat metadata response."""
    id: str
    title: str
    created_at: datetime
    updated_at: datetime
    message_count: int
    pinned: bool
    archived: bool
    preview: Optional[str] = None


class ChatListResponse(BaseModel):
    """List of chats response."""
    chats: List[ChatResponse]
    total: int


# ============================================================================
# Message Models
# ============================================================================

class MessageRole(str):
    """Message role types."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"


class ToolCall(BaseModel):
    """Tool call information."""
    id: str
    name: str
    args: Dict[str, Any]


class ToolResult(BaseModel):
    """Tool execution result."""
    tool_call_id: str
    name: str
    result: Any
    success: bool
    error: Optional[str] = None


class Message(BaseModel):
    """Chat message."""
    id: str
    role: Literal["user", "assistant", "system", "tool"]
    content: str
    created_at: datetime
    tool_calls: Optional[List[ToolCall]] = None
    tool_results: Optional[List[ToolResult]] = None
    metadata: Optional[Dict[str, Any]] = None


class MessageCreate(BaseModel):
    """Request to send a message."""
    content: str
    chat_id: str


class MessageResponse(BaseModel):
    """Message response."""
    message: Message


class ChatHistoryResponse(BaseModel):
    """Full chat history response."""
    chat_id: str
    messages: List[Message]
    files: Dict[str, str]
    todos: List[Dict[str, Any]]


# ============================================================================
# Streaming Event Models
# ============================================================================

class StreamEventType(str):
    """Streaming event types."""
    START = "start"
    STEP = "step"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    MESSAGE = "message"
    TODO_UPDATE = "todo_update"
    FILE_UPDATE = "file_update"
    APPROVAL_REQUEST = "approval_request"
    COMPLETE = "complete"
    ERROR = "error"


class StreamEvent(BaseModel):
    """Base streaming event."""
    type: str
    data: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.now)


class StartEvent(BaseModel):
    """Execution started event."""
    type: Literal["start"] = "start"
    chat_id: str
    message_id: str
    timestamp: datetime = Field(default_factory=datetime.now)


class StepEvent(BaseModel):
    """Agent step event."""
    type: Literal["step"] = "step"
    step_number: int
    node_name: str
    friendly_name: str
    is_subagent: bool
    subagent_name: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)


class ToolCallEvent(BaseModel):
    """Tool call event."""
    type: Literal["tool_call"] = "tool_call"
    tool_call_id: str
    name: str
    args: Dict[str, Any]
    is_subagent: bool
    timestamp: datetime = Field(default_factory=datetime.now)


class ToolResultEvent(BaseModel):
    """Tool result event."""
    type: Literal["tool_result"] = "tool_result"
    tool_call_id: str
    name: str
    result: Any
    success: bool
    error: Optional[str] = None
    is_subagent: bool
    timestamp: datetime = Field(default_factory=datetime.now)


class MessageEvent(BaseModel):
    """Message update event."""
    type: Literal["message"] = "message"
    message: Message
    timestamp: datetime = Field(default_factory=datetime.now)


class TodoUpdateEvent(BaseModel):
    """Todo list update event."""
    type: Literal["todo_update"] = "todo_update"
    todos: List[Dict[str, Any]]
    timestamp: datetime = Field(default_factory=datetime.now)


class FileUpdateEvent(BaseModel):
    """File update event."""
    type: Literal["file_update"] = "file_update"
    files: List[str]
    timestamp: datetime = Field(default_factory=datetime.now)


class ApprovalRequest(BaseModel):
    """Approval request details."""
    action_request: Dict[str, Any]
    review_config: Dict[str, Any]


class ApprovalRequestEvent(BaseModel):
    """Approval request event."""
    type: Literal["approval_request"] = "approval_request"
    requests: List[ApprovalRequest]
    timestamp: datetime = Field(default_factory=datetime.now)


class CompleteEvent(BaseModel):
    """Execution complete event."""
    type: Literal["complete"] = "complete"
    message: Message
    timestamp: datetime = Field(default_factory=datetime.now)


class ErrorEvent(BaseModel):
    """Error event."""
    type: Literal["error"] = "error"
    error: str
    details: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)


# ============================================================================
# Approval Models
# ============================================================================

class ApprovalDecision(BaseModel):
    """User's approval decision."""
    type: Literal["approve", "reject", "edit"]
    modified_args: Optional[Dict[str, Any]] = None


class ApprovalResponse(BaseModel):
    """Response to approval request."""
    decisions: List[ApprovalDecision]


# ============================================================================
# File Models
# ============================================================================

class FileInfo(BaseModel):
    """File information."""
    path: str
    size: int
    modified: datetime
    is_directory: bool


class FileListResponse(BaseModel):
    """List of files response."""
    files: List[FileInfo]
    session_id: str


class FileContentResponse(BaseModel):
    """File content response."""
    path: str
    content: str
    size: int


# ============================================================================
# Settings Models
# ============================================================================

class AgentSettings(BaseModel):
    """Agent configuration settings."""
    model: str = "glm-4.6"
    temperature: float = 0.0
    max_tokens: Optional[int] = None
    enable_human_in_loop: bool = True


class UserSettings(BaseModel):
    """User preferences."""
    theme: Literal["light", "dark", "auto"] = "auto"
    auto_scroll: bool = True
    show_typing_indicators: bool = True
    collapse_tool_calls: bool = False
    enable_sound: bool = False
    agent_settings: AgentSettings = Field(default_factory=AgentSettings)
