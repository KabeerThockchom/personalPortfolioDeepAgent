#!/usr/bin/env python3
"""Portfolio Update Tools MCP Server - Persist changes to portfolio.json"""

import asyncio
import sys
from pathlib import Path
import json
import os
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# Initialize MCP server
app = Server("portfolio-update-tools")

# Portfolio file path (absolute)
PORTFOLIO_FILE_PATH = "/home/user/personalPortfolioDeepAgent/portfolio.json"


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available portfolio update tools."""
    return [
        Tool(
            name="update_investment_holding",
            description="Update investment holdings (buy, sell, or adjust position)",
            inputSchema={
                "type": "object",
                "properties": {
                    "account_name": {
                        "type": "string",
                        "description": "Account key (e.g., '401k', 'roth_ira', 'taxable_brokerage', 'hsa')"
                    },
                    "ticker": {
                        "type": "string",
                        "description": "Stock/fund ticker symbol (e.g., 'AAPL', 'VOO', 'VTSAX')"
                    },
                    "action": {
                        "type": "string",
                        "enum": ["buy", "sell"],
                        "description": "Action to perform: 'buy' or 'sell'"
                    },
                    "shares": {
                        "type": "number",
                        "description": "Number of shares bought/sold"
                    },
                    "price_per_share": {
                        "type": "number",
                        "description": "Price per share for this transaction"
                    },
                    "name": {
                        "type": "string",
                        "description": "Full name of security (optional, only needed for new holdings)"
                    },
                    "asset_class": {
                        "type": "string",
                        "description": "Asset class (optional, e.g., 'US Equity', 'Bonds', 'International Equity')"
                    }
                },
                "required": ["account_name", "ticker", "action", "shares", "price_per_share"]
            }
        ),
        Tool(
            name="update_cash_balance",
            description="Update cash/bank balances (checking, savings, emergency fund)",
            inputSchema={
                "type": "object",
                "properties": {
                    "account_type": {
                        "type": "string",
                        "enum": ["checking", "savings"],
                        "description": "Account type: 'checking' or 'savings'"
                    },
                    "amount": {
                        "type": "number",
                        "description": "Dollar amount (positive number)"
                    },
                    "action": {
                        "type": "string",
                        "enum": ["deposit", "withdraw"],
                        "description": "Action to perform: 'deposit' or 'withdraw'"
                    },
                    "description": {
                        "type": "string",
                        "description": "Optional note about transaction"
                    }
                },
                "required": ["account_type", "amount", "action"]
            }
        ),
        Tool(
            name="record_expense",
            description="Record an expense and update cash balance",
            inputSchema={
                "type": "object",
                "properties": {
                    "amount": {
                        "type": "number",
                        "description": "Dollar amount spent (positive number)"
                    },
                    "category": {
                        "type": "string",
                        "description": "Expense category (e.g., 'groceries', 'rent', 'dining_out', 'transportation')"
                    },
                    "description": {
                        "type": "string",
                        "description": "Optional description of expense"
                    },
                    "payment_method": {
                        "type": "string",
                        "enum": ["checking", "savings"],
                        "default": "checking",
                        "description": "Payment method: 'checking' or 'savings' (default: checking)"
                    }
                },
                "required": ["amount", "category"]
            }
        ),
        Tool(
            name="update_credit_card_balance",
            description="Update credit card balance",
            inputSchema={
                "type": "object",
                "properties": {
                    "card_name": {
                        "type": "string",
                        "description": "Credit card key (e.g., 'apple_card', 'chase_credit_card', 'amex_gold')"
                    },
                    "new_balance": {
                        "type": "number",
                        "description": "New current balance"
                    }
                },
                "required": ["card_name", "new_balance"]
            }
        ),
        Tool(
            name="recalculate_net_worth",
            description="Recalculate total net worth after multiple updates",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool execution."""
    try:
        result = None

        if name == "update_investment_holding":
            result = _update_investment_holding(
                arguments["account_name"],
                arguments["ticker"],
                arguments["action"],
                arguments["shares"],
                arguments["price_per_share"],
                arguments.get("name"),
                arguments.get("asset_class")
            )

        elif name == "update_cash_balance":
            result = _update_cash_balance(
                arguments["account_type"],
                arguments["amount"],
                arguments["action"],
                arguments.get("description")
            )

        elif name == "record_expense":
            result = _record_expense(
                arguments["amount"],
                arguments["category"],
                arguments.get("description"),
                arguments.get("payment_method", "checking")
            )

        elif name == "update_credit_card_balance":
            result = _update_credit_card_balance(
                arguments["card_name"],
                arguments["new_balance"]
            )

        elif name == "recalculate_net_worth":
            result = _recalculate_net_worth()

        else:
            raise ValueError(f"Unknown tool: {name}")

        return [TextContent(type="text", text=result)]

    except Exception as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]


# Helper functions

def _load_portfolio() -> dict:
    """Load current portfolio from disk."""
    if not os.path.exists(PORTFOLIO_FILE_PATH):
        raise FileNotFoundError(f"Portfolio file not found: {PORTFOLIO_FILE_PATH}")

    with open(PORTFOLIO_FILE_PATH, "r") as f:
        return json.load(f)


def _save_portfolio(portfolio: dict) -> None:
    """Save updated portfolio to disk."""
    with open(PORTFOLIO_FILE_PATH, "w") as f:
        json.dump(portfolio, f, indent=2)


# Tool implementation functions (from src/tools/portfolio_update_tools.py)

def _update_investment_holding(
    account_name: str,
    ticker: str,
    action: str,
    shares: float,
    price_per_share: float,
    name: str = None,
    asset_class: str = None
) -> str:
    """Update investment holdings (buy, sell, or adjust position)."""
    try:
        portfolio = _load_portfolio()

        # Navigate to account
        if account_name not in portfolio.get("investment_accounts", {}):
            return f"Error: Account '{account_name}' not found in portfolio. Available accounts: {list(portfolio.get('investment_accounts', {}).keys())}"

        account = portfolio["investment_accounts"][account_name]
        holdings = account.get("holdings", [])

        # Find existing holding
        holding_index = None
        for i, holding in enumerate(holdings):
            if holding.get("ticker") == ticker:
                holding_index = i
                break

        if action == "buy":
            if holding_index is not None:
                # Update existing holding
                existing = holdings[holding_index]
                old_shares = existing.get("shares", 0)
                old_cost_basis = existing.get("cost_basis", 0)

                # Calculate new weighted average cost basis
                total_cost = (old_shares * old_cost_basis) + (shares * price_per_share)
                new_shares = old_shares + shares
                new_cost_basis = total_cost / new_shares if new_shares > 0 else 0

                existing["shares"] = round(new_shares, 4)
                existing["cost_basis"] = round(new_cost_basis, 2)
                existing["current_value"] = round(new_shares * price_per_share, 2)

                message = f"Updated {ticker}: {old_shares} -> {new_shares} shares @ ${new_cost_basis:.2f} avg cost"
            else:
                # Add new holding
                new_holding = {
                    "ticker": ticker,
                    "name": name or ticker,
                    "shares": round(shares, 4),
                    "cost_basis": round(price_per_share, 2),
                    "current_value": round(shares * price_per_share, 2),
                    "asset_class": asset_class or "US Equity"
                }
                holdings.append(new_holding)
                message = f"Added new holding: {ticker} - {shares} shares @ ${price_per_share:.2f}"

        elif action == "sell":
            if holding_index is None:
                return f"Error: Cannot sell {ticker} - not found in {account_name}"

            existing = holdings[holding_index]
            old_shares = existing.get("shares", 0)

            if shares > old_shares:
                return f"Error: Cannot sell {shares} shares of {ticker} - only {old_shares} shares available"

            new_shares = old_shares - shares

            if new_shares < 0.001:  # Close to zero, remove holding
                holdings.pop(holding_index)
                message = f"Sold all {ticker} shares - position closed"
            else:
                existing["shares"] = round(new_shares, 4)
                existing["current_value"] = round(new_shares * price_per_share, 2)
                message = f"Sold {shares} shares of {ticker}: {old_shares} -> {new_shares} shares remaining"

        else:
            return f"Error: Invalid action '{action}'. Use 'buy' or 'sell'"

        # Recalculate account total
        account["total_value"] = round(sum(h.get("current_value", 0) for h in holdings), 2)

        # Save to disk
        _save_portfolio(portfolio)

        return f"{message}\nAccount {account_name} total: ${account['total_value']:,.2f}\nPortfolio saved to disk"

    except Exception as e:
        return f"Error updating portfolio: {str(e)}"


def _update_cash_balance(
    account_type: str,
    amount: float,
    action: str,
    description: str = None
) -> str:
    """Update cash/bank balances (checking, savings, emergency fund)."""
    try:
        portfolio = _load_portfolio()

        emergency_fund = portfolio.get("other_assets", {}).get("emergency_fund", {})

        if account_type not in ["checking", "savings"]:
            return f"Error: Invalid account_type '{account_type}'. Use 'checking' or 'savings'"

        current_balance = emergency_fund.get(account_type, 0)

        if action == "deposit":
            new_balance = current_balance + amount
            message = f"Deposited ${amount:,.2f} to {account_type}"
        elif action == "withdraw":
            if amount > current_balance:
                return f"Error: Cannot withdraw ${amount:,.2f} - only ${current_balance:,.2f} available in {account_type}"
            new_balance = current_balance - amount
            message = f"Withdrew ${amount:,.2f} from {account_type}"
        else:
            return f"Error: Invalid action '{action}'. Use 'deposit' or 'withdraw'"

        emergency_fund[account_type] = round(new_balance, 2)

        # Update notes with timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        note = f"[{timestamp}] {action.title()}: ${amount:,.2f}"
        if description:
            note += f" - {description}"

        current_notes = emergency_fund.get("notes", "")
        emergency_fund["notes"] = f"{note} | {current_notes}"[:500]  # Keep last 500 chars

        # Save to disk
        _save_portfolio(portfolio)

        return f"{message}: ${current_balance:,.2f} -> ${new_balance:,.2f}\nPortfolio saved to disk"

    except Exception as e:
        return f"Error updating cash balance: {str(e)}"


def _record_expense(
    amount: float,
    category: str,
    description: str = None,
    payment_method: str = "checking"
) -> str:
    """Record an expense and update cash balance."""
    try:
        portfolio = _load_portfolio()

        emergency_fund = portfolio.get("other_assets", {}).get("emergency_fund", {})
        current_balance = emergency_fund.get(payment_method, 0)

        if amount > current_balance:
            return f"Warning: Expense ${amount:,.2f} exceeds {payment_method} balance ${current_balance:,.2f}. Transaction recorded but account may be overdrawn."

        new_balance = current_balance - amount
        emergency_fund[payment_method] = round(new_balance, 2)

        # Update monthly expenses (approximate tracking)
        expenses = portfolio.get("monthly_cash_flow", {}).get("expenses", {})

        # Try to map to existing expense categories
        if category in ["groceries", "dining_out"]:
            food_section = expenses.get("food", {})
            food_section[category] = food_section.get(category, 0) + amount
        elif category in ["rent", "utilities", "internet_phone"]:
            housing_section = expenses.get("housing", {})
            housing_section[category] = housing_section.get(category, 0) + amount

        # Save to disk
        _save_portfolio(portfolio)

        timestamp = datetime.now().strftime("%Y-%m-%d")
        desc_text = f" - {description}" if description else ""

        return f"Recorded expense: ${amount:,.2f} ({category}){desc_text}\n{payment_method.title()}: ${current_balance:,.2f} -> ${new_balance:,.2f}\nPortfolio saved to disk"

    except Exception as e:
        return f"Error recording expense: {str(e)}"


def _update_credit_card_balance(
    card_name: str,
    new_balance: float
) -> str:
    """Update credit card balance."""
    try:
        portfolio = _load_portfolio()

        credit_cards = portfolio.get("liabilities", {}).get("credit_cards", {})

        if card_name not in credit_cards or card_name == "total_balance":
            available = [k for k in credit_cards.keys() if k != "total_balance" and k != "note"]
            return f"Error: Card '{card_name}' not found. Available cards: {available}"

        old_balance = credit_cards[card_name].get("current_balance", 0)
        credit_cards[card_name]["current_balance"] = round(new_balance, 2)

        # Recalculate total
        total = sum(
            card.get("current_balance", 0)
            for key, card in credit_cards.items()
            if key not in ["total_balance", "note"] and isinstance(card, dict)
        )
        credit_cards["total_balance"] = round(total, 2)

        # Update total liabilities
        portfolio["net_worth_summary"]["total_liabilities"] = credit_cards["total_balance"]
        portfolio["net_worth_summary"]["total_net_worth"] = (
            portfolio["net_worth_summary"]["total_assets"] - credit_cards["total_balance"]
        )

        # Save to disk
        _save_portfolio(portfolio)

        return f"Updated {card_name}: ${old_balance:,.2f} -> ${new_balance:,.2f}\nTotal CC balance: ${total:,.2f}\nPortfolio saved to disk"

    except Exception as e:
        return f"Error updating credit card: {str(e)}"


def _recalculate_net_worth() -> str:
    """Recalculate total net worth after multiple updates."""
    try:
        portfolio = _load_portfolio()

        # Calculate total investment accounts
        investment_total = sum(
            account.get("total_value", 0)
            for account in portfolio.get("investment_accounts", {}).values()
        )

        # Calculate cash
        emergency_fund = portfolio.get("other_assets", {}).get("emergency_fund", {})
        cash_total = emergency_fund.get("checking", 0) + emergency_fund.get("savings", 0)

        # Calculate total assets
        total_assets = investment_total + cash_total

        # Calculate total liabilities (credit cards only for now)
        credit_cards = portfolio.get("liabilities", {}).get("credit_cards", {})
        total_liabilities = credit_cards.get("total_balance", 0)

        # Update net worth summary
        net_worth_summary = portfolio.get("net_worth_summary", {})
        net_worth_summary["total_assets"] = round(total_assets, 2)
        net_worth_summary["total_liabilities"] = round(total_liabilities, 2)
        net_worth_summary["total_net_worth"] = round(total_assets - total_liabilities, 2)
        net_worth_summary["breakdown"] = {
            "investment_accounts": round(investment_total, 2),
            "cash_and_bank": round(cash_total, 2),
            "real_estate": 0,
            "vehicles": 0,
            "other_assets": 0
        }

        portfolio["net_worth_summary"] = net_worth_summary
        portfolio["portfolio_analysis"]["total_investment_portfolio"] = round(investment_total, 2)

        # Save to disk
        _save_portfolio(portfolio)

        return f"""Net worth recalculated:

Assets: ${total_assets:,.2f}
   • Investments: ${investment_total:,.2f}
   • Cash: ${cash_total:,.2f}

Liabilities: ${total_liabilities:,.2f}

Net Worth: ${net_worth_summary['total_net_worth']:,.2f}

Portfolio saved to disk"""

    except Exception as e:
        return f"Error recalculating net worth: {str(e)}"


async def main():
    """Run the MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
