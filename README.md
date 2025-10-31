# Personal Finance Deep Agent 🤖💰

A production-ready multi-agent financial analysis system powered by **DeepAgents**, **LangGraph**, and **Z.ai GLM-4.6**. Features real-time market data, web search capabilities, intelligent portfolio management, and **complete execution visibility** with 74+ specialized financial tools across 8 expert subagents.

## 🆕 Recent Updates (2025-10-31)

**🚀 NEW: Ultra-Rich Terminal Output (Just Added!)**
- ✅ **Smart JSON Parsing** - Converts raw JSON to beautiful bullet-point format (NEW!)
  - Stock quotes: Price, change %, volume, market cap with color coding
  - Financial metrics: Auto-formatted numbers ($1.5B, $234.5M)
  - All tool results shown in full (no more "✓ SUCCESS" without data)
- ✅ **Full Data Display** - Increased limits from 500→10000 chars, 10→100 lines
  - Tool arguments: 300→5000 char display
  - Proper text wrapping with textwrap module (no more broken words)
  - Shows first 20 list items (was 5), 30 summary lines (was 10)
- ✅ **Enhanced Visual Elements** - Rich icons and colors throughout
  - Icons: 📊 stock data, 💰 metrics, 📋 summaries, 💾 saved files, 📦 data, ℹ️ info
  - Colors: Green for gains, red for losses, cyan for info, blue for data
- ✅ **Debug Output Removed** - Clean production display without technical noise

**🚀 Token Optimization & Custom Model Backend:**
- ✅ **99.5% Token Reduction** - Optimized tool responses from 26K → 138 tokens per call
  - Deep analysis now uses ~150K tokens instead of 2.8M tokens
  - Removed full JSON payloads, extracted key metrics only
  - Smart summaries: "META - Price: $666.47 (-85.20, -0.11%), Vol: 87.34M, MCap: $1.68T"
- ✅ **Z.ai GLM-4.6 Model** - Switched from OpenAI to Z.ai's GLM-4.6 for all agents
- ✅ **Subagent Model Inheritance Fix** - Fixed `'NoneType' has no attribute 'bind_tools'` error
- ✅ **Async Execution** - Fully asynchronous with `asyncio` for 3-5x faster parallel operations
- ✅ **CompositeBackend** - Intelligent routing to different storage backends
- ✅ **StateBackend** - Ephemeral files in LangGraph state (fast, auto-cleanup)
- ✅ **StoreBackend** - Persistent cross-session memory (user preferences, analysis history)
- ✅ **FilesystemBackend** - Real disk files with security hardening (reports, data)
- ✅ **FilesystemMiddleware** - Auto-eviction of large tool results (60-80% context savings)
- ✅ **Security** - Path traversal protection, O_NOFOLLOW, sandboxing
- ✅ **Performance** - Ripgrep integration for 10-100x faster file search

**Major enhancements from 2025-10-30:**
- ✅ **Date/Time Awareness** - All agents now know current date/time for accurate calculations
- ✅ **Store Infrastructure** - LangGraph Store integrated for future cross-session memory
- ✅ **Tool Logging** - Subagent tool calls now visible in real-time (even in "black box" subagents)
- ✅ **Friendly Node Names** - Clear agent labels ("🤖 Main Agent") and context details
- ✅ **Hybrid Agent Architecture** - Main agent has 6 quick-access tools for instant responses
- ✅ **Human-in-the-Loop Approvals** - Agent asks permission before sensitive operations
- ✅ **Code Cleanup** - Removed legacy routing code for cleaner architecture

**Hybrid Architecture = Best of Both Worlds:**
- **Simple queries** → Main agent uses tools directly → ⚡ **Instant response** (2 steps)
  - "What's AAPL price?" → Direct `get_stock_quote` call → Done!
- **Complex analysis** → Delegates to expert subagents → 🎓 **Specialized expertise**
  - "Analyze portfolio risk" → Spawns `risk-assessor` → Expert analysis

**Complete Visibility:**
- Which agent is executing (Main Agent clearly labeled)
- What middleware is doing (Pre-processing, Context Management)
- Which tools are being called with full arguments
- What results are returned with smart formatting

## ✨ Key Features

### Architecture
⚡ **Hybrid Agent System** - Main agent handles simple queries instantly, delegates complex work to specialists
🤖 **8 Specialized Subagents** - Market data, research, portfolio, cash flow, goals, debt, tax, risk
📊 **80+ Financial Tools** - 6 quick-access tools + 74+ specialized tools across subagents

### Data & Integration
🔥 **Real-Time Market Data** - Yahoo Finance API integration with 30+ endpoints
🔍 **Web Search** - Tavily API for current news, events, and financial analysis
💼 **Portfolio Persistence** - Trades, expenses, and transactions saved to disk
⚡ **Smart API Caching** - 15-minute TTL, response optimization, rate limiting

### User Experience
💬 **Interactive Chat** - Natural language with streaming execution and rich colored output
👁️ **Complete Visibility** - See every tool call with full inputs/outputs (even from subagents!)
🎨 **Ultra-Rich Display** - Smart JSON parsing with bullet points, icons, and color coding
  - Stock quotes with price changes (green ↑ / red ↓)
  - Auto-formatted financial metrics ($1.5B, $234.5M)
  - Full data display (10K chars, 100 lines, no truncation)
  - Proper text wrapping (no broken words)
🏷️ **Friendly Node Names** - Clear agent labels ("🤖 Main Agent") and middleware context
📅 **Time-Aware** - All agents know current date/time for accurate calculations
🛡️ **Human-in-the-Loop Approvals** - Agent asks permission before sensitive operations (portfolio changes, subagent spawning)

### Advanced Features
🎯 **Monte Carlo Simulations** - Probabilistic retirement projections with 10,000 scenarios
💾 **Store Infrastructure** - Foundation for long-term memory across sessions
🔄 **Parallel Execution** - Independent subagents run simultaneously for speed

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
# Clone the repository
git clone https://github.com/KabeerThockchom/personalPortfolioDeepAgent.git
cd personalPortfolioDeepAgent

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install packages
pip install -r requirements.txt
```

### 2. Set Up API Keys

```bash
# Copy environment template
cp .env.example .env

# Add your API keys to .env:
# - Z.ai API credentials are hardcoded in src/deep_agent.py and src/subagents_config.py
# - RAPIDAPI_KEY (required - get from https://rapidapi.com/sparior/api/yahoo-finance15)
# - TAVILY_API_KEY (optional - defaults to dev key, get from https://tavily.com)
```

### 3. Run the Interactive Chat

```bash
python3 chat.py
```

**Example conversation:**
```
You: Calculate my portfolio value with current prices
🤖 Fetching real-time quotes from Yahoo Finance...
    Your portfolio is worth $48,744.64
    • 401(k): $23,872.09
    • Robinhood: $6,982.83
    • Cash: $17,888.88

You: I bought 5 shares of AAPL at $180
🤖 ✅ Updated AAPL: 0 → 5 shares @ $180.00
    💾 Portfolio saved to disk

You: What's the latest news on NVDA?
🤖 🔍 Searching financial news...
    [Returns recent NVIDIA news from Bloomberg, WSJ, Reuters]
```

### 4. (Optional) Deep Agents UI - Next.js Web Interface 🌐 ⭐ NEW

For the official **deep-agents-ui** with rich web interface:

**Step 1: Start LangGraph Server**
```bash
# From project root
./start_langgraph_server.sh

# Or manually:
langgraph dev
```

**Step 2: Clone and Set Up UI (first time only)**
```bash
# Clone UI (outside this project)
cd ..
git clone https://github.com/langchain-ai/deep-agents-ui.git
cd deep-agents-ui

# Install dependencies
npm install

# Configure environment
cat > .env.local << EOF
NEXT_PUBLIC_DEPLOYMENT_URL="http://127.0.0.1:2024"
NEXT_PUBLIC_AGENT_ID="finance-agent"
EOF
```

**Step 3: Start UI**
```bash
cd ../deep-agents-ui
npm run dev
```

Visit **http://localhost:3000** for the official LangChain deep-agents-ui!

**Features:**
- 🌐 Modern Next.js interface
- 💬 Real-time streaming chat
- 🔧 Tool call visualization
- 🤖 Subagent activity tracking
- 🛡️ Human-in-the-loop approvals
- 📊 LangSmith integration (production)

**📖 Full Setup Guide:** See `DEEPAGENTS_UI_SETUP.md` for complete instructions

---

### 4b. (Alternative) Custom FastAPI Web Interface

For the custom WebSocket-based interface:

**Start Backend API:**
```bash
# From project root
uvicorn api.server:app --reload --port 8000
```

**Start Frontend (in new terminal):**
```bash
cd ../personal-finance-frontend
npm install
npm run dev
```

Visit **http://localhost:5173** for the custom web interface!

**Features:**
- 💬 Real-time chat with streaming responses
- 🔧 Tool call visualization with animated cards
- 🤖 Live subagent activity tracking
- 📊 Portfolio dashboard
- ✅ Task progress monitoring
- 📁 File explorer for agent-created files

See `api/README.md` and `../personal-finance-frontend/README.md` for detailed documentation.

---

## 🏗️ Architecture

The system uses **DeepAgents** framework with a supervisor pattern. The main agent spawns specialized subagents for focused analysis:

```
                    ┌─────────────────────┐
                    │   Main Deep Agent   │
                    │   (Z.ai GLM-4.6)    │
                    └──────────┬──────────┘
                               │
        ┌──────────────────────┼──────────────────────┐
        │                      │                      │
   ┌────▼─────┐         ┌──────▼──────┐       ┌──────▼──────┐
   │  Market  │         │  Research   │       │  Portfolio  │
   │   Data   │         │  Analyst    │       │  Analyzer   │
   └──────────┘         └─────────────┘       └─────────────┘
        │                      │                      │
   ┌────▼─────┐         ┌──────▼──────┐       ┌──────▼──────┐
   │ Cash Flow│         │    Goal     │       │    Debt     │
   │ Analyzer │         │   Planner   │       │   Manager   │
   └──────────┘         └─────────────┘       └─────────────┘
        │                      │                      │
   ┌────▼─────┐         ┌──────▼──────┐
   │   Tax    │         │    Risk     │
   │Optimizer │         │  Assessor   │
   └──────────┘         └─────────────┘
```

---

## 🤖 8 Specialized Subagents

### 1. 📊 Market Data Fetcher ⭐ NEW

**Real-time Yahoo Finance API integration**

**Capabilities:**
- Current stock quotes and prices (single or batch)
- Historical price data and charts
- Company fundamentals (balance sheet, income statement, cash flow)
- Key statistics (P/E ratio, market cap, beta, dividend yield)
- Stock/ETF/fund profiles and holdings

**Tools (17 total):**
- `get_stock_quote`, `get_multiple_quotes`, `get_stock_summary`
- `get_stock_chart`, `get_stock_timeseries`
- `get_stock_statistics`, `get_stock_financials`, `get_stock_earnings`
- `search_stocks`, `get_fund_profile`, `get_top_holdings`
- Plus web search tools (3)

**API Features:**
- 15-minute caching for performance
- Rate limiting (100 requests/min)
- Auto-saves large responses to `/financial_data/`

---

### 2. 🔬 Research Analyst ⭐ NEW

**Deep company research and market intelligence**

**Capabilities:**
- Company profiles and business descriptions
- Analyst recommendations and price targets
- Recent upgrades/downgrades
- Insider trading activity (buying/selling by executives)
- Major institutional holders and ownership changes
- Financial news and company updates
- SEC filings (10-K, 10-Q, 8-K)
- ESG (Environmental, Social, Governance) scores
- Similar/comparable companies
- Upcoming events (earnings, dividends)

**Tools (23 total):**
- `get_stock_profile`, `get_stock_insights`, `get_stock_recent_updates`
- `get_stock_analysis`, `get_stock_recommendations`, `get_upgrades_downgrades`
- `get_insider_transactions`, `get_insider_roster`
- `get_stock_holders`, `get_major_holders`
- `get_esg_scores`, `get_esg_chart`, `get_esg_peer_scores`
- `get_news_list`, `get_news_article`, `get_sec_filings`
- `get_similar_stocks`, `get_calendar_events`
- Plus web search tools (3)

---

### 3. 💼 Portfolio Analyzer

**Investment analysis and optimization**

**Capabilities:**
- Portfolio valuation with real-time prices
- Asset allocation analysis
- Concentration risk identification
- Risk-adjusted returns (Sharpe ratio)
- Rebalancing recommendations
- **Portfolio updates** - Buy/sell stocks and persist to disk ⭐ NEW

**Tools (15 total):**
- `calculate_portfolio_value`, `calculate_asset_allocation`
- `calculate_concentration_risk`, `calculate_sharpe_ratio`
- `check_rebalancing_needs`, `generate_allocation_chart`
- `update_investment_holding` ⭐ NEW - Record buys/sells
- `recalculate_net_worth` ⭐ NEW - Refresh totals
- Plus market data tools (4) and web search (3)

**Example:**
```
You: I bought 10 shares of MSFT at $350 in my 401k
Agent: ✅ Added new holding: MSFT - 10 shares @ $350.00
       💾 401(k) total: $27,372.09
       📁 Portfolio saved to disk
```

---

### 4. 💵 Cash Flow Analyzer

**Income, expenses, and budgeting analysis**

**Capabilities:**
- Net monthly cash flow calculation
- Savings rate (gross and net)
- Expense categorization and trends
- Future cash flow projections
- Emergency fund runway (burn rate)
- **Transaction recording** - Track expenses and cash movements ⭐ NEW

**Tools (13 total):**
- `analyze_monthly_cashflow`, `calculate_savings_rate`
- `categorize_expenses`, `project_future_cashflow`
- `calculate_burn_rate`, `generate_waterfall_chart`
- `update_cash_balance` ⭐ NEW - Deposits/withdrawals
- `record_expense` ⭐ NEW - Track spending
- `update_credit_card_balance` ⭐ NEW - Update cards
- `recalculate_net_worth` ⭐ NEW
- Plus web search tools (3)

**Example:**
```
You: I spent $150 on groceries today
Agent: ✅ Recorded expense: $150.00 (groceries)
       💰 Checking: $11,573.76 → $11,423.76
       📁 Portfolio saved to disk
```

---

### 5. 🎯 Goal Planner

**Retirement and financial goal planning**

**Capabilities:**
- Retirement readiness assessment
- Monte Carlo simulations (1000+ scenarios)
- Required savings rate calculations
- FIRE (Financial Independence) number calculation
- College funding (529 plan) analysis
- Goal progress tracking
portfolio
**Tools (12 total):**
- `calculate_retirement_gap`, `run_monte_carlo_simulation`
- `calculate_required_savings_rate`, `calculate_fire_number`
- `project_college_funding`, `generate_monte_carlo_chart`
- Plus market data tools (3) and web search (3)

---

### 6. 💳 Debt Manager

**Debt optimization and payoff strategies**

**Capabilities:**
- Debt payoff timeline calculation
- Avalanche vs snowball strategy comparison
- Optimal extra payment allocation
- Total interest cost analysis
- Debt-to-income ratio assessment
- Refinancing opportunity identification

**Tools (9 total):**
- `calculate_debt_payoff_timeline`, `compare_avalanche_vs_snowball`
- `calculate_total_interest_cost`, `optimize_extra_payment_allocation`
- `calculate_debt_to_income_ratio`, `generate_payoff_chart`
- Plus web search tools (3)

---

### 7. 🧾 Tax Optimizer

**Tax-efficient strategies and optimization**

**Capabilities:**
- Effective tax rate calculation
- Tax loss harvesting opportunity identification
- Roth conversion analysis
- Tax-efficient withdrawal sequence optimization
- Capital gains tax calculation

**Tools (8 total):**
- `calculate_effective_tax_rate`
- `identify_tax_loss_harvesting_opportunities`
- `analyze_roth_conversion_opportunity`
- `optimize_withdrawal_sequence`
- `calculate_capital_gains_tax`
- Plus web search tools (3)

---

### 8. ⚠️ Risk Assessor

**Financial risk analysis and stress testing**

**Capabilities:**
- Emergency fund adequacy assessment
- Insurance coverage gap identification
- Portfolio volatility calculation
- Stress test scenarios (market crashes)
- Value at Risk (VaR) calculation
- Concentration risk analysis

**Tools (15 total):**
- `calculate_emergency_fund_adequacy`, `analyze_insurance_gaps`
- `calculate_portfolio_volatility`, `run_stress_test_scenarios`
- `calculate_value_at_risk`, `analyze_concentration_risk`
- `generate_risk_dashboard`
- Plus market data tools (4), ESG tools (2), web search (3)

---

## 🌐 API Integrations

### Yahoo Finance Real-Time API (RapidAPI)

**Endpoint:** https://rapidapi.com/sparior/api/yahoo-finance15

**Features:**
- 30+ endpoints implemented
- Real-time quotes, historical data, fundamentals
- Company profiles, analyst ratings, SEC filings
- ESG scores, insider transactions, news
- 15-minute caching with TTL
- Rate limiting: 100 requests/minute
- Auto-optimization for large responses

**API Key Required:** `RAPIDAPI_KEY` in `.env`

---

### Tavily Search API

**Endpoint:** https://tavily.com

**Features:**
- Real-time web search for current events
- News-specific search with time constraints
- Financial news from trusted sources (Bloomberg, WSJ, Reuters, etc.)
- Domain filtering and relevance scoring

**Tools:**
- `web_search` - General web search with domain filtering
- `web_search_news` - Time-constrained news search
- `web_search_financial` - Financial sources only

**API Key:** `TAVILY_API_KEY` in `.env` (optional, defaults to dev key)

**Example:**
```
You: What's the latest on Federal Reserve rate decisions?
Agent: 🔍 Searching financial news...
       [Returns recent Fed articles from WSJ, Bloomberg, Reuters]
```

---

## 💾 Portfolio Update System ⭐ NEW

The system can now **persist changes to your portfolio file** (`kabeer_portfolio.json`) when you report transactions.

### 5 Update Tools

**1. `update_investment_holding`** - Buy/sell stocks
```
You: I bought 10 shares of Apple at $150 in my Robinhood account
Agent: ✅ Added new holding: AAPL - 10 shares @ $150.00
       💾 Account taxable_brokerage total: $8,482.83
       📁 Portfolio saved to disk
```

**2. `update_cash_balance`** - Deposits/withdrawals
```
You: I deposited $1000 to savings
Agent: ✅ Deposited $1,000.00 to savings
       💰 Savings: $6,315.12 → $7,315.12
       📁 Portfolio saved to disk
```

**3. `record_expense`** - Track spending
```
You: I spent $80 on dinner
Agent: ✅ Recorded expense: $80.00 (dining_out)
       💰 Checking: $11,573.76 → $11,493.76
       📁 Portfolio saved to disk
```

**4. `update_credit_card_balance`** - Update cards
```
You: My Apple Card balance is now $850
Agent: ✅ Updated apple_card: $695.90 → $850.00
       💳 Total CC balance: $2,091.90
       📁 Portfolio saved to disk
```

**5. `recalculate_net_worth`** - Refresh totals
```
Agent: ✅ Net worth recalculated:
       📊 Assets: $48,291.97
       💳 Liabilities: $1,936.80
       💰 Net Worth: $46,355.17
```

---

## 🛡️ Human-in-the-Loop Approvals ⭐ NEW

The agent now **asks for your permission** before executing sensitive operations. This prevents accidental portfolio changes and gives you control over complex tasks.

### What Requires Approval?

**Tier 1 - Portfolio Modifications** (always require approval):
- `update_investment_holding` - Buy/sell stocks
- `update_cash_balance` - Deposits/withdrawals
- `record_expense` - Track spending
- `update_credit_card_balance` - Update credit cards
- `recalculate_net_worth` - Recalculate totals

**Tier 2 - Complex Planning** (requires approval):
- `task` - Spawning subagents for complex analysis

### How It Works

1. Agent detects a sensitive operation
2. Execution pauses automatically
3. You see tool name + arguments
4. You decide: **approve** or **reject**
5. Agent continues with your decision

### Example: Portfolio Trade Approval
```
You: Buy 10 shares of NVDA in my 401k

Agent: I'll update your investment holding.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🛑 Agent Paused - Approval Required
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚠️  APPROVAL REQUIRED
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Tool: update_investment_holding
Arguments:
  account_name: 401k
  ticker: NVDA
  shares: 10
  transaction_type: buy
  price_per_share: None (will fetch current price)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Approve? ([y]es/[n]o): y
✓ Approved

🔄 Resuming agent execution...
✓ Purchased 10 shares of NVDA at $147.63
  💾 401(k) total: $25,348.39
  📁 Portfolio saved to disk
```

### Example: Subagent Approval
```
You: Do a deep dive analysis on META stock

Agent: I'll spawn subagents to analyze META comprehensively.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🛑 Agent Paused - Approval Required
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Request 1 of 2:
⚠️  APPROVAL REQUIRED
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Tool: task
Arguments:
  agent_name: research-analyst
  task_description: Get comprehensive research data on META including analyst ratings, insider trades, and ESG scores
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Approve? ([y]es/[n]o): y
✓ Approved

Request 2 of 2:
⚠️  APPROVAL REQUIRED
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Tool: task
Arguments:
  agent_name: market-data-fetcher
  task_description: Fetch current price, fundamentals, and historical performance for META
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Approve? ([y]es/[n]o): y
✓ Approved

🔄 Resuming agent execution...
🚀 Spawning research-analyst subagent...
🚀 Spawning market-data-fetcher subagent...
[Full analysis continues...]
```

### Technical Implementation

Uses **LangGraph's native interrupt capabilities** with checkpointing:
- `MemorySaver` checkpointer tracks conversation state
- Thread ID enables pause/resume across turns
- Interrupt detection: `node_name == "__interrupt__"`
- Interrupts come as tuples: `(Interrupt(...),)`
- Each interrupt has `.value` with `action_requests` and `review_configs`

See `CLAUDE.md` for detailed implementation notes.

---

## 📊 Example Use Cases

### 1. Portfolio Analysis with Real Prices
```
You: Calculate my portfolio value with current prices

Agent:
🚀 Spawning market-data-fetcher subagent...
📊 Fetching quotes for: NVDA, AVGO, UNH, MRVL, VOO, FSRNX, OXY, FBCGX

Your portfolio is worth $48,744.64:
• 401(k): $23,872.09
  - Vanguard Target 2065: $17,156.35
  - SP 500 Index: $1,945.26
  - Fidelity Blue Chip Growth: $2,058.07

• Robinhood: $6,982.83
  - NVDA (20.74 shares): $4,294.21 (+78% gain)
  - AVGO (2 shares): $772.70 (+133% gain)
  - UNH (2.02 shares): $716.28

• Emergency Fund: $17,888.88
  - Checking: $11,573.76
  - Savings: $6,315.12

💰 Total Net Worth: $46,806.84
```

---

### 2. Company Research
```
You: Research Tesla stock (TSLA)

Agent:
🚀 Spawning research-analyst subagent...

📊 Tesla, Inc. (TSLA)
• Price: $242.84 (+2.3% today)
• Market Cap: $772B
• P/E Ratio: 76.5

👔 Analyst Ratings:
• Buy: 40% (12 analysts)
• Hold: 35% (10 analysts)
• Sell: 25% (7 analysts)
• Avg Price Target: $285

📰 Recent News:
• [Bloomberg] Tesla Q3 deliveries beat estimates...
• [WSJ] Musk's robotaxi event planned for October...

🏢 Insider Activity:
• Last 6 months: 3 buys, 8 sells (net selling)

🌱 ESG Score: 68/100 (B rating)
• Environmental: 72
• Social: 58
• Governance: 71

⚠️ Key Risks: Elevated valuation, execution risk on robotaxis
```

---

### 3. Retirement Planning
```
You: How am I doing on retirement?

Agent:
🚀 Spawning goal-planner subagent...
🎲 Running Monte Carlo simulation (1000 scenarios)...

📊 Retirement Readiness Assessment

Target: Age 67 (43 years from now)
Desired Income: $48,000/year ($4,000/month)

Current Savings: $30,854.92
Required Savings: $1,200,000

📈 Monte Carlo Results (1000 simulations):
• 90th percentile: $2.4M ✅
• 50th percentile (median): $1.5M ✅
• 10th percentile: $890K ⚠️

Probability of Success: 72%

💡 Recommendations:
1. Increase 401(k) contributions by $200/month → 85% success
2. Open Roth IRA and max out ($6,500/year) → 91% success
3. Reduce high-risk individual stocks → more consistent returns
```

---

### 4. Cash Flow Analysis
```
You: Analyze my spending patterns

Agent:
🚀 Spawning cashflow-analyzer subagent...

💵 Monthly Cash Flow Analysis

Income:
• Gross Salary: $10,833.33
• Net (after tax): $6,224.20

Expenses:
• Housing: $2,350.00 (38%)
• Food: $1,400.00 (22%)
  - Groceries: $400
  - Dining Out: $1,000 ⚠️ Over budget
• Transportation: $200.00 (3%)
• Financial: $750.00 (12%)
• Other: $1,724.30 (25%)

Total Expenses: $6,424.30
Net Cash Flow: -$200.10 ⚠️ Deficit

📊 Savings Rate: -3.2% (target: 20%)

⚠️ Issues Identified:
1. Spending exceeds income by $200/month
2. Dining out: $1,000 (budget: $1,000) - consider reducing
3. Emergency fund: 2.8 months (target: 6 months)

💡 Recommendations:
1. Reduce dining out to $700/month → $300/month savings
2. Cut discretionary spending by $150/month
3. Result: +$450/month positive cash flow
```

---

### 5. Stock Purchase + Update
```
You: I bought 5 shares of Microsoft at $380 in my Robinhood account

Agent:
🚀 Spawning portfolio-analyzer subagent...
💾 Updating portfolio...

✅ Added new holding: MSFT - 5 shares @ $380.00
💰 Purchase cost: $1,900.00
📊 Robinhood account total: $8,882.83

Updated Asset Allocation:
• US Equity: 68% (was 65%)
• Tech Sector: 72% (was 70%) ⚠️ High concentration

⚠️ Concentration Warning:
Your tech exposure is now 72%. Consider diversifying into:
• Bonds (currently 3%)
• International equity (currently 3%)
• REITs (currently 9%)

📁 Portfolio saved to kabeer_portfolio.json
```

---

## 📁 Project Structure

```
personalPortfolioDeepAgent/
├── src/
│   ├── agents/                      # Original 6 agent files (legacy)
│   │   ├── orchestrator.py
│   │   ├── portfolio_agent.py
│   │   ├── cashflow_agent.py
│   │   ├── goal_agent.py
│   │   ├── debt_agent.py
│   │   ├── tax_agent.py
│   │   └── risk_agent.py
│   ├── tools/
│   │   ├── portfolio_tools.py        # 6 tools
│   │   ├── cashflow_tools.py         # 6 tools
│   │   ├── goal_tools.py             # 6 tools
│   │   ├── debt_tools.py             # 6 tools
│   │   ├── tax_tools.py              # 5 tools
│   │   ├── risk_tools.py             # 7 tools
│   │   ├── market_data_tools.py      # 30+ tools ⭐ NEW
│   │   ├── search_tools.py           # 3 tools ⭐ NEW
│   │   └── portfolio_update_tools.py # 5 tools ⭐ NEW
│   ├── utils/
│   │   ├── api_cache.py              # Yahoo Finance caching
│   │   └── response_optimizer.py     # Large response handler
│   ├── deep_agent.py                 # DeepAgents main agent
│   ├── agent_graph.py                # Graph export for LangGraph server ⭐ NEW
│   ├── subagents_config.py           # 8 subagent definitions
│   ├── backends_config.py            # File storage backend
│   ├── state.py                      # Shared state schema
│   └── graph.py                      # LangGraph workflow (legacy)
├── tests/                            # Test files
├── chat.py                           # 🎯 Main entry point (CLI chat)
├── langgraph.json                    # LangGraph server config ⭐ NEW
├── start_langgraph_server.sh         # Server startup script ⭐ NEW
├── kabeer_portfolio.json             # Example portfolio data
├── requirements.txt                  # Python dependencies
├── .env                              # API keys (not committed)
├── .env.example                      # Template for API keys
├── DEEPAGENTS_UI_SETUP.md            # Deep Agents UI setup guide ⭐ NEW
├── .gitignore                        # Git ignore rules
└── README.md                         # This file
```

---

## 🛠️ Requirements

**Python:** 3.11+

**Dependencies:**
```
langgraph              # Workflow orchestration
langgraph-cli          # LangGraph server for deep-agents-ui ⭐ NEW
langchain              # LLM framework
langchain-anthropic    # Claude integration
deepagents             # Multi-agent framework
numpy, pandas, scipy   # Calculations
python-dotenv          # Environment variables
plotly                 # Visualizations
tavily-python          # Web search API
certifi                # SSL certificates
```

**API Keys:**
- **Z.ai API** (hardcoded in config) - GLM-4.6 model for all agents
- **RapidAPI** (required) - Yahoo Finance Real-Time API
- **Tavily API** (optional) - Web search (defaults to dev key)

---

## 🔐 Environment Setup

Create `.env` file with your API keys:

```bash
# Z.ai API credentials are hardcoded in:
# - src/deep_agent.py (main agent)
# - src/subagents_config.py (all subagents)
# Model: glm-4.6
# API Base: https://api.z.ai/api/paas/v4/

# Required: Yahoo Finance Real-Time API
RAPIDAPI_KEY=xxxxx

# Optional: Web search (has default dev key)
TAVILY_API_KEY=tvly-xxxxx
```

**Get API Keys:**
- Z.ai: https://api.z.ai (credentials already configured in code)
- RapidAPI (Yahoo Finance): https://rapidapi.com/sparior/api/yahoo-finance15
- Tavily: https://tavily.com

---

## 🚦 Usage Examples

### Basic Chat
```bash
python3 chat.py
```

### Example Queries

**Portfolio Analysis:**
```
• Calculate my portfolio value with current prices
• Analyze my asset allocation
• What's my largest holding?
• Am I too concentrated in tech stocks?
```

**Market Research:**
```
• Research Apple stock (AAPL)
• What do analysts say about Tesla?
• Get ESG scores for Microsoft
• What's the latest news on NVDA?
```

**Transaction Recording:**
```
• I bought 10 shares of AAPL at $150
• I sold 5 shares of NVDA at $800
• I spent $150 on groceries
• My checking balance is now $12,000
```

**Financial Planning:**
```
• How am I doing on retirement?
• What if the market crashes 30%?
• Should I pay off debt or invest?
• Analyze my monthly cash flow
```

**Web Search:**
```
• What's the latest Federal Reserve decision?
• Search for inflation news
• What are analysts saying about tech stocks?
```

---

## 📈 Performance & Caching

**API Caching:**
- Yahoo Finance responses cached for 15 minutes
- Reduces API calls and costs
- TTL-based expiration
- In-memory cache (no Redis required)

**Response Optimization:**
- Large API responses (>500 chars) auto-saved to `/financial_data/`
- Agent receives compact summary
- Prevents context window overflow
- User can view full data in saved files

**Rate Limiting:**
- Yahoo Finance: 100 requests/minute
- Automatic retry with exponential backoff
- Respects API quotas

---

## 🧪 Testing

The project includes comprehensive tests:

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_portfolio_tools.py

# Run with verbose output
pytest -v
```

---

## 🤝 Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📝 License

MIT License - see LICENSE file for details

---

## 🙏 Acknowledgments

Built with:
- **[DeepAgents](https://github.com/anthropics/deepagents)** by Anthropic - Multi-agent framework
- **[LangGraph](https://github.com/langchain-ai/langgraph)** - Workflow orchestration
- **[Z.ai GLM-4.6](https://api.z.ai)** - AI reasoning (custom OpenAI-compatible API for all agents)
- **[Yahoo Finance API](https://rapidapi.com/sparior/api/yahoo-finance15)** - Market data
- **[Tavily](https://tavily.com)** - Web search API

---

## 📧 Contact

**Kabeer Singh Thockchom**
- GitHub: [@KabeerThockchom](https://github.com/KabeerThockchom)
- Repository: [personalPortfolioDeepAgent](https://github.com/KabeerThockchom/personalPortfolioDeepAgent)

---

## 🗺️ Roadmap

### ✅ Completed
- [x] 8 specialized subagents
- [x] 74+ financial tools
- [x] Yahoo Finance API integration (30+ endpoints)
- [x] Tavily web search integration
- [x] Portfolio update system with disk persistence
- [x] API caching and rate limiting
- [x] Interactive chat interface
- [x] Response optimization for large API calls

### 🚧 In Progress
- [x] deep-agents-ui integration (LangGraph server) ⭐ NEW
- [ ] Gradio web UI with visualizations
- [ ] Real-time chart rendering (Plotly)

### 🔮 Future
- [ ] Long-term memory with LangGraph Store
- [ ] Multi-client support with persistent threads
- [ ] Automated scheduled analyses (cron jobs)
- [ ] LangSmith deployment with monitoring
- [ ] Mobile app integration

---

**Made with ❤️ and Z.ai GLM-4.6**
