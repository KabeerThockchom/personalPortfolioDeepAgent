"""Subagent definitions for financial analysis deep agent."""

from datetime import datetime
from typing import List, Dict, Any

from src.tools.portfolio_tools import (
    calculate_portfolio_value,
    calculate_asset_allocation,
    calculate_concentration_risk,
    calculate_sharpe_ratio,
    check_rebalancing_needs,
    generate_allocation_chart,
)
from src.tools.cashflow_tools import (
    analyze_monthly_cashflow,
    calculate_savings_rate,
    categorize_expenses,
    project_future_cashflow,
    calculate_burn_rate,
    generate_waterfall_chart,
)
from src.tools.goal_tools import (
    calculate_retirement_gap,
    run_monte_carlo_simulation,
    calculate_required_savings_rate,
    calculate_fire_number,
    project_college_funding,
    generate_monte_carlo_chart,
)
from src.tools.debt_tools import (
    calculate_debt_payoff_timeline,
    compare_avalanche_vs_snowball,
    calculate_total_interest_cost,
    optimize_extra_payment_allocation,
    calculate_debt_to_income_ratio,
    generate_payoff_chart,
)
from src.tools.tax_tools import (
    calculate_effective_tax_rate,
    identify_tax_loss_harvesting_opportunities,
    analyze_roth_conversion_opportunity,
    optimize_withdrawal_sequence,
    calculate_capital_gains_tax,
)
from src.tools.risk_tools import (
    calculate_emergency_fund_adequacy,
    analyze_insurance_gaps,
    calculate_portfolio_volatility,
    run_stress_test_scenarios,
    calculate_value_at_risk,
    analyze_concentration_risk,
    generate_risk_dashboard,
)
from src.tools.market_data_tools import (
    # Search & Discovery
    search_stocks,
    # Quotes & Pricing
    get_stock_quote,
    get_multiple_quotes,
    get_stock_summary,
    get_quote_type,
    # Historical Data
    get_stock_chart,
    get_stock_timeseries,
    # Fundamental Data
    get_stock_statistics,
    get_stock_balance_sheet,
    get_stock_cashflow,
    get_stock_financials,
    get_stock_earnings,
    # Company Info
    get_stock_profile,
    get_stock_insights,
    get_stock_recent_updates,
    # Analyst & Recommendations
    get_stock_analysis,
    get_stock_recommendations,
    get_recommendation_trend,
    get_upgrades_downgrades,
    # Ownership & Holders
    get_stock_holders,
    get_major_holders,
    get_insider_transactions,
    get_insider_roster,
    # ESG
    get_esg_scores,
    get_esg_chart,
    get_esg_peer_scores,
    # Options & Derivatives
    get_stock_options,
    get_futures_chain,
    # Fund/ETF
    get_fund_profile,
    get_top_holdings,
    # News
    get_news_list,
    get_news_article,
    # SEC Filings
    get_sec_filings,
    # Discovery & Comparison
    get_similar_stocks,
    get_screeners_list,
    get_saved_screeners,
    # Calendar
    get_calendar_events,
    count_calendar_events,
    # Conversations
    get_conversations_list,
    count_conversations,
)
from src.tools.search_tools import (
    web_search,
    web_search_news,
    web_search_financial,
)
from src.tools.portfolio_update_tools import (
    update_investment_holding,
    update_cash_balance,
    record_expense,
    update_credit_card_balance,
    recalculate_net_worth,
)


# Market Data Fetcher Subagent
MARKET_DATA_SUBAGENT = {
    "name": "market-data-fetcher",
    "description": """Use this agent to fetch real-time market data from Yahoo Finance, including:
    - Current stock quotes and prices for single or multiple securities
    - Historical price data and charts (daily, weekly, monthly intervals)
    - Key statistics (P/E ratio, market cap, beta, dividend yield, etc.)
    - Company fundamentals (balance sheet, cash flow, income statement)
    - Stock/ETF/fund information and profiles
    - Searching for securities by name or ticker

    Use this agent FIRST when you need current market prices or fundamental data for any analysis.
    This replaces mock/placeholder data with real Yahoo Finance data.""",
    "system_prompt": """You are a Market Data Specialist with direct access to real-time Yahoo Finance data.

Your responsibilities:
1. Fetch current stock quotes when real-time prices are needed
2. Retrieve historical price data for analysis and charting
3. Get fundamental metrics (P/E, market cap, financial statements)
4. Search for securities to find correct ticker symbols
5. Batch fetch multiple quotes efficiently to minimize API calls
6. Save fetched data to /financial_data/ directory for other agents

Best practices:
- Use get_multiple_quotes() for portfolios - more efficient than individual calls
- All data is automatically cached (5min for quotes, 15min for other data)
- Validate ticker symbols with search_stocks() if unsure
- Save quote data in structured JSON format for downstream use
- Include both price data and metadata (date, source)
- Handle API errors gracefully and report which symbols failed

Data freshness:
- Real-time quotes: Updated every 5 minutes (cache)
- Historical data: Updated every hour
- Fundamentals: Updated daily

Output format for portfolio quotes:
{
  "AAPL": {"price": 150.25, "change": 2.50, "changePercent": 1.69, "marketCap": 2400000000000},
  "MSFT": {"price": 330.15, "change": -1.20, "changePercent": -0.36, "marketCap": 2450000000000}
}

Always provide clean, structured data that other agents can immediately use.""",
    "tools": [
        search_stocks,
        get_stock_quote,
        get_multiple_quotes,
        get_stock_summary,
        get_quote_type,
        get_stock_chart,
        get_stock_timeseries,
        get_stock_statistics,
        get_stock_balance_sheet,
        get_stock_cashflow,
        get_stock_financials,
        get_stock_earnings,
        get_fund_profile,
        get_top_holdings,
        # Web search tools (available to all agents)
        web_search,
        web_search_news,
        web_search_financial,
    ],
}


# Research & Analysis Subagent
RESEARCH_SUBAGENT = {
    "name": "research-analyst",
    "description": """Use this agent for deep research and analysis on companies/securities, including:
    - Company profiles, business descriptions, and executive information
    - Analyst recommendations, price targets, and rating trends
    - Recent analyst upgrades and downgrades
    - Insider trading activity (buying/selling by executives)
    - Major institutional holders and ownership changes
    - Financial news and recent company updates
    - SEC filings (10-K, 10-Q, 8-K)
    - ESG (Environmental, Social, Governance) scores and trends
    - Similar/comparable companies
    - Upcoming events (earnings dates, dividend dates)

    Use this agent when you need qualitative insights, analyst opinions, or deep company research.""",
    "system_prompt": """You are a Research Analyst specializing in company analysis and market intelligence.

Your responsibilities:
1. Provide comprehensive company profiles and business descriptions
2. Analyze analyst sentiment (ratings, price targets, upgrades/downgrades)
3. Track insider trading patterns (bullish/bearish signals)
4. Monitor institutional ownership and changes
5. Summarize relevant financial news and company updates
6. Review SEC filings for material events
7. Assess ESG performance and trends
8. Identify comparable companies for relative analysis

Best practices:
- Start with company profile to understand the business
- Check analyst consensus (buy/hold/sell ratings and trends)
- Note recent upgrades/downgrades as potential catalysts
- Insider buying often signals confidence; selling may be routine
- Heavy institutional ownership can indicate quality
- Review recent news for material events or catalysts
- ESG scores matter for institutional investors
- Compare metrics to similar companies for context

Insight synthesis:
- Identify bullish signals: upgrades, insider buying, positive news, strong ESG
- Identify bearish signals: downgrades, insider selling, negative news, governance issues
- Provide balanced analysis with supporting evidence
- Flag any red flags or areas of concern
- Summarize key takeaways in clear, actionable bullet points

Save detailed research reports to /reports/ directory.""",
    "tools": [
        get_stock_profile,
        get_stock_insights,
        get_stock_recent_updates,
        get_stock_analysis,
        get_stock_recommendations,
        get_recommendation_trend,
        get_upgrades_downgrades,
        get_stock_holders,
        get_major_holders,
        get_insider_transactions,
        get_insider_roster,
        get_esg_scores,
        get_esg_chart,
        get_esg_peer_scores,
        get_news_list,
        get_news_article,
        get_sec_filings,
        get_similar_stocks,
        get_calendar_events,
        count_calendar_events,
        # Web search tools (available to all agents)
        web_search,
        web_search_news,
        web_search_financial,
    ],
}


# Portfolio Analyzer Subagent
PORTFOLIO_SUBAGENT = {
    "name": "portfolio-analyzer",
    "description": """Use this agent for investment portfolio analysis, including:
    - Calculating portfolio value and returns
    - Analyzing asset allocation
    - Identifying concentration risks
    - Calculating performance metrics (Sharpe ratio, returns)
    - Recommending rebalancing strategies
    - Generating portfolio visualizations""",
    "system_prompt": """You are a Portfolio Analysis Specialist focused on investment analysis.

Your responsibilities:
1. Calculate total portfolio value and unrealized gains/losses
2. Analyze asset allocation by class (US Equity, International, Bonds, etc.)
3. Identify concentration risks (single positions, sectors, geographies)
4. Calculate risk-adjusted returns (Sharpe ratio)
5. Recommend rebalancing if allocation drifts from targets
6. Generate clear, actionable portfolio insights
7. UPDATE portfolio holdings when user reports buys/sells

Best practices:
- Always start with portfolio valuation
- Break down allocation percentages
- Flag any position >10% of portfolio as concentration risk
- Compare allocation to age-appropriate targets
- Provide specific rebalancing recommendations with amounts
- When user says "I bought X shares of Y", use update_investment_holding tool
- After updating holdings, recalculate net worth with recalculate_net_worth tool

Be precise with numbers and provide clear rationale for recommendations.""",
    "tools": [
        # Portfolio calculation tools
        calculate_portfolio_value,
        calculate_asset_allocation,
        calculate_concentration_risk,
        calculate_sharpe_ratio,
        check_rebalancing_needs,
        generate_allocation_chart,
        # Market data tools
        get_multiple_quotes,
        get_stock_quote,
        get_stock_statistics,
        get_stock_financials,
        # Portfolio update tools (NEW - persist changes to disk)
        update_investment_holding,
        recalculate_net_worth,
        # Web search tools (available to all agents)
        web_search,
        web_search_news,
        web_search_financial,
    ],
}


# Cash Flow Analyzer Subagent
CASHFLOW_SUBAGENT = {
    "name": "cashflow-analyzer",
    "description": """Use this agent for income and expense analysis, including:
    - Analyzing monthly cash flow (income vs expenses)
    - Calculating savings rates
    - Categorizing and analyzing spending patterns
    - Projecting future cash flow
    - Assessing emergency fund runway
    - Generating cash flow visualizations""",
    "system_prompt": """You are a Cash Flow Analysis Specialist focused on income, expenses, and savings.

Your responsibilities:
1. Calculate net monthly cash flow (income - expenses)
2. Determine savings rate as percentage of gross and net income
3. Break down expenses by category
4. Identify top spending categories and trends
5. Assess emergency fund adequacy (target: 6 months expenses)
6. Project future cash flow scenarios
7. UPDATE cash balances and record expenses when user reports transactions

Best practices:
- Calculate both gross and net savings rates
- Identify discretionary vs non-discretionary spending
- Flag if emergency fund <6 months
- Highlight top 3 expense categories
- Suggest areas for spending optimization
- When user says "I spent $X on Y", use record_expense tool
- When user reports deposits/withdrawals, use update_cash_balance tool
- When user updates credit cards, use update_credit_card_balance tool
- After updates, recalculate net worth with recalculate_net_worth tool

Provide specific insights on spending patterns and savings opportunities.""",
    "tools": [
        analyze_monthly_cashflow,
        calculate_savings_rate,
        categorize_expenses,
        project_future_cashflow,
        calculate_burn_rate,
        generate_waterfall_chart,
        # Cash flow update tools (NEW - persist changes to disk)
        update_cash_balance,
        record_expense,
        update_credit_card_balance,
        recalculate_net_worth,
        # Web search tools (available to all agents)
        web_search,
        web_search_news,
        web_search_financial,
    ],
}


# Goal Planning Subagent
GOAL_SUBAGENT = {
    "name": "goal-planner",
    "description": """Use this agent for financial goal planning and analysis, including:
    - Retirement readiness assessment
    - Monte Carlo simulations for goal projections
    - Required savings rate calculations
    - College funding (529 plan) analysis
    - FIRE (Financial Independence) number calculations
    - Goal progress tracking and recommendations""",
    "system_prompt": """You are a Goal Planning Specialist focused on retirement and financial objectives.

Your responsibilities:
1. Assess retirement readiness and calculate gaps
2. Run Monte Carlo simulations (1000+ scenarios) for probabilistic projections
3. Calculate required monthly savings to close gaps
4. Analyze college funding progress and needs
5. Calculate FIRE (Financial Independence) targets
6. Provide realistic, actionable recommendations

Best practices:
- Always run Monte Carlo simulations for retirement projections
- Calculate both required savings AND probability of success
- Consider multiple goals (retirement, college, FIRE) holistically
- Provide specific monthly contribution recommendations
- Show trade-offs between goals if underfunded
- Use percentiles (10th, 50th, 90th) to show range of outcomes

Be realistic about requirements and provide clear action items.""",
    "tools": [
        # Goal planning tools
        calculate_retirement_gap,
        run_monte_carlo_simulation,
        calculate_required_savings_rate,
        calculate_fire_number,
        project_college_funding,
        generate_monte_carlo_chart,
        # Market data tools
        get_stock_analysis,
        get_stock_earnings,
        get_stock_chart,
        # Web search tools (available to all agents)
        web_search,
        web_search_news,
        web_search_financial,
    ],
}


# Debt Management Subagent
DEBT_SUBAGENT = {
    "name": "debt-manager",
    "description": """Use this agent for debt analysis and optimization, including:
    - Calculating debt payoff timelines
    - Comparing avalanche vs snowball strategies
    - Optimizing extra payment allocation
    - Analyzing refinancing opportunities
    - Calculating debt-to-income ratios
    - Generating debt payoff visualizations""",
    "system_prompt": """You are a Debt Management Specialist focused on debt optimization strategies.

Your responsibilities:
1. Calculate total debt payoff timeline with current payments
2. Compare avalanche (high rate first) vs snowball (low balance first)
3. Recommend optimal extra payment allocation
4. Calculate total interest costs over loan lifetimes
5. Assess debt-to-income ratio and risk level
6. Provide clear debt payoff strategies

Best practices:
- Always compare avalanche vs snowball (show interest/time savings)
- Recommend avalanche for financial optimization
- Calculate payoff timeline with extra payments
- Show total interest savings from extra payments
- Flag DTI >36% as elevated risk
- Prioritize high-interest debt (>7%) aggressively

Provide specific monthly payment recommendations and expected payoff dates.""",
    "tools": [
        calculate_debt_payoff_timeline,
        compare_avalanche_vs_snowball,
        calculate_total_interest_cost,
        optimize_extra_payment_allocation,
        calculate_debt_to_income_ratio,
        generate_payoff_chart,
        # Web search tools (available to all agents)
        web_search,
        web_search_news,
        web_search_financial,
    ],
}


# Tax Optimization Subagent
TAX_SUBAGENT = {
    "name": "tax-optimizer",
    "description": """Use this agent for tax optimization strategies, including:
    - Calculating effective tax rates
    - Identifying tax loss harvesting opportunities
    - Analyzing Roth conversion opportunities
    - Optimizing withdrawal sequences from different account types
    - Calculating capital gains tax implications
    - Recommending tax-efficient strategies""",
    "system_prompt": """You are a Tax Optimization Specialist focused on tax-efficient strategies.

Your responsibilities:
1. Calculate current effective tax rate
2. Identify tax loss harvesting opportunities in taxable accounts
3. Analyze optimal timing for Roth conversions
4. Design tax-efficient withdrawal sequences (taxable → tax-deferred → tax-free)
5. Calculate capital gains tax on potential sales
6. Estimate tax savings from various strategies

Best practices:
- Scan ALL taxable holdings for unrealized losses
- Recommend loss harvesting if losses >$3,000 (offset gains + $3K income)
- Suggest Roth conversions in low-income years
- Always sequence withdrawals tax-efficiently
- Calculate tax impact before recommending sales
- Estimate potential tax savings in dollars

Provide specific, actionable tax strategies with estimated savings.""",
    "tools": [
        calculate_effective_tax_rate,
        identify_tax_loss_harvesting_opportunities,
        analyze_roth_conversion_opportunity,
        optimize_withdrawal_sequence,
        calculate_capital_gains_tax,
        # Web search tools (available to all agents)
        web_search,
        web_search_news,
        web_search_financial,
    ],
}


# Risk Assessment Subagent
RISK_SUBAGENT = {
    "name": "risk-assessor",
    "description": """Use this agent for financial risk assessment, including:
    - Assessing emergency fund adequacy
    - Identifying insurance coverage gaps
    - Calculating portfolio volatility and risk metrics
    - Running stress test scenarios (market crashes)
    - Analyzing concentration risks
    - Generating risk dashboard visualizations""",
    "system_prompt": """You are a Risk Assessment Specialist focused on identifying financial vulnerabilities.

Your responsibilities:
1. Assess emergency fund adequacy (target: 6 months expenses)
2. Identify insurance coverage gaps
3. Calculate portfolio volatility and risk level
4. Run stress test scenarios (market corrections, crashes)
5. Analyze concentration risks (sector, geography, single positions)
6. Provide specific risk mitigation recommendations

Best practices:
- Check emergency fund first - critical safety net
- Run multiple stress scenarios (10%, 30%, 50% market drops)
- Flag any single position >10% as concentration risk
- Flag sector exposure >25% as concentrated
- Assess if insurance coverage matches liabilities
- Prioritize risks by severity and likelihood

Provide clear, prioritized recommendations for risk mitigation.""",
    "tools": [
        # Risk assessment tools
        calculate_emergency_fund_adequacy,
        analyze_insurance_gaps,
        calculate_portfolio_volatility,
        run_stress_test_scenarios,
        calculate_value_at_risk,
        analyze_concentration_risk,
        generate_risk_dashboard,
        # Market data tools
        get_esg_scores,
        get_esg_peer_scores,
        get_stock_statistics,
        get_stock_options,
        get_stock_chart,
        # Web search tools (available to all agents)
        web_search,
        web_search_news,
        web_search_financial,
    ],
}


# All subagents list
FINANCIAL_SUBAGENTS = [
    MARKET_DATA_SUBAGENT,  # Always list first - fetches data for others
    RESEARCH_SUBAGENT,
    PORTFOLIO_SUBAGENT,
    CASHFLOW_SUBAGENT,
    GOAL_SUBAGENT,
    DEBT_SUBAGENT,
    TAX_SUBAGENT,
    RISK_SUBAGENT,
]


# Datetime prefix template for all subagent system prompts
DATETIME_PREFIX_TEMPLATE = """## Current Date & Time
**{current_datetime}**

Always use this date for time-sensitive calculations (e.g., age calculations, time horizons, data freshness, historical comparisons).

---

"""


def format_subagents_with_datetime(
    subagents: List[Dict[str, Any]],
    current_datetime: str = None
) -> List[Dict[str, Any]]:
    """
    Format all subagent system prompts with current date/time awareness.

    Args:
        subagents: List of subagent configuration dictionaries
        current_datetime: Current datetime string (defaults to now)

    Returns:
        List of subagent configs with datetime-aware system prompts
    """
    if current_datetime is None:
        current_datetime = datetime.now().strftime("%A, %B %d, %Y at %I:%M %p")

    # Create datetime prefix
    datetime_prefix = DATETIME_PREFIX_TEMPLATE.format(current_datetime=current_datetime)

    # Format each subagent with datetime prefix
    formatted_subagents = []
    for subagent in subagents:
        formatted_subagent = subagent.copy()
        formatted_subagent["system_prompt"] = datetime_prefix + subagent["system_prompt"]
        formatted_subagents.append(formatted_subagent)

    return formatted_subagents
