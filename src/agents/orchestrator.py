"""Orchestrator Agent - Routes queries to specialized agents."""

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_anthropic import ChatAnthropic
from typing import Literal


def orchestrator_node(state, config):
    """
    Orchestrator agent that analyzes the user query and decides which specialized agent(s) to route to.
    """
    llm = ChatAnthropic(model="claude-haiku-4-5", temperature=0)

    last_message = state["messages"][-1].content
    agents_consulted = state.get("agents_consulted", [])

    routing_prompt = f"""You are a Financial Analysis Orchestrator. Analyze the user's question and decide which specialized agent(s) should handle it.

Available agents:
1. **portfolio** - Investment analysis, asset allocation, returns, rebalancing, concentration risk
2. **cashflow** - Income/expense analysis, savings rate, spending patterns, budget analysis
3. **goal** - Retirement planning, college funding, FIRE goals, Monte Carlo simulations
4. **debt** - Debt payoff strategies, avalanche vs snowball, interest optimization
5. **tax** - Tax optimization, loss harvesting, Roth conversions, withdrawal strategies
6. **risk** - Emergency fund, insurance gaps, portfolio volatility, stress tests, concentration risk

User question: {last_message}

Agents already consulted: {agents_consulted if agents_consulted else "None"}

Analyze the question and respond with ONLY ONE of these exact keywords:
- portfolio
- cashflow
- goal
- debt
- tax
- risk
- synthesize (if enough agents have been consulted and you're ready to provide final answer)

Rules:
- Choose the MOST relevant single agent for this query
- If the query spans multiple domains, start with the primary domain
- If 2+ agents have already been consulted, consider using "synthesize"
- Return ONLY the keyword, nothing else"""

    response = llm.invoke([
        HumanMessage(content=routing_prompt)
    ])

    next_agent = response.content.strip().lower()

    # Validate the response
    valid_agents = ["portfolio", "cashflow", "goal", "debt", "tax", "risk", "synthesize"]
    if next_agent not in valid_agents:
        # Default to synthesize if invalid
        next_agent = "synthesize"

    return {
        "next_agent": next_agent,
        "messages": [AIMessage(content=f"Routing to {next_agent} agent...")]
    }


def synthesizer_node(state, config):
    """
    Synthesizer node that aggregates insights from consulted agents and provides final response.
    """
    llm = ChatAnthropic(model="claude-haiku-4-5", temperature=0)

    user_question = state["messages"][0].content  # Original question
    agents_consulted = state.get("agents_consulted", [])

    # Gather all agent responses
    analyses = []
    if "portfolio" in agents_consulted and state.get("portfolio_analysis"):
        analyses.append(f"**Portfolio Analysis:**\n{state['portfolio_analysis'].get('agent_response', '')}")

    if "cashflow" in agents_consulted and state.get("cashflow_analysis"):
        analyses.append(f"**Cash Flow Analysis:**\n{state['cashflow_analysis'].get('agent_response', '')}")

    if "goal" in agents_consulted and state.get("goal_analysis"):
        analyses.append(f"**Goal Planning Analysis:**\n{state['goal_analysis'].get('agent_response', '')}")

    if "debt" in agents_consulted and state.get("debt_analysis"):
        analyses.append(f"**Debt Management Analysis:**\n{state['debt_analysis'].get('agent_response', '')}")

    if "tax" in agents_consulted and state.get("tax_analysis"):
        analyses.append(f"**Tax Optimization Analysis:**\n{state['tax_analysis'].get('agent_response', '')}")

    if "risk" in agents_consulted and state.get("risk_analysis"):
        analyses.append(f"**Risk Assessment:**\n{state['risk_analysis'].get('agent_response', '')}")

    combined_analyses = "\n\n".join(analyses)

    synthesis_prompt = f"""You are a Financial Advisor synthesizing insights from specialized agents.

Original user question: {user_question}

Agent analyses:
{combined_analyses}

Your task:
1. Provide a clear, comprehensive answer to the user's original question
2. Synthesize insights from all agents consulted
3. Highlight key findings and numbers
4. Provide 2-3 specific, actionable recommendations
5. Keep the response concise but complete (aim for 200-300 words)

Do NOT simply repeat what the agents said - synthesize and add value."""

    response = llm.invoke([
        HumanMessage(content=synthesis_prompt)
    ])

    return {
        "messages": [AIMessage(content=response.content)],
        "ready_to_respond": True
    }


def route_to_agent(state) -> Literal["portfolio", "cashflow", "goal", "debt", "tax", "risk", "synthesize", "end"]:
    """
    Conditional edge function that routes to the appropriate agent based on orchestrator decision.
    """
    next_agent = state.get("next_agent", "synthesize")

    if state.get("ready_to_respond", False):
        return "end"

    return next_agent
