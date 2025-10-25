"""
Stock trading tools - Mock implementations for stock operations.
"""

import random
from typing import Dict, Any, List
from langchain.tools import tool

from src.config.settings import settings
from src.monitoring.logger import get_logger

logger = get_logger(__name__)

# Mock stock database
STOCK_PRICES = {
    "AAPL": 175.50,
    "GOOGL": 140.25,
    "MSFT": 380.75,
    "TSLA": 245.30,
    "AMZN": 145.80,
    "META": 485.20,
    "NVDA": 875.40,
    "JPM": 195.60,
    "V": 270.90,
    "WMT": 165.30
}

# Mock user portfolios
USER_PORTFOLIOS: Dict[str, Dict[str, Any]] = {}


@tool
async def get_stock_price(symbol: str) -> Dict[str, Any]:
    """
    Get current stock price for a given symbol.
    
    Args:
        symbol: Stock ticker symbol (e.g., AAPL, GOOGL)
        
    Returns:
        Dict with price information
    """
    try:
        symbol = symbol.upper().strip()
        
        logger.info("Fetching stock price", symbol=symbol)
        
        if symbol not in STOCK_PRICES:
            return {
                "success": False,
                "error": f"Stock symbol {symbol} not found"
            }
        
        # Add small random variation
        base_price = STOCK_PRICES[symbol]
        price = round(base_price * (1 + random.uniform(-0.02, 0.02)), 2)
        
        return {
            "success": True,
            "symbol": symbol,
            "price": price,
            "currency": "USD",
            "timestamp": "2025-10-25T10:00:00Z"
        }
        
    except Exception as e:
        logger.error("Error fetching stock price", error=str(e), symbol=symbol)
        return {"success": False, "error": str(e)}


@tool
async def execute_trade(
    symbol: str,
    action: str,
    quantity: int,
    user_id: str = "default"
) -> Dict[str, Any]:
    """
    Execute a stock trade (buy or sell).
    
    Args:
        symbol: Stock ticker symbol
        action: 'buy' or 'sell'
        quantity: Number of shares
        user_id: User identifier
        
    Returns:
        Dict with trade execution result
    """
    try:
        symbol = symbol.upper().strip()
        action = action.lower().strip()
        
        logger.info("Executing trade", symbol=symbol, action=action, quantity=quantity, user_id=user_id)
        
        # Validate inputs
        if action not in ["buy", "sell"]:
            return {"success": False, "error": "Action must be 'buy' or 'sell'"}
        
        if quantity <= 0:
            return {"success": False, "error": "Quantity must be positive"}
        
        if symbol not in STOCK_PRICES:
            return {"success": False, "error": f"Stock symbol {symbol} not found"}
        
        # Get current price
        price_result = await get_stock_price(symbol)
        if not price_result["success"]:
            return price_result
        
        price = price_result["price"]
        total_amount = price * quantity
        
        # Check guardrails
        if total_amount > settings.max_trade_amount:
            return {
                "success": False,
                "error": f"Trade amount ${total_amount:,.2f} exceeds maximum allowed ${settings.max_trade_amount:,.2f}"
            }
        
        if total_amount < settings.min_trade_amount:
            return {
                "success": False,
                "error": f"Trade amount ${total_amount:,.2f} below minimum ${settings.min_trade_amount:,.2f}"
            }
        
        # Initialize portfolio if needed
        if user_id not in USER_PORTFOLIOS:
            USER_PORTFOLIOS[user_id] = {
                "cash": 100000.0,  # Starting cash
                "holdings": {}
            }
        
        portfolio = USER_PORTFOLIOS[user_id]
        
        # Execute trade
        if action == "buy":
            if portfolio["cash"] < total_amount:
                return {
                    "success": False,
                    "error": f"Insufficient funds. Need ${total_amount:,.2f}, have ${portfolio['cash']:,.2f}"
                }
            
            portfolio["cash"] -= total_amount
            portfolio["holdings"][symbol] = portfolio["holdings"].get(symbol, 0) + quantity
            
        else:  # sell
            current_holding = portfolio["holdings"].get(symbol, 0)
            if current_holding < quantity:
                return {
                    "success": False,
                    "error": f"Insufficient shares. Have {current_holding}, trying to sell {quantity}"
                }
            
            portfolio["cash"] += total_amount
            portfolio["holdings"][symbol] -= quantity
            
            if portfolio["holdings"][symbol] == 0:
                del portfolio["holdings"][symbol]
        
        trade_id = f"TRD-{random.randint(100000, 999999)}"
        
        logger.info("Trade executed successfully", trade_id=trade_id, symbol=symbol, action=action)
        
        return {
            "success": True,
            "trade_id": trade_id,
            "symbol": symbol,
            "action": action,
            "quantity": quantity,
            "price": price,
            "total_amount": total_amount,
            "remaining_cash": portfolio["cash"],
            "message": f"Successfully {action} {quantity} shares of {symbol} at ${price:.2f}"
        }
        
    except Exception as e:
        logger.error("Trade execution failed", error=str(e))
        return {"success": False, "error": str(e)}


@tool
async def get_portfolio(user_id: str = "default") -> Dict[str, Any]:
    """
    Get user's current portfolio.
    
    Args:
        user_id: User identifier
        
    Returns:
        Dict with portfolio information
    """
    try:
        logger.info("Fetching portfolio", user_id=user_id)
        
        if user_id not in USER_PORTFOLIOS:
            return {
                "success": True,
                "cash": 100000.0,
                "holdings": {},
                "total_value": 100000.0,
                "message": "New portfolio initialized"
            }
        
        portfolio = USER_PORTFOLIOS[user_id]
        holdings_value = 0.0
        detailed_holdings = []
        
        for symbol, quantity in portfolio["holdings"].items():
            price_result = await get_stock_price(symbol)
            if price_result["success"]:
                price = price_result["price"]
                value = price * quantity
                holdings_value += value
                
                detailed_holdings.append({
                    "symbol": symbol,
                    "quantity": quantity,
                    "current_price": price,
                    "total_value": value
                })
        
        total_value = portfolio["cash"] + holdings_value
        
        return {
            "success": True,
            "cash": portfolio["cash"],
            "holdings": detailed_holdings,
            "holdings_value": holdings_value,
            "total_value": total_value
        }
        
    except Exception as e:
        logger.error("Portfolio fetch failed", error=str(e))
        return {"success": False, "error": str(e)}


async def get_stock_tools() -> List:
    """Get all stock-related tools."""
    return [get_stock_price, execute_trade, get_portfolio]