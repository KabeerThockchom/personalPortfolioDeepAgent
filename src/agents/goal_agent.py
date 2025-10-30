"""Goal Planning Agent."""

from langchain_core.messages import HumanMessage, AIMessage
from langchain_anthropic import ChatAnthropic
from langgraph.prebuilt import create_react_agent

from ..tools.goal_tools import (
    calculate_retirement_gap,
    run_monte_carlo_simulation,
    calculate_required_savings_rate,
    calculate_fire_number,
    project_college_funding,
    generate_monte_carlo_chart
)


def create_goal_agent(llm: ChatAnthropic):
    """Create the goal planning agent."""

    tools = [
        calculate_retirement_gap,
        run_monte_carlo_simulation,
        calculate_required_savings_rate,
        calculate_fire_number,
        project_college_funding,
        generate_monte_carlo_chart
    ]

    system_message = """You are a Goal Planning Agent specializing in retirement and financial goal analysis.

Your responsibilities:
- Assess retirement readiness and calculate gaps
- Run Monte Carlo simulations for goal projections
- Calculate required savings rates for goals
- Analyze college funding progress (529 plans)
- Calculate FIRE (Financial Independence) numbers
- Generate goal projection visualizations

When analyzing:
1. Assess current savings vs goal targets
2. Run Monte Carlo simulations for probabilistic outcomes
3. Calculate required monthly contributions
4. Provide specific recommendations to close gaps
5. Consider multiple goals (retirement, college, FIRE)
6. Generate fan charts or progress visualizations

Provide realistic assessments with actionable steps."""

    agent = create_react_agent(
        llm,
        tools,
        prompt=system_message
    )

    return agent


def goal_agent_node(state, config):
    """Goal planning agent node for the graph."""
    from langchain_anthropic import ChatAnthropic

    llm = ChatAnthropic(model="claude-4.5 Haiku-4-5", temperature=0)
    agent = create_goal_agent(llm)

    # Extract goal data from state
    portfolio = state.get("client_portfolio", {})
    goals = portfolio.get("financial_goals", {})

    last_message = state["messages"][-1].content
    focused_message = f"""Analyze the client's financial goals and readiness.

Client question: {last_message}

Available data:
- Financial goals: {list(goals.keys())}
- Current client age: {portfolio.get('client', {}).get('age')}
- Investment accounts: {list(portfolio.get('investment_accounts', {}).keys())}

Provide a comprehensive goal analysis with Monte Carlo projections where relevant."""

    result = agent.invoke({
        "messages": [HumanMessage(content=focused_message)]
    })

    return {
        "messages": [AIMessage(content=result["messages"][-1].content)],
        "goal_analysis": {"agent_response": result["messages"][-1].content},
        "agents_consulted": state.get("agents_consulted", []) + ["goal"]
    }
