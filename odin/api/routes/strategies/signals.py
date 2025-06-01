# odin/api/routes/strategies/signals.py
"""
Strategy signals endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import Dict, Any, Optional
import logging
from datetime import datetime

from odin.strategies.base import BaseStrategy
from odin.api.dependencies import (
    get_strategy_by_name,
    get_strategy_rate_limiter,
    validate_timeframe
)
from odin.core.trading_engine import TradingEngine

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/{strategy_name}/{hours}", response_model=Dict[str, Any])
async def get_strategy_signals(
    strategy_name: str,
    hours: int,
    signal_type: Optional[str] = Query(None, description="Filter by signal type (BUY/SELL)"),
    strategy: BaseStrategy = Depends(get_strategy_by_name),
    rate_limiter = Depends(get_strategy_rate_limiter),
    validated_hours: int = Depends(validate_timeframe)
):
    """Get historical signals from strategy with execution status"""
    try:
        signals = await strategy.get_historical_signals(
            hours=validated_hours,
            signal_type=signal_type
        )
        
        if not signals:
            return {
                "strategy": strategy_name,
                "signals": [],
                "count": 0,
                "hours": validated_hours,
                "signal_type_filter": signal_type,
                "status": "success"
            }
        
        # Enhance signals with execution data
        trading_engine = TradingEngine()
        enhanced_signals = []
        
        for signal in signals:
            # Check if signal was executed
            execution_data = await trading_engine.get_signal_execution(
                strategy=strategy_name,
                signal_id=signal.get("id"),
                timestamp=signal.get("timestamp")
            )
            
            enhanced_signal = {
                **signal,
                "executed": execution_data.get("executed", False),
                "execution_price": execution_data.get("execution_price"),
                "execution_time": execution_data.get("execution_time"),
                "trade_id": execution_data.get("trade_id"),
                "profit_loss": execution_data.get("profit_loss"),
                "fees_paid": execution_data.get("fees_paid")
            }
            enhanced_signals.append(enhanced_signal)
        
        # Calculate signal performance statistics
        executed_signals = [s for s in enhanced_signals if s["executed"]]
        profitable_signals = [s for s in executed_signals if s.get("profit_loss", 0) > 0]
        
        signal_stats = {
            "total_signals": len(signals),
            "executed_signals": len(executed_signals),
            "execution_rate": len(executed_signals) / len(signals) * 100 if signals else 0,
            "profitable_signals": len(profitable_signals),
            "win_rate": len(profitable_signals) / len(executed_signals) * 100 if executed_signals else 0,
            "total_pnl": sum(s.get("profit_loss", 0) for s in executed_signals),
            "total_fees": sum(s.get("fees_paid", 0) for s in executed_signals)
        }
        
        return {
            "strategy": strategy_name,
            "signals": enhanced_signals,
            "signal_stats": signal_stats,
            "count": len(enhanced_signals),
            "hours": validated_hours,
            "signal_type_filter": signal_type,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "success"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting signals for {strategy_name}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get signals for {strategy_name} strategy"
        )


@router.get("/alerts", response_model=Dict[str, Any])
async def get_strategy_alerts(
    active_only: bool = Query(True, description="Show only active alerts"),
    severity: Optional[str] = Query(None, description="Filter by severity (low, medium, high, critical)"),
    rate_limiter = Depends(get_strategy_rate_limiter)
):
    """Get current strategy alerts and notifications"""
    try:
        # This would integrate with a real alerting system
        alerts = [
            {
                "id": "alert_001",
                "strategy": "ma",
                "type": "signal_generated",
                "severity": "high",
                "message": "Strong BUY signal detected",
                "timestamp": datetime.utcnow().isoformat(),
                "active": True,
                "requires_action": True
            },
            {
                "id": "alert_002", 
                "strategy": "rsi",
                "type": "overbought_condition",
                "severity": "medium",
                "message": "RSI indicates overbought condition",
                "timestamp": datetime.utcnow().isoformat(),
                "active": True,
                "requires_action": False
            }
        ]
        
        # Filter alerts
        if active_only:
            alerts = [a for a in alerts if a.get("active", False)]
        
        if severity:
            alerts = [a for a in alerts if a.get("severity") == severity]
        
        # Categorize alerts
        alert_categories = {
            "critical": [a for a in alerts if a.get("severity") == "critical"],
            "high": [a for a in alerts if a.get("severity") == "high"], 
            "medium": [a for a in alerts if a.get("severity") == "medium"],
            "low": [a for a in alerts if a.get("severity") == "low"]
        }
        
        return {
            "alerts": alerts,
            "categories": alert_categories,
            "total_count": len(alerts),
            "active_only": active_only,
            "severity_filter": severity,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "success"
        }
        
    except Exception as e:
        logger.error(f"Error getting strategy alerts: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get strategy alerts"
        )


@router.post("/webhook", response_model=Dict[str, Any])
async def strategy_webhook(
    webhook_data: Dict[str, Any],
    strategy_name: Optional[str] = None,
    rate_limiter = Depends(get_strategy_rate_limiter)
):
    """Webhook endpoint for external strategy signals"""
    try:
        # Validate webhook data
        required_fields = ["signal", "price", "timestamp"]
        for field in required_fields:
            if field not in webhook_data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Missing required field: {field}"
                )
        
        # Process webhook signal
        webhook_result = {
            "received": True,
            "signal": webhook_data["signal"],
            "price": webhook_data["price"],
            "timestamp": webhook_data["timestamp"],
            "strategy_filter": strategy_name,
            "processed_at": datetime.utcnow().isoformat()
        }
        
        # Log webhook for audit
        logger.info(f"Webhook received: {webhook_data}")
        
        return {
            "webhook": webhook_result,
            "status": "success",
            "message": "Webhook processed successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Webhook processing error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process webhook"
        )