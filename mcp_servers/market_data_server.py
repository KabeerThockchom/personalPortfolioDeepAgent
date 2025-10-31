#!/usr/bin/env python3
"""
MCP Server for Market Data Tools

Exposes Yahoo Finance real-time market data tools as MCP tools.
Includes comprehensive stock data, historical prices, fundamentals,
analyst ratings, ESG scores, news, and more.
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from mcp.server.fastmcp import FastMCP
from src.tools.market_data_tools import (
    # Search & Discovery
    search_stocks,
    # Quotes & Pricing
    get_stock_quote,
    get_multiple_quotes,
    get_stock_summary,
    get_quote_type,
    # Historical Data
    get_stock_chart,
    get_stock_timeseries,
    # Fundamental Data
    get_stock_statistics,
    get_stock_balance_sheet,
    get_stock_cashflow,
    get_stock_financials,
    get_stock_earnings,
    # Company Info
    get_stock_profile,
    get_stock_insights,
    get_stock_recent_updates,
    # Analyst & Recommendations
    get_stock_analysis,
    get_stock_recommendations,
    get_recommendation_trend,
    get_upgrades_downgrades,
    # Ownership & Holders
    get_stock_holders,
    get_major_holders,
    get_insider_transactions,
    get_insider_roster,
    # ESG
    get_esg_scores,
    get_esg_chart,
    get_esg_peer_scores,
    # Options & Derivatives
    get_stock_options,
    get_futures_chain,
    # Fund/ETF
    get_fund_profile,
    get_top_holdings,
    # News
    get_news_list,
    get_news_article,
    # SEC Filings
    get_sec_filings,
    # Discovery & Comparison
    get_similar_stocks,
    get_screeners_list,
    get_saved_screeners,
    # Calendar
    get_calendar_events,
    count_calendar_events,
    # Conversations
    get_conversations_list,
    count_conversations
)

# Create MCP server
mcp = FastMCP("Market Data")


# Wrapper functions for MCP
@mcp.tool()
def search_stocks_tool(query: str, region: str = "US"):
    """Search for stocks by name or ticker"""
    return search_stocks.invoke({"query": query, "region": region})


@mcp.tool()
def get_stock_quote_tool(symbol: str, region: str = "US", lang: str = "en-US"):
    """Get real-time stock quote and summary data"""
    return get_stock_quote.invoke({"symbol": symbol, "region": region, "lang": lang})


@mcp.tool()
def get_multiple_quotes_tool(symbols: list, region: str = "US"):
    """Get quotes for multiple symbols efficiently"""
    return get_multiple_quotes.invoke({"symbols": symbols, "region": region})


@mcp.tool()
def get_stock_summary_tool(symbol: str, region: str = "US", lang: str = "en-US"):
    """Get high-level summary information for a stock"""
    return get_stock_summary.invoke({"symbol": symbol, "region": region, "lang": lang})


@mcp.tool()
def get_stock_chart_tool(symbol: str, interval: str = "1d", range_period: str = "1y", region: str = "US"):
    """Get historical price chart data"""
    return get_stock_chart.invoke({"symbol": symbol, "interval": interval, "range_period": range_period, "region": region})


@mcp.tool()
def get_stock_statistics_tool(symbol: str, region: str = "US", lang: str = "en-US"):
    """Get key statistics and valuation metrics"""
    return get_stock_statistics.invoke({"symbol": symbol, "region": region, "lang": lang})


@mcp.tool()
def get_stock_financials_tool(symbol: str, region: str = "US", lang: str = "en-US"):
    """Get income statement / P&L data"""
    return get_stock_financials.invoke({"symbol": symbol, "region": region, "lang": lang})


@mcp.tool()
def get_stock_balance_sheet_tool(symbol: str, region: str = "US", lang: str = "en-US"):
    """Get balance sheet data"""
    return get_stock_balance_sheet.invoke({"symbol": symbol, "region": region, "lang": lang})


@mcp.tool()
def get_stock_cashflow_tool(symbol: str, region: str = "US", lang: str = "en-US"):
    """Get cash flow statement data"""
    return get_stock_cashflow.invoke({"symbol": symbol, "region": region, "lang": lang})


@mcp.tool()
def get_stock_earnings_tool(symbol: str, region: str = "US", lang: str = "en-US"):
    """Get earnings history and estimates"""
    return get_stock_earnings.invoke({"symbol": symbol, "region": region, "lang": lang})


@mcp.tool()
def get_stock_profile_tool(symbol: str, region: str = "US", lang: str = "en-US"):
    """Get company profile and business description"""
    return get_stock_profile.invoke({"symbol": symbol, "region": region, "lang": lang})


@mcp.tool()
def get_stock_analysis_tool(symbol: str, region: str = "US", lang: str = "en-US"):
    """Get analyst analysis and price targets"""
    return get_stock_analysis.invoke({"symbol": symbol, "region": region, "lang": lang})


@mcp.tool()
def get_upgrades_downgrades_tool(symbol: str, region: str = "US", lang: str = "en-US"):
    """Get recent analyst upgrades and downgrades"""
    return get_upgrades_downgrades.invoke({"symbol": symbol, "region": region, "lang": lang})


@mcp.tool()
def get_insider_transactions_tool(symbol: str, region: str = "US", lang: str = "en-US"):
    """Get insider buying and selling transactions"""
    return get_insider_transactions.invoke({"symbol": symbol, "region": region, "lang": lang})


@mcp.tool()
def get_esg_scores_tool(symbol: str, region: str = "US", lang: str = "en-US"):
    """Get ESG (Environmental, Social, Governance) scores"""
    return get_esg_scores.invoke({"symbol": symbol, "region": region, "lang": lang})


@mcp.tool()
def get_news_list_tool(symbol: str = None, category: str = None, count: int = 10):
    """Get financial news articles"""
    params = {"count": count, "region": "US", "lang": "en-US"}
    if symbol:
        params["symbol"] = symbol
    if category:
        params["category"] = category
    return get_news_list.invoke(params)


@mcp.tool()
def get_sec_filings_tool(symbol: str, region: str = "US", lang: str = "en-US"):
    """Get SEC filing documents (10-K, 10-Q, 8-K, etc.)"""
    return get_sec_filings.invoke({"symbol": symbol, "region": region, "lang": lang})


@mcp.tool()
def get_similar_stocks_tool(symbol: str, region: str = "US", lang: str = "en-US"):
    """Get similar or related stocks"""
    return get_similar_stocks.invoke({"symbol": symbol, "region": region, "lang": lang})


if __name__ == "__main__":
    # Run MCP server with stdio transport for local subprocess communication
    mcp.run(transport="stdio")
