"""
Pydantic models for API requests and responses.
"""
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel


class ChatMessage(BaseModel):
    """User message sent to the agent."""
    content: str
    session_id: Optional[str] = None


class AgentEvent(BaseModel):
    """Base event emitted during agent execution."""
    type: str
    timestamp: float


class ThinkingEvent(AgentEvent):
    """Agent is processing/thinking."""
    type: Literal["thinking"] = "thinking"
    node: str


class ToolCallEvent(AgentEvent):
    """Tool is being called."""
    type: Literal["tool_call"] = "tool_call"
    tool_name: str
    args: Dict[str, Any]
    tool_call_id: str
    is_subagent_spawn: bool = False
    subagent_name: Optional[str] = None


class ToolResultEvent(AgentEvent):
    """Tool execution result."""
    type: Literal["tool_result"] = "tool_result"
    tool_name: str
    result: str
    tool_call_id: str
    success: bool = True


class FileUpdateEvent(AgentEvent):
    """File was created or updated."""
    type: Literal["file_update"] = "file_update"
    paths: List[str]
    action: Literal["created", "updated"] = "updated"


class TodoUpdateEvent(AgentEvent):
    """TODO list was updated."""
    type: Literal["todo_update"] = "todo_update"
    todos: List[Dict[str, str]]


class MessageEvent(AgentEvent):
    """Agent sent a message."""
    type: Literal["message"] = "message"
    role: Literal["assistant"] = "assistant"
    content: str


class SubagentSpawnEvent(AgentEvent):
    """Subagent was spawned."""
    type: Literal["subagent_spawn"] = "subagent_spawn"
    name: str
    description: str
    status: Literal["spawning", "active", "completed"] = "spawning"


class SubagentCompleteEvent(AgentEvent):
    """Subagent completed execution."""
    type: Literal["subagent_complete"] = "subagent_complete"
    name: str


class CompleteEvent(AgentEvent):
    """Agent execution completed."""
    type: Literal["complete"] = "complete"


class ErrorEvent(AgentEvent):
    """Error occurred during execution."""
    type: Literal["error"] = "error"
    error: str
    details: Optional[str] = None


class PortfolioResponse(BaseModel):
    """Portfolio data response."""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class TradeRequest(BaseModel):
    """Request to execute a trade."""
    action: Literal["buy", "sell"]
    account_name: str
    ticker: str
    shares: float
    price: Optional[float] = None  # If not provided, will fetch current price


class TradeResponse(BaseModel):
    """Trade execution response."""
    success: bool
    message: str
    updated_holding: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class FileListResponse(BaseModel):
    """List of files in agent filesystem."""
    files: List[str]
    directories: Dict[str, List[str]]  # directory_path -> list of files


class FileContentResponse(BaseModel):
    """File content response."""
    success: bool
    path: str
    content: Optional[str] = None
    error: Optional[str] = None
