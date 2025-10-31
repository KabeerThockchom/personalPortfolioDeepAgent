from src.utils.tool_logger import logged_tool

"""
Web Search Tools using Tavily API

Provides real-time web search capabilities for AI agents to access
current information, news, and data beyond their training knowledge.
"""

import os
from typing import Dict, Optional, List
from dotenv import load_dotenv
from langchain_core.tools import tool
from tavily import TavilyClient

# Load environment variables
load_dotenv()

# API Configuration
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "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")

# Initialize Tavily client
tavily_client = TavilyClient(api_key=TAVILY_API_KEY)


@tool
@logged_tool
def web_search(
    query: str,
    search_depth: str = "basic",
    max_results: int = 5,
    include_domains: Optional[List[str]] = None,
    exclude_domains: Optional[List[str]] = None
) -> Dict:
    """
    Search the web for current information using Tavily API.

    Use this tool when you need:
    - Current news or events
    - Recent market information
    - Company announcements or updates
    - Financial news and analysis
    - General information not in your training data

    Args:
        query: Search query (e.g., "latest tech earnings reports 2025")
        search_depth: "basic" for quick results, "advanced" for comprehensive search (default: "basic")
        max_results: Number of results to return, 1-10 (default: 5)
        include_domains: Optional list of domains to include (e.g., ["wsj.com", "bloomberg.com"])
        exclude_domains: Optional list of domains to exclude

    Returns:
        Dict with search results including titles, URLs, content snippets, and relevance scores

    Example:
        web_search("Apple stock news today") -> Recent Apple stock articles
        web_search("Federal Reserve interest rate decision", search_depth="advanced")
        -> Comprehensive Fed policy coverage
    """
    try:
        # Build search parameters
        search_params = {
            "query": query,
            "search_depth": search_depth,
            "max_results": min(max_results, 10)  # Cap at 10
        }

        # Add domain filters if provided
        if include_domains:
            search_params["include_domains"] = include_domains
        if exclude_domains:
            search_params["exclude_domains"] = exclude_domains

        # Execute search
        response = tavily_client.search(**search_params)

        # Format results
        results = []
        for result in response.get("results", []):
            results.append({
                "title": result.get("title", ""),
                "url": result.get("url", ""),
                "content": result.get("content", ""),
                "score": result.get("score", 0),
                "published_date": result.get("published_date", "")
            })

        return {
            "success": True,
            "query": query,
            "results": results,
            "answer": response.get("answer", ""),  # Tavily's AI-generated answer
            "total_results": len(results)
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "query": query
        }


@tool
@logged_tool
def web_search_news(
    query: str,
    days: int = 7,
    max_results: int = 5
) -> Dict:
    """
    Search for recent news articles using Tavily API.

    Optimized for finding current news and articles within a specific timeframe.

    Args:
        query: News search query (e.g., "Tesla earnings report")
        days: Number of days to look back (default: 7)
        max_results: Number of articles to return, 1-10 (default: 5)

    Returns:
        Dict with recent news articles including titles, URLs, snippets, and dates

    Example:
        web_search_news("NVIDIA AI chip announcement", days=3)
        -> NVIDIA news from last 3 days
    """
    try:
        # Add time constraint to query
        time_query = f"{query} (last {days} days)"

        response = tavily_client.search(
            query=time_query,
            search_depth="basic",
            max_results=min(max_results, 10),
            include_answer=True
        )

        # Format news results
        news_items = []
        for result in response.get("results", []):
            news_items.append({
                "title": result.get("title", ""),
                "url": result.get("url", ""),
                "snippet": result.get("content", "")[:300] + "...",  # First 300 chars
                "published_date": result.get("published_date", ""),
                "relevance_score": result.get("score", 0)
            })

        return {
            "success": True,
            "query": query,
            "timeframe_days": days,
            "news": news_items,
            "summary": response.get("answer", ""),
            "total_articles": len(news_items)
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "query": query
        }


@tool
@logged_tool
def web_search_financial(
    query: str,
    max_results: int = 5
) -> Dict:
    """
    Search for financial news and information from trusted sources.

    Automatically filters to reputable financial news sources like
    Bloomberg, WSJ, Reuters, Financial Times, etc.

    Args:
        query: Financial search query (e.g., "S&P 500 performance today")
        max_results: Number of results to return, 1-10 (default: 5)

    Returns:
        Dict with financial news from trusted sources

    Example:
        web_search_financial("inflation rate forecast 2025")
        -> Financial news about inflation from reputable sources
    """
    try:
        # List of trusted financial domains
        financial_domains = [
            "bloomberg.com",
            "wsj.com",
            "reuters.com",
            "ft.com",
            "marketwatch.com",
            "cnbc.com",
            "forbes.com",
            "barrons.com",
            "investors.com",
            "seekingalpha.com"
        ]

        response = tavily_client.search(
            query=query,
            search_depth="advanced",
            max_results=min(max_results, 10),
            include_domains=financial_domains
        )

        # Format results
        articles = []
        for result in response.get("results", []):
            # Extract source domain
            url = result.get("url", "")
            source = url.split("/")[2] if "/" in url else "Unknown"

            articles.append({
                "title": result.get("title", ""),
                "source": source,
                "url": url,
                "content": result.get("content", ""),
                "published_date": result.get("published_date", ""),
                "relevance": result.get("score", 0)
            })

        return {
            "success": True,
            "query": query,
            "articles": articles,
            "summary": response.get("answer", ""),
            "total_articles": len(articles),
            "sources_searched": financial_domains
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "query": query
        }
