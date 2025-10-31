#!/usr/bin/env python3
"""
Generate all remaining MCP servers from existing tool modules.

This script creates MCP server files that directly import and wrap
the existing tool functions from src/tools/.
"""

import os


def create_server_file(server_name, module_name, tools_list):
    """
    Create an MCP server file.

    Args:
        server_name: Display name for the server
        module_name: Python module name (e.g., 'src.tools.debt_tools')
        tools_list: List of tool function names to wrap
    """
    server_filename = f"{server_name.lower().replace(' ', '_').replace('-', '_')}_server.py"
    server_path = os.path.join(os.path.dirname(__file__), server_filename)

    # Skip if already exists
    if os.path.exists(server_path):
        print(f"Skipping {server_filename} - already exists")
        return

    # Generate import list
    imports = ', '.join(tools_list)

    # Generate tool registrations
    tool_registrations = []
    for tool_name in tools_list:
        tool_registrations.append(f'''
@mcp.tool()
def {tool_name}(*args, **kwargs):
    """Wrapper for {tool_name} from {module_name}"""
    tool_func = globals()['{tool_name}_impl']
    if hasattr(tool_func, 'invoke'):
        return tool_func.invoke(kwargs if kwargs else {{}})
    else:
        return tool_func(*args, **kwargs)
''')

    # Create the server file content
    content = f'''#!/usr/bin/env python3
"""
MCP Server for {server_name}

Automatically generated server that wraps tools from {module_name}
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from mcp.server.fastmcp import FastMCP
from {module_name} import (
    {imports}
)

# Store tool implementations
{chr(10).join([f'{tool}_impl = {tool}' for tool in tools_list])}

# Create MCP server
mcp = FastMCP("{server_name}")

{''.join(tool_registrations)}

if __name__ == "__main__":
    # Run MCP server with stdio transport for local subprocess communication
    mcp.run(transport="stdio")
'''

    # Write the file
    with open(server_path, 'w') as f:
        f.write(content)

    # Make executable
    os.chmod(server_path, 0o755)

    print(f"Created: {server_filename}")


if __name__ == "__main__":
    # Define all servers to create
    servers = [
        ("Debt Management", "src.tools.debt_tools", [
            "calculate_debt_payoff_timeline",
            "compare_avalanche_vs_snowball",
            "calculate_total_interest_cost",
            "optimize_extra_payment_allocation",
            "calculate_debt_to_income_ratio",
            "generate_payoff_chart"
        ]),
        ("Tax Optimization", "src.tools.tax_tools", [
            "calculate_effective_tax_rate",
            "identify_tax_loss_harvesting_opportunities",
            "analyze_roth_conversion_opportunity",
            "optimize_withdrawal_sequence",
            "calculate_capital_gains_tax"
        ]),
        ("Risk Assessment", "src.tools.risk_tools", [
            "calculate_emergency_fund_adequacy",
            "analyze_insurance_gaps",
            "calculate_portfolio_volatility",
            "run_stress_test_scenarios",
            "calculate_value_at_risk",
            "analyze_concentration_risk",
            "generate_risk_dashboard"
        ]),
        ("Web Search", "src.tools.search_tools", [
            "web_search",
            "web_search_news",
            "web_search_financial"
        ]),
        ("Portfolio Updates", "src.tools.portfolio_update_tools", [
            "update_investment_holding",
            "update_cash_balance",
            "record_expense",
            "update_credit_card_balance",
            "recalculate_net_worth"
        ]),
    ]

    print("Generating MCP servers...\n")

    for server_name, module_name, tools_list in servers:
        create_server_file(server_name, module_name, tools_list)

    print("\n✅ All MCP servers generated successfully!")
