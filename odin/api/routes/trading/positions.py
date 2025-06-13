# odin/api/routes/trading/positions.py
"""
Position management endpoints
"""

import logging
from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from odin.api.dependencies import get_strategy_rate_limiter, require_authentication
from odin.core.portfolio_manager import PortfolioManager
from odin.core.trading_engine import TradingEngine

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/", response_model=Dict[str, Any])
async def get_all_positions(
    strategy_filter: Optional[str] = Query(None, description="Filter by strategy"),
    current_user: dict = Depends(require_authentication),
    rate_limiter=Depends(get_strategy_rate_limiter),
):
    """Get all current positions"""
    try:
        portfolio_manager = PortfolioManager()
        positions = await portfolio_manager.get_all_positions(
            user_id=current_user["username"], strategy_filter=strategy_filter
        )

        # Calculate total unrealized P&L
        total_unrealized_pnl = sum(pos.get("unrealized_pnl", 0) for pos in positions)

        # Categorize positions
        position_categories = {
            "profitable": [p for p in positions if p.get("unrealized_pnl", 0) > 0],
            "losing": [p for p in positions if p.get("unrealized_pnl", 0) < 0],
            "long": [p for p in positions if p.get("side") == "LONG"],
            "short": [p for p in positions if p.get("side") == "SHORT"],
        }

        return {
            "positions": positions,
            "categories": position_categories,
            "total_count": len(positions),
            "total_unrealized_pnl": total_unrealized_pnl,
            "strategy_filter": strategy_filter,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "success",
        }

    except Exception as e:
        logger.error(f"Error getting positions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get positions",
        )


@router.get("/{position_id}", response_model=Dict[str, Any])
async def get_position_details(
    position_id: str,
    current_user: dict = Depends(require_authentication),
    rate_limiter=Depends(get_strategy_rate_limiter),
):
    """Get detailed information about a specific position"""
    try:
        portfolio_manager = PortfolioManager()
        position_details = await portfolio_manager.get_position_details(
            position_id=position_id, user_id=current_user["username"]
        )

        if not position_details:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Position {position_id} not found",
            )

        # Get related orders for this position
        trading_engine = TradingEngine()
        related_orders = await trading_engine.get_position_orders(
            position_id=position_id
        )

        return {
            "position": position_details,
            "related_orders": related_orders,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "success",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting position details for {position_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get position details for {position_id}",
        )


@router.post("/{position_id}/close", response_model=Dict[str, Any])
async def close_position(
    position_id: str,
    close_request: Dict[str, Any],
    current_user: dict = Depends(require_authentication),
    rate_limiter=Depends(get_strategy_rate_limiter),
):
    """Close a specific position"""
    try:
        trading_engine = TradingEngine()

        # Validate close request
        close_percentage = close_request.get("percentage", 100)
        if not 0 < close_percentage <= 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Close percentage must be between 0 and 100",
            )

        close_result = await trading_engine.close_position(
            position_id=position_id,
            percentage=close_percentage,
            order_type=close_request.get("order_type", "MARKET"),
            limit_price=close_request.get("limit_price"),
            user_id=current_user["username"],
        )

        if not close_result["success"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to close position: {close_result['error']}",
            )

        logger.info(f"Position {position_id} closed by {current_user['username']}")

        return {
            "position_id": position_id,
            "close_result": close_result,
            "close_percentage": close_percentage,
            "closed_by": current_user["username"],
            "timestamp": datetime.utcnow().isoformat(),
            "status": "success",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error closing position {position_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to close position {position_id}",
        )


@router.post("/close-all", response_model=Dict[str, Any])
async def close_all_positions(
    close_request: Dict[str, Any],
    current_user: dict = Depends(require_authentication),
    rate_limiter=Depends(get_strategy_rate_limiter),
):
    """Close all positions (emergency function)"""
    try:
        portfolio_manager = PortfolioManager()

        # Safety check - require confirmation
        if not close_request.get("confirm", False):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Confirmation required to close all positions",
            )

        close_result = await portfolio_manager.close_all_positions(
            user_id=current_user["username"],
            strategy_filter=close_request.get("strategy_filter"),
        )

        logger.warning(
            f"All positions closed by {current_user['username']}: {close_result}"
        )

        return {
            "close_all_result": close_result,
            "positions_closed": close_result.get("positions_closed", 0),
            "total_realized_pnl": close_result.get("total_realized_pnl", 0),
            "closed_by": current_user["username"],
            "timestamp": datetime.utcnow().isoformat(),
            "status": "success",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error closing all positions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to close all positions",
        )
