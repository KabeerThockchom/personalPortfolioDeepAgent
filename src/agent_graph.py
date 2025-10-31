"""
Agent graph module for LangGraph server deployment.

This module exports the compiled finance deep agent graph for use with LangGraph server.
The graph is used by deep-agents-ui for a rich web interface.
"""
from src.deep_agent import create_finance_deep_agent

# Create and export the agent graph
# The LangGraph server will look for a 'graph' variable in this module
graph = create_finance_deep_agent(
    enable_human_in_loop=True,  # Enable approval requests for sensitive operations
    session_id="default"  # Will be overridden per thread by LangGraph server
)

# Export for LangGraph server
__all__ = ["graph"]
