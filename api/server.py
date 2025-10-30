"""
FastAPI server for Personal Finance Deep Agent web interface.

Run with: uvicorn api.server:app --reload --port 8000
"""
import json
import os
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api.models import (
    ChatMessage,
    PortfolioResponse,
    TradeRequest,
    TradeResponse,
    FileListResponse,
    FileContentResponse,
)
from api.session_manager import session_manager
from api.agent_service import agent_service

# Create FastAPI app
app = FastAPI(
    title="Personal Finance Deep Agent API",
    description="WebSocket API for real-time financial agent interactions",
    version="1.0.0"
)

# Add CORS middleware for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],  # Vite default ports
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "Personal Finance Deep Agent API",
        "version": "1.0.0"
    }


@app.websocket("/api/chat")
async def websocket_chat(websocket: WebSocket, session_id: Optional[str] = Query(None)):
    """
    WebSocket endpoint for real-time agent chat.

    Query params:
        session_id: Optional session ID to continue a conversation

    Client sends: {"type": "message", "content": "user message"}
    Server sends: AgentEvent objects as JSON
    """
    await websocket.accept()

    # Get or create session
    session = session_manager.get_session(session_id)

    try:
        await websocket.send_json({
            "type": "connected",
            "session_id": session.session_id,
            "message": "Connected to agent"
        })

        while True:
            # Receive message from client
            data = await websocket.receive_json()

            if data.get("type") == "message":
                user_message = data.get("content", "")

                if not user_message.strip():
                    await websocket.send_json({
                        "type": "error",
                        "error": "Empty message"
                    })
                    continue

                # Stream agent response
                try:
                    for event in agent_service.stream_response(session, user_message):
                        # Send event as JSON
                        await websocket.send_json(event.model_dump())

                except Exception as e:
                    await websocket.send_json({
                        "type": "error",
                        "error": str(e),
                        "details": "Error during agent execution"
                    })

            elif data.get("type") == "ping":
                await websocket.send_json({"type": "pong"})

            else:
                await websocket.send_json({
                    "type": "error",
                    "error": f"Unknown message type: {data.get('type')}"
                })

    except WebSocketDisconnect:
        print(f"Client disconnected from session {session.session_id}")
    except Exception as e:
        print(f"WebSocket error: {e}")
        try:
            await websocket.send_json({
                "type": "error",
                "error": str(e)
            })
        except:
            pass


@app.get("/api/portfolio", response_model=PortfolioResponse)
async def get_portfolio():
    """Get current portfolio data from portfolio.json."""
    try:
        portfolio = agent_service.load_portfolio_from_disk()

        if "error" in portfolio:
            return PortfolioResponse(
                success=False,
                error=portfolio["error"]
            )

        return PortfolioResponse(
            success=True,
            data=portfolio
        )

    except Exception as e:
        return PortfolioResponse(
            success=False,
            error=str(e)
        )


@app.post("/api/portfolio/trade", response_model=TradeResponse)
async def execute_trade(trade: TradeRequest):
    """Execute a trade (buy or sell)."""
    try:
        result = agent_service.execute_trade(
            action=trade.action,
            account_name=trade.account_name,
            ticker=trade.ticker,
            shares=trade.shares,
            price=trade.price
        )

        if result["success"]:
            return TradeResponse(
                success=True,
                message=result["message"],
                updated_holding={
                    "ticker": trade.ticker,
                    "action": trade.action,
                    "shares": trade.shares,
                    "account": trade.account_name
                }
            )
        else:
            return TradeResponse(
                success=False,
                message=result["message"],
                error=result.get("error")
            )

    except Exception as e:
        return TradeResponse(
            success=False,
            message="Failed to execute trade",
            error=str(e)
        )


@app.get("/api/files", response_model=FileListResponse)
async def list_files(session_id: Optional[str] = Query(None)):
    """
    List files in the agent's virtual filesystem.

    Returns files from the session's files dict.
    """
    try:
        session = session_manager.get_session(session_id)
        files = session.files

        # Organize by directory
        directories = {}
        all_files = []

        for path in files.keys():
            all_files.append(path)

            # Extract directory
            directory = str(Path(path).parent)
            if directory not in directories:
                directories[directory] = []
            directories[directory].append(path)

        return FileListResponse(
            files=all_files,
            directories=directories
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/files/{path:path}", response_model=FileContentResponse)
async def get_file_content(path: str, session_id: Optional[str] = Query(None)):
    """
    Get content of a specific file from agent's virtual filesystem.

    Args:
        path: File path (e.g., "financial_data/portfolio.json")
        session_id: Session ID
    """
    try:
        session = session_manager.get_session(session_id)

        # Normalize path (add leading slash if missing)
        if not path.startswith("/"):
            path = "/" + path

        if path not in session.files:
            return FileContentResponse(
                success=False,
                path=path,
                error="File not found"
            )

        file_data = session.files[path]

        # Extract content from file data object
        # DeepAgents file format: {"content": "...", "metadata": {...}}
        if isinstance(file_data, dict):
            content = file_data.get("content", str(file_data))
        else:
            content = str(file_data)

        return FileContentResponse(
            success=True,
            path=path,
            content=content
        )

    except Exception as e:
        return FileContentResponse(
            success=False,
            path=path,
            error=str(e)
        )


@app.post("/api/session/clear")
async def clear_session(session_id: str):
    """Clear a session's conversation history."""
    success = session_manager.clear_session(session_id)

    if success:
        return {"success": True, "message": "Session cleared"}
    else:
        raise HTTPException(status_code=404, detail="Session not found")


@app.get("/api/sessions")
async def list_sessions():
    """List all active sessions."""
    sessions = session_manager.get_all_sessions()
    return {"sessions": sessions}


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "agent_initialized": agent_service.agent is not None,
        "active_sessions": len(session_manager.sessions)
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
