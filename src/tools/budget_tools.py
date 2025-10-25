"""
Budget calculation and financial analysis tools.
"""

from typing import Dict, Any, List
from langchain.tools import tool

from src.monitoring.logger import get_logger

logger = get_logger(__name__)


@tool
async def calculate_budget(
    monthly_income: float,
    monthly_expenses: float,
    investment_goal: float = 0.0
) -> Dict[str, Any]:
    """
    Calculate investment budget based on income and expenses.
    
    Args:
        monthly_income: Monthly income in USD
        monthly_expenses: Monthly expenses in USD
        investment_goal: Target investment amount per month
        
    Returns:
        Dict with budget analysis
    """
    try:
        logger.info("Calculating budget", income=monthly_income, expenses=monthly_expenses)
        
        if monthly_income <= 0:
            return {
                "success": False,
                "error": "Monthly income must be positive"
            }
        
        if monthly_expenses < 0:
            return {
                "success": False,
                "error": "Monthly expenses cannot be negative"
            }
        
        # Calculate available funds
        available = monthly_income - monthly_expenses
        
        if available <= 0:
            return {
                "success": True,
                "available_for_investment": 0.0,
                "recommendation": "Your expenses exceed income. Focus on reducing expenses before investing.",
                "budget_status": "deficit"
            }
        
        # Calculate recommended allocations
        # 50/30/20 rule: 50% needs, 30% wants, 20% savings/investments
        recommended_investment = monthly_income * 0.20
        max_safe_investment = available * 0.80  # Keep 20% buffer
        
        # Determine if goal is achievable
        can_meet_goal = investment_goal <= max_safe_investment if investment_goal > 0 else True
        
        return {
            "success": True,
            "monthly_income": monthly_income,
            "monthly_expenses": monthly_expenses,
            "available_for_investment": round(available, 2),
            "recommended_investment": round(recommended_investment, 2),
            "max_safe_investment": round(max_safe_investment, 2),
            "investment_goal": investment_goal,
            "can_meet_goal": can_meet_goal,
            "budget_status": "surplus",
            "savings_rate": round((available / monthly_income) * 100, 2),
            "recommendation": f"You can safely invest ${max_safe_investment:.2f} per month while maintaining a buffer."
        }
        
    except Exception as e:
        logger.error("Budget calculation failed", error=str(e))
        return {
            "success": False,
            "error": str(e)
        }


@tool
async def calculate_portfolio_allocation(
    total_investment: float,
    risk_tolerance: str = "moderate"
) -> Dict[str, Any]:
    """
    Calculate recommended portfolio allocation based on risk tolerance.
    
    Args:
        total_investment: Total amount to invest
        risk_tolerance: Risk level (conservative, moderate, aggressive)
        
    Returns:
        Dict with allocation recommendations
    """
    try:
        logger.info("Calculating portfolio allocation", amount=total_investment, risk=risk_tolerance)
        
        if total_investment <= 0:
            return {
                "success": False,
                "error": "Investment amount must be positive"
            }
        
        # Define allocation strategies
        allocations = {
            "conservative": {
                "stocks": 0.30,
                "bonds": 0.50,
                "cash": 0.20,
                "description": "Low risk, stable returns"
            },
            "moderate": {
                "stocks": 0.60,
                "bonds": 0.30,
                "cash": 0.10,
                "description": "Balanced risk and returns"
            },
            "aggressive": {
                "stocks": 0.80,
                "bonds": 0.15,
                "cash": 0.05,
                "description": "High risk, high potential returns"
            }
        }
        
        risk_level = risk_tolerance.lower()
        if risk_level not in allocations:
            risk_level = "moderate"
        
        allocation = allocations[risk_level]
        
        return {
            "success": True,
            "total_investment": total_investment,
            "risk_tolerance": risk_level,
            "description": allocation["description"],
            "allocation": {
                "stocks": {
                    "percentage": allocation["stocks"] * 100,
                    "amount": round(total_investment * allocation["stocks"], 2)
                },
                "bonds": {
                    "percentage": allocation["bonds"] * 100,
                    "amount": round(total_investment * allocation["bonds"], 2)
                },
                "cash": {
                    "percentage": allocation["cash"] * 100,
                    "amount": round(total_investment * allocation["cash"], 2)
                }
            },
            "recommendation": f"For {risk_level} risk tolerance, invest {allocation['stocks']*100:.0f}% in stocks, {allocation['bonds']*100:.0f}% in bonds, and keep {allocation['cash']*100:.0f}% in cash."
        }
        
    except Exception as e:
        logger.error("Portfolio allocation calculation failed", error=str(e))
        return {
            "success": False,
            "error": str(e)
        }


@tool
async def calculate_returns(
    initial_investment: float,
    annual_return_rate: float,
    years: int,
    monthly_contribution: float = 0.0
) -> Dict[str, Any]:
    """
    Calculate potential investment returns over time.
    
    Args:
        initial_investment: Starting investment amount
        annual_return_rate: Expected annual return rate (as percentage, e.g., 7.0 for 7%)
        years: Investment time horizon in years
        monthly_contribution: Additional monthly investment
        
    Returns:
        Dict with return projections
    """
    try:
        logger.info("Calculating returns", initial=initial_investment, rate=annual_return_rate, years=years)
        
        if initial_investment < 0 or years <= 0:
            return {
                "success": False,
                "error": "Invalid parameters"
            }
        
        # Convert annual rate to monthly
        monthly_rate = annual_return_rate / 100 / 12
        months = years * 12
        
        # Calculate future value with monthly contributions
        future_value = initial_investment * ((1 + monthly_rate) ** months)
        
        if monthly_contribution > 0:
            # Future value of monthly contributions (annuity)
            fv_contributions = monthly_contribution * (((1 + monthly_rate) ** months - 1) / monthly_rate)
            future_value += fv_contributions
        
        total_invested = initial_investment + (monthly_contribution * months)
        total_returns = future_value - total_invested
        
        return {
            "success": True,
            "initial_investment": initial_investment,
            "monthly_contribution": monthly_contribution,
            "total_invested": round(total_invested, 2),
            "annual_return_rate": annual_return_rate,
            "years": years,
            "projected_value": round(future_value, 2),
            "total_returns": round(total_returns, 2),
            "return_percentage": round((total_returns / total_invested) * 100, 2) if total_invested > 0 else 0,
            "recommendation": f"With {annual_return_rate}% annual returns over {years} years, your ${total_invested:,.2f} investment could grow to ${future_value:,.2f}."
        }
        
    except Exception as e:
        logger.error("Returns calculation failed", error=str(e))
        return {
            "success": False,
            "error": str(e)
        }


async def get_budget_tools() -> List:
    """Get all budget-related tools."""
    return [
        calculate_budget,
        calculate_portfolio_allocation,
        calculate_returns
    ]