# odin/api/routes/strategies/backtesting.py
"""
Strategy backtesting endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import Dict, Any
import logging
from datetime import datetime

from odin.strategies.base import BaseStrategy
from odin.api.dependencies import (
    get_strategy_by_name,
    get_strategy_rate_limiter,
    validate_timeframe
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/{strategy_name}/{hours}", response_model=Dict[str, Any])
async def backtest_strategy(
    strategy_name: str,
    hours: int,
    initial_balance: float = Query(10000.0, description="Initial balance for backtesting"),
    include_fees: bool = Query(True, description="Include trading fees in backtest"),
    include_slippage: bool = Query(True, description="Include market slippage"),
    strategy: BaseStrategy = Depends(get_strategy_by_name),
    rate_limiter = Depends(get_strategy_rate_limiter),
    validated_hours: int = Depends(validate_timeframe)
):
    """Run backtest on specific strategy with realistic trading conditions"""
    try:
        backtest_result = await strategy.backtest(
            hours=validated_hours,
            initial_balance=initial_balance,
            include_fees=include_fees,
            include_slippage=include_slippage,
            max_position_size=0.95
        )
        
        if not backtest_result or "error" in backtest_result:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=backtest_result.get("error", "Backtest failed")
            )
        
        # Add realistic trading metrics
        trading_metrics = {
            "total_fees_paid": backtest_result.get("total_fees", 0),
            "slippage_cost": backtest_result.get("slippage_cost", 0),
            "net_profit_after_costs": backtest_result.get("final_value", initial_balance) - initial_balance,
            "profit_factor": backtest_result.get("profit_factor", 1.0),
            "maximum_consecutive_losses": backtest_result.get("max_consecutive_losses", 0),
            "recovery_factor": backtest_result.get("recovery_factor", 0),
            "calmar_ratio": backtest_result.get("calmar_ratio", 0)
        }
        
        return {
            "strategy": strategy_name,
            "backtest": backtest_result,
            "trading_metrics": trading_metrics,
            "parameters": {
                "hours": validated_hours,
                "initial_balance": initial_balance,
                "fees_included": include_fees,
                "slippage_included": include_slippage
            },
            "timestamp": datetime.utcnow().isoformat(),
            "status": "success"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error backtesting {strategy_name} strategy: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to backtest {strategy_name} strategy"
        )


@router.post("/{strategy_name}/custom", response_model=Dict[str, Any])
async def custom_backtest(
    strategy_name: str,
    backtest_config: Dict[str, Any],
    strategy: BaseStrategy = Depends(get_strategy_by_name),
    rate_limiter = Depends(get_strategy_rate_limiter)
):
    """Run custom backtest with specific parameters"""
    try:
        # Validate backtest config
        required_fields = ["start_date", "end_date", "initial_balance"]
        for field in required_fields:
            if field not in backtest_config:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Missing required field: {field}"
                )
        
        backtest_result = await strategy.custom_backtest(
            config=backtest_config
        )
        
        return {
            "strategy": strategy_name,
            "backtest": backtest_result,
            "config": backtest_config,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "success"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error running custom backtest for {strategy_name}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to run custom backtest for {strategy_name}"
        )


@router.get("/compare/{hours}", response_model=Dict[str, Any])
async def compare_backtests(
    hours: int,
    strategies: str = Query(..., description="Comma-separated strategy names"),
    initial_balance: float = Query(10000.0),
    rate_limiter = Depends(get_strategy_rate_limiter),
    validated_hours: int = Depends(validate_timeframe)
):
    """Compare backtest results across multiple strategies"""
    try:
        strategy_names = [s.strip() for s in strategies.split(",")]
        
        if len(strategy_names) < 2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least 2 strategies required for comparison"
            )
        
        comparison_results = {}
        
        # This would need to be implemented with proper strategy loading
        # For now, return a structured response
        for strategy_name in strategy_names:
            # Mock backtest results for structure
            comparison_results[strategy_name] = {
                "return_percent": 0.0,
                "total_trades": 0,
                "win_rate": 0.0,
                "max_drawdown": 0.0,
                "sharpe_ratio": 0.0
            }
        
        return {
            "comparison": comparison_results,
            "parameters": {
                "hours": validated_hours,
                "initial_balance": initial_balance,
                "strategies": strategy_names
            },
            "timestamp": datetime.utcnow().isoformat(),
            "status": "success"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error comparing backtests: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to compare backtest results"
        )