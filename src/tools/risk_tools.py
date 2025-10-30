"""Risk assessment calculation tools."""

from langchain_core.tools import tool
import numpy as np
from typing import Dict, List


@tool
def calculate_emergency_fund_adequacy(
    liquid_assets: float,
    monthly_expenses: float
) -> Dict:
    """
    Calculate emergency fund adequacy in months of expenses.

    Args:
        liquid_assets: Total liquid assets (checking + savings)
        monthly_expenses: Average monthly expenses

    Returns:
        Emergency fund analysis
    """
    months_covered = liquid_assets / monthly_expenses if monthly_expenses > 0 else 0

    # Target is typically 6 months
    target_months = 6
    target_amount = monthly_expenses * target_months
    shortfall = max(0, target_amount - liquid_assets)

    if months_covered >= 6:
        status = "Excellent"
    elif months_covered >= 3:
        status = "Adequate"
    elif months_covered >= 1:
        status = "Minimal"
    else:
        status = "Critical"

    return {
        "liquid_assets": round(liquid_assets, 2),
        "monthly_expenses": round(monthly_expenses, 2),
        "months_covered": round(months_covered, 1),
        "target_months": target_months,
        "target_amount": round(target_amount, 2),
        "shortfall": round(shortfall, 2),
        "status": status
    }


@tool
def analyze_insurance_gaps(
    current_coverage: Dict,
    recommended_coverage: Dict
) -> Dict:
    """
    Analyze insurance coverage gaps.

    Args:
        current_coverage: Dict of insurance_type -> coverage_amount
        recommended_coverage: Dict of insurance_type -> recommended_amount

    Returns:
        Insurance gap analysis
    """
    gaps = []

    for insurance_type, recommended in recommended_coverage.items():
        current = current_coverage.get(insurance_type, 0)

        # Convert to float if they're strings
        try:
            recommended = float(recommended)
            current = float(current)
        except (ValueError, TypeError):
            recommended = 0
            current = 0

        gap = max(0, recommended - current)

        gaps.append({
            "insurance_type": insurance_type,
            "current_coverage": round(current, 2),
            "recommended_coverage": round(recommended, 2),
            "gap": round(gap, 2),
            "adequate": gap == 0
        })

    total_gap = sum(g["gap"] for g in gaps)

    return {
        "gaps": gaps,
        "total_coverage_gap": round(total_gap, 2),
        "fully_insured": total_gap == 0
    }


@tool
def calculate_portfolio_volatility(
    asset_allocation: Dict[str, float],
    volatility_by_asset: Dict[str, float] = None
) -> Dict:
    """
    Calculate portfolio volatility based on asset allocation.

    Args:
        asset_allocation: Dict of asset_class -> percentage
        volatility_by_asset: Dict of asset_class -> annual volatility (optional)

    Returns:
        Portfolio volatility metrics
    """
    # Default volatilities if not provided
    if volatility_by_asset is None:
        volatility_by_asset = {
            "US Equity": 0.18,
            "International Equity": 0.20,
            "Bonds": 0.05,
            "Real Estate": 0.15,
            "Crypto": 0.80,
            "Target Date Fund": 0.12
        }

    # Calculate weighted volatility (simplified, assumes some correlation)
    weighted_vol = 0
    for asset_class, pct in asset_allocation.items():
        vol = volatility_by_asset.get(asset_class, 0.15)  # Default 15%
        weighted_vol += (pct / 100) * vol

    # Adjust for diversification benefit (assume 0.8 correlation)
    diversification_factor = 0.85
    portfolio_vol = weighted_vol * diversification_factor

    if portfolio_vol < 0.08:
        risk_level = "Conservative"
    elif portfolio_vol < 0.15:
        risk_level = "Moderate"
    elif portfolio_vol < 0.25:
        risk_level = "Aggressive"
    else:
        risk_level = "Very Aggressive"

    return {
        "portfolio_volatility": round(portfolio_vol * 100, 2),
        "risk_level": risk_level,
        "expected_annual_range": f"±{round(portfolio_vol * 100, 1)}%"
    }


@tool
def run_stress_test_scenarios(
    portfolio_value: float,
    equity_percentage: float,
    scenarios: List[Dict] = None
) -> Dict:
    """
    Run stress test scenarios on portfolio.

    Args:
        portfolio_value: Current portfolio value
        equity_percentage: Percentage in equities
        scenarios: List of stress test scenarios (optional)

    Returns:
        Stress test results
    """
    if scenarios is None:
        scenarios = [
            {"name": "Mild Correction (-10%)", "equity_change": -0.10, "bond_change": 0.02},
            {"name": "Bear Market (-30%)", "equity_change": -0.30, "bond_change": 0.05},
            {"name": "Severe Crash (-50%)", "equity_change": -0.50, "bond_change": 0.10},
            {"name": "2008 Financial Crisis", "equity_change": -0.37, "bond_change": 0.05},
        ]

    results = []

    equity_value = portfolio_value * (equity_percentage / 100)
    bond_value = portfolio_value - equity_value

    for scenario in scenarios:
        equity_after = equity_value * (1 + scenario.get("equity_change", 0))
        bond_after = bond_value * (1 + scenario.get("bond_change", 0))
        portfolio_after = equity_after + bond_after

        loss = portfolio_value - portfolio_after
        loss_pct = (loss / portfolio_value * 100) if portfolio_value > 0 else 0

        results.append({
            "scenario": scenario.get("name", "Unknown Scenario"),
            "portfolio_before": round(portfolio_value, 2),
            "portfolio_after": round(portfolio_after, 2),
            "loss_amount": round(loss, 2),
            "loss_percentage": round(loss_pct, 2)
        })

    return {
        "stress_test_results": results,
        "current_portfolio": round(portfolio_value, 2),
        "equity_percentage": equity_percentage
    }


@tool
def calculate_value_at_risk(
    portfolio_value: float,
    portfolio_volatility: float,
    confidence_level: float = 0.95,
    time_horizon_days: int = 1
) -> Dict:
    """
    Calculate Value at Risk (VaR) for portfolio.

    Args:
        portfolio_value: Current portfolio value
        portfolio_volatility: Annual portfolio volatility
        confidence_level: Confidence level (default 0.95 = 95%)
        time_horizon_days: Time horizon in days (default 1)

    Returns:
        VaR calculation
    """
    # Convert annual volatility to daily
    daily_volatility = portfolio_volatility / np.sqrt(252)  # 252 trading days

    # Scale for time horizon
    horizon_volatility = daily_volatility * np.sqrt(time_horizon_days)

    # Z-score for confidence level (95% = 1.645, 99% = 2.326)
    z_scores = {0.90: 1.282, 0.95: 1.645, 0.99: 2.326}
    z_score = z_scores.get(confidence_level, 1.645)

    # VaR calculation
    var_amount = portfolio_value * horizon_volatility * z_score

    return {
        "portfolio_value": round(portfolio_value, 2),
        "var_amount": round(var_amount, 2),
        "confidence_level": round(confidence_level * 100, 1),
        "time_horizon_days": time_horizon_days,
        "interpretation": f"{confidence_level*100}% confident losses won't exceed ${round(var_amount, 2)} in {time_horizon_days} day(s)"
    }


@tool
def analyze_concentration_risk(
    holdings_by_sector: Dict[str, float],
    holdings_by_geography: Dict[str, float]
) -> Dict:
    """
    Analyze concentration risk by sector and geography.

    Args:
        holdings_by_sector: Dict of sector -> percentage
        holdings_by_geography: Dict of geography -> percentage

    Returns:
        Concentration risk analysis
    """
    # Sector concentration
    max_sector = max(holdings_by_sector.items(), key=lambda x: x[1]) if holdings_by_sector else ("None", 0)
    sector_concentrated = max_sector[1] > 25  # More than 25% in one sector

    # Geographic concentration
    max_geo = max(holdings_by_geography.items(), key=lambda x: x[1]) if holdings_by_geography else ("None", 0)
    geo_concentrated = max_geo[1] > 70  # More than 70% in one geography

    risk_factors = []
    if sector_concentrated:
        risk_factors.append(f"High sector concentration: {max_sector[0]} ({max_sector[1]}%)")
    if geo_concentrated:
        risk_factors.append(f"High geographic concentration: {max_geo[0]} ({max_geo[1]}%)")

    overall_risk = "High" if (sector_concentrated or geo_concentrated) else "Moderate" if max_sector[1] > 15 else "Low"

    return {
        "sector_concentration": {
            "highest_sector": max_sector[0],
            "percentage": round(max_sector[1], 2),
            "concentrated": sector_concentrated
        },
        "geographic_concentration": {
            "highest_geography": max_geo[0],
            "percentage": round(max_geo[1], 2),
            "concentrated": geo_concentrated
        },
        "risk_factors": risk_factors,
        "overall_concentration_risk": overall_risk
    }


@tool
def generate_risk_dashboard(risk_metrics: Dict) -> Dict:
    """
    Generate risk dashboard visualization data.

    Args:
        risk_metrics: Dictionary of various risk metrics

    Returns:
        Chart data structure for UI rendering
    """
    return {
        "chart_type": "gauge",
        "title": "Risk Assessment Dashboard",
        "data": {
            "metrics": risk_metrics
        },
        "library": "plotly"
    }
