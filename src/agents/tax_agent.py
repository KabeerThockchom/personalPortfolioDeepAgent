"""Tax Optimization Agent."""

from langchain_core.messages import HumanMessage, AIMessage
from langchain_anthropic import ChatAnthropic
from langgraph.prebuilt import create_react_agent

from ..tools.tax_tools import (
    calculate_effective_tax_rate,
    identify_tax_loss_harvesting_opportunities,
    analyze_roth_conversion_opportunity,
    optimize_withdrawal_sequence,
    calculate_capital_gains_tax
)


def create_tax_agent(llm: ChatAnthropic):
    """Create the tax optimization agent."""

    tools = [
        calculate_effective_tax_rate,
        identify_tax_loss_harvesting_opportunities,
        analyze_roth_conversion_opportunity,
        optimize_withdrawal_sequence,
        calculate_capital_gains_tax
    ]

    system_message = """You are a Tax Optimization Agent specializing in tax-efficient strategies.

Your responsibilities:
- Calculate effective tax rates
- Identify tax loss harvesting opportunities
- Analyze Roth conversion opportunities
- Optimize withdrawal sequences from different account types
- Calculate capital gains tax implications
- Recommend tax-efficient strategies

When analyzing:
1. Calculate current effective tax rate
2. Scan for tax loss harvesting opportunities
3. Evaluate Roth conversion timing
4. Design tax-efficient withdrawal strategies
5. Consider capital gains implications
6. Estimate tax savings from strategies

Provide specific tax optimization recommendations with estimated savings."""

    agent = create_react_agent(
        llm,
        tools,
        prompt=system_message
    )

    return agent


def tax_agent_node(state, config):
    """Tax optimization agent node for the graph."""
    from langchain_anthropic import ChatAnthropic

    llm = ChatAnthropic(model="claude-haiku-4-5", temperature=0)
    agent = create_tax_agent(llm)

    portfolio = state.get("client_portfolio", {})
    tax_situation = portfolio.get("tax_situation", {})

    last_message = state["messages"][-1].content
    focused_message = f"""Analyze tax optimization opportunities for the client.

Client question: {last_message}

Available data:
- Tax filing status: {tax_situation.get('filing_status')}
- Marginal tax bracket: {tax_situation.get('marginal_tax_bracket_federal')}
- Investment accounts with cost basis data
- Current prices available for loss harvesting

Provide comprehensive tax optimization strategies."""

    result = agent.invoke({
        "messages": [HumanMessage(content=focused_message)]
    })

    return {
        "messages": [AIMessage(content=result["messages"][-1].content)],
        "tax_analysis": {"agent_response": result["messages"][-1].content},
        "agents_consulted": state.get("agents_consulted", []) + ["tax"]
    }
