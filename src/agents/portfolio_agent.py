"""Portfolio Analyzer Agent."""

from langchain_core.messages import HumanMessage, AIMessage
from langchain_anthropic import ChatAnthropic
from langgraph.prebuilt import create_react_agent

from ..tools.portfolio_tools import (
    calculate_portfolio_value,
    calculate_asset_allocation,
    calculate_concentration_risk,
    calculate_sharpe_ratio,
    check_rebalancing_needs,
    generate_allocation_chart
)


def create_portfolio_agent(llm: ChatAnthropic):
    """Create the portfolio analyzer agent."""

    tools = [
        calculate_portfolio_value,
        calculate_asset_allocation,
        calculate_concentration_risk,
        calculate_sharpe_ratio,
        check_rebalancing_needs,
        generate_allocation_chart
    ]

    system_message = """You are a Portfolio Analyzer Agent specializing in investment analysis.

Your responsibilities:
- Analyze portfolio composition and asset allocation
- Calculate performance metrics (returns, Sharpe ratio, volatility)
- Identify concentration risks
- Recommend rebalancing strategies
- Generate portfolio visualizations

When analyzing:
1. Start with overall portfolio value and returns
2. Break down asset allocation
3. Identify any concentration risks
4. Check if rebalancing is needed
5. Generate relevant charts

Be specific with numbers and provide clear recommendations."""

    agent = create_react_agent(
        llm,
        tools,
        prompt=system_message
    )

    return agent


def portfolio_agent_node(state, config):
    """Portfolio agent node for the graph."""
    from langchain_anthropic import ChatAnthropic

    llm = ChatAnthropic(model="claude-4.5 Haiku-4-5", temperature=0)
    agent = create_portfolio_agent(llm)

    # Extract portfolio data and current prices from state
    portfolio = state.get("client_portfolio", {})
    current_prices = state.get("current_prices", {})

    # Create a focused message for the portfolio agent
    last_message = state["messages"][-1].content
    focused_message = f"""Analyze the client's investment portfolio.

Client question: {last_message}

Available data:
- Portfolio accounts: {list(portfolio.get('investment_accounts', {}).keys())}
- Current prices available: {len(current_prices)} securities

Provide a comprehensive portfolio analysis."""

    result = agent.invoke({
        "messages": [HumanMessage(content=focused_message)]
    })

    # Update state with analysis
    return {
        "messages": [AIMessage(content=result["messages"][-1].content)],
        "portfolio_analysis": {"agent_response": result["messages"][-1].content},
        "agents_consulted": state.get("agents_consulted", []) + ["portfolio"]
    }
