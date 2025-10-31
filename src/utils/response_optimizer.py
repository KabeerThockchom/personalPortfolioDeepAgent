"""
Response Optimizer for Market Data Tools

Automatically saves large API responses to files and returns compact summaries
to prevent context bloat in LLM conversations.
"""

import json
import os
from typing import Dict, Any, Optional
from pathlib import Path


# Threshold for auto-saving responses (in characters)
LARGE_RESPONSE_THRESHOLD = 1000

# Directory for saving responses
DATA_DIR = "/financial_data"


def ensure_data_dir():
    """Ensure the data directory exists."""
    # In DeepAgents, directories are virtual - no need to create
    pass


def save_large_response(
    data: Dict[str, Any],
    filename: str,
    symbol: Optional[str] = None,
    session_id: Optional[str] = None
) -> str:
    """
    Save large response data to a file.

    Args:
        data: The response data to save
        filename: Base filename (e.g., "quote", "statistics")
        symbol: Stock symbol (optional, added to filename)
        session_id: Session ID for determining actual disk location

    Returns:
        File path where data was saved (virtual path)
    """
    # Generate virtual filename
    if symbol:
        file_path = f"{DATA_DIR}/{symbol}_{filename}.json"
    else:
        file_path = f"{DATA_DIR}/{filename}.json"

    # Actually write the file to disk using FilesystemBackend logic
    # We need to write to sessions/{session_id}/financial_data/ on disk
    try:
        if session_id:
            # Write to actual disk location
            actual_dir = Path("sessions") / session_id / "financial_data"
            actual_dir.mkdir(parents=True, exist_ok=True)
            
            # Determine actual filename
            if symbol:
                actual_filename = f"{symbol}_{filename}.json"
            else:
                actual_filename = f"{filename}.json"
            
            actual_path = actual_dir / actual_filename
            
            # Write JSON file
            with open(actual_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        else:
            # Fallback: try to write to sessions directory if we can find a recent one
            sessions_dir = Path("sessions")
            if sessions_dir.exists():
                # Find most recent session directory
                session_dirs = [d for d in sessions_dir.iterdir() if d.is_dir()]
                if session_dirs:
                    latest_session = max(session_dirs, key=lambda p: p.stat().st_mtime)
                    actual_dir = latest_session / "financial_data"
                    actual_dir.mkdir(parents=True, exist_ok=True)
                    
                    if symbol:
                        actual_filename = f"{symbol}_{filename}.json"
                    else:
                        actual_filename = f"{filename}.json"
                    
                    actual_path = actual_dir / actual_filename
                    with open(actual_path, "w", encoding="utf-8") as f:
                        json.dump(data, f, indent=2)
    except Exception as e:
        # If file writing fails, log but continue - agent can still use the path
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Failed to write file {file_path}: {e}")

    return file_path


def extract_quote_metrics(data: Dict) -> Dict[str, Any]:
    """
    Extract key metrics from quote/summary data.

    Args:
        data: Yahoo Finance quote response

    Returns:
        Dict with key metrics
    """
    try:
        # Yahoo Finance structure: quoteSummary.result[0]
        if "quoteSummary" in data and "result" in data["quoteSummary"]:
            result = data["quoteSummary"]["result"][0] if data["quoteSummary"]["result"] else {}
            price_data = result.get("price", {})
            summary = result.get("summaryDetail", {})
        else:
            # Fallback: try direct access
            price_data = data.get("price", {})
            summary = data.get("summaryDetail", {})

        metrics = {
            "symbol": price_data.get("symbol", data.get("symbol", "")),
            "price": price_data.get("regularMarketPrice") or summary.get("previousClose", 0),
            "change": price_data.get("regularMarketChange", 0),
            "change_percent": price_data.get("regularMarketChangePercent", 0),
            "volume": price_data.get("regularMarketVolume", 0),
            "market_cap": summary.get("marketCap") or price_data.get("marketCap", 0),
            "day_high": summary.get("dayHigh", 0),
            "day_low": summary.get("dayLow", 0),
            "52w_high": summary.get("fiftyTwoWeekHigh", 0),
            "52w_low": summary.get("fiftyTwoWeekLow", 0),
            "beta": summary.get("beta", 0),
            "pe_ratio": summary.get("trailingPE", 0),
        }

        return {k: v for k, v in metrics.items() if v}  # Remove empty values

    except Exception as e:
        return {}


def extract_statistics_metrics(data: Dict) -> Dict[str, Any]:
    """
    Extract key metrics from statistics data.

    Args:
        data: Yahoo Finance statistics response

    Returns:
        Dict with key metrics
    """
    try:
        stats = data.get("data", {})

        metrics = {
            "symbol": data.get("symbol", ""),
            "pe_ratio": stats.get("trailingPE", 0),
            "forward_pe": stats.get("forwardPE", 0),
            "peg_ratio": stats.get("pegRatio", 0),
            "price_to_book": stats.get("priceToBook", 0),
            "beta": stats.get("beta", 0),
            "dividend_yield": stats.get("dividendYield", 0),
            "profit_margin": stats.get("profitMargins", 0),
            "revenue_growth": stats.get("revenueGrowth", 0),
        }

        return {k: v for k, v in metrics.items() if v}

    except Exception:
        return {}


def extract_analysis_metrics(data: Dict) -> Dict[str, Any]:
    """
    Extract key metrics from analyst analysis data.

    Args:
        data: Yahoo Finance analysis response

    Returns:
        Dict with key metrics
    """
    try:
        analysis = data.get("data", {})

        metrics = {
            "symbol": data.get("symbol", ""),
            "target_mean_price": analysis.get("targetMeanPrice", 0),
            "target_high_price": analysis.get("targetHighPrice", 0),
            "target_low_price": analysis.get("targetLowPrice", 0),
            "recommendation": analysis.get("recommendationMean", 0),
            "num_analysts": analysis.get("numberOfAnalystOpinions", 0),
        }

        return {k: v for k, v in metrics.items() if v}

    except Exception:
        return {}


def format_number(num: float, prefix: str = "", suffix: str = "") -> str:
    """Format a number with optional prefix/suffix."""
    if not num:
        return "N/A"

    # Handle large numbers
    if abs(num) >= 1_000_000_000_000:  # Trillion
        return f"{prefix}{num/1_000_000_000_000:.2f}T{suffix}"
    elif abs(num) >= 1_000_000_000:  # Billion
        return f"{prefix}{num/1_000_000_000:.2f}B{suffix}"
    elif abs(num) >= 1_000_000:  # Million
        return f"{prefix}{num/1_000_000:.2f}M{suffix}"
    elif abs(num) >= 1_000:  # Thousand
        return f"{prefix}{num/1_000:.2f}K{suffix}"
    else:
        return f"{prefix}{num:.2f}{suffix}"


def create_quote_summary(metrics: Dict, file_path: str) -> str:
    """
    Create a compact summary for quote data.

    Args:
        metrics: Extracted key metrics
        file_path: Path where full data was saved

    Returns:
        Formatted summary string
    """
    symbol = metrics.get("symbol", "")
    price = metrics.get("price", 0)
    change = metrics.get("change", 0)
    change_pct = metrics.get("change_percent", 0)
    volume = metrics.get("volume", 0)
    mcap = metrics.get("market_cap", 0)

    summary_parts = []

    if price:
        change_str = f"+{change:.2f}" if change >= 0 else f"{change:.2f}"
        pct_str = f"+{change_pct:.2f}" if change_pct >= 0 else f"{change_pct:.2f}"
        summary_parts.append(f"Price: ${price:.2f} ({change_str}, {pct_str}%)")

    if volume:
        summary_parts.append(f"Vol: {format_number(volume)}")

    if mcap:
        summary_parts.append(f"MCap: {format_number(mcap, '$')}")

    summary = f"✓ {symbol} - {', '.join(summary_parts)}" if summary_parts else f"✓ Data retrieved for {symbol}"
    summary += f"\n📁 Full data: {file_path}"

    return summary


def create_statistics_summary(metrics: Dict, file_path: str) -> str:
    """Create a compact summary for statistics data."""
    symbol = metrics.get("symbol", "")
    pe = metrics.get("pe_ratio", 0)
    beta = metrics.get("beta", 0)
    div_yield = metrics.get("dividend_yield", 0)
    margin = metrics.get("profit_margin", 0)

    summary_parts = []

    if pe:
        summary_parts.append(f"P/E: {pe:.2f}")
    if beta:
        summary_parts.append(f"Beta: {beta:.2f}")
    if div_yield:
        summary_parts.append(f"Div Yield: {div_yield*100:.2f}%")
    if margin:
        summary_parts.append(f"Margin: {margin*100:.2f}%")

    summary = f"✓ {symbol} Stats - {', '.join(summary_parts)}" if summary_parts else f"✓ Statistics for {symbol}"
    summary += f"\n📁 Full data: {file_path}"

    return summary


def create_analysis_summary(metrics: Dict, file_path: str) -> str:
    """Create a compact summary for analyst analysis data."""
    symbol = metrics.get("symbol", "")
    target = metrics.get("target_mean_price", 0)
    rec = metrics.get("recommendation", 0)
    num = metrics.get("num_analysts", 0)

    # Convert recommendation mean to text (1=Strong Buy, 5=Sell)
    rec_text = "N/A"
    if rec:
        if rec < 1.5:
            rec_text = "Strong Buy"
        elif rec < 2.5:
            rec_text = "Buy"
        elif rec < 3.5:
            rec_text = "Hold"
        elif rec < 4.5:
            rec_text = "Sell"
        else:
            rec_text = "Strong Sell"

    summary_parts = []

    if target:
        summary_parts.append(f"Target: ${target:.2f}")
    if rec_text != "N/A":
        summary_parts.append(f"Rating: {rec_text}")
    if num:
        summary_parts.append(f"{num} analysts")

    summary = f"✓ {symbol} Analysis - {', '.join(summary_parts)}" if summary_parts else f"✓ Analysis for {symbol}"
    summary += f"\n📁 Full data: {file_path}"

    return summary


def create_generic_summary(data: Dict, filename: str, file_path: str) -> str:
    """Create a generic summary for other data types."""
    symbol = data.get("symbol", "")

    # Count items in response
    data_content = data.get("data", {})
    if isinstance(data_content, dict):
        item_count = len(data_content)
        summary = f"✓ Retrieved {filename} data for {symbol} ({item_count} fields)"
    elif isinstance(data_content, list):
        item_count = len(data_content)
        summary = f"✓ Retrieved {item_count} {filename} items for {symbol}"
    else:
        summary = f"✓ Retrieved {filename} data for {symbol}"

    summary += f"\n📁 Full data: {file_path}"

    return summary


def optimize_tool_response(
    response: Dict[str, Any],
    tool_name: str,
    symbol: Optional[str] = None,
    session_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Optimize a tool response by saving large data to files and returning summaries.

    Args:
        response: Original tool response
        tool_name: Name of the tool (e.g., "get_stock_quote")
        symbol: Stock symbol (optional)
        session_id: Session ID for file storage (optional, will try to auto-detect)

    Returns:
        Optimized response with summary and file reference
    """
    # If response failed or is small, return as-is
    response_str = json.dumps(response)
    if not response.get("success") or len(response_str) < LARGE_RESPONSE_THRESHOLD:
        return response

    # Extract filename from tool name
    filename = tool_name.replace("get_stock_", "").replace("get_", "")

    # Generate file path and actually write the file
    file_path = save_large_response(response.get("data", {}), filename, symbol, session_id)

    # Extract metrics based on tool type (pass response["data"] to extractors)
    response_data = response.get("data", {})

    if "quote" in tool_name or "summary" in tool_name:
        metrics = extract_quote_metrics(response_data)
        summary = create_quote_summary(metrics, file_path)
    elif "statistics" in tool_name:
        metrics = extract_statistics_metrics(response_data)
        summary = create_statistics_summary(metrics, file_path)
    elif "analysis" in tool_name or "recommendation" in tool_name:
        metrics = extract_analysis_metrics(response_data)
        summary = create_analysis_summary(metrics, file_path)
    else:
        metrics = {}
        summary = create_generic_summary(response, filename, file_path)

    # Return optimized response (WITHOUT full_data_json to save tokens)
    return {
        "success": True,
        "symbol": symbol or response.get("symbol", ""),
        "summary": summary,
        "key_metrics": metrics,
        "file_path": file_path,
        # NOTE: full_data_json removed - it was causing massive token waste (26K+ tokens per call)
        # The full data is already saved to file_path by the calling tool
    }


def should_optimize_response(response: Dict) -> bool:
    """
    Check if a response should be optimized.

    Args:
        response: Tool response

    Returns:
        True if response should be optimized
    """
    if not response.get("success"):
        return False

    response_str = json.dumps(response)
    return len(response_str) >= LARGE_RESPONSE_THRESHOLD
