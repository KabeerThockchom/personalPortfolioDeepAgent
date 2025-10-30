#!/usr/bin/env python3
"""Market Data Tools MCP Server - Yahoo Finance API Integration"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path to import tools
sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
import json
import os
import http.client
import time
import logging
import ssl
import certifi
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# API Configuration
RAPIDAPI_HOST = "yahoo-finance-real-time1.p.rapidapi.com"
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")

# Rate limiting configuration
_last_request_time = 0
_request_count = 0
_rate_limit_window = 60
_max_requests_per_window = 100

# Initialize MCP server
app = Server("market-data-tools")


# API Helper Functions
class APIError(Exception):
    """Custom exception for API errors."""
    pass


def _check_rate_limit():
    """Check and enforce rate limiting."""
    global _last_request_time, _request_count

    current_time = time.time()
    if current_time - _last_request_time > _rate_limit_window:
        _request_count = 0
        _last_request_time = current_time

    if _request_count >= _max_requests_per_window:
        sleep_time = _rate_limit_window - (current_time - _last_request_time)
        if sleep_time > 0:
            time.sleep(sleep_time)
            _request_count = 0
            _last_request_time = time.time()

    _request_count += 1


def _make_api_call(endpoint: str, params: dict = None) -> dict:
    """Internal helper for making Yahoo Finance API calls."""
    if not RAPIDAPI_KEY:
        raise APIError("RAPIDAPI_KEY not configured")

    _check_rate_limit()

    query_string = ""
    if params:
        query_params = [f"{k}={v}" for k, v in params.items() if v is not None]
        if query_params:
            query_string = "?" + "&".join(query_params)

    ssl_context = ssl.create_default_context(cafile=certifi.where())
    conn = http.client.HTTPSConnection(RAPIDAPI_HOST, context=ssl_context)
    headers = {
        'x-rapidapi-host': RAPIDAPI_HOST,
        'x-rapidapi-key': RAPIDAPI_KEY
    }

    try:
        full_path = endpoint + query_string
        conn.request("GET", full_path, headers=headers)
        res = conn.getresponse()
        data = res.read()

        response_text = data.decode("utf-8")
        if res.status != 200:
            raise APIError(f"API returned status {res.status}: {response_text[:200]}")

        return json.loads(response_text)
    except json.JSONDecodeError as e:
        raise APIError(f"Invalid JSON response: {str(e)}")
    except Exception as e:
        raise APIError(f"API request failed: {str(e)}")
    finally:
        conn.close()


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available market data tools."""
    return [
        # Search & Discovery
        Tool(
            name="search_stocks",
            description="Search for stocks, ETFs, mutual funds by name or ticker",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search term"},
                    "region": {"type": "string", "default": "US"}
                },
                "required": ["query"]
            }
        ),
        # Quotes & Pricing
        Tool(
            name="get_stock_quote",
            description="Get comprehensive real-time quote and summary data for a stock",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {"type": "string", "description": "Stock ticker (e.g., AAPL)"},
                    "region": {"type": "string", "default": "US"},
                    "lang": {"type": "string", "default": "en-US"}
                },
                "required": ["symbol"]
            }
        ),
        Tool(
            name="get_multiple_quotes",
            description="Get real-time quotes for multiple symbols efficiently",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbols": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of stock tickers"
                    },
                    "region": {"type": "string", "default": "US"}
                },
                "required": ["symbols"]
            }
        ),
        Tool(
            name="get_stock_summary",
            description="Get high-level summary information for a stock",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {"type": "string"},
                    "region": {"type": "string", "default": "US"},
                    "lang": {"type": "string", "default": "en-US"}
                },
                "required": ["symbol"]
            }
        ),
        # Historical Data
        Tool(
            name="get_stock_chart",
            description="Get historical price chart data for technical analysis",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {"type": "string"},
                    "interval": {"type": "string", "default": "1d", "description": "1m, 5m, 15m, 1h, 1d, 1wk, 1mo"},
                    "range_period": {"type": "string", "default": "1y", "description": "1d, 5d, 1mo, 3mo, 6mo, 1y, 5y, max"},
                    "region": {"type": "string", "default": "US"}
                },
                "required": ["symbol"]
            }
        ),
        # Fundamental Data
        Tool(
            name="get_stock_statistics",
            description="Get key statistics and valuation metrics (P/E, beta, market cap, etc.)",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {"type": "string"},
                    "region": {"type": "string", "default": "US"}
                },
                "required": ["symbol"]
            }
        ),
        Tool(
            name="get_stock_financials",
            description="Get income statement / P&L data (revenue, EBITDA, net income, EPS)",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {"type": "string"},
                    "region": {"type": "string", "default": "US"}
                },
                "required": ["symbol"]
            }
        ),
        Tool(
            name="get_stock_balance_sheet",
            description="Get balance sheet data (assets, liabilities, equity, cash, debt)",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {"type": "string"},
                    "region": {"type": "string", "default": "US"}
                },
                "required": ["symbol"]
            }
        ),
        Tool(
            name="get_stock_cashflow",
            description="Get cash flow statement data (operating, investing, financing cash flow)",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {"type": "string"},
                    "region": {"type": "string", "default": "US"}
                },
                "required": ["symbol"]
            }
        ),
        Tool(
            name="get_stock_earnings",
            description="Get earnings history and estimates (EPS actual vs estimate, earnings dates)",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {"type": "string"},
                    "region": {"type": "string", "default": "US"}
                },
                "required": ["symbol"]
            }
        ),
        # Company Info
        Tool(
            name="get_stock_profile",
            description="Get company profile and business description (sector, industry, employees)",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {"type": "string"},
                    "region": {"type": "string", "default": "US"}
                },
                "required": ["symbol"]
            }
        ),
        # Analyst & Recommendations
        Tool(
            name="get_stock_analysis",
            description="Get comprehensive analyst analysis and price targets",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {"type": "string"},
                    "region": {"type": "string", "default": "US"}
                },
                "required": ["symbol"]
            }
        ),
        Tool(
            name="get_upgrades_downgrades",
            description="Get recent analyst upgrades and downgrades",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {"type": "string"},
                    "region": {"type": "string", "default": "US"}
                },
                "required": ["symbol"]
            }
        ),
        # Ownership & Holders
        Tool(
            name="get_insider_transactions",
            description="Get insider buying and selling transactions",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {"type": "string"},
                    "region": {"type": "string", "default": "US"}
                },
                "required": ["symbol"]
            }
        ),
        Tool(
            name="get_stock_holders",
            description="Get information about major shareholders",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {"type": "string"},
                    "region": {"type": "string", "default": "US"}
                },
                "required": ["symbol"]
            }
        ),
        # ESG
        Tool(
            name="get_esg_scores",
            description="Get Environmental, Social, and Governance (ESG) scores",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {"type": "string"},
                    "region": {"type": "string", "default": "US"}
                },
                "required": ["symbol"]
            }
        ),
        # News
        Tool(
            name="get_news_list",
            description="Get financial news articles, optionally filtered by symbol",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {"type": "string", "description": "Optional stock ticker to filter news"},
                    "count": {"type": "integer", "default": 10},
                    "region": {"type": "string", "default": "US"}
                }
            }
        ),
        # SEC Filings
        Tool(
            name="get_sec_filings",
            description="Get SEC filing documents (10-K, 10-Q, 8-K, etc.)",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {"type": "string"},
                    "region": {"type": "string", "default": "US"}
                },
                "required": ["symbol"]
            }
        ),
        # Fund/ETF
        Tool(
            name="get_fund_profile",
            description="Get mutual fund or ETF profile information",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {"type": "string", "description": "Fund ticker (e.g., VTSAX, SPY)"},
                    "region": {"type": "string", "default": "US"}
                },
                "required": ["symbol"]
            }
        ),
        # Note: Due to length constraints, I'm including key tools. Add more as needed.
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool execution."""
    try:
        result = None

        # Search & Discovery
        if name == "search_stocks":
            result = _make_api_call("/search", {
                "query": arguments["query"],
                "region": arguments.get("region", "US")
            })

        # Quotes & Pricing
        elif name == "get_stock_quote":
            result = _make_api_call("/stock/get-quote-summary", {
                "symbol": arguments["symbol"],
                "region": arguments.get("region", "US"),
                "lang": arguments.get("lang", "en-US")
            })

        elif name == "get_multiple_quotes":
            results = {}
            for symbol in arguments["symbols"]:
                try:
                    quote = _make_api_call("/stock/get-quote-summary", {
                        "symbol": symbol,
                        "region": arguments.get("region", "US")
                    })
                    results[symbol] = {"success": True, "data": quote}
                except Exception as e:
                    results[symbol] = {"success": False, "error": str(e)}
            result = results

        elif name == "get_stock_summary":
            result = _make_api_call("/stock/get-summary", {
                "symbol": arguments["symbol"],
                "region": arguments.get("region", "US"),
                "lang": arguments.get("lang", "en-US")
            })

        # Historical Data
        elif name == "get_stock_chart":
            params = {
                "symbol": arguments["symbol"],
                "interval": arguments.get("interval", "1d"),
                "range": arguments.get("range_period", "1y"),
                "region": arguments.get("region", "US")
            }
            result = _make_api_call("/stock/get-chart", params)

        # Fundamental Data
        elif name == "get_stock_statistics":
            result = _make_api_call("/stock/get-statistics", {
                "symbol": arguments["symbol"],
                "region": arguments.get("region", "US")
            })

        elif name == "get_stock_financials":
            result = _make_api_call("/stock/get-financials", {
                "symbol": arguments["symbol"],
                "region": arguments.get("region", "US")
            })

        elif name == "get_stock_balance_sheet":
            result = _make_api_call("/stock/get-balance-sheet", {
                "symbol": arguments["symbol"],
                "region": arguments.get("region", "US")
            })

        elif name == "get_stock_cashflow":
            result = _make_api_call("/stock/get-cashflow", {
                "symbol": arguments["symbol"],
                "region": arguments.get("region", "US")
            })

        elif name == "get_stock_earnings":
            result = _make_api_call("/stock/get-earnings", {
                "symbol": arguments["symbol"],
                "region": arguments.get("region", "US")
            })

        # Company Info
        elif name == "get_stock_profile":
            result = _make_api_call("/stock/get-profile", {
                "symbol": arguments["symbol"],
                "region": arguments.get("region", "US")
            })

        # Analyst & Recommendations
        elif name == "get_stock_analysis":
            result = _make_api_call("/stock/get-analysis", {
                "symbol": arguments["symbol"],
                "region": arguments.get("region", "US")
            })

        elif name == "get_upgrades_downgrades":
            result = _make_api_call("/stock/get-upgrades-downgrades", {
                "symbol": arguments["symbol"],
                "region": arguments.get("region", "US")
            })

        # Ownership & Holders
        elif name == "get_insider_transactions":
            result = _make_api_call("/stock/get-insider-transactions", {
                "symbol": arguments["symbol"],
                "region": arguments.get("region", "US")
            })

        elif name == "get_stock_holders":
            result = _make_api_call("/stock/get-holders", {
                "symbol": arguments["symbol"],
                "region": arguments.get("region", "US")
            })

        # ESG
        elif name == "get_esg_scores":
            result = _make_api_call("/stock/get-esg-scores", {
                "symbol": arguments["symbol"],
                "region": arguments.get("region", "US")
            })

        # News
        elif name == "get_news_list":
            params = {"region": arguments.get("region", "US")}
            if "symbol" in arguments:
                params["symbol"] = arguments["symbol"]
            if "count" in arguments:
                params["count"] = arguments["count"]
            result = _make_api_call("/news/get-list", params)

        # SEC Filings
        elif name == "get_sec_filings":
            result = _make_api_call("/stock/get-sec-filings", {
                "symbol": arguments["symbol"],
                "region": arguments.get("region", "US")
            })

        # Fund/ETF
        elif name == "get_fund_profile":
            result = _make_api_call("/stock/get-fund-profile", {
                "symbol": arguments["symbol"],
                "region": arguments.get("region", "US")
            })

        else:
            raise ValueError(f"Unknown tool: {name}")

        return [TextContent(type="text", text=json.dumps({
            "success": True,
            "data": result
        }, indent=2))]

    except Exception as e:
        logger.error(f"Tool {name} failed: {e}")
        return [TextContent(type="text", text=json.dumps({
            "success": False,
            "error": str(e)
        }, indent=2))]


async def main():
    """Run the MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
