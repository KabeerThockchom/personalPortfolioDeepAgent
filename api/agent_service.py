"""
Agent service for executing financial agent with streaming support.
"""
import json
import time
from typing import AsyncIterator, Dict, Any, List
from langchain_core.messages import HumanMessage
from langgraph.types import Command

from src.deep_agent import create_finance_deep_agent
from api.event_parser import EventParser
from api.models import AgentEvent
from api.session_manager import Session


class AgentService:
    """Service for managing agent execution."""

    def __init__(self):
        self.agent = None
        self.parser_instances = {}  # Store parser instances per session
        self._initialize_agent()

    def _initialize_agent(self):
        """Initialize the finance deep agent."""
        try:
            self.agent = create_finance_deep_agent()
        except Exception as e:
            print(f"Error initializing agent: {e}")
            raise

    async def stream_response(
        self,
        session: Session,
        user_message: str = None,
        is_resume: bool = False,
        decisions: List[Dict] = None
    ) -> AsyncIterator[AgentEvent]:
        """
        Stream agent response as events (async).

        Args:
            session: Chat session with conversation history
            user_message: User's message (not used if is_resume=True)
            is_resume: Whether this is resuming from an interrupt
            decisions: User decisions for interrupted tools (if is_resume=True)

        Yields:
            AgentEvent objects
        """
        if not is_resume:
            # Add user message to session
            session.add_message(HumanMessage(content=user_message))

            # Prune conversation history (keep last 5 turns)
            session.prune_history(max_turns=5)

        # Get current state and config
        state = session.get_state() if not is_resume else Command(resume={"decisions": decisions or []})
        config = session.get_config()

        # Get or create parser instance for this session
        parser = self.parser_instances.get(session.session_id)
        if not parser:
            parser = EventParser()
            self.parser_instances[session.session_id] = parser

        try:
            # Use async streaming with config for checkpointing support
            async for chunk in self.agent.astream(state, config=config, stream_mode="updates"):
                # Check each state update for interrupts
                for node_name, state_update in chunk.items():
                    # Detect interrupts
                    if state_update and isinstance(state_update, dict) and "__interrupt__" in state_update:
                        # Store interrupts in session
                        interrupts = state_update["__interrupt__"]
                        if isinstance(interrupts, list):
                            session.pending_interrupts.extend(interrupts)
                        else:
                            session.pending_interrupts.append(interrupts)

                        # Yield approval request event
                        from api.models import ApprovalRequestEvent
                        yield ApprovalRequestEvent(
                            action_requests=self._extract_action_requests(session.pending_interrupts),
                            timestamp=time.time()
                        )
                        # Stop streaming - wait for user decisions
                        return

                # Parse chunk into events using session-specific parser
                events = parser.parse_chunk(chunk)
                for event in events:
                    yield event
            
            # Emit final events after stream completes
            final_events = parser.finalize()
            for event in final_events:
                yield event
            # Reset parser for next request
            parser = EventParser()
            self.parser_instances[session.session_id] = parser

        except Exception as e:
            # Yield error event
            from api.models import ErrorEvent
            yield ErrorEvent(
                error=str(e),
                details="Error during agent execution",
                timestamp=time.time()
            )

    def _extract_action_requests(self, interrupts: List) -> List[Dict]:
        """Extract action requests from interrupt objects."""
        all_action_requests = []
        for interrupt in interrupts:
            if hasattr(interrupt, 'value') and isinstance(interrupt.value, dict):
                interrupt_data = interrupt.value
            elif isinstance(interrupt, dict):
                interrupt_data = interrupt
            else:
                continue

            action_requests = interrupt_data.get("action_requests", [])
            review_configs = interrupt_data.get("review_configs", [])

            # Enrich action requests with review configs
            for action_request in action_requests:
                tool_name = action_request.get("name", "unknown")
                # Find matching review config
                review_config = next(
                    (cfg for cfg in review_configs if cfg.get("action_name") == tool_name),
                    {"allowed_decisions": ["approve", "reject"]}
                )
                action_request["allowed_decisions"] = review_config.get("allowed_decisions", ["approve", "reject"])
                all_action_requests.append(action_request)

        return all_action_requests

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
