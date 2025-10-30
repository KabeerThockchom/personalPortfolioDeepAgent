"""Debt Management Agent."""

from langchain_core.messages import HumanMessage, AIMessage
from langchain_anthropic import ChatAnthropic
from langgraph.prebuilt import create_react_agent

from ..tools.debt_tools import (
    calculate_debt_payoff_timeline,
    compare_avalanche_vs_snowball,
    calculate_total_interest_cost,
    optimize_extra_payment_allocation,
    calculate_debt_to_income_ratio,
    generate_payoff_chart
)


def create_debt_agent(llm: ChatAnthropic):
    """Create the debt management agent."""

    tools = [
        calculate_debt_payoff_timeline,
        compare_avalanche_vs_snowball,
        calculate_total_interest_cost,
        optimize_extra_payment_allocation,
        calculate_debt_to_income_ratio,
        generate_payoff_chart
    ]

    system_message = """You are a Debt Management Agent specializing in debt optimization strategies.

Your responsibilities:
- Analyze debt payoff timelines
- Compare avalanche vs snowball strategies
- Calculate total interest costs
- Optimize extra payment allocation
- Assess debt-to-income ratios
- Generate debt visualizations

When analyzing:
1. Calculate current debt-to-income ratio
2. Analyze total interest costs at current payment rates
3. Compare avalanche (high rate first) vs snowball (low balance first)
4. Recommend optimal extra payment strategy
5. Calculate time and interest savings
6. Generate payoff timeline visualizations

Provide specific, actionable debt payoff strategies."""

    agent = create_react_agent(
        llm,
        tools,
        prompt=system_message
    )

    return agent


def debt_agent_node(state, config):
    """Debt management agent node for the graph."""
    from langchain_anthropic import ChatAnthropic

    llm = ChatAnthropic(model="claude-4.5 Haiku-4-5", temperature=0)
    agent = create_debt_agent(llm)

    portfolio = state.get("client_portfolio", {})
    liabilities = portfolio.get("liabilities", {})

    last_message = state["messages"][-1].content
    focused_message = f"""Analyze the client's debt and recommend payoff strategies.

Client question: {last_message}

Available data:
- Debts: {list(liabilities.keys())}
- Monthly cash flow data available

Provide comprehensive debt analysis and optimization strategies."""

    result = agent.invoke({
        "messages": [HumanMessage(content=focused_message)]
    })

    return {
        "messages": [AIMessage(content=result["messages"][-1].content)],
        "debt_analysis": {"agent_response": result["messages"][-1].content},
        "agents_consulted": state.get("agents_consulted", []) + ["debt"]
    }
