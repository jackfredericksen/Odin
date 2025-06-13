# odin/api/routes/trading/orders.py
"""
Order management endpoints
"""

import logging
from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from odin.api.dependencies import get_strategy_rate_limiter, require_authentication
from odin.core.trading_engine import TradingEngine

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/active", response_model=Dict[str, Any])
async def get_active_orders(
    strategy_filter: Optional[str] = Query(None, description="Filter by strategy"),
    current_user: dict = Depends(require_authentication),
    rate_limiter=Depends(get_strategy_rate_limiter),
):
    """Get all active trading orders"""
    try:
        trading_engine = TradingEngine()
        active_orders = await trading_engine.get_active_orders(
            user_id=current_user["username"], strategy=strategy_filter
        )

        # Categorize orders
        order_categories = {
            "pending": [o for o in active_orders if o["status"] == "PENDING"],
            "partially_filled": [
                o for o in active_orders if o["status"] == "PARTIALLY_FILLED"
            ],
            "stop_orders": [
                o
                for o in active_orders
                if o["order_type"] in ["STOP_LOSS", "TAKE_PROFIT"]
            ],
            "limit_orders": [o for o in active_orders if o["order_type"] == "LIMIT"],
        }

        return {
            "active_orders": active_orders,
            "categories": order_categories,
            "total_count": len(active_orders),
            "strategy_filter": strategy_filter,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "success",
        }

    except Exception as e:
        logger.error(f"Error getting active orders: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get active orders",
        )


@router.post("/{order_id}/cancel", response_model=Dict[str, Any])
async def cancel_order(
    order_id: str,
    current_user: dict = Depends(require_authentication),
    rate_limiter=Depends(get_strategy_rate_limiter),
):
    """Cancel an active trading order"""
    try:
        trading_engine = TradingEngine()
        cancellation_result = await trading_engine.cancel_order(
            order_id=order_id, user_id=current_user["username"]
        )

        if not cancellation_result["success"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to cancel order: {cancellation_result['error']}",
            )

        logger.info(f"Order {order_id} cancelled by {current_user['username']}")

        return {
            "order_id": order_id,
            "cancellation": cancellation_result,
            "cancelled_by": current_user["username"],
            "timestamp": datetime.utcnow().isoformat(),
            "status": "cancelled",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling order {order_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cancel order",
        )


@router.post("/stop-loss/update", response_model=Dict[str, Any])
async def update_stop_loss(
    update_request: Dict[str, Any],
    current_user: dict = Depends(require_authentication),
    rate_limiter=Depends(get_strategy_rate_limiter),
):
    """Update stop-loss orders for active positions"""
    try:
        required_fields = ["position_id", "new_stop_price"]
        for field in required_fields:
            if field not in update_request:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Missing required field: {field}",
                )

        trading_engine = TradingEngine()
        update_result = await trading_engine.update_stop_loss(
            position_id=update_request["position_id"],
            new_stop_price=update_request["new_stop_price"],
            user_id=current_user["username"],
        )

        if not update_result["success"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to update stop-loss: {update_result['error']}",
            )

        logger.info(f"Stop-loss updated for position {update_request['position_id']}")

        return {
            "position_id": update_request["position_id"],
            "update_result": update_result,
            "new_stop_price": update_request["new_stop_price"],
            "updated_by": current_user["username"],
            "timestamp": datetime.utcnow().isoformat(),
            "status": "updated",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating stop-loss: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update stop-loss",
        )


@router.get("/history", response_model=Dict[str, Any])
async def get_order_history(
    limit: int = Query(50, description="Number of orders to return"),
    status_filter: Optional[str] = Query(None, description="Filter by order status"),
    current_user: dict = Depends(require_authentication),
    rate_limiter=Depends(get_strategy_rate_limiter),
):
    """Get order history"""
    try:
        trading_engine = TradingEngine()
        order_history = await trading_engine.get_order_history(
            user_id=current_user["username"], limit=limit, status_filter=status_filter
        )

        return {
            "order_history": order_history,
            "count": len(order_history),
            "limit": limit,
            "status_filter": status_filter,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "success",
        }

    except Exception as e:
        logger.error(f"Error getting order history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get order history",
        )
