# odin/api/routes/trading/execution.py
"""
Live trade execution endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import Dict, Any
import logging
from datetime import datetime

from odin.strategies.base import BaseStrategy
from odin.api.dependencies import (
    get_strategy_by_name,
    get_strategy_rate_limiter,
    require_authentication,
    validate_timeframe
)
from odin.core.trading_engine import TradingEngine
from odin.core.risk_manager import RiskManager

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/{strategy_name}/execute", response_model=Dict[str, Any])
async def execute_live_trade(
    strategy_name: str,
    trade_request: Dict[str, Any],
    strategy: BaseStrategy = Depends(get_strategy_by_name),
    current_user: dict = Depends(require_authentication),
    rate_limiter = Depends(get_strategy_rate_limiter)
):
    """Execute live trade based on strategy signal"""
    try:
        # Validate trade request
        required_fields = ["signal_type", "amount_usd"]
        for field in required_fields:
            if field not in trade_request:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Missing required field: {field}"
                )
        
        signal_type = trade_request["signal_type"].upper()
        if signal_type not in ["BUY", "SELL"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Signal type must be 'BUY' or 'SELL'"
            )
        
        # Risk management checks
        risk_manager = RiskManager()
        risk_check = await risk_manager.validate_trade(
            strategy=strategy_name,
            signal_type=signal_type,
            amount_usd=trade_request["amount_usd"],
            user_id=current_user["username"]
        )
        
        if not risk_check["approved"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Trade rejected by risk management: {risk_check['reason']}"
            )
        
        # Execute live trade
        trading_engine = TradingEngine()
        trade_result = await trading_engine.execute_trade(
            strategy=strategy_name,
            signal_type=signal_type,
            amount_usd=trade_request["amount_usd"],
            user_id=current_user["username"],
            notes=trade_request.get("notes", ""),
            order_type=trade_request.get("order_type", "MARKET"),
            limit_price=trade_request.get("limit_price"),
            stop_loss=trade_request.get("stop_loss"),
            take_profit=trade_request.get("take_profit")
        )
        
        logger.info(f"Live trade executed: {trade_result}")
        
        return {
            "strategy": strategy_name,
            "trade": trade_result,
            "risk_assessment": risk_check,
            "execution_time": datetime.utcnow().isoformat(),
            "user": current_user["username"],
            "status": "executed" if trade_result["success"] else "failed"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Live trade execution failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to execute live trade"
        )


@router.get("/execution-quality", response_model=Dict[str, Any])
async def get_execution_quality(
    hours: int = Query(24, description="Hours of execution data"),
    current_user: dict = Depends(require_authentication),
    rate_limiter = Depends(get_strategy_rate_limiter),
    validated_hours: int = Depends(validate_timeframe)
):
    """Get trade execution quality metrics"""
    try:
        trading_engine = TradingEngine()
        execution_metrics = await trading_engine.get_execution_quality(
            user_id=current_user["username"],
            hours=validated_hours
        )
        
        # Benchmark against market standards
        benchmarks = {
            "average_slippage_bps": 2.5,
            "fill_rate_percent": 95.0,
            "average_fill_time_ms": 150
        }
        
        # Performance vs benchmarks
        performance_vs_benchmark = {}
        for metric, benchmark_value in benchmarks.items():
            actual_value = execution_metrics.get(metric, 0)
            performance_vs_benchmark[metric] = {
                "actual": actual_value,
                "benchmark": benchmark_value,
                "performance": "better" if actual_value < benchmark_value else "worse"
            }
        
        return {
            "execution_metrics": execution_metrics,
            "benchmarks": benchmarks,
            "performance_comparison": performance_vs_benchmark,
            "hours_analyzed": validated_hours,
            "total_trades": execution_metrics.get("total_trades", 0),
            "timestamp": datetime.utcnow().isoformat(),
            "status": "success"
        }
        
    except Exception as e:
        logger.error(f"Error getting execution quality: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get execution quality metrics"
        )


@router.post("/emergency-stop", response_model=Dict[str, Any])
async def emergency_stop_all_trading(
    current_user: dict = Depends(require_authentication),
    rate_limiter = Depends(get_strategy_rate_limiter)
):
    """Emergency stop all trading activities"""
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
            "reason": "Emergency stop initiated by user"
        }
        
        logger.critical(f"EMERGENCY STOP executed by {current_user['username']}: {emergency_result}")
        
        return {
            "emergency_stop": emergency_result,
            "status": "executed",
            "message": "All trading activities have been stopped"
        }
        
    except Exception as e:
        logger.error(f"Error executing emergency stop: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to execute emergency stop"
        )