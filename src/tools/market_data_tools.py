"""
Yahoo Finance Market Data Tools

Comprehensive suite of tools for fetching real-time and historical market data
from Yahoo Finance via RapidAPI.

All tools include:
- Automatic caching (15-minute TTL)
- Rate limiting (100 requests/min)
- Retry logic with exponential backoff
- Comprehensive error handling
"""

import os
import http.client
import json
import time
import logging
import ssl
import certifi
from typing import Dict, List, Optional, Any
from functools import wraps
from dotenv import load_dotenv
from langchain_core.tools import tool

from src.utils.api_cache import get_cache
from src.utils.response_optimizer import optimize_tool_response
from src.utils.tool_logger import logged_tool

# Load environment variables FIRST
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# API Configuration
RAPIDAPI_HOST = "yahoo-finance-real-time1.p.rapidapi.com"
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")

if not RAPIDAPI_KEY:
    logger.warning("RAPIDAPI_KEY environment variable not set. Market data tools will not function.")

# Rate limiting configuration
_last_request_time = 0
_request_count = 0
_rate_limit_window = 60  # seconds
_max_requests_per_window = 100

# Cache instance
cache = get_cache()


class APIError(Exception):
    """Custom exception for API errors."""
    pass


def _check_rate_limit():
    """Check and enforce rate limiting."""
    global _last_request_time, _request_count

    current_time = time.time()

    # Reset counter if window has passed
    if current_time - _last_request_time > _rate_limit_window:
        _request_count = 0
        _last_request_time = current_time

    # Check if we've exceeded the limit
    if _request_count >= _max_requests_per_window:
        sleep_time = _rate_limit_window - (current_time - _last_request_time)
        if sleep_time > 0:
            logger.warning(f"Rate limit reached. Sleeping for {sleep_time:.2f} seconds.")
            time.sleep(sleep_time)
            _request_count = 0
            _last_request_time = time.time()

    _request_count += 1


def _retry_on_failure(max_retries=3, backoff_factor=2):
    """Decorator to retry function on failure with exponential backoff."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        wait_time = backoff_factor ** attempt
                        logger.warning(
                            f"{func.__name__} failed (attempt {attempt + 1}/{max_retries}). "
                            f"Retrying in {wait_time}s. Error: {str(e)}"
                        )
                        time.sleep(wait_time)
                    else:
                        logger.error(
                            f"{func.__name__} failed after {max_retries} attempts. Error: {str(e)}"
                        )

            raise last_exception

        return wrapper
    return decorator


@_retry_on_failure(max_retries=3)
def _make_api_call(endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict:
    """
    Internal helper for making Yahoo Finance API calls.

    Args:
        endpoint: API endpoint path (e.g., "/stock/get-quote-summary")
        params: Query parameters as dict

    Returns:
        Parsed JSON response

    Raises:
        APIError: If API call fails or returns error
    """
    if not RAPIDAPI_KEY:
        raise APIError("RAPIDAPI_KEY not configured")

    # Check rate limit before making request
    _check_rate_limit()

    # Build query string
    query_string = ""
    if params:
        query_params = [f"{k}={v}" for k, v in params.items() if v is not None]
        if query_params:
            query_string = "?" + "&".join(query_params)

    # Create SSL context with certifi certificates
    ssl_context = ssl.create_default_context(cafile=certifi.where())

    # Make API request with SSL context
    conn = http.client.HTTPSConnection(RAPIDAPI_HOST, context=ssl_context)
    headers = {
        'x-rapidapi-host': RAPIDAPI_HOST,
        'x-rapidapi-key': RAPIDAPI_KEY
    }

    try:
        full_path = endpoint + query_string
        logger.debug(f"Making API request: {full_path}")

        conn.request("GET", full_path, headers=headers)
        res = conn.getresponse()
        data = res.read()

        # Parse response
        response_text = data.decode("utf-8")

        if res.status != 200:
            raise APIError(f"API returned status {res.status}: {response_text[:200]}")

        response_data = json.loads(response_text)

        return response_data

    except json.JSONDecodeError as e:
        raise APIError(f"Invalid JSON response: {str(e)}")
    except Exception as e:
        raise APIError(f"API request failed: {str(e)}")
    finally:
        conn.close()


# ============================================================================
# SEARCH & DISCOVERY TOOLS
# ============================================================================

@tool
@logged_tool
@cache.cached(ttl=900)  # 15 minutes
def search_stocks(query: str, region: str = "US") -> Dict:
    """
    Search for stocks, ETFs, mutual funds, and other securities by name or ticker.

    Use this when you need to:
    - Find a ticker symbol from a company name
    - Search for securities matching a keyword
    - Discover related securities

    Args:
        query: Search term (company name, ticker, or keyword)
        region: Region code (default: "US")

    Returns:
        Dict with:
        - quotes: List of matching securities with ticker, name, type, exchange
        - news: Related news articles
        - count: Number of results

    Example:
        search_stocks("Apple") -> Returns AAPL and related securities
        search_stocks("NVDA") -> Returns Nvidia info
    """
    try:
        result = _make_api_call("/search", {"query": query, "region": region})
        return {
            "success": True,
            "count": result.get("count", 0),
            "quotes": result.get("quotes", []),
            "news": result.get("news", [])[:5],  # Limit news to 5 items
        }
    except Exception as e:
        logger.error(f"search_stocks failed: {e}")
        return {"success": False, "error": str(e), "quotes": []}


# ============================================================================
# QUOTE & PRICING TOOLS
# ============================================================================

@tool
@logged_tool
@cache.cached(ttl=300)  # 5 minutes for real-time quotes
def get_stock_quote(symbol: str, region: str = "US", lang: str = "en-US") -> Dict:
    """
    Get comprehensive real-time quote and summary data for a stock.

    Returns extensive data including:
    - Current price, volume, market cap
    - Day high/low, 52-week high/low
    - P/E ratio, dividend yield, beta
    - Analyst recommendations
    - Company profile summary

    Args:
        symbol: Stock ticker (e.g., "AAPL", "MSFT", "GOOGL")
        region: Region code (default: "US")
        lang: Language code (default: "en-US")

    Returns:
        Dict with price, summaryDetail, financialData, defaultKeyStatistics, etc.

    Example:
        get_stock_quote("AAPL") -> Complete quote data for Apple
    """
    try:
        result = _make_api_call("/stock/get-quote-summary", {
            "symbol": symbol,
            "region": region,
            "lang": lang
        })
        response = {"success": True, "symbol": symbol, "data": result}
        return optimize_tool_response(response, "get_stock_quote", symbol)
    except Exception as e:
        logger.error(f"get_stock_quote failed for {symbol}: {e}")
        return {"success": False, "error": str(e), "symbol": symbol}


@tool
@logged_tool
@cache.cached(ttl=300)
def get_multiple_quotes(symbols: List[str], region: str = "US") -> Dict[str, Dict]:
    """
    Get real-time quotes for multiple symbols efficiently.

    Optimized for fetching many quotes at once (e.g., entire portfolio).
    Uses caching to minimize API calls.

    Args:
        symbols: List of stock tickers
        region: Region code (default: "US")

    Returns:
        Dict mapping symbol -> quote data

    Example:
        get_multiple_quotes(["AAPL", "MSFT", "GOOGL"])
        -> {"AAPL": {...}, "MSFT": {...}, "GOOGL": {...}}
    """
    results = {}

    for symbol in symbols:
        try:
            quote = get_stock_quote.invoke({"symbol": symbol, "region": region})
            results[symbol] = quote
        except Exception as e:
            logger.error(f"Failed to get quote for {symbol}: {e}")
            results[symbol] = {"success": False, "error": str(e)}

    return results


@tool
@logged_tool
@cache.cached(ttl=900)
def get_stock_summary(symbol: str, region: str = "US", lang: str = "en-US") -> Dict:
    """
    Get high-level summary information for a stock.

    Lighter-weight alternative to get_stock_quote for basic info.

    Args:
        symbol: Stock ticker
        region: Region code (default: "US")
        lang: Language code (default: "en-US")

    Returns:
        Dict with summary data

    Example:
        get_stock_summary("TSLA") -> Summary data for Tesla
    """
    try:
        result = _make_api_call("/stock/get-summary", {
            "symbol": symbol,
            "region": region,
            "lang": lang
        })
        response = {"success": True, "symbol": symbol, "data": result}
        return optimize_tool_response(response, "get_stock_summary", symbol)
    except Exception as e:
        logger.error(f"get_stock_summary failed for {symbol}: {e}")
        return {"success": False, "error": str(e), "symbol": symbol}


@tool
@logged_tool
@cache.cached(ttl=300)
def get_quote_type(symbol: str, region: str = "US", lang: str = "en-US") -> Dict:
    """
    Get the quote type and basic classification for a symbol.

    Useful for determining if a symbol is a stock, ETF, mutual fund, etc.

    Args:
        symbol: Security ticker
        region: Region code (default: "US")
        lang: Language code (default: "en-US")

    Returns:
        Dict with quoteType, exchange, longName, shortName

    Example:
        get_quote_type("SPY") -> Shows SPY is an ETF
    """
    try:
        result = _make_api_call("/stock/get-quote-type", {
            "symbol": symbol,
            "region": region,
            "lang": lang
        })
        response = {"success": True, "symbol": symbol, "data": result}
        return optimize_tool_response(response, "get_quote_type", symbol)
    except Exception as e:
        logger.error(f"get_quote_type failed for {symbol}: {e}")
        return {"success": False, "error": str(e), "symbol": symbol}


# ============================================================================
# HISTORICAL DATA TOOLS
# ============================================================================

@tool
@logged_tool
@cache.cached(ttl=3600)  # 1 hour for historical data
def get_stock_chart(
    symbol: str,
    interval: str = "1d",
    range_period: str = "1y",
    region: str = "US",
    lang: str = "en-US",
    useYfid: bool = True,
    includeAdjustedClose: bool = True,
    events: Optional[str] = None,
    includePrePost: bool = False
) -> Dict:
    """
    Get historical price chart data for technical analysis.

    Intervals: 1m, 5m, 15m, 1h, 1d, 1wk, 1mo
    Ranges: 1d, 5d, 1mo, 3mo, 6mo, 1y, 5y, max

    Args:
        symbol: Stock ticker
        interval: Data interval (default: "1d")
        range_period: Time range (default: "1y")
        region: Region code (default: "US")
        lang: Language code (default: "en-US")
        useYfid: Use Yahoo Finance ID (default: True)
        includeAdjustedClose: Include adjusted close prices (default: True)
        events: Comma-separated list of events to include (e.g., "div,split,earn")
        includePrePost: Include pre/post-market data (default: False)

    Returns:
        Dict with timestamp, open, high, low, close, volume arrays

    Example:
        get_stock_chart("AAPL", interval="1d", range_period="1y")
        -> Daily prices for Apple over past year
        get_stock_chart("AAPL", events="div,split", includePrePost=True)
        -> Prices with dividend/split events and extended hours data
    """
    try:
        params = {
            "symbol": symbol,
            "interval": interval,
            "range": range_period,
            "region": region,
            "lang": lang,
            "useYfid": useYfid,
            "includeAdjustedClose": includeAdjustedClose,
            "includePrePost": includePrePost
        }
        if events:
            params["events"] = events

        result = _make_api_call("/stock/get-chart", params)
        response = {"success": True, "symbol": symbol, "data": result}
        return optimize_tool_response(response, "get_stock_chart", symbol)
    except Exception as e:
        logger.error(f"get_stock_chart failed for {symbol}: {e}")
        return {"success": False, "error": str(e), "symbol": symbol}


@tool
@logged_tool
@cache.cached(ttl=3600)
def get_stock_timeseries(symbol: str, region: str = "US", lang: str = "en-US") -> Dict:
    """
    Get time series data including historical prices and metrics.

    Args:
        symbol: Stock ticker
        region: Region code (default: "US")
        lang: Language code (default: "en-US")

    Returns:
        Dict with time series price and volume data

    Example:
        get_stock_timeseries("MSFT") -> Time series data for Microsoft
    """
    try:
        result = _make_api_call("/stock/get-timeseries", {
            "symbol": symbol,
            "region": region,
            "lang": lang
        })
        response = {"success": True, "symbol": symbol, "data": result}
        return optimize_tool_response(response, "get_stock_timeseries", symbol)
    except Exception as e:
        logger.error(f"get_stock_timeseries failed for {symbol}: {e}")
        return {"success": False, "error": str(e), "symbol": symbol}


# ============================================================================
# FUNDAMENTAL DATA TOOLS
# ============================================================================

@tool
@logged_tool
@cache.cached(ttl=86400)  # 24 hours
def get_stock_statistics(symbol: str, region: str = "US", lang: str = "en-US") -> Dict:
    """
    Get key statistics and valuation metrics.

    Includes:
    - P/E ratio, PEG ratio, Price/Sales, Price/Book
    - Beta, 52-week change
    - Shares outstanding, float
    - Dividend rate and yield
    - Profit margins, ROE, ROA

    Args:
        symbol: Stock ticker
        region: Region code (default: "US")
        lang: Language code (default: "en-US")

    Returns:
        Dict with comprehensive statistics

    Example:
        get_stock_statistics("AAPL") -> Key stats for Apple
    """
    try:
        result = _make_api_call("/stock/get-statistics", {
            "symbol": symbol,
            "region": region,
            "lang": lang
        })
        response = {"success": True, "symbol": symbol, "data": result}
        return optimize_tool_response(response, "get_stock_statistics", symbol)
    except Exception as e:
        logger.error(f"get_stock_statistics failed for {symbol}: {e}")
        return {"success": False, "error": str(e), "symbol": symbol}


@tool
@logged_tool
@cache.cached(ttl=86400)
def get_stock_balance_sheet(symbol: str, region: str = "US", lang: str = "en-US") -> Dict:
    """
    Get balance sheet data (annual and quarterly).

    Includes:
    - Total assets, total liabilities
    - Cash and cash equivalents
    - Total debt
    - Shareholder equity
    - Inventory, receivables

    Args:
        symbol: Stock ticker
        region: Region code (default: "US")
        lang: Language code (default: "en-US")

    Returns:
        Dict with balance sheet statements

    Example:
        get_stock_balance_sheet("TSLA") -> Tesla's balance sheet
    """
    try:
        result = _make_api_call("/stock/get-balance-sheet", {
            "symbol": symbol,
            "region": region,
            "lang": lang
        })
        response = {"success": True, "symbol": symbol, "data": result}
        return optimize_tool_response(response, "get_stock_balance_sheet", symbol)
    except Exception as e:
        logger.error(f"get_stock_balance_sheet failed for {symbol}: {e}")
        return {"success": False, "error": str(e), "symbol": symbol}


@tool
@logged_tool
@cache.cached(ttl=86400)
def get_stock_cashflow(symbol: str, region: str = "US", lang: str = "en-US") -> Dict:
    """
    Get cash flow statement data (annual and quarterly).

    Includes:
    - Operating cash flow
    - Investing cash flow
    - Financing cash flow
    - Free cash flow
    - Capital expenditures

    Args:
        symbol: Stock ticker
        region: Region code (default: "US")
        lang: Language code (default: "en-US")

    Returns:
        Dict with cash flow statements

    Example:
        get_stock_cashflow("MSFT") -> Microsoft's cash flow
    """
    try:
        result = _make_api_call("/stock/get-cashflow", {
            "symbol": symbol,
            "region": region,
            "lang": lang
        })
        response = {"success": True, "symbol": symbol, "data": result}
        return optimize_tool_response(response, "get_stock_cashflow", symbol)
    except Exception as e:
        logger.error(f"get_stock_cashflow failed for {symbol}: {e}")
        return {"success": False, "error": str(e), "symbol": symbol}


@tool
@logged_tool
@cache.cached(ttl=86400)
def get_stock_financials(symbol: str, region: str = "US", lang: str = "en-US") -> Dict:
    """
    Get income statement / P&L data (annual and quarterly).

    Includes:
    - Total revenue
    - Cost of revenue, gross profit
    - Operating expenses
    - EBIT, EBITDA
    - Net income
    - EPS

    Args:
        symbol: Stock ticker
        region: Region code (default: "US")
        lang: Language code (default: "en-US")

    Returns:
        Dict with income statements

    Example:
        get_stock_financials("GOOGL") -> Google's income statement
    """
    try:
        result = _make_api_call("/stock/get-financials", {
            "symbol": symbol,
            "region": region,
            "lang": lang
        })
        response = {"success": True, "symbol": symbol, "data": result}
        return optimize_tool_response(response, "get_stock_financials", symbol)
    except Exception as e:
        logger.error(f"get_stock_financials failed for {symbol}: {e}")
        return {"success": False, "error": str(e), "symbol": symbol}


@tool
@logged_tool
@cache.cached(ttl=86400)
def get_stock_earnings(symbol: str, region: str = "US", lang: str = "en-US") -> Dict:
    """
    Get earnings history and estimates.

    Includes:
    - Historical quarterly earnings
    - EPS actual vs estimate
    - Revenue actual vs estimate
    - Future earnings dates
    - Earnings trends

    Args:
        symbol: Stock ticker
        region: Region code (default: "US")
        lang: Language code (default: "en-US")

    Returns:
        Dict with earnings data

    Example:
        get_stock_earnings("NVDA") -> Nvidia's earnings history
    """
    try:
        result = _make_api_call("/stock/get-earnings", {
            "symbol": symbol,
            "region": region,
            "lang": lang
        })
        response = {"success": True, "symbol": symbol, "data": result}
        return optimize_tool_response(response, "get_stock_earnings", symbol)
    except Exception as e:
        logger.error(f"get_stock_earnings failed for {symbol}: {e}")
        return {"success": False, "error": str(e), "symbol": symbol}


# ============================================================================
# COMPANY INFO TOOLS
# ============================================================================

@tool
@logged_tool
@cache.cached(ttl=86400)
def get_stock_profile(symbol: str, region: str = "US", lang: str = "en-US") -> Dict:
    """
    Get company profile and business description.

    Includes:
    - Business summary
    - Sector and industry
    - Number of employees
    - Address and website
    - Key executives
    - Company officers

    Args:
        symbol: Stock ticker
        region: Region code (default: "US")
        lang: Language code (default: "en-US")

    Returns:
        Dict with company profile

    Example:
        get_stock_profile("AAPL") -> Apple's company profile
    """
    try:
        result = _make_api_call("/stock/get-profile", {
            "symbol": symbol,
            "region": region,
            "lang": lang
        })
        response = {"success": True, "symbol": symbol, "data": result}
        return optimize_tool_response(response, "get_stock_profile", symbol)
    except Exception as e:
        logger.error(f"get_stock_profile failed for {symbol}: {e}")
        return {"success": False, "error": str(e), "symbol": symbol}


@tool
@logged_tool
@cache.cached(ttl=86400)
def get_stock_insights(symbol: str, region: str = "US", lang: str = "en-US") -> Dict:
    """
    Get stock insights and key metrics summary.

    Provides high-level insights about company performance,
    valuation, and analyst sentiment.

    Args:
        symbol: Stock ticker
        region: Region code (default: "US")
        lang: Language code (default: "en-US")

    Returns:
        Dict with insights data

    Example:
        get_stock_insights("TSLA") -> Insights about Tesla
    """
    try:
        result = _make_api_call("/stock/get-insights", {
            "symbol": symbol,
            "region": region,
            "lang": lang
        })
        response = {"success": True, "symbol": symbol, "data": result}
        return optimize_tool_response(response, "get_stock_insights", symbol)
    except Exception as e:
        logger.error(f"get_stock_insights failed for {symbol}: {e}")
        return {"success": False, "error": str(e), "symbol": symbol}


@tool
@logged_tool
@cache.cached(ttl=86400)
def get_stock_recent_updates(symbol: str, region: str = "US", lang: str = "en-US") -> Dict:
    """
    Get recent updates and news for a stock.

    Args:
        symbol: Stock ticker
        region: Region code (default: "US")
        lang: Language code (default: "en-US")

    Returns:
        Dict with recent updates

    Example:
        get_stock_recent_updates("AAPL") -> Recent updates for Apple
    """
    try:
        result = _make_api_call("/stock/get-recent-updates", {
            "symbol": symbol,
            "region": region,
            "lang": lang
        })
        response = {"success": True, "symbol": symbol, "data": result}
        return optimize_tool_response(response, "get_stock_recent_updates", symbol)
    except Exception as e:
        logger.error(f"get_stock_recent_updates failed for {symbol}: {e}")
        return {"success": False, "error": str(e), "symbol": symbol}


# ============================================================================
# ANALYST & RECOMMENDATIONS TOOLS
# ============================================================================

@tool
@logged_tool
@cache.cached(ttl=86400)
def get_stock_analysis(symbol: str, region: str = "US", lang: str = "en-US") -> Dict:
    """
    Get comprehensive analyst analysis and price targets.

    Includes:
    - Current price targets (high, low, mean)
    - Number of analyst opinions
    - Recommendation trend
    - Earnings estimates

    Args:
        symbol: Stock ticker
        region: Region code (default: "US")
        lang: Language code (default: "en-US")

    Returns:
        Dict with analyst analysis

    Example:
        get_stock_analysis("MSFT") -> Analyst analysis for Microsoft
    """
    try:
        result = _make_api_call("/stock/get-analysis", {
            "symbol": symbol,
            "region": region,
            "lang": lang
        })
        response = {"success": True, "symbol": symbol, "data": result}
        return optimize_tool_response(response, "get_stock_analysis", symbol)
    except Exception as e:
        logger.error(f"get_stock_analysis failed for {symbol}: {e}")
        return {"success": False, "error": str(e), "symbol": symbol}


@tool
@logged_tool
@cache.cached(ttl=86400)
def get_stock_recommendations(symbol: str) -> Dict:
    """
    Get recommended/similar stocks for a given symbol.

    Args:
        symbol: Stock ticker

    Returns:
        Dict with recommendation data

    Example:
        get_stock_recommendations("NVDA") -> Recommended stocks similar to Nvidia
    """
    try:
        result = _make_api_call("/stock/get-recommendations", {
            "symbols": symbol  # API uses "symbols" not "symbol"
        })
        response = {"success": True, "symbol": symbol, "data": result}
        return optimize_tool_response(response, "get_stock_recommendations", symbol)
    except Exception as e:
        logger.error(f"get_stock_recommendations failed for {symbol}: {e}")
        return {"success": False, "error": str(e), "symbol": symbol}


@tool
@logged_tool
@cache.cached(ttl=86400)
def get_recommendation_trend(symbol: str, region: str = "US", lang: str = "en-US") -> Dict:
    """
    Get trend in analyst recommendations over time.

    Shows how analyst sentiment has changed (more bullish/bearish).

    Args:
        symbol: Stock ticker
        region: Region code (default: "US")
        lang: Language code (default: "en-US")

    Returns:
        Dict with recommendation trends

    Example:
        get_recommendation_trend("AAPL") -> How analyst views on Apple have evolved
    """
    try:
        result = _make_api_call("/stock/get-recommendation-trend", {
            "symbol": symbol,
            "region": region,
            "lang": lang
        })
        response = {"success": True, "symbol": symbol, "data": result}
        return optimize_tool_response(response, "get_recommendation_trend", symbol)
    except Exception as e:
        logger.error(f"get_recommendation_trend failed for {symbol}: {e}")
        return {"success": False, "error": str(e), "symbol": symbol}


@tool
@logged_tool
@cache.cached(ttl=86400)
def get_upgrades_downgrades(symbol: str, region: str = "US", lang: str = "en-US") -> Dict:
    """
    Get recent analyst upgrades and downgrades.

    Tracks when analysts raise or lower their ratings on a stock.

    Args:
        symbol: Stock ticker
        region: Region code (default: "US")
        lang: Language code (default: "en-US")

    Returns:
        Dict with upgrade/downgrade history

    Example:
        get_upgrades_downgrades("TSLA") -> Recent rating changes for Tesla
    """
    try:
        result = _make_api_call("/stock/get-upgrades-downgrades", {
            "symbol": symbol,
            "region": region,
            "lang": lang
        })
        response = {"success": True, "symbol": symbol, "data": result}
        return optimize_tool_response(response, "get_upgrades_downgrades", symbol)
    except Exception as e:
        logger.error(f"get_upgrades_downgrades failed for {symbol}: {e}")
        return {"success": False, "error": str(e), "symbol": symbol}


# ============================================================================
# OWNERSHIP & HOLDERS TOOLS
# ============================================================================

@tool
@logged_tool
@cache.cached(ttl=86400)
def get_stock_holders(symbol: str, region: str = "US", lang: str = "en-US") -> Dict:
    """
    Get information about major shareholders.

    Includes institutional holders and their positions.

    Args:
        symbol: Stock ticker
        region: Region code (default: "US")
        lang: Language code (default: "en-US")

    Returns:
        Dict with holder information

    Example:
        get_stock_holders("AAPL") -> Major shareholders of Apple
    """
    try:
        result = _make_api_call("/stock/get-holders", {
            "symbol": symbol,
            "region": region,
            "lang": lang
        })
        response = {"success": True, "symbol": symbol, "data": result}
        return optimize_tool_response(response, "get_stock_holders", symbol)
    except Exception as e:
        logger.error(f"get_stock_holders failed for {symbol}: {e}")
        return {"success": False, "error": str(e), "symbol": symbol}


@tool
@logged_tool
@cache.cached(ttl=86400)
def get_major_holders(symbol: str, region: str = "US", lang: str = "en-US") -> Dict:
    """
    Get major institutional holders and ownership breakdown.

    Shows percentage held by institutions, insiders, etc.

    Args:
        symbol: Stock ticker
        region: Region code (default: "US")
        lang: Language code (default: "en-US")

    Returns:
        Dict with major holder data

    Example:
        get_major_holders("MSFT") -> Ownership breakdown for Microsoft
    """
    try:
        result = _make_api_call("/stock/get-major-holders", {
            "symbol": symbol,
            "region": region,
            "lang": lang
        })
        response = {"success": True, "symbol": symbol, "data": result}
        return optimize_tool_response(response, "get_major_holders", symbol)
    except Exception as e:
        logger.error(f"get_major_holders failed for {symbol}: {e}")
        return {"success": False, "error": str(e), "symbol": symbol}


@tool
@logged_tool
@cache.cached(ttl=86400)
def get_insider_transactions(symbol: str, region: str = "US", lang: str = "en-US") -> Dict:
    """
    Get insider buying and selling transactions.

    Tracks when company insiders buy or sell shares, which can
    indicate insider confidence in the company.

    Args:
        symbol: Stock ticker
        region: Region code (default: "US")
        lang: Language code (default: "en-US")

    Returns:
        Dict with insider transaction history

    Example:
        get_insider_transactions("NVDA") -> Insider trades for Nvidia
    """
    try:
        result = _make_api_call("/stock/get-insider-transactions", {
            "symbol": symbol,
            "region": region,
            "lang": lang
        })
        response = {"success": True, "symbol": symbol, "data": result}
        return optimize_tool_response(response, "get_insider_transactions", symbol)
    except Exception as e:
        logger.error(f"get_insider_transactions failed for {symbol}: {e}")
        return {"success": False, "error": str(e), "symbol": symbol}


@tool
@logged_tool
@cache.cached(ttl=86400)
def get_insider_roster(symbol: str, region: str = "US", lang: str = "en-US") -> Dict:
    """
    Get list of company insiders and their positions.

    Args:
        symbol: Stock ticker
        region: Region code (default: "US")
        lang: Language code (default: "en-US")

    Returns:
        Dict with insider roster

    Example:
        get_insider_roster("TSLA") -> Tesla's insider roster
    """
    try:
        result = _make_api_call("/stock/get-insider-roster", {
            "symbol": symbol,
            "region": region,
            "lang": lang
        })
        response = {"success": True, "symbol": symbol, "data": result}
        return optimize_tool_response(response, "get_insider_roster", symbol)
    except Exception as e:
        logger.error(f"get_insider_roster failed for {symbol}: {e}")
        return {"success": False, "error": str(e), "symbol": symbol}


# ============================================================================
# ESG TOOLS
# ============================================================================

@tool
@logged_tool
@cache.cached(ttl=86400)
def get_esg_scores(symbol: str, region: str = "US", lang: str = "en-US") -> Dict:
    """
    Get Environmental, Social, and Governance (ESG) scores.

    ESG scores rate companies on:
    - Environmental: Climate impact, waste, resource use
    - Social: Labor practices, diversity, community
    - Governance: Board structure, ethics, shareholder rights

    Args:
        symbol: Stock ticker
        region: Region code (default: "US")
        lang: Language code (default: "en-US")

    Returns:
        Dict with ESG scores and ratings

    Example:
        get_esg_scores("AAPL") -> Apple's ESG scores
    """
    try:
        result = _make_api_call("/stock/get-esg-scores", {
            "symbol": symbol,
            "region": region,
            "lang": lang
        })
        response = {"success": True, "symbol": symbol, "data": result}
        return optimize_tool_response(response, "get_esg_scores", symbol)
    except Exception as e:
        logger.error(f"get_esg_scores failed for {symbol}: {e}")
        return {"success": False, "error": str(e), "symbol": symbol}


@tool
@logged_tool
@cache.cached(ttl=86400)
def get_esg_chart(symbol: str, region: str = "US", lang: str = "en-US") -> Dict:
    """
    Get ESG score trends over time.

    Shows how company's ESG performance has changed.

    Args:
        symbol: Stock ticker
        region: Region code (default: "US")
        lang: Language code (default: "en-US")

    Returns:
        Dict with ESG score history

    Example:
        get_esg_chart("MSFT") -> Microsoft's ESG score trends
    """
    try:
        result = _make_api_call("/stock/get-esg-chart", {
            "symbol": symbol,
            "region": region,
            "lang": lang
        })
        response = {"success": True, "symbol": symbol, "data": result}
        return optimize_tool_response(response, "get_esg_chart", symbol)
    except Exception as e:
        logger.error(f"get_esg_chart failed for {symbol}: {e}")
        return {"success": False, "error": str(e), "symbol": symbol}


@tool
@logged_tool
@cache.cached(ttl=86400)
def get_esg_peer_scores(symbol: str, region: str = "US", lang: str = "en-US") -> Dict:
    """
    Get ESG scores compared to industry peers.

    Useful for understanding relative ESG performance.

    Args:
        symbol: Stock ticker
        region: Region code (default: "US")
        lang: Language code (default: "en-US")

    Returns:
        Dict with peer ESG comparison

    Example:
        get_esg_peer_scores("TSLA") -> Tesla's ESG vs competitors
    """
    try:
        result = _make_api_call("/stock/get-esg-peer-scores", {
            "symbol": symbol,
            "region": region,
            "lang": lang
        })
        response = {"success": True, "symbol": symbol, "data": result}
        return optimize_tool_response(response, "get_esg_peer_scores", symbol)
    except Exception as e:
        logger.error(f"get_esg_peer_scores failed for {symbol}: {e}")
        return {"success": False, "error": str(e), "symbol": symbol}


# ============================================================================
# OPTIONS & DERIVATIVES TOOLS
# ============================================================================

@tool
@logged_tool
@cache.cached(ttl=900)
def get_stock_options(symbol: str, region: str = "US", lang: str = "en-US") -> Dict:
    """
    Get options chain data (calls and puts).

    Includes:
    - Available expiration dates
    - Strike prices
    - Options premiums
    - Implied volatility
    - Greeks (delta, gamma, etc.)

    Args:
        symbol: Stock ticker
        region: Region code (default: "US")
        lang: Language code (default: "en-US")

    Returns:
        Dict with options chain

    Example:
        get_stock_options("AAPL") -> Options data for Apple
    """
    try:
        result = _make_api_call("/stock/get-options", {
            "symbol": symbol,
            "region": region,
            "lang": lang
        })
        response = {"success": True, "symbol": symbol, "data": result}
        return optimize_tool_response(response, "get_stock_options", symbol)
    except Exception as e:
        logger.error(f"get_stock_options failed for {symbol}: {e}")
        return {"success": False, "error": str(e), "symbol": symbol}


@tool
@logged_tool
@cache.cached(ttl=900)
def get_futures_chain(symbol: str, region: str = "US", lang: str = "en-US") -> Dict:
    """
    Get futures contract chain data.

    Args:
        symbol: Futures symbol
        region: Region code (default: "US")
        lang: Language code (default: "en-US")

    Returns:
        Dict with futures data

    Example:
        get_futures_chain("ES=F") -> S&P 500 futures
    """
    try:
        result = _make_api_call("/stock/get-futures-chain", {
            "symbol": symbol,
            "region": region,
            "lang": lang
        })
        response = {"success": True, "symbol": symbol, "data": result}
        return optimize_tool_response(response, "get_futures_chain", symbol)
    except Exception as e:
        logger.error(f"get_futures_chain failed for {symbol}: {e}")
        return {"success": False, "error": str(e), "symbol": symbol}


# ============================================================================
# FUND/ETF TOOLS
# ============================================================================

@tool
@logged_tool
@cache.cached(ttl=86400)
def get_fund_profile(symbol: str, region: str = "US", lang: str = "en-US") -> Dict:
    """
    Get mutual fund or ETF profile information.

    Includes:
    - Fund family
    - Category
    - Investment strategy
    - Expense ratio
    - Minimum investment

    Args:
        symbol: Fund ticker (e.g., "VTSAX", "SPY")
        region: Region code (default: "US")
        lang: Language code (default: "en-US")

    Returns:
        Dict with fund profile

    Example:
        get_fund_profile("SPY") -> SPDR S&P 500 ETF profile
    """
    try:
        result = _make_api_call("/stock/get-fund-profile", {
            "symbol": symbol,
            "region": region,
            "lang": lang
        })
        response = {"success": True, "symbol": symbol, "data": result}
        return optimize_tool_response(response, "get_fund_profile", symbol)
    except Exception as e:
        logger.error(f"get_fund_profile failed for {symbol}: {e}")
        return {"success": False, "error": str(e), "symbol": symbol}


@tool
@logged_tool
@cache.cached(ttl=86400)
def get_top_holdings(symbol: str, region: str = "US", lang: str = "en-US") -> Dict:
    """
    Get top holdings for an ETF or mutual fund.

    Shows the largest positions in the fund's portfolio.

    Args:
        symbol: Fund ticker
        region: Region code (default: "US")
        lang: Language code (default: "en-US")

    Returns:
        Dict with top holdings

    Example:
        get_top_holdings("VOO") -> Vanguard S&P 500 ETF holdings
    """
    try:
        result = _make_api_call("/stock/get-top-holdings", {
            "symbol": symbol,
            "region": region,
            "lang": lang
        })
        response = {"success": True, "symbol": symbol, "data": result}
        return optimize_tool_response(response, "get_top_holdings", symbol)
    except Exception as e:
        logger.error(f"get_top_holdings failed for {symbol}: {e}")
        return {"success": False, "error": str(e), "symbol": symbol}


# ============================================================================
# NEWS TOOLS
# ============================================================================

@tool
@logged_tool
@cache.cached(ttl=900)
def get_news_list(
    symbol: Optional[str] = None,
    category: Optional[str] = None,
    region: str = "US",
    lang: str = "en-US",
    count: int = 10
) -> Dict:
    """
    Get financial news articles.

    Can filter by symbol or get general market news.

    Args:
        symbol: Optional stock ticker to filter news
        category: Optional category filter
        region: Region code (default: "US")
        lang: Language code (default: "en-US")
        count: Number of articles (default: 10)

    Returns:
        Dict with news articles

    Example:
        get_news_list(symbol="AAPL", count=5) -> Latest Apple news
        get_news_list(category="technology") -> Tech sector news
    """
    try:
        params = {"region": region, "lang": lang}
        if symbol:
            params["symbol"] = symbol
        if category:
            params["category"] = category
        if count:
            params["count"] = count

        result = _make_api_call("/news/get-list", params)
        return {"success": True, "data": result}
    except Exception as e:
        logger.error(f"get_news_list failed: {e}")
        return {"success": False, "error": str(e)}


@tool
@logged_tool
@cache.cached(ttl=3600)
def get_news_article(uuid: str, region: str = "US", lang: str = "en-US") -> Dict:
    """
    Get full content of a news article by UUID.

    Args:
        uuid: Article UUID from news list
        region: Region code (default: "US")
        lang: Language code (default: "en-US")

    Returns:
        Dict with article content

    Example:
        get_news_article(uuid="abc-123") -> Full article text
    """
    try:
        result = _make_api_call("/news/get-article", {
            "uuid": uuid,
            "region": region,
            "lang": lang
        })
        return {"success": True, "data": result}
    except Exception as e:
        logger.error(f"get_news_article failed: {e}")
        return {"success": False, "error": str(e)}


# ============================================================================
# SEC FILINGS TOOLS
# ============================================================================

@tool
@logged_tool
@cache.cached(ttl=86400)
def get_sec_filings(symbol: str, region: str = "US", lang: str = "en-US") -> Dict:
    """
    Get SEC filing documents (10-K, 10-Q, 8-K, etc.).

    Args:
        symbol: Stock ticker
        region: Region code (default: "US")
        lang: Language code (default: "en-US")

    Returns:
        Dict with SEC filings list

    Example:
        get_sec_filings("TSLA") -> Tesla's SEC filings
    """
    try:
        result = _make_api_call("/stock/get-sec-filings", {
            "symbol": symbol,
            "region": region,
            "lang": lang
        })
        response = {"success": True, "symbol": symbol, "data": result}
        return optimize_tool_response(response, "get_sec_filings", symbol)
    except Exception as e:
        logger.error(f"get_sec_filings failed for {symbol}: {e}")
        return {"success": False, "error": str(e), "symbol": symbol}


# ============================================================================
# DISCOVERY & COMPARISON TOOLS
# ============================================================================

@tool
@logged_tool
@cache.cached(ttl=86400)
def get_similar_stocks(symbol: str, region: str = "US", lang: str = "en-US") -> Dict:
    """
    Get similar or related stocks.

    Useful for discovering comparable companies or alternatives.

    Args:
        symbol: Stock ticker
        region: Region code (default: "US")
        lang: Language code (default: "en-US")

    Returns:
        Dict with similar stocks

    Example:
        get_similar_stocks("AAPL") -> Stocks similar to Apple
    """
    try:
        result = _make_api_call("/stock/get-similar", {
            "symbol": symbol,
            "region": region,
            "lang": lang
        })
        response = {"success": True, "symbol": symbol, "data": result}
        return optimize_tool_response(response, "get_similar_stocks", symbol)
    except Exception as e:
        logger.error(f"get_similar_stocks failed for {symbol}: {e}")
        return {"success": False, "error": str(e), "symbol": symbol}


@tool
@logged_tool
@cache.cached(ttl=86400)
def get_screeners_list(region: str = "US", lang: str = "en-US") -> Dict:
    """
    Get list of available stock screeners.

    Screeners help filter stocks by criteria (e.g., high dividend,
    growth stocks, undervalued, etc.).

    Args:
        region: Region code (default: "US")
        lang: Language code (default: "en-US")

    Returns:
        Dict with available screeners

    Example:
        get_screeners_list() -> List of predefined screeners
    """
    try:
        result = _make_api_call("/screeners/get-list", {
            "region": region,
            "lang": lang
        })
        return {"success": True, "data": result}
    except Exception as e:
        logger.error(f"get_screeners_list failed: {e}")
        return {"success": False, "error": str(e)}


@tool
@logged_tool
@cache.cached(ttl=3600)
def get_saved_screeners(slug: str, count: int = 10, start: int = 0) -> Dict:
    """
    Get saved screener results by slug identifier.

    Args:
        slug: Screener identifier (e.g., "SOLID_LARGE_GROWTH_FUNDS")
        count: Number of results to return (default: 10)
        start: Starting offset for pagination (default: 0)

    Returns:
        Dict with saved screener results

    Example:
        get_saved_screeners("SOLID_LARGE_GROWTH_FUNDS") -> Solid Large Growth Funds screener results
    """
    try:
        result = _make_api_call("/screeners/get-saved", {
            "slug": slug,
            "count": count,
            "start": start
        })
        response = {"success": True, "slug": slug, "data": result}
        return optimize_tool_response(response, "get_saved_screeners", slug)
    except Exception as e:
        logger.error(f"get_saved_screeners failed for {slug}: {e}")
        return {"success": False, "error": str(e), "slug": slug}


# ============================================================================
# CALENDAR TOOLS
# ============================================================================

@tool
@logged_tool
@cache.cached(ttl=3600)
def get_calendar_events(
    entityIdType: str,
    sortType: str = "ASC",
    sortField: str = "startdatetime",
    region: str = "US",
    size: int = 100,
    lang: str = "en-US",
    offset: int = 0,
    includeFields: Optional[str] = None
) -> Dict:
    """
    Get upcoming calendar events (earnings, dividends, splits, etc.).

    Args:
        entityIdType: Type of event (required) - "earnings", "dividends", "splits", etc.
        sortType: Sort order - "ASC" or "DESC" (default: "ASC")
        sortField: Field to sort by (default: "startdatetime")
        region: Region code (default: "US")
        size: Number of results to return (default: 100)
        lang: Language code (default: "en-US")
        offset: Starting offset for pagination (default: 0)
        includeFields: Optional JSON array of fields to include (e.g., '["ticker","companyshortname","eventname"]')

    Returns:
        Dict with calendar events

    Example:
        get_calendar_events("earnings") -> Upcoming earnings events
        get_calendar_events("dividends", size=50) -> Next 50 dividend events
    """
    try:
        params = {
            "entityIdType": entityIdType,
            "sortType": sortType,
            "sortField": sortField,
            "region": region,
            "size": size,
            "lang": lang,
            "offset": offset
        }
        if includeFields:
            params["includeFields"] = includeFields

        result = _make_api_call("/calendar/get-events", params)
        response = {"success": True, "entityIdType": entityIdType, "data": result}
        return optimize_tool_response(response, "get_calendar_events", entityIdType)
    except Exception as e:
        logger.error(f"get_calendar_events failed for {entityIdType}: {e}")
        return {"success": False, "error": str(e), "entityIdType": entityIdType}


@tool
@logged_tool
@cache.cached(ttl=3600)
def count_calendar_events(entityIdType: str, region: str = "US", lang: str = "en-US") -> Dict:
    """
    Get count of upcoming calendar events by type.

    Args:
        entityIdType: Type of event (required) - "earnings", "dividends", "splits", etc.
        region: Region code (default: "US")
        lang: Language code (default: "en-US")

    Returns:
        Dict with event counts aggregated by date

    Example:
        count_calendar_events("earnings") -> Daily counts of upcoming earnings events
        count_calendar_events("dividends") -> Daily counts of upcoming dividend payments
    """
    try:
        result = _make_api_call("/calendar/count-events", {
            "entityIdType": entityIdType,
            "region": region,
            "lang": lang
        })
        response = {"success": True, "entityIdType": entityIdType, "data": result}
        return optimize_tool_response(response, "count_calendar_events", entityIdType)
    except Exception as e:
        logger.error(f"count_calendar_events failed for {entityIdType}: {e}")
        return {"success": False, "error": str(e), "entityIdType": entityIdType}


# ============================================================================
# CONVERSATIONS TOOLS (Community/Social)
# ============================================================================

@tool
@logged_tool
@cache.cached(ttl=900)
def get_conversations_list(postId: str, offset: int = 0, sort_by: str = "newest", count: int = 10) -> Dict:
    """
    Get community conversations/discussions for a message board.

    Args:
        postId: Message board identifier (e.g., "finmb_29096" for a stock's board)
        offset: Starting offset for pagination (default: 0)
        sort_by: Sort order - "newest", "oldest", or "best" (default: "newest")
        count: Number of conversations to return (default: 10)

    Returns:
        Dict with conversation threads

    Example:
        get_conversations_list("finmb_29096") -> Discussions on the board
    """
    try:
        result = _make_api_call("/conversations/get-list", {
            "postId": postId,
            "offset": offset,
            "sort_by": sort_by,
            "count": count
        })
        response = {"success": True, "postId": postId, "data": result}
        return optimize_tool_response(response, "get_conversations_list", postId)
    except Exception as e:
        logger.error(f"get_conversations_list failed for {postId}: {e}")
        return {"success": False, "error": str(e), "postId": postId}


@tool
@logged_tool
@cache.cached(ttl=900)
def count_conversations(postId: str) -> Dict:
    """
    Get count of conversations/messages for a message board.

    Useful for gauging social interest/activity on a stock's message board.

    Args:
        postId: Message board identifier (e.g., "finmb_29096" for a stock's board)

    Returns:
        Dict with conversation count (replies and comments)

    Example:
        count_conversations("finmb_29096") -> Number of discussions on the board
    """
    try:
        result = _make_api_call("/conversations/count", {
            "postId": postId
        })
        response = {"success": True, "postId": postId, "data": result}
        return optimize_tool_response(response, "count_conversations", postId)
    except Exception as e:
        logger.error(f"count_conversations failed for {postId}: {e}")
        return {"success": False, "error": str(e), "postId": postId}


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def get_all_market_data_tools():
    """
    Get list of all market data tool functions.

    Useful for registering tools with subagents.

    Returns:
        List of all tool functions
    """
    return [
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
        count_conversations,
    ]
