# Quick Start Guide - Web Interface

This guide will help you get the Personal Finance Deep Agent web interface up and running.

## Prerequisites

- Python 3.8+
- All dependencies installed (`pip install -r requirements.txt`)
- `portfolio.json` file in the project root (optional, but recommended)

## Starting the Server

1. **Activate your virtual environment** (if using one):
   ```bash
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Start the FastAPI server**:
   ```bash
   uvicorn api.server:app --reload --port 8000
   ```

   The server will start on `http://localhost:8000`

3. **Open your browser**:
   Navigate to `http://localhost:8000` - the frontend will load automatically!

## Using the Web Interface

### Basic Usage

1. **Wait for Connection**: The status indicator in the top-right should show "Connected" (green dot)
2. **Ask Questions**: Type your financial questions in the input box at the bottom
3. **Press Enter or Click Send**: Your message will be sent to the agent
4. **Watch Progress**: 
   - See tool calls being executed in real-time
   - Watch subagents spawn and complete
   - View results as they come in

### Example Questions

- "What's the current price of AAPL?"
- "Calculate my portfolio value"
- "Analyze my monthly cash flow"
- "How am I doing on retirement?"
- "Research Tesla stock"
- "What are my tax optimization opportunities?"

### Approval Requests

When the agent needs your approval for sensitive operations (like portfolio changes):

1. A modal will appear with the action details
2. Review the tool name and arguments
3. Click **Approve** or **Reject**
4. The agent will continue based on your decision

### Features

- **Real-time Updates**: See everything as it happens
- **Tool Execution**: Watch tools being called with their arguments
- **Subagent Visualization**: See when specialized agents are spawned
- **File Updates**: Notifications when files are created/updated
- **Todo Lists**: View planning tasks as they're created
- **Error Handling**: Clear error messages if something goes wrong

## Troubleshooting

### Connection Issues

- **Status shows "Disconnected"**: 
  - Check that the server is running
  - Verify the WebSocket URL is correct
  - Check browser console for errors

- **Can't connect**:
  - Make sure port 8000 is not in use
  - Check firewall settings
  - Try refreshing the page

### Frontend Not Loading

- **404 errors for CSS/JS**:
  - Verify `frontend/` directory exists
  - Check that files are in the correct location
  - Look at browser Network tab for specific errors

### Agent Not Responding

- **Check server logs**: Look at the terminal where uvicorn is running
- **Check browser console**: Look for JavaScript errors
- **Verify portfolio.json**: Some features require portfolio data

## Development

### File Structure

```
├── api/
│   ├── server.py          # FastAPI server with WebSocket endpoint
│   ├── agent_service.py    # Agent execution service
│   ├── event_parser.py    # Parses agent events for frontend
│   ├── models.py          # Pydantic models
│   └── session_manager.py # Session management
├── frontend/
│   ├── index.html         # Main HTML
│   ├── styles.css        # Styling
│   ├── app.js            # WebSocket client
│   └── README.md         # Frontend docs
└── QUICKSTART.md         # This file
```

### Making Changes

- **Backend**: Edit files in `api/` directory, server auto-reloads with `--reload`
- **Frontend**: Edit files in `frontend/` directory, refresh browser to see changes

### Testing

Test the WebSocket connection:
```bash
# Terminal 1: Start server
uvicorn api.server:app --reload --port 8000

# Terminal 2: Test with curl (optional)
curl http://localhost:8000/api/health
```

## Next Steps

- Load your portfolio data by asking: "Load my portfolio"
- Try complex queries: "Analyze my complete financial picture"
- Explore subagents: "Use the research-analyst to research AAPL"
- Review the [API documentation](api/README.md) for more details

## Support

For issues or questions:
1. Check server logs in the terminal
2. Check browser console (F12)
3. Review error messages in the UI
4. Check `api/README.md` for API details

