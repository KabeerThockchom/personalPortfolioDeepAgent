"""Chat management endpoints."""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional

from api.models import (
    ChatCreate,
    ChatUpdate,
    ChatResponse,
    ChatListResponse,
    ChatHistoryResponse,
)
from api.services.chat_service import (
    create_new_chat,
    get_chat_data,
    update_chat_data,
    delete_chat_data,
    list_all_chats,
    search_chats_by_query,
    get_full_chat_history,
    clear_chat_history,
)


router = APIRouter(prefix="/chat", tags=["Chat Management"])


@router.post("/new", response_model=ChatResponse)
async def create_chat(request: ChatCreate):
    """Create a new chat."""
    chat = create_new_chat(
        title=request.title,
        load_portfolio=request.load_portfolio
    )
    return chat


@router.get("/{chat_id}", response_model=ChatHistoryResponse)
async def get_chat(chat_id: str):
    """Get chat history with all messages."""
    chat = get_full_chat_history(chat_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    return chat


@router.put("/{chat_id}", response_model=ChatResponse)
async def update_chat(chat_id: str, request: ChatUpdate):
    """Update chat metadata (title, pinned, archived)."""
    chat = update_chat_data(
        chat_id=chat_id,
        title=request.title,
        pinned=request.pinned,
        archived=request.archived
    )
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    return chat


@router.delete("/{chat_id}")
async def remove_chat(chat_id: str):
    """Delete a chat and all its messages."""
    success = delete_chat_data(chat_id)
    if not success:
        raise HTTPException(status_code=404, detail="Chat not found")
    return {"success": True, "message": "Chat deleted successfully"}


@router.delete("/{chat_id}/messages")
async def clear_messages(chat_id: str):
    """Clear all messages from a chat."""
    count = clear_chat_history(chat_id)
    return {"success": True, "deleted_count": count}


@router.get("/", response_model=ChatListResponse)
async def list_chats(
    archived: bool = Query(False, description="Show archived chats"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0)
):
    """List all chats with pagination."""
    chats, total = list_all_chats(archived=archived, limit=limit, offset=offset)
    return {"chats": chats, "total": total}


@router.get("/search/", response_model=ChatListResponse)
async def search_chats(
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(50, ge=1, le=200)
):
    """Search chats by title or content."""
    chats = search_chats_by_query(q, limit=limit)
    return {"chats": chats, "total": len(chats)}
