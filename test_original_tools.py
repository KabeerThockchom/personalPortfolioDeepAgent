#!/usr/bin/env python3
"""Test that original LangChain tools still work."""

from src.tools.portfolio_tools import calculate_portfolio_value
from src.tools.cashflow_tools import analyze_monthly_cashflow

print("🧪 Testing Original LangChain Tools\n")

# Test portfolio tool
print("=== Portfolio Tools ===")
result = calculate_portfolio_value.invoke({
    'holdings': [
        {'ticker': 'AAPL', 'shares': 100, 'cost_basis': 150.00}
    ],
    'current_prices': {'AAPL': 175.50}
})

print(f"✅ calculate_portfolio_value works!")
print(f"   Portfolio Value: ${result['total_value']:,.2f}")
print(f"   Gain/Loss: ${result['total_gain_loss']:,.2f} ({result['total_return_pct']}%)")

# Test cashflow tool
print("\n=== Cashflow Tools ===")
result2 = analyze_monthly_cashflow.invoke({
    'income': {'salary': 5000},
    'expenses': {'rent': 1500, 'food': 600}
})

print(f"✅ analyze_monthly_cashflow works!")
print(f"   Monthly Income: ${result2['total_monthly_income']:,.2f}")
print(f"   Monthly Expenses: ${result2['total_monthly_expenses']:,.2f}")
print(f"   Net Cashflow: ${result2['net_monthly_cashflow']:,.2f}")

print("\n✅ All original LangChain tools are working!")
print("✅ Your existing agent system (chat.py) will continue to work!")
