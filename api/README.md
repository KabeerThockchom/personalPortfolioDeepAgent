# Personal Finance Deep Agent - Backend API

FastAPI backend for the chat interface with real-time WebSocket streaming.

## 🚀 Quick Start

### Installation

```bash
# Install backend dependencies
pip install -r api/requirements.txt

# OR install all dependencies (includes main app)
pip install -r requirements.txt
```

### Running the Server

```bash
# From project root
python -m api.server

# OR using uvicorn directly
uvicorn api.server:app --reload --host 0.0.0.0 --port 8000
```

The server will start on `http://localhost:8000`

- **API Documentation**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc
- **WebSocket**: ws://localhost:8000/ws/{chat_id}

## 📡 API Endpoints

### REST API

#### Chat Management

- **POST** `/api/chat/new` - Create a new chat
- **GET** `/api/chat/{chat_id}` - Get chat history
- **PUT** `/api/chat/{chat_id}` - Update chat (title, pinned, archived)
- **DELETE** `/api/chat/{chat_id}` - Delete chat
- **GET** `/api/chat/` - List all chats (paginated)
- **GET** `/api/chat/search/` - Search chats by query
- **DELETE** `/api/chat/{chat_id}/messages` - Clear chat messages

#### File Management

- **GET** `/api/files/{session_id}` - List session files
- **GET** `/api/files/{session_id}/content?path=...` - Get file content
- **GET** `/api/files/{session_id}/download?path=...` - Download file

#### Health & Info

- **GET** `/` - API info
- **GET** `/health` - Health check

### WebSocket

#### Connection

```
ws://localhost:8000/ws/{chat_id}
```

#### Client → Server Messages

**Send a message:**
```json
{
  "type": "message",
  "data": {
    "content": "Calculate my portfolio value",
    "session_id": "abc-123-...",
    "enable_hitl": true
  }
}
```

**Respond to approval request:**
```json
{
  "type": "approval_response",
  "data": {
    "decisions": [
      {"type": "approve"},
      {"type": "reject"}
    ]
  }
}
```

**Ping:**
```json
{
  "type": "ping"
}
```

#### Server → Client Events

**Execution started:**
```json
{
  "type": "start",
  "data": {
    "chat_id": "...",
    "message_id": "..."
  },
  "timestamp": "2025-11-02T12:34:56"
}
```

**Agent step:**
```json
{
  "type": "step",
  "data": {
    "step_number": 1,
    "node_name": "model",
    "friendly_name": "🤖 Main Agent",
    "is_subagent": false,
    "subagent_name": null
  },
  "timestamp": "..."
}
```

**Tool call:**
```json
{
  "type": "tool_call",
  "data": {
    "tool_call_id": "...",
    "name": "get_stock_quote",
    "args": {"symbol": "NVDA"},
    "is_subagent": false
  },
  "timestamp": "..."
}
```

**Tool result:**
```json
{
  "type": "tool_result",
  "data": {
    "tool_call_id": "...",
    "name": "get_stock_quote",
    "result": {...},
    "success": true,
    "error": null,
    "is_subagent": false
  },
  "timestamp": "..."
}
```

**Todo update:**
```json
{
  "type": "todo_update",
  "data": {
    "todos": [
      {"content": "Fetch prices", "status": "completed", "activeForm": "..."},
      {"content": "Calculate value", "status": "in_progress", "activeForm": "..."}
    ]
  },
  "timestamp": "..."
}
```

**File update:**
```json
{
  "type": "file_update",
  "data": {
    "files": ["/financial_data/prices.json"]
  },
  "timestamp": "..."
}
```

**Approval request:**
```json
{
  "type": "approval_request",
  "data": {
    "requests": [
      {
        "action_request": {
          "name": "update_investment_holding",
          "args": {"ticker": "NVDA", "shares": 10}
        },
        "review_config": {
          "allowed_decisions": ["approve", "reject", "edit"]
        }
      }
    ]
  },
  "timestamp": "..."
}
```

**Execution complete:**
```json
{
  "type": "complete",
  "data": {
    "message": {
      "id": "...",
      "role": "assistant",
      "content": "Your portfolio is worth $46,355.17",
      "created_at": "..."
    }
  },
  "timestamp": "..."
}
```

**Error:**
```json
{
  "type": "error",
  "data": {
    "error": "Error message",
    "details": "Stack trace or additional info"
  },
  "timestamp": "..."
}
```

## 🗄️ Database

The API uses SQLite for chat/message storage:
- Database file: `chat_history.db` (created automatically)
- Tables: `chats`, `messages`
- Auto-initialized on startup

## 📁 File Structure

```
api/
├── server.py              # Main FastAPI app & WebSocket
├── websocket.py           # WebSocket connection manager
├── models.py              # Pydantic models
├── database.py            # SQLite database operations
├── routes/
│   ├── chat.py           # Chat CRUD endpoints
│   └── files.py          # File management endpoints
└── services/
    ├── agent_service.py  # Agent execution & streaming
    └── chat_service.py   # Chat business logic
```

## 🔧 Configuration

### Environment Variables

Create `.env` file with:

```bash
# Required
ANTHROPIC_API_KEY=your_key_here
RAPIDAPI_KEY=your_key_here

# Optional
TAVILY_API_KEY=your_key_here
```

### CORS

Update allowed origins in `api/server.py`:

```python
allow_origins=[
    "http://localhost:3000",      # Next.js dev
    "http://localhost:5173",      # Vite dev
    "https://yourdomain.com",     # Production
]
```

## 🧪 Testing

### Using cURL

**Create chat:**
```bash
curl -X POST http://localhost:8000/api/chat/new \
  -H "Content-Type: application/json" \
  -d '{"title": "Test Chat", "load_portfolio": true}'
```

**List chats:**
```bash
curl http://localhost:8000/api/chat/
```

**Get chat:**
```bash
curl http://localhost:8000/api/chat/{chat_id}
```

### Using WebSocket (Python)

```python
import asyncio
import websockets
import json

async def test_websocket():
    uri = "ws://localhost:8000/ws/your-chat-id"

    async with websockets.connect(uri) as websocket:
        # Send message
        await websocket.send(json.dumps({
            "type": "message",
            "data": {
                "content": "What's my portfolio value?",
                "session_id": "your-session-id"
            }
        }))

        # Receive events
        while True:
            response = await websocket.recv()
            event = json.loads(response)
            print(f"Event: {event['type']}")

            if event['type'] == 'complete':
                print(f"Response: {event['data']['message']['content']}")
                break

asyncio.run(test_websocket())
```

### Using Postman/Insomnia

1. Import OpenAPI spec from http://localhost:8000/openapi.json
2. Test REST endpoints
3. Use WebSocket client for real-time streaming

## 🐛 Debugging

**Enable debug logging:**
```bash
uvicorn api.server:app --reload --log-level debug
```

**View database:**
```bash
sqlite3 chat_history.db
.tables
SELECT * FROM chats;
SELECT * FROM messages;
```

## 📝 Notes

- WebSocket connections are stateful - each chat can have multiple clients
- Agent instances are pooled per session_id
- Approval requests block execution until user responds (5 min timeout)
- Large API responses are auto-saved to `sessions/{session_id}/` directory
- Database grows over time - implement cleanup for production

## 🔐 Security

For production:
- [ ] Add authentication (JWT, OAuth)
- [ ] Rate limiting (slowapi, fastapi-limiter)
- [ ] Input validation (already using Pydantic)
- [ ] HTTPS only (configure uvicorn with SSL)
- [ ] Restrict CORS origins
- [ ] Add request logging
- [ ] Implement user isolation (multi-tenancy)

## 📚 Next Steps

1. **Build Frontend**: Create React/Next.js app that connects to this API
2. **Add Auth**: Implement user authentication
3. **Deploy**: Deploy to Railway, Render, or DigitalOcean
4. **Monitoring**: Add Sentry, LogRocket, or similar
5. **Scale**: Move to PostgreSQL + Redis for production
