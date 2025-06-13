# odin/api/routes/portfolio/status.py
"""
Portfolio status endpoints
"""

import logging
from datetime import datetime
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, status

from odin.api.dependencies import get_strategy_rate_limiter, require_authentication
from odin.core.portfolio_manager import PortfolioManager

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/", response_model=Dict[str, Any])
async def get_portfolio_status(
    current_user: dict = Depends(require_authentication),
    rate_limiter=Depends(get_strategy_rate_limiter),
):
    """Get current live portfolio status across all strategies"""
    try:
        portfolio_manager = PortfolioManager()
        portfolio_data = await portfolio_manager.get_current_status(
            user_id=current_user["username"]
        )

        # Get real-time positions
        positions = await portfolio_manager.get_all_positions()

        # Calculate unrealized P&L
        unrealized_pnl = await portfolio_manager.calculate_unrealized_pnl()

        # Get recent trades
        recent_trades = await portfolio_manager.get_recent_trades(limit=10)

        # Strategy performance breakdown
        strategy_performance = await portfolio_manager.get_strategy_performance()

        return {
            "portfolio": {
                "total_value_usd": portfolio_data["total_value"],
                "initial_value_usd": portfolio_data["initial_value"],
                "total_return_percent": portfolio_data["total_return_percent"],
                "realized_pnl_usd": portfolio_data["realized_pnl"],
                "unrealized_pnl_usd": unrealized_pnl,
                "cash_balance_usd": portfolio_data["cash_balance"],
                "btc_holdings": portfolio_data["btc_holdings"],
                "current_btc_value_usd": portfolio_data["btc_value"],
                "margin_used": portfolio_data.get("margin_used", 0),
                "buying_power": portfolio_data.get("buying_power", 0),
                "allocation": portfolio_data["allocation"],
            },
            "positions": positions,
            "recent_trades": recent_trades,
            "strategy_performance": strategy_performance,
            "last_updated": datetime.utcnow().isoformat(),
            "status": "success",
        }

    except Exception as e:
        logger.error(f"Error getting portfolio status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get portfolio status",
        )


@router.get("/summary", response_model=Dict[str, Any])
async def get_portfolio_summary(
    current_user: dict = Depends(require_authentication),
    rate_limiter=Depends(get_strategy_rate_limiter),
):
    """Get portfolio summary with key metrics"""
    try:
        portfolio_manager = PortfolioManager()
        summary = await portfolio_manager.get_portfolio_summary(
            user_id=current_user["username"]
        )

        return {
            "summary": summary,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "success",
        }

    except Exception as e:
        logger.error(f"Error getting portfolio summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get portfolio summary",
        )


@router.get("/allocation", response_model=Dict[str, Any])
async def get_portfolio_allocation(
    current_user: dict = Depends(require_authentication),
    rate_limiter=Depends(get_strategy_rate_limiter),
):
    """Get current portfolio allocation breakdown"""
    try:
        portfolio_manager = PortfolioManager()
        allocation = await portfolio_manager.get_allocation_breakdown(
            user_id=current_user["username"]
        )

        return {
            "allocation": allocation,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "success",
        }

    except Exception as e:
        logger.error(f"Error getting portfolio allocation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get portfolio allocation",
        )
