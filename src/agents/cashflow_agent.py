"""Cash Flow Analyzer Agent."""

from langchain_core.messages import HumanMessage, AIMessage
from langchain_anthropic import ChatAnthropic
from langgraph.prebuilt import create_react_agent

from ..tools.cashflow_tools import (
    analyze_monthly_cashflow,
    calculate_savings_rate,
    categorize_expenses,
    project_future_cashflow,
    calculate_burn_rate,
    generate_waterfall_chart
)


def create_cashflow_agent(llm: ChatAnthropic):
    """Create the cash flow analyzer agent."""

    tools = [
        analyze_monthly_cashflow,
        calculate_savings_rate,
        categorize_expenses,
        project_future_cashflow,
        calculate_burn_rate,
        generate_waterfall_chart
    ]

    system_message = """You are a Cash Flow Analyzer Agent specializing in income and expense analysis.

Your responsibilities:
- Analyze monthly cash flow (income vs expenses)
- Calculate savings rate
- Identify spending patterns and top expense categories
- Project future cash flow scenarios
- Calculate emergency fund runway
- Generate cash flow visualizations

When analyzing:
1. Calculate net monthly cash flow
2. Determine savings rate (as % of gross and net income)
3. Break down expenses by category
4. Identify top spending categories
5. Assess emergency fund adequacy
6. Generate waterfall or other relevant charts

Provide specific insights on spending patterns and savings opportunities."""

    agent = create_react_agent(
        llm,
        tools,
        prompt=system_message
    )

    return agent


def cashflow_agent_node(state, config):
    """Cash flow agent node for the graph."""
    from langchain_anthropic import ChatAnthropic

    llm = ChatAnthropic(model="claude-4.5 Haiku-4-5", temperature=0)
    agent = create_cashflow_agent(llm)

    # Extract cash flow data from state
    portfolio = state.get("client_portfolio", {})
    cashflow = portfolio.get("monthly_cash_flow", {})

    last_message = state["messages"][-1].content
    focused_message = f"""Analyze the client's cash flow and spending patterns.

Client question: {last_message}

Available data:
- Income sources: {list(cashflow.get('income', {}).keys())}
- Expense categories: {list(cashflow.get('expenses', {}).keys())}
- Taxes and deductions available

Provide a comprehensive cash flow analysis."""

    result = agent.invoke({
        "messages": [HumanMessage(content=focused_message)]
    })

    return {
        "messages": [AIMessage(content=result["messages"][-1].content)],
        "cashflow_analysis": {"agent_response": result["messages"][-1].content},
        "agents_consulted": state.get("agents_consulted", []) + ["cashflow"]
    }
