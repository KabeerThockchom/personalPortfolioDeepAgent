#!/usr/bin/env python3
"""Web Search Tools MCP Server - Tavily API Integration"""

import asyncio
import sys
from pathlib import Path
import os
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
import json
from tavily import TavilyClient

# Load environment variables
load_dotenv()

# Initialize Tavily client
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "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")
tavily_client = TavilyClient(api_key=TAVILY_API_KEY)

# Initialize MCP server
app = Server("search-tools")


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available search tools."""
    return [
        Tool(
            name="web_search",
            description="Search the web for current information using Tavily API",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                    "search_depth": {"type": "string", "default": "basic", "enum": ["basic", "advanced"]},
                    "max_results": {"type": "integer", "default": 5, "minimum": 1, "maximum": 10},
                    "include_domains": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Optional list of domains to include"
                    },
                    "exclude_domains": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Optional list of domains to exclude"
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="web_search_news",
            description="Search for recent news articles using Tavily API",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "News search query"},
                    "days": {"type": "integer", "default": 7, "description": "Number of days to look back"},
                    "max_results": {"type": "integer", "default": 5, "minimum": 1, "maximum": 10}
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="web_search_financial",
            description="Search for financial news from trusted sources (Bloomberg, WSJ, Reuters, etc.)",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Financial search query"},
                    "max_results": {"type": "integer", "default": 5, "minimum": 1, "maximum": 10}
                },
                "required": ["query"]
            }
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool execution."""
    try:
        result = None

        if name == "web_search":
            search_params = {
                "query": arguments["query"],
                "search_depth": arguments.get("search_depth", "basic"),
                "max_results": min(arguments.get("max_results", 5), 10)
            }
            if "include_domains" in arguments:
                search_params["include_domains"] = arguments["include_domains"]
            if "exclude_domains" in arguments:
                search_params["exclude_domains"] = arguments["exclude_domains"]

            response = tavily_client.search(**search_params)

            results = []
            for res in response.get("results", []):
                results.append({
                    "title": res.get("title", ""),
                    "url": res.get("url", ""),
                    "content": res.get("content", ""),
                    "score": res.get("score", 0),
                    "published_date": res.get("published_date", "")
                })

            result = {
                "success": True,
                "query": arguments["query"],
                "results": results,
                "answer": response.get("answer", ""),
                "total_results": len(results)
            }

        elif name == "web_search_news":
            time_query = f"{arguments['query']} (last {arguments.get('days', 7)} days)"
            response = tavily_client.search(
                query=time_query,
                search_depth="basic",
                max_results=min(arguments.get("max_results", 5), 10),
                include_answer=True
            )

            news_items = []
            for res in response.get("results", []):
                news_items.append({
                    "title": res.get("title", ""),
                    "url": res.get("url", ""),
                    "snippet": res.get("content", "")[:300] + "...",
                    "published_date": res.get("published_date", ""),
                    "relevance_score": res.get("score", 0)
                })

            result = {
                "success": True,
                "query": arguments["query"],
                "timeframe_days": arguments.get("days", 7),
                "news": news_items,
                "summary": response.get("answer", ""),
                "total_articles": len(news_items)
            }

        elif name == "web_search_financial":
            financial_domains = [
                "bloomberg.com", "wsj.com", "reuters.com", "ft.com",
                "marketwatch.com", "cnbc.com", "forbes.com", "barrons.com",
                "investors.com", "seekingalpha.com"
            ]

            response = tavily_client.search(
                query=arguments["query"],
                search_depth="advanced",
                max_results=min(arguments.get("max_results", 5), 10),
                include_domains=financial_domains
            )

            articles = []
            for res in response.get("results", []):
                url = res.get("url", "")
                source = url.split("/")[2] if "/" in url else "Unknown"

                articles.append({
                    "title": res.get("title", ""),
                    "source": source,
                    "url": url,
                    "content": res.get("content", ""),
                    "published_date": res.get("published_date", ""),
                    "relevance": res.get("score", 0)
                })

            result = {
                "success": True,
                "query": arguments["query"],
                "articles": articles,
                "summary": response.get("answer", ""),
                "total_articles": len(articles),
                "sources_searched": financial_domains
            }

        else:
            raise ValueError(f"Unknown tool: {name}")

        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    except Exception as e:
        return [TextContent(type="text", text=json.dumps({
            "success": False,
            "error": str(e),
            "query": arguments.get("query", "")
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
