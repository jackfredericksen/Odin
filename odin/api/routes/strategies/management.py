# odin/api/routes/strategies/management.py
"""
Strategy management endpoints
"""

import logging
from datetime import datetime
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, status

from odin.api.dependencies import (
    get_strategy_by_name,
    get_strategy_rate_limiter,
    require_authentication,
)
from odin.strategies.base import BaseStrategy

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/{strategy_name}/enable", response_model=Dict[str, Any])
async def enable_strategy(
    strategy_name: str,
    config: Dict[str, Any],
    strategy: BaseStrategy = Depends(get_strategy_by_name),
    current_user: dict = Depends(require_authentication),
    rate_limiter=Depends(get_strategy_rate_limiter),
):
    """Enable a trading strategy"""
    try:
        # Validate configuration
        required_fields = ["allocation_percent"]
        for field in required_fields:
            if field not in config:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Missing required field: {field}",
                )

        if not 0 < config["allocation_percent"] <= 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Allocation percent must be between 0 and 100",
            )

        enable_result = await strategy.enable(
            user_id=current_user["username"], config=config
        )

        if not enable_result.get("success", False):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to enable strategy: {enable_result.get('error')}",
            )

        logger.info(f"Strategy {strategy_name} enabled by {current_user['username']}")

        return {
            "strategy": strategy_name,
            "enabled": True,
            "config": config,
            "enabled_by": current_user["username"],
            "timestamp": datetime.utcnow().isoformat(),
            "status": "success",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error enabling strategy {strategy_name}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to enable {strategy_name} strategy",
        )


@router.post("/{strategy_name}/disable", response_model=Dict[str, Any])
async def disable_strategy(
    strategy_name: str,
    strategy: BaseStrategy = Depends(get_strategy_by_name),
    current_user: dict = Depends(require_authentication),
    rate_limiter=Depends(get_strategy_rate_limiter),
):
    """Disable a trading strategy"""
    try:
        disable_result = await strategy.disable(user_id=current_user["username"])

        if not disable_result.get("success", False):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to disable strategy: {disable_result.get('error')}",
            )

        logger.info(f"Strategy {strategy_name} disabled by {current_user['username']}")

        return {
            "strategy": strategy_name,
            "enabled": False,
            "disabled_by": current_user["username"],
            "pending_orders_cancelled": disable_result.get("orders_cancelled", 0),
            "timestamp": datetime.utcnow().isoformat(),
            "status": "success",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error disabling strategy {strategy_name}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to disable {strategy_name} strategy",
        )


@router.put("/{strategy_name}/config", response_model=Dict[str, Any])
async def update_strategy_config(
    strategy_name: str,
    config_update: Dict[str, Any],
    strategy: BaseStrategy = Depends(get_strategy_by_name),
    current_user: dict = Depends(require_authentication),
    rate_limiter=Depends(get_strategy_rate_limiter),
):
    """Update strategy configuration"""
    try:
        update_result = await strategy.update_config(
            config_update=config_update, user_id=current_user["username"]
        )

        if not update_result.get("success", False):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to update config: {update_result.get('error')}",
            )

        return {
            "strategy": strategy_name,
            "config_updated": config_update,
            "updated_by": current_user["username"],
            "timestamp": datetime.utcnow().isoformat(),
            "status": "success",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating config for {strategy_name}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update config for {strategy_name}",
        )
