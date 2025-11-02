# Finance Chat UI - SvelteKit Frontend

Modern, responsive chat interface for the Personal Finance Deep Agent built with SvelteKit, TypeScript, and Tailwind CSS.

## 🎨 Features

### Core Features
- ✅ **Real-time WebSocket Streaming** - Live agent execution updates
- ✅ **Markdown Rendering** - Beautiful formatted AI responses with tables, code blocks, lists
- ✅ **Collapsible Tool Calls** - View tool executions with arguments and results
- ✅ **Approval Modal** - Human-in-the-loop UI for portfolio modifications
- ✅ **Live Todo List** - Real-time task tracking with progress bar
- ✅ **Chat Management** - Create, search, pin, archive, delete chats
- ✅ **Auto-scroll** - Smart scrolling with manual override
- ✅ **Dark/Light Theme** - DaisyUI theme support
- ✅ **Responsive Design** - Mobile, tablet, and desktop layouts

### UI Components
1. **ChatSidebar** - Chat list with search and management
2. **MessageList** - Message display with markdown and typing indicators
3. **MessageInput** - Multi-line input with keyboard shortcuts
4. **ToolCall** - Collapsible tool execution display
5. **ApprovalModal** - Multi-step approval workflow
6. **TodoWidget** - Live task list with progress

## 🚀 Quick Start

### Prerequisites

- Node.js 18+ (check: `node --version`)
- Backend API running at http://localhost:8000
- npm or pnpm

### Installation

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

The app will be available at: **http://localhost:3000**

### Build for Production

```bash
npm run build
npm run preview
```

## 📁 Project Structure

```
frontend/
├── src/
│   ├── lib/
│   │   ├── api.ts                  # REST API client
│   │   ├── websocket.ts            # WebSocket store
│   │   ├── types.ts                # TypeScript interfaces
│   │   └── components/
│   │       ├── ChatSidebar.svelte  # Chat list & search
│   │       ├── MessageList.svelte  # Message display
│   │       ├── MessageInput.svelte # Input area
│   │       ├── ToolCall.svelte     # Tool execution display
│   │       ├── ApprovalModal.svelte # Approval UI
│   │       └── TodoWidget.svelte   # Task list
│   ├── routes/
│   │   ├── +layout.svelte          # Root layout
│   │   ├── +page.svelte            # Home page
│   │   └── chat/[id]/+page.svelte  # Chat page
│   └── app.css                     # Global styles
├── static/                         # Static assets
├── package.json
├── svelte.config.js
├── tailwind.config.js
├── tsconfig.json
└── vite.config.ts
```

## 🔧 Configuration

### Backend API URL

Edit `src/lib/api.ts` and `src/lib/websocket.ts`:

```typescript
// api.ts
const API_BASE = 'http://localhost:8000/api';

// websocket.ts
const WS_BASE = 'ws://localhost:8000/ws';
```

For production, use environment variables:

```bash
# .env
PUBLIC_API_BASE=https://api.yourfin domain.com/api
PUBLIC_WS_BASE=wss://api.yourdomain.com/ws
```

Then update the files to use:

```typescript
const API_BASE = import.meta.env.PUBLIC_API_BASE || 'http://localhost:8000/api';
const WS_BASE = import.meta.env.PUBLIC_WS_BASE || 'ws://localhost:8000/ws';
```

### Theme Customization

Edit `tailwind.config.js` to customize colors:

```javascript
daisyui: {
	themes: [
		{
			light: {
				primary: "#3b82f6",    // Blue
				secondary: "#8b5cf6",  // Purple
				accent: "#06b6d4",     // Cyan
				// ... more colors
			}
		}
	]
}
```

## 🎯 Usage

### Starting a New Chat

1. Click "New Chat" button in sidebar
2. Type your message in the input box
3. Press Enter to send (Shift+Enter for new line)

### Viewing Tool Executions

- Tool calls appear as collapsible cards
- Click to expand and see arguments & results
- Shows real-time status: Running → Success/Failed
- Subagent tools are indented

### Handling Approvals

When the agent needs approval:
1. Modal appears with tool details
2. Review the arguments
3. Click "Approve" or "Reject"
4. Multiple approvals handled sequentially

### Managing Chats

- **Search**: Type in search box, press Enter
- **Pin**: Hover over chat → click pin icon
- **Delete**: Hover over chat → click trash icon
- **Archive**: Update chat via settings (coming soon)

## 🔌 WebSocket Events

The frontend listens to these events from the backend:

| Event Type | Description |
|------------|-------------|
| `start` | Execution started |
| `step` | Agent step (e.g., "🤖 Main Agent") |
| `tool_call` | Tool called with arguments |
| `tool_result` | Tool execution result |
| `todo_update` | Task list updated |
| `file_update` | Files modified |
| `approval_request` | Needs user approval |
| `complete` | Execution finished |
| `error` | Error occurred |

## 📝 Code Examples

### Sending a Message

```typescript
import { wsManager } from '$lib/websocket';

const chatId = 'your-chat-id';
const sessionId = 'your-session-id';
const wsStore = wsManager.getOrCreate(chatId);

wsStore.sendMessage('Calculate my portfolio value', sessionId, true);
```

### Subscribing to Events

```svelte
<script>
	import { wsManager } from '$lib/websocket';

	const chatId = 'your-chat-id';
	const wsStore = wsManager.getOrCreate(chatId);

	$: events = $wsStore.events;
	$: isExecuting = $wsStore.isExecuting;

	// Process events
	$: {
		if (events.length > 0) {
			const latest = events[events.length - 1];
			console.log('Latest event:', latest.type);
		}
	}
</script>
```

### Creating a Chat

```typescript
import { createChat } from '$lib/api';
import { goto } from '$app/navigation';

const chat = await createChat('My Portfolio Analysis', true);
goto(`/chat/${chat.id}`);
```

## 🎨 Styling

### Tailwind CSS + DaisyUI

The UI uses Tailwind utility classes and DaisyUI components:

```svelte
<!-- Button -->
<button class="btn btn-primary btn-lg">Click Me</button>

<!-- Card -->
<div class="card bg-base-200">
	<div class="card-body">
		<h2 class="card-title">Title</h2>
		<p>Content</p>
	</div>
</div>

<!-- Badge -->
<span class="badge badge-success">Online</span>
```

### Custom Animations

Defined in `app.css`:
- `.typing-dot` - Typing indicator animation
- `.animate-pulse-slow` - Slow pulse effect
- Custom scrollbar styling

## 🐛 Debugging

### Enable Console Logs

```typescript
// websocket.ts - Add logging
ws.onmessage = (event) => {
	const data = JSON.parse(event.data);
	console.log('📥 Event:', data); // Debug line
	// ...
};
```

### Check WebSocket Connection

Open browser DevTools → Network → WS:
- Should see WebSocket connection to `ws://localhost:8000/ws/{chatId}`
- Click to view frames (messages sent/received)

### View API Requests

DevTools → Network → XHR:
- All REST API calls to `http://localhost:8000/api/*`
- Check status codes and responses

## 📱 Responsive Design

### Breakpoints

- **Mobile** (<768px): Single column, hamburger menu
- **Tablet** (768-1024px): Sidebar + chat
- **Desktop** (>1024px): Sidebar + chat + right panel

### Mobile Optimizations

- Touch-friendly buttons (min 44px)
- Swipe gestures (coming soon)
- Collapsible sidebar
- Bottom navigation bar

## ⚡ Performance

### Optimizations

- **Lazy Loading**: Components loaded on-demand
- **Virtual Scrolling**: For long message lists (coming soon)
- **Debounced Search**: 300ms delay on search input
- **WebSocket Reconnection**: Auto-reconnect with exponential backoff
- **Message Pagination**: Load messages in chunks (coming soon)

### Bundle Size

```bash
npm run build

# Check bundle size
npm run preview
```

Target: <500KB initial bundle

## 🚢 Deployment

### Vercel (Recommended)

```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
cd frontend
vercel
```

### Netlify

```bash
# Build
npm run build

# Deploy
netlify deploy --prod --dir=build
```

### Docker

```dockerfile
FROM node:18-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

FROM node:18-alpine
WORKDIR /app
COPY --from=builder /app/build ./build
COPY package*.json ./
RUN npm install --production
CMD ["node", "build"]
```

## 🧪 Testing

### Run Type Check

```bash
npm run check
```

### Test WebSocket Connection

```javascript
// Browser console
const ws = new WebSocket('ws://localhost:8000/ws/test-chat-id');
ws.onmessage = (e) => console.log(JSON.parse(e.data));
ws.send(JSON.stringify({
	type: 'message',
	data: {
		content: 'Hello',
		session_id: 'test-session'
	}
}));
```

## 🔐 Security

### Production Checklist

- [ ] Use HTTPS/WSS (not HTTP/WS)
- [ ] Add authentication (Auth0, Clerk, etc.)
- [ ] Sanitize markdown output (XSS protection)
- [ ] Rate limit API calls
- [ ] Validate all user inputs
- [ ] Add CORS restrictions
- [ ] Enable CSP headers

### Environment Variables

Never commit:
- API keys
- Secret tokens
- Private URLs

Use `.env.example` for documentation.

## 📚 Resources

- **SvelteKit Docs**: https://kit.svelte.dev/docs
- **Tailwind CSS**: https://tailwindcss.com/docs
- **DaisyUI**: https://daisyui.com/components
- **Marked**: https://marked.js.org/
- **WebSocket API**: https://developer.mozilla.org/en-US/docs/Web/API/WebSocket

## 🤝 Contributing

1. Create a feature branch
2. Make changes
3. Run type check: `npm run check`
4. Test manually
5. Submit pull request

## 📄 License

Same as parent project

---

**Questions?** Check the main project README or open an issue.

**Happy coding!** 🎉
