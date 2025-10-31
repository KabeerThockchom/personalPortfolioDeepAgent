# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 🆕 Recent Updates (2025-10-31)

**Major enhancements added - see `RECENT_UPDATES.md` for full details:**
- ✅ **Ultra-Rich Terminal Output** - Complete redesign of display system (NEW!)
  - Smart JSON parsing with bullet-point formatting
  - Tool-specific formatters for stocks, metrics, news
  - Full data display (10K char limit, up from 500)
  - Proper text wrapping with textwrap module
  - Enhanced visual elements (icons, colors, boxes)
  - All tool I/O shown completely (no "✓ SUCCESS" without data)
  - Debug output removed from production
- ✅ **Token Optimization** - 99.5% token reduction in tool responses (2.8M → 150K tokens for deep analysis)
- ✅ **Custom Model Backend** - Switched to Z.ai GLM-4.6 model for all agents
- ✅ **Subagent Model Inheritance Fix** - Fixed `'NoneType' has no attribute 'bind_tools'` error
- ✅ **Human-in-the-Loop** - Agent now asks permission before portfolio modifications and complex tasks
- ✅ **Date/Time Awareness** - All 9 agents now know current date/time
- ✅ **Store Infrastructure** - Foundation for long-term memory (InMemoryStore integrated)
- ✅ **Enhanced Display** - Full tool inputs/outputs with smart formatting in chat
- ✅ **Tool Logging** - Subagent tool calls now visible in real-time (74+ tools wrapped)
- ✅ **Friendly Node Names** - Clear agent labels ("🤖 Main Agent") and middleware context details
- ✅ **Hybrid Architecture** - Main agent has 6 quick-access tools for instant responses
- ✅ **Code Cleanup** - Removed legacy routing code (src/agents/, graph.py, state.py)

## Project Overview

Personal Finance Deep Agent - A multi-agent financial analysis system using DeepAgents framework with LangGraph orchestration. Features 8 specialized subagents, 74+ financial tools, real-time Yahoo Finance API integration, web search via Tavily, portfolio persistence, and complete execution visibility.

## Development Commands

### Setup
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment (required before running)
cp .env.example .env
# Edit .env with your API keys:
# - ANTHROPIC_API_KEY (required)
# - RAPIDAPI_KEY (required for Yahoo Finance)
# - TAVILY_API_KEY (optional, has default dev key)
```

### Running
```bash
# Interactive chat interface (main entry point)
python3 chat.py

# Test agent creation
python3 -m src.deep_agent
```

### Testing
```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_portfolio_tools.py

# Verbose output
pytest -v
```

## Architecture

### Hybrid Multi-Agent System (DeepAgents + LangGraph)

**Main Agent** (`src/deep_agent.py`):
- Orchestrates subagents using DeepAgents framework
- OpenAI GPT-5 Mini model (configurable via `init_chat_model`)
- **NEW: Has 6 quick-access tools** for instant responses to simple queries
- Uses `task` tool to spawn specialized subagents for complex work
- Manages filesystem backend for data persistence
- System prompt guides when to use direct tools vs delegate

**Main Agent Quick-Access Tools** (80+ total tools):
```python
MAIN_AGENT_QUICK_TOOLS = [
    get_stock_quote,           # "What's AAPL price?"
    get_multiple_quotes,       # "Show AAPL, MSFT, GOOGL"
    calculate_portfolio_value, # "What's my portfolio worth?"
    analyze_monthly_cashflow,  # "What's my cash flow?"
    calculate_savings_rate,    # "What's my savings rate?"
    web_search,                # "Search for Fed news"
]
```

**Hybrid Decision Logic:**
- Simple lookups → Main agent uses tools directly → ⚡ Instant (2 steps)
- Complex analysis → Delegates to expert subagent → 🎓 Specialized (4-6 steps)

**Benefits:**
- 🚀 70% faster for common queries (no subagent overhead)
- 💰 Lower token costs (only 6 tool schemas vs 74+ for subagents)
- 🎓 Still gets expert analysis when needed
- 🧠 Main agent learns when to delegate vs handle directly

**8 Specialized Subagents** (`src/subagents_config.py`):
1. **market-data-fetcher** - Real-time Yahoo Finance API (quotes, fundamentals, historical data)
2. **research-analyst** - Company research (analyst ratings, insider trades, ESG, news, SEC filings)
3. **portfolio-analyzer** - Investment analysis (valuation, allocation, concentration, Sharpe ratio, rebalancing)
4. **cashflow-analyzer** - Income/expense analysis (cash flow, savings rate, categorization, burn rate)
5. **goal-planner** - Retirement planning (Monte Carlo simulations, FIRE calculations, college funding)
6. **debt-manager** - Debt optimization (payoff timelines, avalanche vs snowball, DTI ratio)
7. **tax-optimizer** - Tax strategies (loss harvesting, Roth conversions, withdrawal sequencing)
8. **risk-assessor** - Risk analysis (emergency fund, insurance gaps, stress testing, VaR)

Each subagent has:
- `name`: Identifier used in `task` tool calls
- `description`: When to use this subagent
- `system_prompt`: Role, responsibilities, best practices
- `tools`: Subset of 74+ total tools
- `model`: Override model for this subagent (optional)

**Model Configuration** (`src/subagents_config.py:23-35`):
All subagents inherit the model from the main agent. The `SUBAGENT_MODELS` dictionary controls this:
```python
# NOTE: All subagents set to None to inherit from main agent
# The _build_subagent() helper only adds "model" key if value is not None
# This ensures proper model inheritance (DeepAgents requires absence of key, not None value)
SUBAGENT_MODELS = {
    "market-data-fetcher": None,  # Omits "model" key → inherits from main agent
    "research-analyst": None,
    "portfolio-analyzer": None,
    # ... all 8 subagents set to None
}
```

**Helper Function** (`src/subagents_config.py:167-180`):
```python
def _build_subagent(name, description, system_prompt, tools):
    """Build subagent dict, only including 'model' key if value is not None."""
    subagent = {
        "name": name,
        "description": description,
        "system_prompt": system_prompt,
        "tools": tools,
    }
    # Only add model key if it's not None (allows proper inheritance)
    model = SUBAGENT_MODELS.get(name)
    if model is not None:
        subagent["model"] = model
    return subagent
```

**Why this matters:** DeepAgents treats `{"model": None}` differently from `{}` (no model key). When the key is present with value `None`, DeepAgents doesn't inherit from main agent, causing `'NoneType' object has no attribute 'bind_tools'` errors. The helper function solves this by omitting the key entirely.

**Main Agent Configuration** (`src/deep_agent.py:360-366`):
```python
from langchain_openai import ChatOpenAI
model = ChatOpenAI(
    temperature=0,
    model="glm-4.6",
    openai_api_key="69feab44626640cfb0d841966bc344a1.szw2ZTaSJ1KwvjS8",
    openai_api_base="https://api.z.ai/api/paas/v4/"
)
```

Format options for `SUBAGENT_MODELS` values:
- `None` = omit "model" key → inherit from main agent (current configuration) ✅
- `"provider:model-name"` = use string identifier (e.g., `"anthropic:claude-sonnet-4-20250514"`, `"openai:gpt-4o"`)
- ❌ **Don't use**: Direct `ChatOpenAI` instances (causes parameter compatibility issues with custom APIs)

### Tool Organization (`src/tools/`)

**Core calculation tools** (original 36 tools):
- `portfolio_tools.py` (6 tools) - Portfolio valuation, allocation, concentration, Sharpe ratio
- `cashflow_tools.py` (6 tools) - Cash flow analysis, savings rate, expense categorization
- `goal_tools.py` (6 tools) - Retirement gap, Monte Carlo, FIRE number, college funding
- `debt_tools.py` (6 tools) - Debt payoff, avalanche/snowball, interest costs
- `tax_tools.py` (5 tools) - Tax rate, loss harvesting, Roth conversions
- `risk_tools.py` (7 tools) - Emergency fund, insurance, volatility, stress tests, VaR

**API integration tools** (38 NEW tools):
- `market_data_tools.py` (30+ tools) - Yahoo Finance Real-Time API wrapper
  - Quotes: `get_stock_quote`, `get_multiple_quotes`, `get_stock_summary`
  - Historical: `get_stock_chart`, `get_stock_timeseries`
  - Fundamentals: `get_stock_statistics`, `get_stock_financials`, `get_stock_earnings`, `get_stock_balance_sheet`, `get_stock_cashflow`
  - Research: `get_stock_profile`, `get_stock_analysis`, `get_stock_recommendations`, `get_upgrades_downgrades`
  - Ownership: `get_insider_transactions`, `get_stock_holders`, `get_major_holders`
  - ESG: `get_esg_scores`, `get_esg_chart`, `get_esg_peer_scores`
  - News: `get_news_list`, `get_sec_filings`
  - Discovery: `search_stocks`, `get_similar_stocks`, `get_calendar_events`
- `search_tools.py` (3 tools) - Tavily web search
  - `web_search` - General search with domain filtering
  - `web_search_news` - Time-constrained news search
  - `web_search_financial` - Financial sources only (Bloomberg, WSJ, Reuters)
- `portfolio_update_tools.py` (5 tools) - Portfolio persistence (NEW feature)
  - `update_investment_holding` - Buy/sell stocks, persists to `portfolio.json`
  - `update_cash_balance` - Deposits/withdrawals
  - `record_expense` - Track spending, deducts from checking
  - `update_credit_card_balance` - Update credit card balances
  - `recalculate_net_worth` - Refresh totals after updates

### API Integrations

**Yahoo Finance Real-Time API** (via RapidAPI):
- Base URL: `https://yahoo-finance15.p.rapidapi.com`
- Rate limit: 100 requests/minute
- Caching: 15-minute TTL via `src/utils/api_cache.py` (in-memory)
- Response optimization: Large responses (>500 chars) auto-saved to `/financial_data/` directory
- All tools in `market_data_tools.py` are wrappers around this API

**Tavily Search API**:
- Used for current financial news, Fed decisions, market trends
- Optional API key (has default dev key fallback)
- Domain filtering for trusted financial sources

### Human-in-the-Loop (`src/deep_agent.py`, `chat.py`, `api/`)

**Overview**:
The agent now asks for user approval before executing sensitive operations. This is implemented using LangGraph's native interrupt capabilities with checkpointing.

**Configuration** (`src/deep_agent.py`):
```python
INTERRUPT_ON_CONFIG = {
    # Tier 1: ALWAYS require approval (portfolio modifications)
    "update_investment_holding": True,     # Buy/sell stocks
    "update_cash_balance": True,            # Deposits/withdrawals
    "record_expense": True,                 # Record spending
    "update_credit_card_balance": True,     # Update credit card
    "recalculate_net_worth": True,          # Recalculate totals

    # Tier 2: Complex planning (task delegation to subagents)
    "task": True,  # Pause before spawning subagents for complex work

    # Tier 3: Auto-approve (read-only operations)
    # All other tools are auto-approved (no entry needed)
}
```

**How It Works**:
1. **Agent Execution**: When agent wants to call a sensitive tool, it pauses automatically
2. **Approval Prompt**: User sees tool name + arguments, decides: approve/reject
3. **Resume**: Agent continues with user's decisions using `Command(resume=...)`

**Implementation Details**:
- Uses `MemorySaver` checkpointer (required for interrupts)
- Thread ID tracks conversation for pause/resume
- Session manager stores pending interrupts
- Chat interface displays approval UI
- WebSocket API supports `approval_response` message type
- **Interrupt Handling**: When `node_name == "__interrupt__"`, `state_update` comes as a tuple `(Interrupt(...),)`. Code uses `isinstance(state_update, (tuple, list))` to unpack correctly
- **Action Extraction**: Each `Interrupt` object has `.value` attribute containing `{"action_requests": [...], "review_configs": [...]}`
- Debug output available in chat.py for troubleshooting interrupt extraction (lines 657-707)

**Example Flow** (CLI):
```
User: "Buy 10 shares of NVDA in my 401k"
Agent: "I'll update your investment holding."

⚠️ APPROVAL REQUIRED
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Tool: update_investment_holding
Arguments:
  account_name: 401k
  ticker: NVDA
  shares: 10
  transaction_type: buy
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Approve? ([y]es/[n]o): y
✓ Approved

🔄 Resuming agent execution...
✓ Purchased 10 shares of NVDA. Your 401k now has...
```

**Disabling HITL** (for testing):
```python
agent = create_finance_deep_agent(enable_human_in_loop=False)
```

**Files Modified**:
- `src/deep_agent.py` - Added checkpointer + interrupt_on config
- `api/session_manager.py` - Added thread_id + pending_interrupts
- `chat.py` - Approval UI and resume logic
- `api/agent_service.py` - Interrupt detection and resume method
- `api/server.py` - WebSocket approval_response handler
- `api/models.py` - ApprovalRequestEvent and ApprovalResponse models

### NEW: Hybrid Backend Architecture (`src/backends/`)

**MAJOR UPGRADE**: Adopted battle-tested backend system from langchain-ai/deepagents with hybrid storage routing!

**Architecture Overview**:
```python
CompositeBackend(
    default=StateBackend(),           # Ephemeral files (within thread)
    routes={
        "/memories/": StoreBackend(), # Persistent (cross-session)
        "/user_profiles/": StoreBackend(),
        "/analysis_history/": StoreBackend(),
        "/reports/": FilesystemBackend(root_dir=session_dir/"reports", virtual_mode=True),
        "/financial_data/": FilesystemBackend(root_dir=session_dir/"financial_data", virtual_mode=True),
    }
)
```

**Three Storage Backends**:

1. **StateBackend** (Ephemeral - Default)
   - Storage: LangGraph agent state (checkpointed)
   - Lifetime: Within conversation thread only
   - Use for: `/working/`, `/temp/`, `/cache/` - temporary files
   - Advantage: Fast, no disk I/O, automatically cleaned up

2. **StoreBackend** (Persistent - Cross-Session)
   - Storage: LangGraph BaseStore (InMemoryStore default, can use PostgreSQL/Redis)
   - Lifetime: Survives across all sessions forever
   - Use for: `/memories/`, `/user_profiles/`, `/analysis_history/`
   - Advantage: True long-term memory, namespace isolation per user

3. **FilesystemBackend** (Real Disk Files)
   - Storage: Actual filesystem at `sessions/{session_id}/`
   - Lifetime: Persists on disk until manually deleted
   - Use for: `/reports/`, `/financial_data/`
   - Advantage: Inspectable, shareable, debuggable

**Directory Structure**:
```
sessions/{session_id}/
├── reports/              # Real disk files (FilesystemBackend)
│   └── retirement_analysis_2025-10-31.md
├── financial_data/       # Real disk files (FilesystemBackend)
│   ├── current_prices.json
│   └── portfolio_snapshot.json

LangGraph State (StateBackend - ephemeral):
├── /working/calculations.txt
├── /temp/scratch.json
└── /cache/api_results.json

LangGraph Store (StoreBackend - persistent):
├── /memories/investment_philosophy.txt
├── /user_profiles/kabeer_preferences.json
└── /analysis_history/2024_review.md
```

**Security Features** (from deepagents):
- ✅ Path traversal protection (.., ~ blocked)
- ✅ O_NOFOLLOW flag to prevent symlink attacks
- ✅ Virtual mode sandboxing (paths contained to root)
- ✅ Path validation and normalization

**Advanced Features**:
- ✅ Ripgrep integration for 10-100x faster file search (with Python fallback)
- ✅ Structured FileInfo and GrepMatch return types
- ✅ File size limits for grep operations (10MB default)
- ✅ Line number formatting with continuation markers
- ✅ Pagination support (offset/limit) for large files

**Backend Protocol** (`src/backends/protocol.py`):
All backends implement unified interface:
```python
class BackendProtocol:
    def ls_info(path: str) -> list[FileInfo]
    def read(file_path: str, offset: int, limit: int) -> str
    def write(file_path: str, content: str) -> WriteResult
    def edit(file_path: str, old_string: str, new_string: str, replace_all: bool) -> EditResult
    def grep_raw(pattern: str, path: str, glob: str) -> list[GrepMatch] | str
    def glob_info(pattern: str, path: str) -> list[FileInfo]
```

**Migration from Old System**:
- ❌ **DEPRECATED**: `LocalFilesystemBackend` (simple disk writes)
- ✅ **NEW**: `CompositeBackend` with hybrid routing
- Files now intelligently routed based on path prefix
- Existing `portfolio.json` still updated by `portfolio_update_tools.py`

**Benefits**:
1. **Context Optimization**: 60-80% reduction for API-heavy workflows (FilesystemMiddleware auto-evicts large results)
2. **True Long-term Memory**: User preferences persist across all sessions forever
3. **Clean Separation**: Ephemeral vs persistent vs reports clearly separated
4. **Security**: Hardened against path traversal and symlink attacks
5. **Performance**: Ripgrep for 10-100x faster file search
6. **Maintainability**: Battle-tested deepagents code instead of custom implementation

### Data Flow Example

1. **User query**: "Calculate my portfolio value with current prices"
2. **Main agent** (`deep_agent.py`):
   - Creates todos with `write_todos`
   - Reads `portfolio.json` → extracts tickers (NVDA, AVGO, etc.)
   - Spawns `market-data-fetcher` subagent via `task` tool
3. **market-data-fetcher subagent**:
   - Uses `get_multiple_quotes(symbols=["NVDA", "AVGO", ...])` from `market_data_tools.py`
   - Yahoo Finance API called (cached 15min via `api_cache.py`)
   - Large responses saved to `/financial_data/current_prices.json`
   - Returns quotes to main agent
4. **Main agent**:
   - Reads prices from `/financial_data/current_prices.json`
   - Spawns `portfolio-analyzer` subagent
5. **portfolio-analyzer subagent**:
   - Uses `calculate_portfolio_value()` from `portfolio_tools.py`
   - Returns breakdown by account
6. **Main agent**:
   - Synthesizes results, responds to user

### Chat Interface (`chat.py`)

**Key features**:
- **🚀 ASYNC EXECUTION**: Fully asynchronous for better performance and responsiveness
- Conversation history pruning: Keeps last 5 turns (user + AI pairs) to prevent context bloat
- Token estimation: Warns if context >150K tokens
- Streaming execution: Shows step-by-step tool calls, file updates, todos
- Colored terminal output with progress indicators
- **Friendly node names**: Clear agent identification ("🤖 Main Agent" instead of "model")
- **Context details**: Shows input/output message breakdown for Context Management step
- Commands: `quit`/`exit`/`q`, `clear` (reset history), `help`

**Async Architecture**:
- Uses `asyncio.run()` to execute the main event loop
- `agent.astream()` for non-blocking streaming execution
- `asyncio.to_thread()` for input operations to prevent blocking
- Enables parallel subagent execution for 3-5x faster responses
- Example: When comparing 3 stocks, all 3 subagents run simultaneously instead of sequentially

**Display enhancements (chat.py:177-426)**:

**Core Display Functions**:
- `format_value()`: Increased limit from 500→10000 chars, shows first 20 list items (was 5)
- `print_tool_call()`: Shows ALL tool arguments with proper wrapping using textwrap module
  - Subagent spawns: Full description with 📋 icon, 90-char width wrapping
  - File operations: Full content preview (was 150 chars, now 5000)
  - Tool args: Increased from 300→5000 char display limit
- `print_tool_result()`: **Complete rewrite** with smart JSON parsing
  - **Smart detection**: Recognizes stock quotes, financial metrics, summaries
  - **Bullet formatting**: Converts JSON to readable bullet points
  - **Stock quotes**: Shows price, change %, volume, market cap with color coding (green=up, red=down)
  - **Financial metrics**: Auto-formats numbers ($1.5B, $234.5M, etc.)
  - **Full display**: Shows up to 5000 chars (was 500), 100 lines (was 10), 30 summary lines (was 10)
  - **Additional fields**: Shows remaining fields not covered by smart detection (15 fields max)
  - **No more "✓ SUCCESS" only**: Always shows actual data content

**Visual Elements**:
- Icons: 📊 (stock data), 💰 (metrics), 📋 (summary), 💾 (saved files), 📦 (data), ℹ️ (info)
- Color coding: Green for positive changes, red for negative, cyan for info, blue for data
- Proper indentation for subagent tool calls (2-space indent)

**Friendly Node Names**:
- `get_friendly_node_name()`: Maps technical names to user-friendly labels
  - "PatchToolCallsMiddleware.before_agent" → "Pre-processing"
  - "SummarizationMiddleware.before_model" → "Context Management"
  - "model" → "🤖 Main Agent"
  - "tools" → "Tool Execution"
- `print_step_header()`: Shows conceptual information for middleware steps
  - Context Management: Shows optimization activities
  - Pre-processing: Shows preparation steps
  - Note: Middleware in `stream_mode="updates"` doesn't provide state deltas, so we show what they do conceptually

**Approval Requests** (`print_approval_request()`, chat.py:485-520):
- Enhanced formatting with textwrap for long descriptions
- Color-coded arguments (cyan)
- Full data display (5000 char limit)
- No more truncation of approval details

**Debug Output Cleanup**:
- Removed all DEBUG prints from production (lines 738-745, 760, 769-770, 775, 780-781 removed)
- Cleaner approval flow without interrupt structure debugging

**State management**:
- `conversation_messages`: List of HumanMessage and AIMessage objects
- `files`: Dict of agent filesystem (merged after each agent call)
- State passed to `agent.astream(state, stream_mode="updates")` (async streaming)
- Async execution with `async for chunk in agent.astream(...)`

### Important Implementation Details

**Model**: Main agent uses Z.ai GLM-4.6, all subagents use Z.ai GLM-4.6 (configured via `ChatOpenAI` instance with custom API endpoint)

**Caching** (`src/utils/api_cache.py`):
- In-memory cache with TTL
- Keys: MD5 hash of (endpoint, params)
- Graceful degradation if cache fails

**Response optimization** (`src/utils/response_optimizer.py`):
- Auto-saves large API responses to disk
- Returns compact summary with extracted metrics (NOT full JSON)
- **99.5% token reduction**: 26,594 tokens → 138 tokens per tool call
- Threshold: 300 characters
- Extracts key metrics: price, volume, market cap, P/E, beta, etc.
- Smart summaries: "META - Price: $666.47 (-85.20, -0.11%), Vol: 87.34M, MCap: $1.68T"

**Portfolio updates** (`portfolio_update_tools.py`):
- Loads `portfolio.json` from disk
- Updates investment holdings, cash accounts, expenses, credit cards
- Saves back to disk with `json.dump()`
- Returns success message with before/after values

## Development Patterns

### Adding a new tool
1. Create tool function in appropriate `src/tools/*_tools.py` file
2. Decorate with `@tool` from `langchain_core.tools`
3. Add comprehensive docstring (used by LLM to understand tool)
4. Import and add to subagent's `tools` list in `src/subagents_config.py`

### Adding a new subagent
1. Define subagent dict in `src/subagents_config.py`:
   - `name`: Kebab-case identifier
   - `description`: When to delegate to this agent
   - `system_prompt`: Role, responsibilities, best practices
   - `tools`: List of tool functions
   - `model`: Model override (optional, add to SUBAGENT_MODELS dict)
2. Append to `FINANCIAL_SUBAGENTS` list
3. Add model config to `SUBAGENT_MODELS` dict
4. Update main agent system prompt in `src/deep_agent.py` to mention new subagent

### Changing models

**Current Setup**: All agents (main + 8 subagents) use Z.ai GLM-4.6

**To change the main agent model** (and all subagents inherit it):
1. Edit `src/deep_agent.py` (lines 360-366)
2. Modify the `ChatOpenAI` instance:
   ```python
   model = ChatOpenAI(
       temperature=0,
       model="your-model-name",
       openai_api_key="your-api-key",
       openai_api_base="https://your-api-endpoint/"
   )
   ```
3. All subagents automatically inherit this model (since `SUBAGENT_MODELS` values are `None`)

**To use different models for specific subagents**:
1. Edit `SUBAGENT_MODELS` dict in `src/subagents_config.py` (lines 26-35)
2. Change from `None` to a string identifier:
   - `"anthropic:claude-sonnet-4-20250514"` = Claude Sonnet 4
   - `"anthropic:claude-haiku-4-20250514"` = Claude Haiku 4
   - `"openai:gpt-4o"` = GPT-4o
   - `"openai:gpt-4o-mini"` = GPT-4o mini
3. **Note**: Avoid using `ChatOpenAI` instances directly in `SUBAGENT_MODELS` - use `None` or string identifiers to prevent parameter compatibility issues

**Example**: Fast subagents with Haiku, complex analysis with Sonnet
```python
SUBAGENT_MODELS = {
    "market-data-fetcher": "anthropic:claude-haiku-4-20250514",  # Simple data fetching
    "research-analyst": "anthropic:claude-sonnet-4-20250514",    # Complex analysis
    "portfolio-analyzer": None,  # Inherit from main agent
    # ...
}
```

### Modifying portfolio schema
The portfolio JSON schema (`portfolio.json`) has this structure:
```json
{
  "client": { "name": "...", "age": 24 },
  "financial_snapshot": { "total_net_worth": 46000 },
  "income": { "gross_annual_salary": 130000, "monthly_net_income": 6224.20 },
  "investment_accounts": {
    "account_name": {
      "account_type": "401k" | "taxable_brokerage" | "roth_ira",
      "total_value": 23000,
      "holdings": [
        { "ticker": "VTSAX", "shares": 100.5, "cost_basis": 95.00 }
      ]
    }
  },
  "liquid_accounts": {
    "checking": 11573.76,
    "savings": 6315.12,
    "emergency_fund": 17888.88
  },
  "liabilities": {
    "credit_cards": {
      "chase_sapphire": 1396.00
    }
  }
}
```

If modifying schema:
1. Update `portfolio.json` example file
2. Update tools in `portfolio_tools.py`, `cashflow_tools.py` to match new structure
3. Update `portfolio_update_tools.py` helper functions (`_load_portfolio`, `_save_portfolio`)
4. Test with `pytest tests/`

### API rate limiting
Yahoo Finance API: 100 requests/minute
- Use `get_multiple_quotes()` instead of multiple `get_stock_quote()` calls
- Leverage 15-minute cache to reduce API hits
- Batch portfolio analysis requests

## Common Gotchas

1. **Two portfolio representations**:
   - `portfolio.json` (project root) = real persistent file, modified by `portfolio_update_tools.py`
   - `sessions/{session_id}/financial_data/*.json` = session-specific files written to disk by agent

2. **Context bloat**: Chat history keeps last 5 turns only. Pruning logic in `chat.py:prune_conversation_history()`. Can increase `MAX_CONVERSATION_TURNS` if needed, but watch token usage.

3. **API key errors**: If Yahoo Finance tools fail, check `RAPIDAPI_KEY` in `.env`. Subscribe at https://rapidapi.com/sparior/api/yahoo-finance15.

4. **Tool docstrings are critical**: LLM uses docstrings to understand when/how to call tools. Make them detailed and include parameter descriptions.

5. **Subagent delegation**: Main agent must explicitly spawn subagents with `task` tool. Subagents don't automatically activate based on user query.

6. **write_file requires content**: The `write_file(file_path, content)` tool requires BOTH arguments. LLMs sometimes try to call it with just file_path, which fails with "content: Field required" error. System prompt now has explicit guidance and examples (src/deep_agent.py:165-170, 294).
