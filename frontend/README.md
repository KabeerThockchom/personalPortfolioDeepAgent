# Personal Finance Deep Agent - Frontend

A modern web interface for the Personal Finance Deep Agent, built with vanilla HTML, CSS, and JavaScript.

## Features

- **Real-time WebSocket Communication**: Instant updates as the agent processes requests
- **Live Tool Execution Display**: See tool calls and results in real-time
- **Subagent Visualization**: Watch as specialized subagents are spawned and complete
- **Approval Requests**: Interactive modal for approving/rejecting sensitive operations
- **Dark Theme UI**: Modern, professional dark theme interface
- **Responsive Design**: Works on desktop and mobile devices

## Running the Application

1. **Start the FastAPI backend**:
   ```bash
   uvicorn api.server:app --reload --port 8000
   ```

2. **Open your browser**:
   Navigate to `http://localhost:8000` - the frontend will be served automatically

## Usage

1. **Connect**: The WebSocket connection establishes automatically when you load the page
2. **Send Messages**: Type your financial questions in the input box and press Enter or click Send
3. **Watch Progress**: See tool calls, subagent spawns, and results in real-time
4. **Approve Actions**: When the agent requests approval, review the details and click Approve or Reject
5. **Clear History**: Click "Clear History" to reset the conversation

## Event Types

The frontend handles these event types from the backend:

- `connected` - WebSocket connection established
- `thinking` - Agent is processing
- `tool_call` - Tool is being executed
- `tool_result` - Tool execution result
- `subagent_spawn` - Specialized subagent started
- `subagent_complete` - Subagent finished
- `message` - Agent's text response
- `file_update` - Files were created/updated
- `todo_update` - TODO list was updated
- `approval_request` - Agent needs approval
- `complete` - Agent finished processing
- `error` - Error occurred

## File Structure

```
frontend/
├── index.html    # Main HTML structure
├── styles.css    # Styling and theme
├── app.js        # WebSocket client and UI logic
└── README.md     # This file
```

## Customization

### Changing Colors

Edit `styles.css` and modify the CSS variables in `:root`:

```css
:root {
    --primary-color: #2563eb;
    --success-color: #10b981;
    --warning-color: #f59e0b;
    --error-color: #ef4444;
    /* ... */
}
```

### Modifying UI Layout

Edit `index.html` for structure changes and `styles.css` for layout modifications.

### Extending Functionality

Edit `app.js` to add new event handlers or UI features.

## Browser Compatibility

- Chrome/Edge (recommended)
- Firefox
- Safari
- Any modern browser with WebSocket support

## Troubleshooting

**Connection Issues**:
- Check that the backend is running on port 8000
- Verify WebSocket URL in browser console
- Check browser console for errors

**Styles Not Loading**:
- Ensure `styles.css` is in the `frontend/` directory
- Check browser network tab for 404 errors

**WebSocket Errors**:
- Verify CORS settings in `api/server.py`
- Check that the WebSocket endpoint `/api/chat` is accessible

