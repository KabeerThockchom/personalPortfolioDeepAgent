# MCP Servers for Personal Finance Deep Agent

This directory contains Model Context Protocol (MCP) server implementations that expose financial analysis tools as MCP servers.

## Overview

The Personal Finance Deep Agent's 74+ tools have been converted into 9 MCP servers, each serving a specific domain:

| Server | Tools | Description |
|--------|-------|-------------|
| **portfolio-tools** | 6 | Portfolio valuation, allocation, concentration risk, Sharpe ratio, rebalancing |
| **market-data-tools** | 19+ | Real-time Yahoo Finance data - quotes, fundamentals, historical data, news |
| **cashflow-tools** | 6 | Cash flow analysis, savings rate, expense categorization, burn rate |
| **goal-tools** | 6 | Retirement planning, Monte Carlo simulations, FIRE calculations, college funding |
| **debt-tools** | 6 | Debt payoff strategies, avalanche vs snowball, interest costs, DTI ratio |
| **tax-tools** | 5 | Tax optimization, loss harvesting, Roth conversions, capital gains |
| **risk-tools** | 7 | Risk assessment, emergency fund, insurance gaps, stress testing, VaR |
| **search-tools** | 3 | Web search via Tavily API - general, news, financial news |
| **portfolio-update-tools** | 5 | Update portfolio holdings, cash balances, expenses, credit cards |

**Total: 74+ financial analysis tools**

## Installation

1. Install MCP dependencies:
```bash
pip install -r requirements.txt
```

2. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your API keys:
# - ANTHROPIC_API_KEY (required for Claude)
# - RAPIDAPI_KEY (required for Yahoo Finance market data)
# - TAVILY_API_KEY (optional for web search, has default dev key)
```

## Usage

### Running Individual MCP Servers

Each server can be run standalone for testing:

```bash
# Portfolio analysis tools
python3 mcp_servers/portfolio_server.py

# Market data from Yahoo Finance
python3 mcp_servers/market_data_server.py

# Cash flow analysis
python3 mcp_servers/cashflow_server.py

# Goal planning and retirement
python3 mcp_servers/goal_server.py

# Debt management
python3 mcp_servers/debt_server.py

# Tax optimization
python3 mcp_servers/tax_server.py

# Risk assessment
python3 mcp_servers/risk_server.py

# Web search (Tavily)
python3 mcp_servers/search_server.py

# Portfolio updates (buy/sell, deposits, expenses)
python3 mcp_servers/portfolio_update_server.py
```

### Using MCP Servers with Claude Desktop

Add the servers to your Claude Desktop configuration (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

```json
{
  "mcpServers": {
    "portfolio-tools": {
      "command": "python3",
      "args": ["/absolute/path/to/personalPortfolioDeepAgent/mcp_servers/portfolio_server.py"]
    },
    "market-data-tools": {
      "command": "python3",
      "args": ["/absolute/path/to/personalPortfolioDeepAgent/mcp_servers/market_data_server.py"],
      "env": {
        "RAPIDAPI_KEY": "your_rapidapi_key_here"
      }
    },
    "search-tools": {
      "command": "python3",
      "args": ["/absolute/path/to/personalPortfolioDeepAgent/mcp_servers/search_server.py"],
      "env": {
        "TAVILY_API_KEY": "your_tavily_api_key_here"
      }
    }
    // ... add other servers as needed
  }
}
```

Alternatively, copy the configuration from `mcp_config.json` in the project root.

### Using with MCP Client Libraries

```python
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Create server parameters
server_params = StdioServerParameters(
    command="python3",
    args=["mcp_servers/portfolio_server.py"],
    env=None
)

# Connect to the server
async with stdio_client(server_params) as (read, write):
    async with ClientSession(read, write) as session:
        # Initialize the session
        await session.initialize()

        # List available tools
        tools = await session.list_tools()
        print(f"Available tools: {[tool.name for tool in tools]}")

        # Call a tool
        result = await session.call_tool(
            "calculate_portfolio_value",
            arguments={
                "holdings": [
                    {"ticker": "AAPL", "shares": 100, "cost_basis": 150.00}
                ],
                "current_prices": {"AAPL": 175.50}
            }
        )
        print(result)
```

## Server Details

### 1. Portfolio Tools Server
**File:** `portfolio_server.py`
**Server Name:** `portfolio-tools`

**Tools:**
- `calculate_portfolio_value` - Calculate total value, cost basis, gains/losses
- `calculate_asset_allocation` - Breakdown by asset class (stocks, bonds, etc.)
- `calculate_concentration_risk` - Identify over-concentration in positions
- `calculate_sharpe_ratio` - Risk-adjusted return metric
- `check_rebalancing_needs` - Compare current vs target allocation
- `generate_allocation_chart` - Pie chart data for visualization

### 2. Market Data Tools Server
**File:** `market_data_server.py`
**Server Name:** `market-data-tools`
**Dependencies:** Requires `RAPIDAPI_KEY` environment variable

**Tools:**
- `search_stocks` - Search for ticker symbols
- `get_stock_quote` - Real-time quote with full data
- `get_multiple_quotes` - Batch fetch multiple quotes
- `get_stock_summary` - High-level summary
- `get_stock_chart` - Historical price data
- `get_stock_statistics` - P/E, market cap, beta, etc.
- `get_stock_financials` - Income statement data
- `get_stock_balance_sheet` - Balance sheet data
- `get_stock_cashflow` - Cash flow statement
- `get_stock_earnings` - Earnings history and estimates
- `get_stock_profile` - Company profile and description
- `get_stock_analysis` - Analyst ratings and price targets
- `get_upgrades_downgrades` - Recent rating changes
- `get_insider_transactions` - Insider buy/sell activity
- `get_stock_holders` - Major shareholders
- `get_esg_scores` - ESG ratings
- `get_news_list` - Financial news articles
- `get_sec_filings` - SEC filings (10-K, 10-Q, 8-K)
- `get_fund_profile` - ETF/mutual fund information

**Features:**
- Automatic caching (5-15 min TTL)
- Rate limiting (100 requests/min)
- Retry logic with exponential backoff

### 3. Cash Flow Tools Server
**File:** `cashflow_server.py`
**Server Name:** `cashflow-tools`

**Tools:**
- `analyze_monthly_cashflow` - Net monthly cash flow
- `calculate_savings_rate` - Savings as % of income
- `categorize_expenses` - Breakdown by category
- `project_future_cashflow` - Future cash flow projections
- `calculate_burn_rate` - Runway in months
- `generate_waterfall_chart` - Visual cash flow breakdown

### 4. Goal Planning Tools Server
**File:** `goal_server.py`
**Server Name:** `goal-tools`

**Tools:**
- `calculate_retirement_gap` - Retirement savings shortfall
- `run_monte_carlo_simulation` - 1000+ scenario simulations
- `calculate_required_savings_rate` - Monthly savings needed
- `calculate_fire_number` - Financial independence targets
- `project_college_funding` - 529 plan projections
- `generate_monte_carlo_chart` - Visualization data

### 5. Debt Management Tools Server
**File:** `debt_server.py`
**Server Name:** `debt-tools`

**Tools:**
- `calculate_debt_payoff_timeline` - Payoff schedule
- `compare_avalanche_vs_snowball` - Strategy comparison
- `calculate_total_interest_cost` - Lifetime interest
- `optimize_extra_payment_allocation` - Best use of extra payments
- `calculate_debt_to_income_ratio` - DTI with risk assessment
- `generate_payoff_chart` - Payoff visualization

### 6. Tax Optimization Tools Server
**File:** `tax_server.py`
**Server Name:** `tax-tools`

**Tools:**
- `calculate_effective_tax_rate` - Current tax rate
- `identify_tax_loss_harvesting_opportunities` - Unrealized losses
- `analyze_roth_conversion_opportunity` - Roth conversion analysis
- `optimize_withdrawal_sequence` - Tax-efficient withdrawals
- `calculate_capital_gains_tax` - Capital gains tax on sales

### 7. Risk Assessment Tools Server
**File:** `risk_server.py`
**Server Name:** `risk-tools`

**Tools:**
- `calculate_emergency_fund_adequacy` - Months of expenses covered
- `analyze_insurance_gaps` - Insurance coverage assessment
- `calculate_portfolio_volatility` - Portfolio risk level
- `run_stress_test_scenarios` - Market crash simulations
- `calculate_value_at_risk` - VaR calculation (95% confidence)
- `analyze_concentration_risk` - Sector/geography concentration
- `generate_risk_dashboard` - Risk metrics visualization

### 8. Search Tools Server
**File:** `search_server.py`
**Server Name:** `search-tools`
**Dependencies:** Uses `TAVILY_API_KEY` (has default dev key)

**Tools:**
- `web_search` - General web search with domain filters
- `web_search_news` - Time-constrained news search
- `web_search_financial` - Financial news from trusted sources

### 9. Portfolio Update Tools Server
**File:** `portfolio_update_server.py`
**Server Name:** `portfolio-update-tools`

**Tools:**
- `update_investment_holding` - Buy/sell stocks (updates portfolio.json)
- `update_cash_balance` - Deposits/withdrawals
- `record_expense` - Track spending
- `update_credit_card_balance` - Update credit card balances
- `recalculate_net_worth` - Refresh totals after updates

**Note:** This server modifies `/home/user/personalPortfolioDeepAgent/portfolio.json`

## Architecture

Each MCP server follows this pattern:

```python
#!/usr/bin/env python3
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
import asyncio
import json

app = Server("server-name")

@app.list_tools()
async def list_tools() -> list[Tool]:
    """Return tool definitions with JSON schemas."""
    return [...]

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Execute tool and return results as JSON."""
    # Tool implementation
    result = _execute_tool(name, arguments)
    return [TextContent(type="text", text=json.dumps(result))]

async def main():
    """Run the MCP server via stdio."""
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(main())
```

## Testing

Test individual tools:

```bash
# Example: Test portfolio valuation
echo '{
  "method": "tools/call",
  "params": {
    "name": "calculate_portfolio_value",
    "arguments": {
      "holdings": [{"ticker": "AAPL", "shares": 100, "cost_basis": 150.00}],
      "current_prices": {"AAPL": 175.50}
    }
  }
}' | python3 mcp_servers/portfolio_server.py
```

## Troubleshooting

### Server won't start
- Check Python version (3.10+ required)
- Install dependencies: `pip install -r requirements.txt`
- Verify MCP library: `pip install mcp>=0.9.0`

### API errors (market_data_server.py)
- Verify `RAPIDAPI_KEY` is set in `.env`
- Subscribe at https://rapidapi.com/sparior/api/yahoo-finance15
- Check rate limits (100 requests/minute)

### Portfolio updates not persisting
- Verify `portfolio.json` exists in project root
- Check file permissions (read/write)
- Ensure valid JSON structure

## Migration from LangChain Tools

The original tools in `src/tools/*.py` used LangChain's `@tool` decorator. The MCP servers:

1. **Preserve all logic** - Tool implementations are identical
2. **Use MCP protocol** - Standard protocol for tool communication
3. **Standalone servers** - Each can run independently
4. **Better scalability** - Can run as separate processes
5. **Language agnostic** - MCP protocol works with any MCP client

## Next Steps

- **Integration**: Update `src/subagents_config.py` to use MCP tools instead of LangChain tools
- **Deployment**: Deploy MCP servers as persistent services
- **Monitoring**: Add logging and metrics collection
- **Documentation**: Auto-generate API docs from tool schemas

## References

- [Model Context Protocol Specification](https://modelcontextprotocol.io/)
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- [Yahoo Finance API Documentation](https://rapidapi.com/sparior/api/yahoo-finance15)
- [Tavily Search API](https://tavily.com/)
