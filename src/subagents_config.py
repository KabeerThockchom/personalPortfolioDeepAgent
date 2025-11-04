"""Subagent definitions for financial analysis deep agent."""

from datetime import datetime
from typing import List, Dict, Any, Optional


# ============================================================================
# SUBAGENT MODEL CONFIGURATION
# ============================================================================
# Configure which model each subagent uses via local Ollama Z.ai API
# All models run locally at http://localhost:11434/v1/
#
# Available Z.ai models:
# - glm-4.6:cloud - Main model (balanced performance)
# - minimax-m2:cloud - Fast model for simple tasks
# - kimi-k2:1t-cloud - Alternative fast model
# ============================================================================

# Z.ai API configuration (local Ollama)
OLLAMA_API_KEY = "6ddb812c07914107ba7c0e504fdcf9f1.gkld5OFtD8NRbDZvMiYtHG6P"
OLLAMA_BASE_URL = "http://localhost:11434/v1/"

# Model tier configuration
# kimi-k2:1t-cloud = FASTEST (simple lookups, quick queries)
# minimax-m2:cloud = MEDIUM SPEED (analysis, research)
# glm-4.6:cloud = MOST POWERFUL (complex reasoning, Monte Carlo, optimization)

from langchain_openai import ChatOpenAI
import httpx

# Create shared HTTP client with rate limiting
# (Rate limiting and retry logic defined in src/deep_agent.py)
http_limits = httpx.Limits(
    max_keepalive_connections=5,
    max_connections=10,
    keepalive_expiry=30.0
)

KIMI_MODEL = ChatOpenAI(
    temperature=0,
    model="kimi-k2:1t-cloud",
    openai_api_key=OLLAMA_API_KEY,
    openai_api_base=OLLAMA_BASE_URL,
    max_retries=10,  # Aggressive retry for rate limits
    timeout=300,
)

MINIMAX_MODEL = ChatOpenAI(
    temperature=0,
    model="minimax-m2:cloud",
    openai_api_key=OLLAMA_API_KEY,
    openai_api_base=OLLAMA_BASE_URL,
    max_retries=10,
    timeout=300,
)

GLM_MODEL = ChatOpenAI(
    temperature=0,
    model="glm-4.6:cloud",
    openai_api_key=OLLAMA_API_KEY,
    openai_api_base=OLLAMA_BASE_URL,
    max_retries=10,
    timeout=300,
)

GLM_MODEL_PAID = ChatOpenAI(
    temperature=0,
    model="glm-4.6",
    openai_api_key="69feab44626640cfb0d841966bc344a1.szw2ZTaSJ1KwvjS8",
    openai_api_base="https://api.z.ai/api/paas/v4/",
    max_retries=10,  # Retry up to 10 times for rate limits
    timeout=300,     # 5 minute timeout for complex requests
    # http_client=http_client,  # Sync client with rate limiting
    # http_async_client=async_http_client  # Async client with rate limiting
)

# Distribute models based on task complexity (3-tier distribution)
SUBAGENT_MODELS = {
    # TIER 1: KIMI (Fastest) - Simple data fetching and quotes
    "market-data-specialist": GLM_MODEL_PAID,      # Real-time quotes, pricing, charts

    # TIER 2: MINIMAX (Medium) - Analysis and research
    "fundamentals-analyst": GLM_MODEL_PAID,     # Financial statements, company intelligence
    "market-intelligence-analyst": GLM_MODEL_PAID, # Sentiment, ratings, news
    "cashflow-analyzer": GLM_MODEL_PAID,        # Income/expense analysis
    "debt-manager": GLM_MODEL_PAID,             # Debt payoff calculations

    # TIER 3: GLM-4.6 (Most Powerful) - Complex calculations and optimization
    "portfolio-analyzer": GLM_MODEL_PAID,           # Portfolio optimization, Sharpe ratio
    "goal-planner": GLM_MODEL_PAID,                 # Monte Carlo simulations (complex!)
    "tax-optimizer": GLM_MODEL_PAID,                # Tax optimization strategies
    "risk-assessor": GLM_MODEL_PAID,                # VaR, stress testing (complex!)
}

# Alternative: Set all subagents to a specific model
# SUBAGENT_MODELS = {
#     "market-data-fetcher": "anthropic:claude-haiku-4-20250514",
#     "research-analyst": "openai:gpt-4o",  # Better for research tasks
#     "portfolio-analyzer": "anthropic:claude-sonnet-4-20250514",  # Complex analysis
#     "cashflow-analyzer": "anthropic:claude-haiku-4-20250514",
#     "goal-planner": "anthropic:claude-sonnet-4-20250514",  # Monte Carlo needs reasoning
#     "debt-manager": "anthropic:claude-haiku-4-20250514",
#     "tax-optimizer": "openai:gpt-4o-mini",
#     "risk-assessor": "anthropic:claude-haiku-4-20250514",
# }

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


# Helper function to build subagent dict with optional model
def _build_subagent(name, description, system_prompt, tools):
    """Build subagent dict, only including 'model' key if value is not None."""
    subagent = {
        "name": name,
        "description": description,
        "system_prompt": system_prompt,
        "tools": tools,
    }
    # Only add model key if it's not None (allows proper inheritance from main agent)
    model = SUBAGENT_MODELS.get(name)
    if model is not None:
        subagent["model"] = model
    return subagent


# ============================================================================
# CONSOLIDATED MARKET DATA AGENTS (3 total - optimized for Ollama performance)
# ============================================================================
# Reduced from 6 agents to 3 to prevent Ollama server overload
# Each agent has max 9 tools (down from 11-14) with zero overlap

# 1. Market Data Specialist - Real-time quotes, pricing, basic metrics, charts
MARKET_DATA_SUBAGENT = _build_subagent(
    name="market-data-specialist",
    description="""Use this agent for real-time market data and technical analysis:
    - Current stock prices (single or batch quotes)
    - Search for ticker symbols by company name
    - Historical price charts and trends
    - Key trading metrics (P/E, beta, volume, 52-week range)

    This is the FASTEST agent - use for price lookups, basic metrics, and chart analysis.""",
    system_prompt="""You are a Market Data Specialist focused on real-time pricing and technical analysis.

Your responsibilities:
1. Fetch current prices for stocks, ETFs, funds (use get_multiple_quotes for 2+ symbols)
2. Search for correct ticker symbols when company name provided
3. Retrieve historical price charts (1-year and 5-year for context)
4. Provide key trading metrics: P/E ratio, beta, volume, market cap, 52-week range
5. Identify technical trends: uptrend/downtrend/sideways, support/resistance levels
6. Save raw data to /financial_data/ and analysis reports to /reports/{SYMBOL}_Technical.md

Best practices:
- ALWAYS use get_multiple_quotes() for 2+ symbols (much faster than individual calls)
- Get both 1-year and 5-year charts for trend context
- Include 52-week high/low context: "Currently at 88% of 52-week range"
- Note technical levels from charts: "Support at $150, resistance at $175"
- Keep responses concise and data-focused

Output format for quotes:
{
  "AAPL": {"price": $150.25, "change": +2.50 (+1.69%), "volume": 50M, "mktCap": $2.4T, "PE": 28.5}
}

Speed and accuracy are your strengths - provide instant market data.""",
    tools=[
        # Discovery & Quotes (3)
        search_stocks,
        get_stock_quote,
        get_multiple_quotes,
        # Technical Analysis (2)
        get_stock_chart,
        get_stock_statistics,
        # Web search tools (3 - available to all agents)
        web_search,
        web_search_news,
        web_search_financial,
    ],
)


# 2. Fundamentals Analyst - Financial statements, company profiles, competitors
FUNDAMENTALS_SUBAGENT = _build_subagent(
    name="fundamentals-analyst",
    description="""Use this agent for fundamental analysis and company intelligence:
    - Financial statements (income, balance sheet, cash flow)
    - Earnings history and trends
    - Company business profile and operations
    - Competitive landscape and peer comparison

    Use for deep financial analysis, valuation, and understanding business models.""",
    system_prompt="""You are a Fundamentals Analyst focused on financial health and business intelligence.

Your responsibilities:
1. Analyze financial statements for health and trends
   - Income statement: revenue growth, profit margins, EPS
   - Balance sheet: assets, liabilities, debt levels, equity
   - Cash flow: operating cash flow, free cash flow
2. Track earnings history and compare to estimates
3. Provide company business overview (what they do, how they make money)
4. Identify key competitors and compare competitive positioning
5. Calculate and interpret key ratios (P/E, ROE, debt-to-equity, margins)
6. Save comprehensive reports to /reports/{SYMBOL}_Fundamentals.md

Best practices:
- Start with company profile for context
- Flag red flags: declining revenue, increasing debt, negative cash flow, low margins
- Identify strengths: consistent growth, strong margins, healthy balance sheet, positive FCF
- Calculate YoY growth rates and 3-year trends
- Compare to competitors using get_similar_stocks()
- Use web search for latest financial results and business developments

Report structure:
## Company Overview
- Business description, products/services, revenue streams
## Financial Health Score (1-10)
## Key Metrics
- Revenue: $XXB (YoY: +X%) | Net Income: $XXB (margin: X%)
- P/E: X.X | ROE: X.X% | Debt/Equity: X.X
## 3-Year Trends
- Revenue, earnings, cash flow trajectory
## Competitive Position
- Key competitors and comparative strengths
## Strengths & Concerns
## Valuation Assessment

Always include numbers, percentages, and year-over-year comparisons.""",
    tools=[
        # Financial Statements (4)
        get_stock_financials,
        get_stock_balance_sheet,
        get_stock_cashflow,
        get_stock_earnings,
        # Company Intelligence (2)
        get_stock_profile,
        get_similar_stocks,
        # Web search tools (3)
        web_search,
        web_search_news,
        web_search_financial,
    ],
)


# 3. Market Intelligence Analyst - Sentiment, ratings, news, insider activity
MARKET_INTELLIGENCE_SUBAGENT = _build_subagent(
    name="market-intelligence-analyst",
    description="""Use this agent for market sentiment and qualitative intelligence:
    - Analyst ratings, price targets, upgrades/downgrades
    - Insider trading activity (executives buying/selling)
    - Institutional ownership and major holders
    - Recent financial news and developments
    - Upcoming earnings dates and market events

    Use to gauge Wall Street consensus, smart money positioning, and news catalysts.""",
    system_prompt="""You are a Market Intelligence Analyst tracking sentiment, ratings, and news.

Your responsibilities:
1. Summarize analyst consensus (buy/hold/sell ratings) and price targets
2. Identify recent upgrades/downgrades as potential catalysts
3. Monitor insider trading activity
   - Insider buying = bullish signal (strong conviction)
   - Insider selling = often routine, but watch for massive sales
4. Track institutional ownership and major holders
5. Summarize recent financial news (last 30 days)
6. Check upcoming calendar events (earnings dates, dividend dates, conference calls)
7. Save intelligence reports to /reports/{SYMBOL}_Intelligence.md

Best practices:
- Analyst consensus: "X of Y analysts rate BUY (X%), median target $XXX (+X% upside)"
- Recent rating changes are IMPORTANT - note date, firm, and reasoning
- Insider activity: Focus on purchases (strong signal), note large executive sales
- Institutional ownership: >70% = institutional quality, but reduces float
- News: Separate material events (earnings, guidance, M&A) from routine announcements
- Calendar events: Highlight upcoming earnings dates and dividend dates (key catalysts)
- Use web search for breaking news and recent developments

Report structure:
## Analyst Consensus
- Ratings distribution: Buy X% | Hold X% | Sell X%
- Price target: $XXX (median) implies +X% upside
## Recent Rating Changes (last 3 months)
- [Date] Firm X: upgraded to BUY (from HOLD) - [Reason]
## Insider Activity
- Recent purchases: [Details with amounts and dates]
- Recent sales: [Details if significant]
- Net sentiment: [Bullish/Neutral/Bearish]
## Institutional Ownership
- Top 5 holders with % stakes
- Recent changes: [Accumulation/Distribution/Stable]
## Recent News (last 30 days)
- Material events with impact assessment
## Upcoming Calendar Events
- Earnings date: [Date]
- Dividend dates: [Ex-date, Payment date]
- Conference calls or investor events
## Overall Sentiment: [Bullish/Neutral/Bearish]

Focus on actionable insights and catalysts.""",
    tools=[
        # Analyst Ratings & Sentiment (3)
        get_stock_analysis,
        get_upgrades_downgrades,
        get_major_holders,
        # Insider Activity (1)
        get_insider_transactions,
        # News & Calendar (3)
        get_news_list,
        get_calendar_events,
        count_calendar_events,
        # Web search tools (3)
        web_search,
        web_search_news,
        web_search_financial,
    ],
)


# Portfolio Analyzer Subagent
PORTFOLIO_SUBAGENT = _build_subagent(
    name="portfolio-analyzer",
    description="""Use this agent for investment portfolio analysis, including:
    - Calculating portfolio value and returns
    - Analyzing asset allocation
    - Identifying concentration risks
    - Calculating performance metrics (Sharpe ratio, returns)
    - Recommending rebalancing strategies
    - Generating portfolio visualizations""",
    system_prompt="""You are a Portfolio Analysis Specialist focused on investment analysis.

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
    tools=[
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
)


# Cash Flow Analyzer Subagent
CASHFLOW_SUBAGENT = _build_subagent(
    name="cashflow-analyzer",
    description="""Use this agent for income and expense analysis, including:
    - Analyzing monthly cash flow (income vs expenses)
    - Calculating savings rates
    - Categorizing and analyzing spending patterns
    - Projecting future cash flow
    - Assessing emergency fund runway
    - Generating cash flow visualizations""",
    system_prompt="""You are a Cash Flow Analysis Specialist focused on income, expenses, and savings.

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
    tools=[
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
)


# Goal Planning Subagent
GOAL_SUBAGENT = _build_subagent(
    name="goal-planner",
    description="""Use this agent for financial goal planning and analysis, including:
    - Retirement readiness assessment
    - Monte Carlo simulations for goal projections
    - Required savings rate calculations
    - College funding (529 plan) analysis
    - FIRE (Financial Independence) number calculations
    - Goal progress tracking and recommendations""",
    system_prompt="""You are a Goal Planning Specialist focused on retirement and financial objectives.

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
    tools=[
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
)


# Debt Management Subagent
DEBT_SUBAGENT = _build_subagent(
    name="debt-manager",
    description="""Use this agent for debt analysis and optimization, including:
    - Calculating debt payoff timelines
    - Comparing avalanche vs snowball strategies
    - Optimizing extra payment allocation
    - Analyzing refinancing opportunities
    - Calculating debt-to-income ratios
    - Generating debt payoff visualizations""",
    system_prompt="""You are a Debt Management Specialist focused on debt optimization strategies.

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
    tools=[
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
)


# Tax Optimization Subagent
TAX_SUBAGENT = _build_subagent(
    name="tax-optimizer",
    description="""Use this agent for tax optimization strategies, including:
    - Calculating effective tax rates
    - Identifying tax loss harvesting opportunities
    - Analyzing Roth conversion opportunities
    - Optimizing withdrawal sequences from different account types
    - Calculating capital gains tax implications
    - Recommending tax-efficient strategies""",
    system_prompt="""You are a Tax Optimization Specialist focused on tax-efficient strategies.

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
    tools=[
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
)


# Risk Assessment Subagent
RISK_SUBAGENT = _build_subagent(
    name="risk-assessor",
    description="""Use this agent for financial risk assessment, including:
    - Assessing emergency fund adequacy
    - Identifying insurance coverage gaps
    - Calculating portfolio volatility and risk metrics
    - Running stress test scenarios (market crashes)
    - Analyzing concentration risks
    - Generating risk dashboard visualizations""",
    system_prompt="""You are a Risk Assessment Specialist focused on identifying financial vulnerabilities.

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
    tools=[
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
)


# All subagents list (9 total: 3 market data + 6 financial analysis)
FINANCIAL_SUBAGENTS = [
    # Market Data Specialists (3 agents) - Consolidated to reduce Ollama load
    MARKET_DATA_SUBAGENT,         # 1. Real-time quotes, pricing, charts, metrics
    FUNDAMENTALS_SUBAGENT,        # 2. Financial statements, company profiles, competitors
    MARKET_INTELLIGENCE_SUBAGENT, # 3. Sentiment, ratings, news, insider activity

    # Financial Analysis Specialists (6 agents) - Unchanged
    PORTFOLIO_SUBAGENT,           # 4. Portfolio valuation and allocation
    CASHFLOW_SUBAGENT,            # 5. Income/expense analysis
    GOAL_SUBAGENT,                # 6. Retirement and goal planning
    DEBT_SUBAGENT,                # 7. Debt optimization
    TAX_SUBAGENT,                 # 8. Tax strategies
    RISK_SUBAGENT,                # 9. Risk assessment
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
