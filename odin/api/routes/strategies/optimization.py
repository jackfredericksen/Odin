"""
Strategy optimization endpoints
"""

import logging
from datetime import datetime
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, Query, status

from odin.api.dependencies import (
    get_strategy_by_name,
    get_strategy_rate_limiter,
    require_authentication,
    validate_timeframe,
)
from odin.strategies.base import BaseStrategy

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/{strategy_name}", response_model=Dict[str, Any])
async def optimize_strategy_parameters(
    strategy_name: str,
    optimization_config: Dict[str, Any],
    hours: int = Query(168, description="Hours of data for optimization"),
    strategy: BaseStrategy = Depends(get_strategy_by_name),
    current_user: dict = Depends(require_authentication),
    rate_limiter=Depends(get_strategy_rate_limiter),
    validated_hours: int = Depends(validate_timeframe),
):
    """Optimize strategy parameters using historical data and live performance"""
    try:
        optimization_result = await strategy.optimize_parameters(
            config=optimization_config,
            hours=validated_hours,
            include_live_performance=True,
            user_id=current_user["username"],
        )

        if not optimization_result or "error" in optimization_result:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=optimization_result.get(
                    "error", "Parameter optimization failed"
                ),
            )

        # Apply optimized parameters if requested
        if optimization_config.get("auto_apply", False):
            apply_result = await strategy.apply_optimized_parameters(
                optimized_params=optimization_result["best_parameters"],
                user_id=current_user["username"],
            )
            optimization_result["applied"] = apply_result

        return {
            "strategy": strategy_name,
            "optimization": optimization_result,
            "config": optimization_config,
            "hours": validated_hours,
            "optimized_by": current_user["username"],
            "timestamp": datetime.utcnow().isoformat(),
            "status": "success",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error optimizing {strategy_name}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to optimize {strategy_name} strategy",
        )


@router.get("/{strategy_name}/history", response_model=Dict[str, Any])
async def get_optimization_history(
    strategy_name: str,
    limit: int = Query(10, description="Number of optimization runs to return"),
    current_user: dict = Depends(require_authentication),
    rate_limiter=Depends(get_strategy_rate_limiter),
):
    """Get optimization history for a strategy"""
    try:
        # This would fetch from database in real implementation
        optimization_history = [
            {
                "id": f"opt_{i}",
                "timestamp": datetime.utcnow().isoformat(),
                "parameters_optimized": ["short_window", "long_window"],
                "best_parameters": {"short_window": 5 + i, "long_window": 20 + i},
                "performance_improvement": round(2.5 + i * 0.5, 2),
                "optimization_metric": "sharpe_ratio",
                "applied": i < 3,
            }
            for i in range(min(limit, 5))
        ]

        return {
            "strategy": strategy_name,
            "optimization_history": optimization_history,
            "count": len(optimization_history),
            "limit": limit,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "success",
        }

    except Exception as e:
        logger.error(f"Error getting optimization history for {strategy_name}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get optimization history for {strategy_name}",
        )


@router.post("/{strategy_name}/parameters/apply", response_model=Dict[str, Any])
async def apply_optimized_parameters(
    strategy_name: str,
    parameters: Dict[str, Any],
    strategy: BaseStrategy = Depends(get_strategy_by_name),
    current_user: dict = Depends(require_authentication),
    rate_limiter=Depends(get_strategy_rate_limiter),
):
    """Apply optimized parameters to a strategy"""
    try:
        apply_result = await strategy.apply_parameters(
            parameters=parameters, user_id=current_user["username"]
        )

        if not apply_result.get("success", False):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to apply parameters: {apply_result.get('error', 'Unknown error')}",
            )

        return {
            "strategy": strategy_name,
            "applied_parameters": parameters,
            "apply_result": apply_result,
            "applied_by": current_user["username"],
            "timestamp": datetime.utcnow().isoformat(),
            "status": "success",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error applying parameters to {strategy_name}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to apply parameters to {strategy_name}",
        )
