"""FastAPI server for Personal Finance Deep Agent chat interface."""

import asyncio
import json
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List

from api.websocket import manager
from api.routes import chat, files
from api.services.agent_service import execute_agent_stream, handle_approval_response
from api.models import ApprovalDecision, ApprovalResponse
from api.database import init_db


# ============================================================================
# App Lifespan
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """App lifespan manager for startup/shutdown."""
    # Startup
    print("🚀 Starting FastAPI server...")
    init_db()
    print("✓ Database initialized")

    yield

    # Shutdown
    print("👋 Shutting down...")


# ============================================================================
# FastAPI App
# ============================================================================

app = FastAPI(
    title="Personal Finance Deep Agent API",
    description="Backend API for chat interface with WebSocket streaming",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware (configure for your frontend domain)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",      # Next.js dev
        "http://localhost:5173",      # Vite dev
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# Include Routers
# ============================================================================

app.include_router(chat.router, prefix="/api")
app.include_router(files.router, prefix="/api")


# ============================================================================
# WebSocket Endpoints
# ============================================================================

class MessageRequest(BaseModel):
    """WebSocket message request."""
    type: str
    data: dict


@app.websocket("/ws/{chat_id}")
async def websocket_endpoint(websocket: WebSocket, chat_id: str):
    """
    WebSocket endpoint for real-time agent streaming.

    Message types (client -> server):
    - {"type": "message", "data": {"content": "user message", "session_id": "..."}}
    - {"type": "approval_response", "data": {"decisions": [...]}}
    - {"type": "ping"}

    Message types (server -> client):
    - start, step, tool_call, tool_result, message, todo_update, file_update
    - approval_request, complete, error
    """
    await manager.connect(websocket, chat_id)

    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()

            try:
                request = json.loads(data)
                msg_type = request.get("type")
                msg_data = request.get("data", {})

                if msg_type == "message":
                    # Execute agent with streaming
                    content = msg_data.get("content")
                    session_id = msg_data.get("session_id")
                    enable_hitl = msg_data.get("enable_hitl", True)

                    if not content or not session_id:
                        await websocket.send_json({
                            "type": "error",
                            "data": {"error": "Missing content or session_id"}
                        })
                        continue

                    # Run agent execution in background
                    try:
                        await execute_agent_stream(
                            chat_id=chat_id,
                            user_message=content,
                            session_id=session_id,
                            enable_hitl=enable_hitl
                        )
                    except Exception as e:
                        await websocket.send_json({
                            "type": "error",
                            "data": {"error": str(e)}
                        })

                elif msg_type == "approval_response":
                    # Handle approval response
                    decisions = msg_data.get("decisions", [])
                    handle_approval_response(chat_id, decisions)

                elif msg_type == "ping":
                    # Respond to ping
                    await websocket.send_json({"type": "pong"})

                else:
                    await websocket.send_json({
                        "type": "error",
                        "data": {"error": f"Unknown message type: {msg_type}"}
                    })

            except json.JSONDecodeError:
                await websocket.send_json({
                    "type": "error",
                    "data": {"error": "Invalid JSON"}
                })

    except WebSocketDisconnect:
        manager.disconnect(websocket)
        print(f"Client disconnected from chat {chat_id[:8]}...")


# ============================================================================
# REST Endpoints
# ============================================================================

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "Personal Finance Deep Agent API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "websocket": "/ws/{chat_id}",
            "chat": "/api/chat/*",
            "files": "/api/files/*"
        }
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.post("/api/approval/respond")
async def approval_respond(chat_id: str, response: ApprovalResponse):
    """
    Respond to an approval request (alternative to WebSocket).

    This endpoint can be used if the client prefers REST API for approvals.
    """
    try:
        decisions = [decision.dict() for decision in response.decisions]
        handle_approval_response(chat_id, decisions)
        return {"success": True, "message": "Approval response submitted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Run Server
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║  Personal Finance Deep Agent - Backend API                   ║
    ╚══════════════════════════════════════════════════════════════╝

    🚀 Starting server...

    📡 WebSocket endpoint: ws://localhost:8000/ws/{chat_id}
    🔗 REST API docs: http://localhost:8000/docs
    🔗 Alternative docs: http://localhost:8000/redoc

    Press CTRL+C to quit
    """)

    uvicorn.run(
        "api.server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Auto-reload on code changes
        log_level="info"
    )
