"""Shared state schema for financial analysis agents."""

from typing import Annotated, Sequence, TypedDict
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class FinancialAnalysisState(TypedDict):
    """Shared state across all financial analysis agents."""

    # Conversation messages
    messages: Annotated[Sequence[BaseMessage], add_messages]

    # Client portfolio data
    client_portfolio: dict

    # Agent outputs
    portfolio_analysis: dict | None
    cashflow_analysis: dict | None
    goal_analysis: dict | None
    tax_analysis: dict | None
    debt_analysis: dict | None
    risk_analysis: dict | None

    # Market data (for now just stored values, no API)
    current_prices: dict[str, float]

    # Visualizations generated
    charts: list[dict]

    # Agent routing
    next_agent: str | None
    agents_consulted: list[str]

    # Final response flag
    ready_to_respond: bool
