# odin/api/routes/trading/automation.py
"""
Auto-trading endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any
import logging
from datetime import datetime

from odin.api.dependencies import (
    get_strategy_rate_limiter,
    require_authentication
)
from odin.core.trading_engine import TradingEngine

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/enable", response_model=Dict[str, Any])
async def enable_auto_trading(
    config: Dict[str, Any],
    current_user: dict = Depends(require_authentication),
    rate_limiter = Depends(get_strategy_rate_limiter)
):
    """Enable automated trading for specified strategies"""
    try:
        required_fields = ["strategies", "max_position_size", "risk_per_trade"]
        for field in required_fields:
            if field not in config:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Missing required field: {field}"
                )
        
        # Validate configuration
        if config["risk_per_trade"] > 0.05:  # Max 5% risk per trade
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Risk per trade cannot exceed 5%"
            )
        
        if config["max_position_size"] > 0.95:  # Max 95% of capital
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Max position size cannot exceed 95%"
            )
        
        trading_engine = TradingEngine()
        auto_trading_result = await trading_engine.enable_auto_trading(
            user_id=current_user["username"],
            config=config
        )
        
        logger.info(f"Auto-trading enabled for {current_user['username']}: {config}")
        
        return {
            "auto_trading": auto_trading_result,
            "config": config,
            "enabled_by": current_user["username"],
            "timestamp": datetime.utcnow().isoformat(),
            "status": "enabled"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error enabling auto-trading: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to enable auto-trading"
        )


@router.post("/disable", response_model=Dict[str, Any])
async def disable_auto_trading(
    current_user: dict = Depends(require_authentication),
    rate_limiter = Depends(get_strategy_rate_limiter)
):
    """Disable automated trading"""
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
            "status": "disabled"
        }
        
    except Exception as e:
        logger.error(f"Error disabling auto-trading: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to disable auto-trading"
        )


@router.get("/status", response_model=Dict[str, Any])
async def get_auto_trading_status(
    current_user: dict = Depends(require_authentication),
    rate_limiter = Depends(get_strategy_rate_limiter)
):
    """Get current auto-trading status and configuration"""
    try:
        trading_engine = TradingEngine()
        auto_trading_status = await trading_engine.get_auto_trading_status(
            user_id=current_user["username"]
        )
        
        return {
            "auto_trading_status": auto_trading_status,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "success"
        }
        
    except Exception as e:
        logger.error(f"Error getting auto-trading status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get auto-trading status"
        )


@router.put("/config", response_model=Dict[str, Any])
async def update_auto_trading_config(
    config_update: Dict[str, Any],
    current_user: dict = Depends(require_authentication),
    rate_limiter = Depends(get_strategy_rate_limiter)
):
    """Update auto-trading configuration"""
    try:
        trading_engine = TradingEngine()
        
        # Validate updated configuration
        if "risk_per_trade" in config_update and config_update["risk_per_trade"] > 0.05:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Risk per trade cannot exceed 5%"
            )
        
        update_result = await trading_engine.update_auto_trading_config(
            user_id=current_user["username"],
            config_update=config_update
        )
        
        if not update_result["success"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to update config: {update_result['error']}"
            )
        
        return {
            "config_updated": config_update,
            "update_result": update_result,
            "updated_by": current_user["username"],
            "timestamp": datetime.utcnow().isoformat(),
            "status": "success"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating auto-trading config: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update auto-trading config"
        )