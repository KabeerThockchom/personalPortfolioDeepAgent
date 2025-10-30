"""Risk Assessment Agent."""

from langchain_core.messages import HumanMessage, AIMessage
from langchain_anthropic import ChatAnthropic
from langgraph.prebuilt import create_react_agent

from ..tools.risk_tools import (
    calculate_emergency_fund_adequacy,
    analyze_insurance_gaps,
    calculate_portfolio_volatility,
    run_stress_test_scenarios,
    calculate_value_at_risk,
    analyze_concentration_risk,
    generate_risk_dashboard
)


def create_risk_agent(llm: ChatAnthropic):
    """Create the risk assessment agent."""

    tools = [
        calculate_emergency_fund_adequacy,
        analyze_insurance_gaps,
        calculate_portfolio_volatility,
        run_stress_test_scenarios,
        calculate_value_at_risk,
        analyze_concentration_risk,
        generate_risk_dashboard
    ]

    system_message = """You are a Risk Assessment Agent specializing in financial risk analysis.

Your responsibilities:
- Assess emergency fund adequacy
- Identify insurance coverage gaps
- Calculate portfolio volatility and risk metrics
- Run stress test scenarios (market crashes)
- Calculate Value at Risk (VaR)
- Analyze concentration risks (sector, geography, single positions)
- Generate risk dashboard visualizations

When analyzing:
1. Check emergency fund adequacy (target: 6 months expenses)
2. Review insurance coverage gaps
3. Calculate portfolio volatility and risk level
4. Run stress test scenarios (mild correction, bear market, severe crash)
5. Identify concentration risks
6. Provide specific risk mitigation recommendations

Be clear about potential vulnerabilities and prioritize recommendations."""

    agent = create_react_agent(
        llm,
        tools,
        prompt=system_message
    )

    return agent


def risk_agent_node(state, config):
    """Risk assessment agent node for the graph."""
    from langchain_anthropic import ChatAnthropic

    llm = ChatAnthropic(model="claude-4.5 Haiku-4-5", temperature=0)
    agent = create_risk_agent(llm)

    portfolio = state.get("client_portfolio", {})
    risk_factors = portfolio.get("risk_factors", {})

    last_message = state["messages"][-1].content
    focused_message = f"""Assess the client's financial risks and vulnerabilities.

Client question: {last_message}

Available data:
- Current risk factors noted: {list(risk_factors.keys())}
- Emergency fund, insurance coverage data available
- Portfolio holdings for concentration analysis

Provide comprehensive risk assessment with mitigation strategies."""

    result = agent.invoke({
        "messages": [HumanMessage(content=focused_message)]
    })

    return {
        "messages": [AIMessage(content=result["messages"][-1].content)],
        "risk_analysis": {"agent_response": result["messages"][-1].content},
        "agents_consulted": state.get("agents_consulted", []) + ["risk"]
    }
