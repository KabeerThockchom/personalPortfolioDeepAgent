# Personal Finance Deep Agent API

FastAPI backend for the Personal Finance Deep Agent web interface. Provides WebSocket streaming for real-time agent interactions and REST endpoints for portfolio management.

## Setup

### Prerequisites
- Python 3.9+
- Virtual environment activated
- `.env` file configured with API keys

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Run Server

```bash
# Development mode (auto-reload)
uvicorn api.server:app --reload --port 8000

# Production mode
uvicorn api.server:app --host 0.0.0.0 --port 8000 --workers 4
```

Server will start at: `http://localhost:8000`

API docs available at: `http://localhost:8000/docs`

## API Endpoints

### WebSocket

#### `WS /api/chat`

Real-time bidirectional communication with the financial agent.

**Query Parameters:**
- `session_id` (optional): Session ID to continue a conversation

**Client → Server:**
```json
{
  "type": "message",
  "content": "Calculate my portfolio value"
}
```

**Server → Client Events:**

1. **Connection established**
```json
{
  "type": "connected",
  "session_id": "uuid-string",
  "message": "Connected to agent"
}
```

2. **Thinking event** (agent processing)
```json
{
  "type": "thinking",
  "node": "agent",
  "timestamp": 1234567890.123
}
```

3. **Tool call event**
```json
{
  "type": "tool_call",
  "tool_name": "get_multiple_quotes",
  "args": {
    "symbols": ["AAPL", "MSFT"]
  },
  "tool_call_id": "call_abc123",
  "is_subagent_spawn": false,
  "timestamp": 1234567890.123
}
```

4. **Subagent spawn event**
```json
{
  "type": "subagent_spawn",
  "name": "market-data-fetcher",
  "description": "Fetch current stock prices",
  "status": "spawning",
  "timestamp": 1234567890.123
}
```

5. **Tool result event**
```json
{
  "type": "tool_result",
  "tool_name": "get_multiple_quotes",
  "result": "AAPL: $150.25, MSFT: $330.15",
  "tool_call_id": "call_abc123",
  "success": true,
  "timestamp": 1234567890.123
}
```

6. **File update event**
```json
{
  "type": "file_update",
  "paths": ["/financial_data/current_prices.json"],
  "action": "updated",
  "timestamp": 1234567890.123
}
```

7. **TODO update event**
```json
{
  "type": "todo_update",
  "todos": [
    {"status": "completed", "content": "Fetch prices"},
    {"status": "in_progress", "content": "Calculate portfolio value"}
  ],
  "timestamp": 1234567890.123
}
```

8. **Message event** (agent response)
```json
{
  "type": "message",
  "role": "assistant",
  "content": "Your portfolio value is $46,234.12",
  "timestamp": 1234567890.123
}
```

9. **Subagent complete event**
```json
{
  "type": "subagent_complete",
  "name": "market-data-fetcher",
  "timestamp": 1234567890.123
}
```

10. **Complete event** (execution finished)
```json
{
  "type": "complete",
  "timestamp": 1234567890.123
}
```

11. **Error event**
```json
{
  "type": "error",
  "error": "Error message",
  "details": "Additional error details",
  "timestamp": 1234567890.123
}
```

### REST Endpoints

#### `GET /`
Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "service": "Personal Finance Deep Agent API",
  "version": "1.0.0"
}
```

#### `GET /api/portfolio`
Get current portfolio data from `portfolio.json`.

**Response:**
```json
{
  "success": true,
  "data": {
    "client": { "name": "John Doe", "age": 24 },
    "financial_snapshot": { "total_net_worth": 46000 },
    "investment_accounts": { ... },
    "liquid_accounts": { ... },
    "liabilities": { ... }
  }
}
```

#### `POST /api/portfolio/trade`
Execute a trade (buy or sell stock).

**Request Body:**
```json
{
  "action": "buy",
  "account_name": "taxable_brokerage",
  "ticker": "AAPL",
  "shares": 10,
  "price": 150.25
}
```

**Response:**
```json
{
  "success": true,
  "message": "Successfully bought 10 shares of AAPL",
  "updated_holding": {
    "ticker": "AAPL",
    "action": "buy",
    "shares": 10,
    "account": "taxable_brokerage"
  }
}
```

#### `GET /api/files`
List files in the agent's virtual filesystem.

**Query Parameters:**
- `session_id` (optional): Session ID

**Response:**
```json
{
  "files": [
    "/financial_data/portfolio.json",
    "/financial_data/current_prices.json",
    "/reports/analysis_2024.txt"
  ],
  "directories": {
    "/financial_data": [
      "/financial_data/portfolio.json",
      "/financial_data/current_prices.json"
    ],
    "/reports": [
      "/reports/analysis_2024.txt"
    ]
  }
}
```

#### `GET /api/files/{path}`
Get content of a specific file.

**Path Parameter:**
- `path`: File path (e.g., `financial_data/portfolio.json`)

**Query Parameters:**
- `session_id` (optional): Session ID

**Response:**
```json
{
  "success": true,
  "path": "/financial_data/portfolio.json",
  "content": "{ ... file content ... }"
}
```

#### `POST /api/session/clear`
Clear a session's conversation history.

**Request Body:**
```json
{
  "session_id": "uuid-string"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Session cleared"
}
```

#### `GET /api/sessions`
List all active sessions.

**Response:**
```json
{
  "sessions": [
    {
      "session_id": "uuid-1",
      "message_count": 12,
      "created_at": "2024-01-15T10:30:00",
      "last_activity": "2024-01-15T11:45:00"
    }
  ]
}
```

#### `GET /api/health`
Detailed health check.

**Response:**
```json
{
  "status": "healthy",
  "agent_initialized": true,
  "active_sessions": 3
}
```

## Architecture

### Components

1. **server.py** - FastAPI application with endpoints
2. **agent_service.py** - Agent initialization and execution wrapper
3. **session_manager.py** - In-memory session storage
4. **event_parser.py** - Parse LangGraph streams into frontend events
5. **models.py** - Pydantic models for request/response validation

### Session Management

- **Storage**: In-memory (dict-based)
- **Timeout**: 24 hours of inactivity
- **History pruning**: Keeps last 5 conversation turns to prevent context bloat
- **Cleanup**: Automatic expired session removal

### Event Streaming

The API parses LangGraph stream chunks (`stream_mode="updates"`) into structured events:

1. **Raw chunk** from LangGraph:
   ```python
   {"agent": {"messages": [AIMessage(...)], "files": {...}}}
   ```

2. **Parsed events** sent to frontend:
   - `thinking` - Agent is processing
   - `tool_call` - Tool being executed
   - `tool_result` - Tool execution complete
   - `file_update` - File created/updated
   - `todo_update` - TODO list changed
   - `message` - Agent response
   - `subagent_spawn` - Subagent spawned
   - `subagent_complete` - Subagent finished
   - `complete` - Execution finished
   - `error` - Error occurred

## Development

### Running Tests

```bash
pytest tests/
```

### API Documentation

Once server is running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### WebSocket Testing

Use a WebSocket client like `wscat`:

```bash
npm install -g wscat
wscat -c "ws://localhost:8000/api/chat"

# Send message
> {"type": "message", "content": "What is my portfolio value?"}
```

## Production Considerations

1. **Session Storage**: Replace in-memory storage with Redis for multi-worker deployments
2. **Authentication**: Add JWT authentication for `/api/chat` WebSocket
3. **Rate Limiting**: Add rate limiting per session/IP
4. **CORS**: Update `allow_origins` in production
5. **HTTPS**: Use reverse proxy (nginx/caddy) with SSL
6. **Workers**: Use multiple uvicorn workers behind a load balancer
7. **Monitoring**: Add logging and metrics (Prometheus, Sentry)

## Troubleshooting

### Agent initialization fails
- Ensure `.env` has `ANTHROPIC_API_KEY` and `RAPIDAPI_KEY`
- Check `portfolio.json` exists in project root

### WebSocket connection refused
- Verify server is running on port 8000
- Check CORS settings if connecting from different origin

### High memory usage
- Reduce session timeout in `session_manager.py`
- Decrease conversation history max turns (currently 5)
- Implement Redis for session storage

### Tool execution errors
- Check API keys are valid
- Verify Yahoo Finance API quota (100 req/min)
- Check internet connection for web search tools

## License

Part of Personal Finance Deep Agent project.
