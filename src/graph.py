"""Main LangGraph workflow for financial analysis multi-agent system."""

from langgraph.graph import StateGraph, END
from .state import FinancialAnalysisState
from .agents.orchestrator import orchestrator_node, synthesizer_node, route_to_agent
from .agents.portfolio_agent import portfolio_agent_node
from .agents.cashflow_agent import cashflow_agent_node
from .agents.goal_agent import goal_agent_node
from .agents.debt_agent import debt_agent_node
from .agents.tax_agent import tax_agent_node
from .agents.risk_agent import risk_agent_node


def create_financial_analysis_graph():
    """Create the financial analysis multi-agent graph."""

    # Create the graph
    workflow = StateGraph(FinancialAnalysisState)

    # Add nodes
    workflow.add_node("orchestrator", orchestrator_node)
    workflow.add_node("portfolio", portfolio_agent_node)
    workflow.add_node("cashflow", cashflow_agent_node)
    workflow.add_node("goal", goal_agent_node)
    workflow.add_node("debt", debt_agent_node)
    workflow.add_node("tax", tax_agent_node)
    workflow.add_node("risk", risk_agent_node)
    workflow.add_node("synthesize", synthesizer_node)

    # Set entry point
    workflow.set_entry_point("orchestrator")

    # Add conditional edges from orchestrator to specialized agents
    workflow.add_conditional_edges(
        "orchestrator",
        route_to_agent,
        {
            "portfolio": "portfolio",
            "cashflow": "cashflow",
            "goal": "goal",
            "debt": "debt",
            "tax": "tax",
            "risk": "risk",
            "synthesize": "synthesize",
            "end": END
        }
    )

    # After each specialized agent, go back to orchestrator for next routing decision
    workflow.add_edge("portfolio", "orchestrator")
    workflow.add_edge("cashflow", "orchestrator")
    workflow.add_edge("goal", "orchestrator")
    workflow.add_edge("debt", "orchestrator")
    workflow.add_edge("tax", "orchestrator")
    workflow.add_edge("risk", "orchestrator")

    # Synthesizer ends the workflow
    workflow.add_edge("synthesize", END)

    # Compile the graph
    app = workflow.compile()

    return app


def visualize_graph():
    """Generate a visual representation of the graph."""
    app = create_financial_analysis_graph()

    try:
        from IPython.display import Image, display
        display(Image(app.get_graph().draw_mermaid_png()))
    except Exception as e:
        print(f"Could not visualize graph: {e}")
        print("Graph created successfully but visualization requires IPython and graphviz")


if __name__ == "__main__":
    # Create and visualize the graph
    app = create_financial_analysis_graph()
    print("Financial Analysis Graph created successfully!")
    print("\nGraph structure:")
    print("- Entry: orchestrator")
    print("- Nodes: orchestrator, portfolio, cashflow, goal, debt, tax, risk, synthesize")
    print("- Flow: orchestrator → agent → orchestrator (loop) → synthesize → END")
