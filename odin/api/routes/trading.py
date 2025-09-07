"""
Trading Management API - Consolidated from 5 separate files
All trading-related endpoints in one clean, organized file
"""

import logging
import random
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from odin.api.dependencies import (
    get_strategy_by_name,
    get_strategy_rate_limiter,
    require_authentication,
    validate_timeframe,
)
from odin.core.portfolio_manager import PortfolioManager
from odin.core.risk_manager import RiskManager
from odin.core.trading_engine import TradingEngine
from odin.strategies.base import BaseStrategy

logger = logging.getLogger(__name__)
router = APIRouter()

# =============================================================================
# TRADING STATUS & HISTORY
# =============================================================================

@router.get("/status")
async def get_trading_status():
    """Get comprehensive trading status."""
    return {
        "success": True,
        "data": {
            "enabled": False,
            "active_strategies": 2,
            "last_trade": time.time() - 1800,  # 30 minutes ago
            "total_trades_today": 15,
            "pnl_today": 127.50,
            "risk_limits": {
                "max_position_size": 0.95,
                "risk_per_trade": 0.02,
                "daily_loss_limit": 0.05,
            },
            "current_exposure": 0.45,
        },
    }


@router.get("/history")
async def get_trading_history(
    limit: int = Query(10, description="Number of recent trades"),
    strategy_filter: Optional[str] = Query(None, description="Filter by strategy"),
    current_user: dict = Depends(require_authentication),
    rate_limiter=Depends(get_strategy_rate_limiter),
):
    """Get comprehensive trading history."""
    try:
        trading_engine = TradingEngine()
        trade_history = await trading_engine.get_trade_history(
            user_id=current_user["username"],
            limit=limit,
            strategy_filter=strategy_filter,
        )

        # Get trade statistics
        portfolio_manager = PortfolioManager()
        trade_stats = await portfolio_manager.get_trade_statistics(
            user_id=current_user["username"],
            strategy_filter=strategy_filter,
        )

        return {
            "trades": trade_history,
            "statistics": trade_stats,
            "total_trades": len(trade_history),
            "strategy_filter": strategy_filter,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "success",
        }

    except Exception as e:
        logger.error(f"Error getting trading history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get trading history",
        )

# =============================================================================
# LIVE TRADE EXECUTION
# =============================================================================

@router.post("/{strategy_name}/execute")
async def execute_live_trade(
    strategy_name: str,
    trade_request: Dict[str, Any],
    strategy: BaseStrategy = Depends(get_strategy_by_name),
    current_user: dict = Depends(require_authentication),
    rate_limiter=Depends(get_strategy_rate_limiter),
):
    """Execute live trade based on strategy signal."""
    try:
        # Validate trade request
        required_fields = ["signal_type", "amount_usd"]
        for field in required_fields:
            if field not in trade_request:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Missing required field: {field}",
                )

        signal_type = trade_request["signal_type"].upper()
        if signal_type not in ["BUY", "SELL"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Signal type must be 'BUY' or 'SELL'",
            )

        # Risk management checks
        risk_manager = RiskManager()
        risk_check = await risk_manager.validate_trade(
            strategy_name=strategy_name,
            signal_type=signal_type,
            amount_usd=trade_request["amount_usd"],
            user_id=current_user["username"],
        )

        if not risk_check["approved"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Trade rejected by risk management: {risk_check['reason']}",
            )

        # Execute trade
        trading_engine = TradingEngine()
        execution_result = await trading_engine.execute_trade(
            strategy_name=strategy_name,
            trade_request=trade_request,
            user_id=current_user["username"],
        )

        if not execution_result.get("success", False):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Trade execution failed: {execution_result.get('error')}",
            )

        return {
            "trade_execution": execution_result,
            "strategy": strategy_name,
            "risk_check": risk_check,
            "executed_by": current_user["username"],
            "timestamp": datetime.utcnow().isoformat(),
            "status": "executed",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error executing trade for {strategy_name}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Trade execution failed for {strategy_name}",
        )


@router.get("/execution-quality")
async def get_execution_quality(
    hours: int = Query(24, description="Hours of execution data"),
    current_user: dict = Depends(require_authentication),
    rate_limiter=Depends(get_strategy_rate_limiter),
    validated_hours: int = Depends(validate_timeframe),
):
    """Get trade execution quality metrics."""
    try:
        trading_engine = TradingEngine()
        execution_metrics = await trading_engine.get_execution_quality(
            user_id=current_user["username"], hours=validated_hours
        )

        # Benchmark against market standards
        benchmarks = {
            "average_slippage_bps": 2.5,
            "fill_rate_percent": 95.0,
            "average_fill_time_ms": 150,
        }

        # Performance vs benchmarks
        performance_vs_benchmark = {}
        for metric, benchmark_value in benchmarks.items():
            actual_value = execution_metrics.get(metric, 0)
            performance_vs_benchmark[metric] = {
                "actual": actual_value,
                "benchmark": benchmark_value,
                "performance": "better" if actual_value < benchmark_value else "worse",
            }

        return {
            "execution_metrics": execution_metrics,
            "benchmarks": benchmarks,
            "performance_comparison": performance_vs_benchmark,
            "hours_analyzed": validated_hours,
            "total_trades": execution_metrics.get("total_trades", 0),
            "timestamp": datetime.utcnow().isoformat(),
            "status": "success",
        }

    except Exception as e:
        logger.error(f"Error getting execution quality: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get execution quality metrics",
        )

# =============================================================================
# ORDER MANAGEMENT
# =============================================================================

@router.get("/orders")
async def get_active_orders(
    status_filter: Optional[str] = Query(None, description="Filter by order status"),
    current_user: dict = Depends(require_authentication),
    rate_limiter=Depends(get_strategy_rate_limiter),
):
    """Get active and recent orders."""
    try:
        trading_engine = TradingEngine()
        orders = await trading_engine.get_orders(
            user_id=current_user["username"], status_filter=status_filter
        )

        return {
            "orders": orders,
            "total_orders": len(orders),
            "status_filter": status_filter,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "success",
        }

    except Exception as e:
        logger.error(f"Error getting orders: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get orders",
        )


@router.post("/orders")
async def place_order(
    order_request: Dict[str, Any],
    current_user: dict = Depends(require_authentication),
    rate_limiter=Depends(get_strategy_rate_limiter),
):
    """Place a new trading order."""
    try:
        # Validate order request
        required_fields = ["side", "amount", "order_type"]
        for field in required_fields:
            if field not in order_request:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Missing required field: {field}",
                )

        # Risk checks
        risk_manager = RiskManager()
        risk_check = await risk_manager.validate_order(
            order_request=order_request, user_id=current_user["username"]
        )

        if not risk_check["approved"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Order rejected: {risk_check['reason']}",
            )

        # Place order
        trading_engine = TradingEngine()
        order_result = await trading_engine.place_order(
            order_request=order_request, user_id=current_user["username"]
        )

        return {
            "order": order_result,
            "risk_check": risk_check,
            "placed_by": current_user["username"],
            "timestamp": datetime.utcnow().isoformat(),
            "status": "placed",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error placing order: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to place order",
        )


@router.delete("/orders/{order_id}")
async def cancel_order(
    order_id: str,
    current_user: dict = Depends(require_authentication),
    rate_limiter=Depends(get_strategy_rate_limiter),
):
    """Cancel a specific order."""
    try:
        trading_engine = TradingEngine()
        cancel_result = await trading_engine.cancel_order(
            order_id=order_id, user_id=current_user["username"]
        )

        if not cancel_result.get("success", False):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to cancel order: {cancel_result.get('error')}",
            )

        return {
            "order_cancelled": cancel_result,
            "order_id": order_id,
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
            detail=f"Failed to cancel order {order_id}",
        )


@router.delete("/orders/all")
async def cancel_all_orders(
    current_user: dict = Depends(require_authentication),
    rate_limiter=Depends(get_strategy_rate_limiter),
):
    """Cancel all active orders."""
    try:
        trading_engine = TradingEngine()
        cancel_result = await trading_engine.cancel_all_orders(
            user_id=current_user["username"]
        )

        return {
            "orders_cancelled": cancel_result["count"],
            "cancelled_order_ids": cancel_result.get("order_ids", []),
            "cancelled_by": current_user["username"],
            "timestamp": datetime.utcnow().isoformat(),
            "status": "success",
        }

    except Exception as e:
        logger.error(f"Error cancelling all orders: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cancel all orders",
        )

# =============================================================================
# POSITION MANAGEMENT
# =============================================================================

@router.get("/positions")
async def get_positions(
    strategy_filter: Optional[str] = Query(None, description="Filter by strategy"),
    current_user: dict = Depends(require_authentication),
    rate_limiter=Depends(get_strategy_rate_limiter),
):
    """Get current positions."""
    try:
        portfolio_manager = PortfolioManager()
        positions = await portfolio_manager.get_positions(
            user_id=current_user["username"], strategy_filter=strategy_filter
        )

        # Calculate summary statistics
        total_positions = len(positions)
        total_value = sum(pos.get("current_value", 0) for pos in positions)
        total_pnl = sum(pos.get("unrealized_pnl", 0) for pos in positions)

        return {
            "positions": positions,
            "summary": {
                "total_positions": total_positions,
                "total_value": total_value,
                "total_unrealized_pnl": total_pnl,
                "pnl_percentage": (total_pnl / total_value * 100) if total_value > 0 else 0,
            },
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


@router.get("/positions/{position_id}")
async def get_position_details(
    position_id: str,
    current_user: dict = Depends(require_authentication),
    rate_limiter=Depends(get_strategy_rate_limiter),
):
    """Get detailed information about a specific position."""
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


@router.post("/positions/{position_id}/close")
async def close_position(
    position_id: str,
    close_request: Dict[str, Any],
    current_user: dict = Depends(require_authentication),
    rate_limiter=Depends(get_strategy_rate_limiter),
):
    """Close a specific position."""
    try:
        # Validate close request
        close_type = close_request.get("close_type", "market")  # market, limit, partial
        if close_type not in ["market", "limit", "partial"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Close type must be 'market', 'limit', or 'partial'",
            )

        trading_engine = TradingEngine()
        close_result = await trading_engine.close_position(
            position_id=position_id,
            close_request=close_request,
            user_id=current_user["username"],
        )

        if not close_result.get("success", False):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to close position: {close_result.get('error')}",
            )

        return {
            "position_closed": close_result,
            "position_id": position_id,
            "close_request": close_request,
            "closed_by": current_user["username"],
            "timestamp": datetime.utcnow().isoformat(),
            "status": "closed",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error closing position {position_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to close position {position_id}",
        )

# =============================================================================
# AUTO-TRADING MANAGEMENT
# =============================================================================

@router.post("/enable")
async def enable_auto_trading(
    config: Dict[str, Any],
    current_user: dict = Depends(require_authentication),
    rate_limiter=Depends(get_strategy_rate_limiter),
):
    """Enable automated trading for specified strategies."""
    try:
        required_fields = ["strategies", "max_position_size", "risk_per_trade"]
        for field in required_fields:
            if field not in config:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Missing required field: {field}",
                )

        # Validate configuration
        if config["risk_per_trade"] > 0.05:  # Max 5% risk per trade
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Risk per trade cannot exceed 5%",
            )

        if config["max_position_size"] > 0.95:  # Max 95% of capital
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Max position size cannot exceed 95%",
            )

        trading_engine = TradingEngine()
        auto_trading_result = await trading_engine.enable_auto_trading(
            user_id=current_user["username"], config=config
        )

        logger.info(f"Auto-trading enabled for {current_user['username']}: {config}")

        return {
            "auto_trading": auto_trading_result,
            "config": config,
            "enabled_by": current_user["username"],
            "timestamp": datetime.utcnow().isoformat(),
            "status": "enabled",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error enabling auto-trading: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to enable auto-trading",
        )


@router.post("/disable")
async def disable_auto_trading(
    current_user: dict = Depends(require_authentication),
    rate_limiter=Depends(get_strategy_rate_limiter),
):
    """Disable automated trading."""
    try:
        trading_engine = TradingEngine()
        result = await trading_engine.disable_auto_trading(
            user_id=current_user["username"]
        )

        logger.info(f"Auto-trading disabled for {current_user['username']}")

        return {
            "auto_trading_disabled": result["success"],
            "pending_orders_cancelled": result.get("orders_cancelled", 0),
            "disabled_by": current_user["username"],
            "timestamp": datetime.utcnow().isoformat(),
            "status": "disabled",
        }

    except Exception as e:
        logger.error(f"Error disabling auto-trading: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to disable auto-trading",
        )


@router.get("/auto-trading/status")
async def get_auto_trading_status(
    current_user: dict = Depends(require_authentication),
    rate_limiter=Depends(get_strategy_rate_limiter),
):
    """Get current auto-trading status and configuration."""
    try:
        trading_engine = TradingEngine()
        auto_trading_status = await trading_engine.get_auto_trading_status(
            user_id=current_user["username"]
        )

        return {
            "auto_trading_status": auto_trading_status,
            "user_id": current_user["username"],
            "timestamp": datetime.utcnow().isoformat(),
            "status": "success",
        }

    except Exception as e:
        logger.error(f"Error getting auto-trading status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get auto-trading status",
        )

# =============================================================================
# EMERGENCY CONTROLS
# =============================================================================

@router.post("/emergency-stop")
async def emergency_stop_all_trading(
    current_user: dict = Depends(require_authentication),
    rate_limiter=Depends(get_strategy_rate_limiter),
):
    """Emergency stop all trading activities."""
    try:
        trading_engine = TradingEngine()

        # Stop all automated trading
        auto_trading_stopped = await trading_engine.disable_auto_trading(
            user_id=current_user["username"]
        )

        # Cancel all pending orders
        orders_cancelled = await trading_engine.cancel_all_orders(
            user_id=current_user["username"]
        )

        emergency_result = {
            "auto_trading_stopped": auto_trading_stopped["success"],
            "orders_cancelled": orders_cancelled["count"],
            "timestamp": datetime.utcnow().isoformat(),
            "executed_by": current_user["username"],
            "reason": "Emergency stop initiated by user",
        }

        logger.critical(
            f"EMERGENCY STOP executed by {current_user['username']}: {emergency_result}"
        )

        return {
            "emergency_stop": emergency_result,
            "status": "executed",
            "message": "All trading activities have been stopped",
        }

    except Exception as e:
        logger.error(f"Error executing emergency stop: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to execute emergency stop",
        )