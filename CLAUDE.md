# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Personal Finance Deep Agent - A multi-agent financial analysis system using DeepAgents framework with LangGraph orchestration. Features 8 specialized subagents, 74+ financial tools, real-time Yahoo Finance API integration, web search via Tavily, and portfolio persistence.

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

### Multi-Agent System (DeepAgents + LangGraph)

**Main Agent** (`src/deep_agent.py`):
- Orchestrates subagents using DeepAgents framework
- Claude 4.5 Haiku model
- Uses `task` tool to spawn specialized subagents
- Manages filesystem backend for data persistence
- System prompt emphasizes: plan with `write_todos`, delegate to subagents, synthesize results

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

### Filesystem Backend (`src/backends_config.py`)

DeepAgents uses a virtual filesystem for data persistence:

**Persistent directories** (intended to persist across sessions):
- `/financial_data/` - User portfolios, accounts, API responses
- `/user_profiles/` - User preferences, risk tolerance
- `/reports/` - Final analysis reports
- `/analysis_history/` - Past analyses

**Ephemeral directories** (temporary):
- `/working/` - Scratch space for calculations
- `/temp/` - Temporary files

**Implementation**: Currently uses `deepagents.backends.utils.create_file_data()` for in-memory file simulation. Files are passed in agent state dict under `"files"` key.

**Important**: `portfolio.json` at project root is the REAL portfolio file that gets updated by `portfolio_update_tools.py`. The `/financial_data/` files are agent-internal representations.

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
- Conversation history pruning: Keeps last 5 turns (user + AI pairs) to prevent context bloat
- Token estimation: Warns if context >150K tokens
- Streaming execution: Shows step-by-step tool calls, file updates, todos
- Colored terminal output with progress indicators
- Commands: `quit`/`exit`/`q`, `clear` (reset history), `help`

**State management**:
- `conversation_messages`: List of HumanMessage and AIMessage objects
- `files`: Dict of agent filesystem (merged after each agent call)
- State passed to `agent.stream(state, stream_mode="updates")`

### Important Implementation Details

**Model**: Uses "claude-haiku-4-5" (typo in code, should be "claude-3-5-haiku-20241022" but works due to LangChain aliasing)

**Caching** (`src/utils/api_cache.py`):
- In-memory cache with TTL
- Keys: MD5 hash of (endpoint, params)
- Graceful degradation if cache fails

**Response optimization** (`src/utils/response_optimizer.py`):
- Auto-saves large API responses to disk
- Returns compact summary to agent to avoid context bloat
- Threshold: 500 characters

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
2. Append to `FINANCIAL_SUBAGENTS` list
3. Update main agent system prompt in `src/deep_agent.py` to mention new subagent

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

1. **Model name typo**: Code uses "claude-haiku-4-5" but should be "claude-3-5-haiku-20241022". Works due to LangChain aliasing, but confusing.

2. **Two portfolio representations**:
   - `portfolio.json` (project root) = real persistent file, modified by `portfolio_update_tools.py`
   - `/financial_data/*.json` (agent filesystem) = in-memory agent state, passed via `files` dict

3. **Context bloat**: Chat history keeps last 5 turns only. Pruning logic in `chat.py:prune_conversation_history()`. Can increase `MAX_CONVERSATION_TURNS` if needed, but watch token usage.

4. **API key errors**: If Yahoo Finance tools fail, check `RAPIDAPI_KEY` in `.env`. Subscribe at https://rapidapi.com/sparior/api/yahoo-finance15.

5. **Tool docstrings are critical**: LLM uses docstrings to understand when/how to call tools. Make them detailed and include parameter descriptions.

6. **Subagent delegation**: Main agent must explicitly spawn subagents with `task` tool. Subagents don't automatically activate based on user query.
