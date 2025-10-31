# Deep Agents UI Setup Guide

This guide explains how to connect the Personal Finance Deep Agent system to the [deep-agents-ui](https://github.com/langchain-ai/deep-agents-ui) for a rich web interface.

## Overview

The deep-agents-ui provides a modern Next.js-based web interface for interacting with deep agents. This setup uses:
- **Backend**: LangGraph server hosting our finance deep agent
- **Frontend**: deep-agents-ui (Next.js) connecting to LangGraph server
- **Protocol**: LangGraph Platform API (replaces custom WebSocket)

## Architecture

```
┌─────────────────────────────────────┐
│   deep-agents-ui (Next.js)          │
│   http://localhost:3000             │
└──────────────┬──────────────────────┘
               │ LangGraph API
               ▼
┌─────────────────────────────────────┐
│   LangGraph Server                  │
│   http://127.0.0.1:2024             │
│                                     │
│   ┌─────────────────────────────┐  │
│   │  Finance Deep Agent         │  │
│   │  - 8 specialized subagents  │  │
│   │  - 74+ financial tools      │  │
│   │  - Human-in-the-loop        │  │
│   └─────────────────────────────┘  │
└─────────────────────────────────────┘
```

## Prerequisites

1. **Python 3.11+** with virtual environment
2. **Node.js 18+** and npm
3. **API Keys** (configured in `.env`):
   - `ANTHROPIC_API_KEY` or custom model API key
   - `RAPIDAPI_KEY` (Yahoo Finance)
   - `TAVILY_API_KEY` (optional)

## Step 1: Install LangGraph CLI

The LangGraph CLI is required to run the LangGraph server locally.

```bash
# Already included in requirements.txt
pip install langgraph-cli

# Verify installation
langgraph --version
```

## Step 2: Configure LangGraph Server

The `langgraph.json` file (already created) configures the server:

```json
{
  "dependencies": ["."],
  "graphs": {
    "finance-agent": "./src/agent_graph.py:graph"
  },
  "env": ".env"
}
```

**Key components:**
- `dependencies`: Lists Python packages to install (`.` = current directory)
- `graphs`: Maps agent IDs to graph modules
  - Agent ID: `finance-agent` (used by UI)
  - Module path: `src/agent_graph.py:graph`
- `env`: Environment variables file

## Step 3: Start LangGraph Server

Run the server from the project root:

```bash
# Activate virtual environment
source venv/bin/activate  # Windows: venv\Scripts\activate

# Start LangGraph server (default port 2024)
langgraph dev

# Alternative: Specify custom port
langgraph dev --port 8000
```

**What happens:**
1. Server reads `langgraph.json` configuration
2. Loads `.env` environment variables
3. Imports `src/agent_graph.py` and extracts `graph` variable
4. Starts server at `http://127.0.0.1:2024`
5. Exposes LangGraph Platform API endpoints

**Expected output:**
```
Starting LangGraph server...
Loading agent graph from src/agent_graph.py:graph
Server running at http://127.0.0.1:2024
Agent ID: finance-agent
```

**Verify server:**
```bash
# Check server health
curl http://127.0.0.1:2024/health

# List available agents
curl http://127.0.0.1:2024/agents
```

## Step 4: Set Up deep-agents-ui

Clone and configure the UI:

```bash
# Clone the UI repository (outside this project)
cd ..
git clone https://github.com/langchain-ai/deep-agents-ui.git
cd deep-agents-ui

# Install dependencies
npm install
```

## Step 5: Configure UI Environment

Create `.env.local` file in the `deep-agents-ui` directory:

```bash
# .env.local
NEXT_PUBLIC_DEPLOYMENT_URL="http://127.0.0.1:2024"
NEXT_PUBLIC_AGENT_ID="finance-agent"
```

**Configuration details:**
- `NEXT_PUBLIC_DEPLOYMENT_URL`: LangGraph server URL
- `NEXT_PUBLIC_AGENT_ID`: Must match the graph ID in `langgraph.json` (`finance-agent`)

**For production deployment:**
```bash
# Add LangSmith API key for cloud deployments
NEXT_PUBLIC_DEPLOYMENT_URL="https://your-deployed-server.com"
NEXT_PUBLIC_AGENT_ID="finance-agent"
NEXT_PUBLIC_LANGSMITH_API_KEY="your-langsmith-api-key"
```

## Step 6: Start the UI

```bash
# From deep-agents-ui directory
npm run dev
```

Access the UI at: **http://localhost:3000**

## Usage

### Basic Interaction

1. Open `http://localhost:3000` in your browser
2. You'll see the Deep Agents chat interface
3. Type a message: *"What's my portfolio worth?"*
4. Watch as:
   - Main agent processes your request
   - Subagents spawn for specialized analysis
   - Tool calls execute with results
   - Approval requests appear for sensitive operations

### Example Queries

**Quick lookups** (main agent handles directly):
```
What's the price of AAPL?
Show me NVDA, MSFT, and GOOGL prices
What's my current savings rate?
```

**Complex analysis** (delegates to subagents):
```
Analyze my portfolio allocation and suggest rebalancing
Should I invest in Tesla based on fundamentals?
Compare NVDA vs AMD vs INTC for investment
Calculate my retirement readiness with Monte Carlo simulation
```

### Human-in-the-Loop Approvals

When the agent wants to perform sensitive operations, you'll see approval requests:

**Tier 1 - Portfolio Modifications** (always require approval):
- Buy/sell stocks
- Deposits/withdrawals
- Record expenses
- Update credit card balances

**Tier 2 - Complex Planning** (configurable):
- Spawning subagents for analysis

**Example flow:**
```
You: "Buy 10 shares of NVDA in my 401k"

Agent: "I'll update your investment holding."

[APPROVAL REQUEST APPEARS IN UI]
Tool: update_investment_holding
Arguments:
  account_name: 401k
  ticker: NVDA
  shares: 10
  transaction_type: buy

[APPROVE] [REJECT]

You: [Click APPROVE]

Agent: "✓ Purchased 10 shares of NVDA. Your 401k now has..."
```

## Advanced Configuration

### Disable Human-in-the-Loop

Edit `src/agent_graph.py`:

```python
graph = create_finance_deep_agent(
    enable_human_in_loop=False,  # Disable approvals
    session_id="default"
)
```

### Customize Interrupt Configuration

Edit `src/deep_agent.py` - `INTERRUPT_ON_CONFIG` dict:

```python
INTERRUPT_ON_CONFIG = {
    # Add new tools requiring approval
    "web_search": True,  # Now requires approval

    # Or remove existing ones (auto-approve)
    "task": False,  # Subagent spawns no longer need approval
}
```

### Use Different Model

Edit `src/deep_agent.py` (lines 360-366):

```python
# Switch to Claude Sonnet
from langchain_anthropic import ChatAnthropic
model = ChatAnthropic(
    model="claude-sonnet-4-20250514",
    temperature=0
)

# Or use OpenAI GPT-4
from langchain_openai import ChatOpenAI
model = ChatOpenAI(
    model="gpt-4o",
    temperature=0
)
```

### Add Custom Tools

1. Create tool in `src/tools/` directory
2. Add to subagent config in `src/subagents_config.py`
3. Restart LangGraph server

## Troubleshooting

### Server won't start

**Error: `ModuleNotFoundError: No module named 'src'`**
```bash
# Ensure you're running from project root
pwd  # Should show .../personalPortfolioDeepAgent
langgraph dev
```

**Error: `Could not find graph at src/agent_graph.py:graph`**
```bash
# Verify file exists
ls src/agent_graph.py

# Check Python syntax
python -c "from src.agent_graph import graph; print(graph)"
```

### UI won't connect

**Error: `Failed to fetch`**
- Check LangGraph server is running (`http://127.0.0.1:2024/health`)
- Verify `NEXT_PUBLIC_DEPLOYMENT_URL` in `.env.local`
- Check browser console for CORS errors

**Error: `Agent ID not found`**
- Verify `NEXT_PUBLIC_AGENT_ID="finance-agent"` matches `langgraph.json`
- Restart LangGraph server after config changes

### Agent errors

**Error: `'NoneType' object has no attribute 'bind_tools'`**
- This means a subagent model is misconfigured
- Check `src/subagents_config.py` - `SUBAGENT_MODELS` dict
- Ensure values are `None` (inherit from main) or valid model strings
- **Don't use**: `ChatOpenAI` instances directly

**Error: `Too many tokens`**
- Context optimization is enabled by default
- Large API responses auto-save to `/financial_data/`
- Check `src/utils/response_optimizer.py` configuration

## Architecture Details

### Session Management

Each UI connection creates a new thread with:
- **Thread ID**: Generated by LangGraph server
- **Checkpointer**: MemorySaver for conversation history
- **Store**: InMemoryStore for long-term memory
- **Backend**: Hybrid storage (state + store + filesystem)

### File Storage

The agent uses a hybrid backend:

```
/financial_data/     → Real disk files (sessions/{session_id}/financial_data/)
/reports/            → Real disk files (sessions/{session_id}/reports/)
/memories/           → LangGraph Store (persistent across sessions)
/user_profiles/      → LangGraph Store (persistent across sessions)
/working/            → LangGraph State (ephemeral, current thread only)
```

### Tool Visibility

- **Main agent**: 6 quick-access tools (quotes, portfolio value, cash flow, search)
- **Subagents**: 74+ specialized tools distributed across 8 subagents
- **UI display**: All tool calls appear in real-time with full arguments and results

### Token Optimization

- **API responses >300 chars**: Auto-saved to disk, summary returned (99.5% reduction)
- **Conversation history**: Pruned to last 5 turns in CLI (no limit in UI)
- **FilesystemMiddleware**: Evicts large files from context automatically

## Comparison: Custom WebSocket vs LangGraph Server

| Feature | Custom WebSocket (`api/server.py`) | LangGraph Server + deep-agents-ui |
|---------|-----------------------------------|-----------------------------------|
| **Protocol** | Custom WebSocket | Standard LangGraph Platform API |
| **UI** | Basic HTML/CSS/JS | Rich Next.js interface |
| **Deployment** | Manual FastAPI setup | LangGraph CLI one-liner |
| **Session Management** | Custom implementation | Built-in with checkpointing |
| **Streaming** | Custom event types | Standard LangGraph streaming |
| **Production Ready** | DIY | Cloud deployment support |
| **Maintenance** | Custom codebase | Maintained by LangChain team |

**Recommendation**: Use LangGraph server + deep-agents-ui for production. Keep custom WebSocket for specialized use cases.

## Production Deployment

### Option 1: LangSmith Deployment (Recommended)

```bash
# Deploy to LangChain Cloud
langgraph deploy

# Follow prompts to configure deployment
# Get deployment URL: https://your-agent.langchain.com
```

Update UI config:
```bash
NEXT_PUBLIC_DEPLOYMENT_URL="https://your-agent.langchain.com"
NEXT_PUBLIC_AGENT_ID="finance-agent"
NEXT_PUBLIC_LANGSMITH_API_KEY="your-api-key"
```

### Option 2: Self-Hosted

Deploy as Docker container:

```dockerfile
FROM langchain/langgraphjs-server:latest
COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt
CMD ["langgraph", "start", "--host", "0.0.0.0", "--port", "8080"]
```

Deploy UI separately (Vercel, Netlify, etc.):
```bash
# Build UI for production
cd deep-agents-ui
npm run build

# Deploy to Vercel
vercel deploy
```

### Option 3: Kubernetes

Use LangGraph Helm charts (see LangGraph docs for k8s deployment).

## Resources

- **LangGraph Docs**: https://langchain-ai.github.io/langgraph/
- **deep-agents-ui**: https://github.com/langchain-ai/deep-agents-ui
- **DeepAgents**: https://github.com/langchain-ai/deepagents
- **LangSmith**: https://www.langchain.com/langsmith

## Support

For issues:
1. Check LangGraph server logs
2. Check browser console (UI errors)
3. Verify `.env` configuration
4. Test agent directly: `python -c "from src.agent_graph import graph; print(graph)"`

For questions about this integration, see `CLAUDE.md` and `RECENT_UPDATES.md`.
