"""
Agent service for executing financial agent with streaming support.
"""
import json
from typing import Iterator, Dict, Any
from langchain_core.messages import HumanMessage

from src.deep_agent import create_finance_deep_agent
from api.event_parser import parse_stream_to_events
from api.models import AgentEvent
from api.session_manager import Session


class AgentService:
    """Service for managing agent execution."""

    def __init__(self):
        self.agent = None
        self._initialize_agent()

    def _initialize_agent(self):
        """Initialize the finance deep agent."""
        try:
            self.agent = create_finance_deep_agent()
        except Exception as e:
            print(f"Error initializing agent: {e}")
            raise

    def stream_response(
        self,
        session: Session,
        user_message: str
    ) -> Iterator[AgentEvent]:
        """
        Stream agent response as events.

        Args:
            session: Chat session with conversation history
            user_message: User's message

        Yields:
            AgentEvent objects
        """
        # Add user message to session
        session.add_message(HumanMessage(content=user_message))

        # Prune conversation history (keep last 5 turns)
        session.prune_history(max_turns=5)

        # Get current state
        state = session.get_state()

        try:
            # Prefer event-level streaming when available to surface updates immediately
            if hasattr(self.agent, "stream_events"):
                # Some runtimes expose a low-level event stream API that yields dict events
                events_iter = self.agent.stream_events(state, version="v1")

                from api.event_parser import EventParser
                parser = EventParser()

                for ev in events_iter:
                    # Try to extract node/state update payloads as they arrive
                    payload = None
                    # Common shapes: {"delta": {node: {...}}} or {"update": {...}}
                    if isinstance(ev, dict):
                        payload = ev.get("delta") or ev.get("update") or ev.get("data") or ev

                    if payload is None:
                        continue

                    for parsed in parser.parse_chunk(payload):
                        yield parsed

                # Finalize to close any open subagents
                for parsed in parser.finalize():
                    yield parsed

            else:
                # Fallback to state streaming
                stream = self.agent.stream(state, stream_mode="updates")

                # Parse stream into events
                for event in parse_stream_to_events(stream):
                    yield event

                # Update session with file changes if FileUpdateEvent
                # (we'll handle this in the server layer)

        except Exception as e:
            # Yield error event
            from api.models import ErrorEvent
            import time
            yield ErrorEvent(
                error=str(e),
                details="Error during agent execution",
                timestamp=time.time()
            )

    def load_portfolio_from_disk(self) -> Dict[str, Any]:
        """Load portfolio.json from disk."""
        try:
            with open("portfolio.json", "r") as f:
                return json.load(f)
        except FileNotFoundError:
            return {
                "error": "portfolio.json not found",
                "message": "Please ensure portfolio.json exists in the project root"
            }
        except json.JSONDecodeError as e:
            return {
                "error": "Invalid JSON in portfolio.json",
                "message": str(e)
            }

    def execute_trade(
        self,
        action: str,
        account_name: str,
        ticker: str,
        shares: float,
        price: float = None
    ) -> Dict[str, Any]:
        """
        Execute a trade using portfolio update tools.

        Args:
            action: "buy" or "sell"
            account_name: Name of investment account
            ticker: Stock ticker symbol
            shares: Number of shares
            price: Price per share (if None, will fetch current price)

        Returns:
            Dict with success status and details
        """
        try:
            # Import the tool
            from src.tools.portfolio_update_tools import update_investment_holding

            # Execute trade
            result = update_investment_holding.invoke({
                "account_name": account_name,
                "ticker": ticker,
                "shares": shares if action == "buy" else -shares,
                "transaction_type": action,
                "price_per_share": price
            })

            return {
                "success": True,
                "message": result,
                "action": action,
                "ticker": ticker,
                "shares": shares,
                "account": account_name
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to execute {action} trade"
            }


# Global agent service instance
agent_service = AgentService()
