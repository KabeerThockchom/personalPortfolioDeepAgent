# Personal Finance MCP Servers

This directory contains **Model Context Protocol (MCP) servers** that expose all 80+ financial analysis tools as standardized MCP services. These servers enable any MCP-compatible client to access portfolio analysis, market data, cash flow calculations, and more through a unified protocol.

## 📁 MCP Servers

| Server | File | Tools | Description |
|--------|------|-------|-------------|
| **Portfolio Analysis** | `portfolio_server.py` | 6 | Portfolio valuation, asset allocation, concentration risk, Sharpe ratio |
| **Cash Flow Analysis** | `cashflow_server.py` | 6 | Monthly cash flow, savings rate, expense categorization, burn rate |
| **Goal Planning** | `goal_server.py` | 6 | Retirement gap, Monte Carlo simulations, FIRE calculations, college funding |
| **Debt Management** | `debt_management_server.py` | 6 | Debt payoff timelines, avalanche vs snowball, DTI ratio |
| **Tax Optimization** | `tax_optimization_server.py` | 5 | Tax rate calculations, loss harvesting, Roth conversions, withdrawal sequencing |
| **Risk Assessment** | `risk_assessment_server.py` | 7 | Emergency fund analysis, insurance gaps, stress tests, VaR |
| **Market Data** | `market_data_server.py` | 40+ | Real-time Yahoo Finance data (quotes, fundamentals, news, ESG, analyst ratings) |
| **Web Search** | `web_search_server.py` | 3 | Tavily API search for current news and financial information |
| **Portfolio Updates** | `portfolio_updates_server.py` | 5 | Persist portfolio changes (buy/sell stocks, update cash, record expenses) |

**Total**: 9 MCP servers, 80+ tools

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install mcp langchain-mcp-adapters
```

### 2. Test a Single Server

```bash
# Run portfolio server
python3 mcp_servers/portfolio_server.py
```

The server runs in stdio mode, ready to accept MCP requests.

### 3. Use with LangChain Agent

```python
import asyncio
from langchain_mcp_adapters.client import MultiServerMCPClient

# Configure MCP servers
mcp_config = {
    "portfolio": {
        "command": "python3",
        "args": ["mcp_servers/portfolio_server.py"],
        "transport": "stdio"
    },
    "market": {
        "command": "python3",
        "args": ["mcp_servers/market_data_server.py"],
        "transport": "stdio"
    }
}

# Create client and get tools
client = MultiServerMCPClient(mcp_config)
tools = await client.get_tools()

# Use with LangChain agent
from langchain.agents import create_agent

agent = create_agent("anthropic:claude-sonnet-4-5", tools)
response = await agent.ainvoke({
    "messages": [{"role": "user", "content": "What's AAPL trading at?"}]
})
```

### 4. Use Helper Module (Simplified)

```python
from src.mcp_tools_loader import get_all_mcp_tools_sync

# Get all tools from all servers
tools = get_all_mcp_tools_sync()

# Or get specific categories
from src.mcp_tools_loader import get_mcp_tools_by_category_sync
tools = get_mcp_tools_by_category_sync(['portfolio', 'market'])
```

## 📋 Configuration

MCP server configuration is defined in `../mcp_config.json`:

```json
{
  "mcpServers": {
    "portfolio": {
      "command": "python3",
      "args": ["mcp_servers/portfolio_server.py"],
      "transport": "stdio",
      "description": "Portfolio analysis and valuation tools"
    },
    ...
  }
}
```

## 🔧 Architecture

### Transport: stdio

All servers use **stdio transport** for local subprocess communication:
- Client launches server as subprocess
- Communication via stdin/stdout
- No network configuration needed
- Ideal for local development and single-user scenarios

### Tool Wrapping

MCP servers wrap existing tool functions from `src/tools/`:

```python
# Original tool in src/tools/portfolio_tools.py
@tool
def calculate_portfolio_value(holdings, current_prices):
    # Implementation...
    pass

# MCP server wraps it
from mcp.server.fastmcp import FastMCP
mcp = FastMCP("Portfolio Analysis")

@mcp.tool()
def calculate_portfolio_value(holdings, current_prices):
    """Calculate total portfolio value"""
    # Same implementation or proxy to original
    pass
```

### Benefits

1. **Standardization**: MCP protocol enables any MCP client to use these tools
2. **Language Agnostic**: Clients can be written in any language (Python, JS, etc.)
3. **Modularity**: Each server can be started/stopped independently
4. **Scalability**: Easy to add new servers or deploy remotely
5. **Compatibility**: Works with Claude Desktop, VSCode MCP extension, custom clients

## 🛠️ Development

### Adding a New Tool

1. **Add tool to existing server** (if it fits a category):
   ```python
   # In portfolio_server.py
   @mcp.tool()
   def new_analysis_tool(param1, param2):
       """Tool description"""
       # Implementation
       return result
   ```

2. **Create a new server** (for new category):
   ```bash
   # Create new server file
   cp mcp_servers/portfolio_server.py mcp_servers/new_category_server.py

   # Edit to add your tools
   vim mcp_servers/new_category_server.py

   # Add to mcp_config.json
   vim mcp_config.json
   ```

### Testing a Server

```bash
# Run server directly (stdio mode)
python3 mcp_servers/portfolio_server.py

# Test with MCP client
python3 <<EOF
import asyncio
from langchain_mcp_adapters.client import MultiServerMCPClient

async def test():
    config = {
        "test": {
            "command": "python3",
            "args": ["mcp_servers/portfolio_server.py"],
            "transport": "stdio"
        }
    }
    client = MultiServerMCPClient(config)
    tools = await client.get_tools()
    print(f"Loaded {len(tools)} tools")
    print("Tools:", [t.name for t in tools])

asyncio.run(test())
EOF
```

## 📚 Tool Reference

### Portfolio Analysis Server

- `calculate_portfolio_value` - Calculate total portfolio value and returns
- `calculate_asset_allocation` - Asset allocation breakdown by class
- `calculate_concentration_risk` - Identify over-concentrated positions
- `calculate_sharpe_ratio` - Risk-adjusted return metric
- `check_rebalancing_needs` - Portfolio rebalancing recommendations
- `generate_allocation_chart` - Pie chart data for allocation

### Cash Flow Analysis Server

- `analyze_monthly_cashflow` - Monthly income/expense analysis
- `calculate_savings_rate` - Savings as % of income
- `categorize_expenses` - Expense breakdown by category
- `project_future_cashflow` - Project cash flow with growth
- `calculate_burn_rate` - Runway calculation (months of expenses)
- `generate_waterfall_chart` - Waterfall chart data

### Goal Planning Server

- `calculate_retirement_gap` - Retirement savings gap analysis
- `run_monte_carlo_simulation` - Monte Carlo retirement projections
- `calculate_required_savings_rate` - Required savings to meet goal
- `calculate_fire_number` - FIRE (Financial Independence) number
- `project_college_funding` - 529 college funding projections
- `generate_monte_carlo_chart` - Monte Carlo fan chart data

### Debt Management Server

- `calculate_debt_payoff_timeline` - Payoff timeline with extra payments
- `compare_avalanche_vs_snowball` - Compare payoff strategies
- `calculate_total_interest_cost` - Lifetime interest costs
- `optimize_extra_payment_allocation` - Optimal payment allocation
- `calculate_debt_to_income_ratio` - DTI ratio calculation
- `generate_payoff_chart` - Debt balance chart data

### Tax Optimization Server

- `calculate_effective_tax_rate` - Effective tax rate calculation
- `identify_tax_loss_harvesting_opportunities` - Tax loss harvesting
- `analyze_roth_conversion_opportunity` - Roth conversion analysis
- `optimize_withdrawal_sequence` - Optimal withdrawal strategy
- `calculate_capital_gains_tax` - Capital gains tax calculation

### Risk Assessment Server

- `calculate_emergency_fund_adequacy` - Emergency fund months
- `analyze_insurance_gaps` - Insurance coverage gaps
- `calculate_portfolio_volatility` - Portfolio volatility metrics
- `run_stress_test_scenarios` - Stress test results
- `calculate_value_at_risk` - Value at Risk (VaR) calculation
- `analyze_concentration_risk` - Sector/geographic concentration
- `generate_risk_dashboard` - Risk dashboard data

### Market Data Server

40+ tools for real-time market data via Yahoo Finance API:

**Quotes**: `get_stock_quote`, `get_multiple_quotes`, `get_stock_summary`
**Historical**: `get_stock_chart`, `get_stock_timeseries`
**Fundamentals**: `get_stock_statistics`, `get_stock_financials`, `get_stock_earnings`, `get_stock_balance_sheet`, `get_stock_cashflow`
**Company Info**: `get_stock_profile`, `get_stock_insights`
**Analyst Data**: `get_stock_analysis`, `get_upgrades_downgrades`, `get_recommendation_trend`
**Ownership**: `get_insider_transactions`, `get_stock_holders`, `get_major_holders`
**ESG**: `get_esg_scores`, `get_esg_chart`, `get_esg_peer_scores`
**News**: `get_news_list`, `get_sec_filings`
**Discovery**: `search_stocks`, `get_similar_stocks`

### Web Search Server

- `web_search` - General web search via Tavily API
- `web_search_news` - Time-constrained news search
- `web_search_financial` - Financial news from trusted sources

### Portfolio Updates Server

- `update_investment_holding` - Buy/sell stocks, update positions
- `update_cash_balance` - Update checking/savings balances
- `record_expense` - Record expense and update cash
- `update_credit_card_balance` - Update credit card balance
- `recalculate_net_worth` - Recalculate total net worth

## 🔗 Integration with Deep Agent

The main deep agent (`src/deep_agent.py`) currently uses direct tool imports. To integrate MCP tools:

### Option 1: Hybrid Approach (Recommended)

Keep existing direct imports for development, use MCP for production/remote deployments:

```python
# In src/deep_agent.py
USE_MCP = os.getenv("USE_MCP", "false").lower() == "true"

if USE_MCP:
    from src.mcp_tools_loader import get_all_mcp_tools_sync
    tools = get_all_mcp_tools_sync()
else:
    from src.tools.market_data_tools import get_stock_quote, get_multiple_quotes
    # ... existing imports
    tools = [get_stock_quote, get_multiple_quotes, ...]
```

### Option 2: Full MCP Migration

Replace all tool imports with MCP tool loading:

```python
# Replace tool imports with MCP loader
from src.mcp_tools_loader import get_mcp_tools_by_category_sync

# Get tools by category
MAIN_AGENT_QUICK_TOOLS = get_mcp_tools_by_category_sync(['market', 'portfolio', 'cashflow', 'search'])
```

## 🌐 Remote Deployment

To deploy MCP servers remotely, use **streamable HTTP** transport:

1. **Update server files** to support HTTP:
   ```python
   if __name__ == "__main__":
       import sys
       transport = sys.argv[1] if len(sys.argv) > 1 else "stdio"
       mcp.run(transport=transport)
   ```

2. **Run server on remote host**:
   ```bash
   python3 mcp_servers/market_data_server.py streamable-http
   # Server runs on http://localhost:8000/mcp
   ```

3. **Configure client**:
   ```json
   {
     "market": {
       "transport": "streamable_http",
       "url": "http://remote-server:8000/mcp"
     }
   }
   ```

## 📝 License

MIT License - See LICENSE file in project root

## 🤝 Contributing

To add a new MCP server:

1. Create server file in `mcp_servers/`
2. Implement tools using `@mcp.tool()` decorator
3. Add server config to `mcp_config.json`
4. Update this README with tool documentation
5. Test with `python3 mcp_servers/your_server.py`

## 📧 Support

For issues or questions:
- GitHub Issues: [github.com/yourusername/repo](https://github.com)
- Documentation: See project README.md
