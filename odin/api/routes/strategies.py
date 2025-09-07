"""
Strategy Management API - Consolidated from 6 separate files
All strategy-related endpoints in one clean, organized file
"""

import logging
import random
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, Query, status

from odin.api.dependencies import (
    get_bb_strategy,
    get_ma_strategy,
    get_macd_strategy,
    get_rsi_strategy,
    get_strategy_by_name,
    get_strategy_rate_limiter,
    require_authentication,
    validate_timeframe,
)
from odin.core.portfolio_manager import PortfolioManager
from odin.strategies.base import BaseStrategy
from odin.strategies.bollinger_bands import BollingerBandsStrategy
from odin.strategies.macd import MACDStrategy
from odin.strategies.moving_average import MovingAverageStrategy
from odin.strategies.rsi import RSIStrategy

logger = logging.getLogger(__name__)
router = APIRouter()

# =============================================================================
# STRATEGY LISTING & ANALYSIS
# =============================================================================

@router.get("/list")
async def list_strategies():
    """Get list of all available strategies."""
    strategies = [
        {
            "name": "ma",
            "display_name": "Moving Average Crossover",
            "description": "MA(5,20) crossover signals for trend following",
            "type": "trend_following",
            "parameters": {"short_window": 5, "long_window": 20},
            "active": True,
            "allocation_percent": 25.0,
        },
        {
            "name": "rsi",
            "display_name": "RSI Momentum",
            "description": "RSI(14) momentum oscillator",
            "type": "momentum",
            "parameters": {"period": 14, "oversold": 30, "overbought": 70},
            "active": True,
            "allocation_percent": 25.0,
        },
        {
            "name": "bb",
            "display_name": "Bollinger Bands",
            "description": "BB(20,2) volatility-based mean reversion",
            "type": "volatility",
            "parameters": {"period": 20, "std_dev": 2},
            "active": True,
            "allocation_percent": 25.0,
        },
        {
            "name": "macd",
            "display_name": "MACD Trend",
            "description": "MACD(12,26,9) trend momentum signals",
            "type": "momentum",
            "parameters": {"fast": 12, "slow": 26, "signal": 9},
            "active": True,
            "allocation_percent": 25.0,
        },
    ]

    return {
        "strategies": strategies,
        "total_strategies": len(strategies),
        "active_strategies": sum(1 for s in strategies if s["active"]),
        "total_allocation": sum(s["allocation_percent"] for s in strategies),
        "timestamp": datetime.utcnow().isoformat(),
        "status": "success",
    }


@router.get("/{strategy_name}/analyze")
async def analyze_strategy(
    strategy_name: str,
    strategy: BaseStrategy = Depends(get_strategy_by_name),
    rate_limiter=Depends(get_strategy_rate_limiter),
):
    """Analyze current strategy performance and recommendations."""
    try:
        # Get strategy analysis
        analysis = await strategy.analyze_current_conditions()
        
        # Get portfolio info
        portfolio_manager = PortfolioManager()
        current_position = await portfolio_manager.get_strategy_position(strategy_name)
        available_capital = await portfolio_manager.get_available_capital()

        return {
            "strategy": strategy_name,
            "analysis": analysis,
            "current_position": current_position,
            "available_capital": available_capital,
            "can_execute": available_capital > 100,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "success",
        }

    except Exception as e:
        logger.error(f"Error analyzing {strategy_name} strategy: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze {strategy_name} strategy",
        )


@router.get("/{strategy_name}/chart/{hours}")
async def get_strategy_chart_data(
    strategy_name: str,
    hours: int,
    strategy: BaseStrategy = Depends(get_strategy_by_name),
    rate_limiter=Depends(get_strategy_rate_limiter),
    validated_hours: int = Depends(validate_timeframe),
):
    """Get strategy data formatted for charting."""
    try:
        chart_data = await strategy.get_chart_data(hours=validated_hours)

        if not chart_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No chart data available for {strategy_name} strategy",
            )

        return {
            "strategy": strategy_name,
            "chart_data": chart_data,
            "hours": validated_hours,
            "data_points": len(chart_data) if isinstance(chart_data, list) else 0,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "success",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting chart data for {strategy_name}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get chart data for {strategy_name} strategy",
        )

# =============================================================================
# STRATEGY BACKTESTING
# =============================================================================

@router.post("/{strategy_name}/backtest/{hours}")
async def backtest_strategy(
    strategy_name: str,
    hours: int,
    backtest_config: Dict[str, Any],
    strategy: BaseStrategy = Depends(get_strategy_by_name),
    current_user: dict = Depends(require_authentication),
    rate_limiter=Depends(get_strategy_rate_limiter),
    validated_hours: int = Depends(validate_timeframe),
):
    """Run comprehensive backtest for strategy."""
    try:
        # Validate backtest configuration
        default_config = {
            "initial_capital": 10000.0,
            "commission": 0.001,
            "slippage": 0.0005,
        }
        config = {**default_config, **backtest_config}

        # Run backtest
        backtest_result = await strategy.run_backtest(
            hours=validated_hours,
            config=config,
            user_id=current_user["username"],
        )

        if not backtest_result or "error" in backtest_result:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=backtest_result.get("error", "Backtest failed"),
            )

        return {
            "strategy": strategy_name,
            "backtest": backtest_result,
            "config": config,
            "hours": validated_hours,
            "run_by": current_user["username"],
            "timestamp": datetime.utcnow().isoformat(),
            "status": "success",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error backtesting {strategy_name}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Backtest failed for {strategy_name}",
        )

# =============================================================================
# STRATEGY COMPARISON
# =============================================================================

@router.get("/compare/all/{hours}")
async def compare_all_strategies(
    hours: int,
    initial_balance: float = Query(10000.0, description="Initial balance for comparison"),
    ma_strategy: MovingAverageStrategy = Depends(get_ma_strategy),
    rsi_strategy: RSIStrategy = Depends(get_rsi_strategy),
    bb_strategy: BollingerBandsStrategy = Depends(get_bb_strategy),
    macd_strategy: MACDStrategy = Depends(get_macd_strategy),
    current_user: dict = Depends(require_authentication),
    rate_limiter=Depends(get_strategy_rate_limiter),
    validated_hours: int = Depends(validate_timeframe),
):
    """Compare live performance of all strategies."""
    try:
        strategies = {
            "ma": ma_strategy,
            "rsi": rsi_strategy,
            "bb": bb_strategy,
            "macd": macd_strategy,
        }

        portfolio_manager = PortfolioManager()
        comparison_results = {}
        
        # Get comparison data for each strategy
        for name, strategy in strategies.items():
            try:
                performance = await strategy.get_performance_metrics(hours=validated_hours)
                comparison_results[name] = {
                    "performance": performance,
                    "current_signal": await strategy.get_current_signal(),
                    "win_rate": performance.get("win_rate", 0),
                    "total_return": performance.get("total_return", 0),
                    "sharpe_ratio": performance.get("sharpe_ratio", 0),
                }
            except Exception as e:
                logger.warning(f"Failed to get data for {name}: {e}")
                comparison_results[name] = {"error": str(e)}

        # Rank strategies by performance
        valid_strategies = {k: v for k, v in comparison_results.items() if "error" not in v}
        rankings = sorted(
            valid_strategies.items(),
            key=lambda x: x[1].get("total_return", 0),
            reverse=True
        )

        return {
            "comparison": comparison_results,
            "rankings": [{"strategy": k, "performance": v} for k, v in rankings],
            "hours_analyzed": validated_hours,
            "initial_balance": initial_balance,
            "strategies_compared": len(comparison_results),
            "timestamp": datetime.utcnow().isoformat(),
            "status": "success",
        }

    except Exception as e:
        logger.error(f"Error comparing strategies: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Strategy comparison failed",
        )


@router.get("/leaderboard")
async def get_strategy_leaderboard(
    period_hours: int = Query(168, description="Period for leaderboard (default: 7 days)"),
    rate_limiter=Depends(get_strategy_rate_limiter),
):
    """Get strategy performance leaderboard."""
    try:
        # Mock leaderboard data - replace with real implementation
        leaderboard = [
            {
                "rank": 1,
                "strategy": "rsi",
                "display_name": "RSI Momentum",
                "total_return": 8.5,
                "win_rate": 67.2,
                "trades": 23,
                "sharpe_ratio": 1.84,
                "max_drawdown": -2.1,
            },
            {
                "rank": 2,
                "strategy": "bb",
                "display_name": "Bollinger Bands",
                "total_return": 6.8,
                "win_rate": 58.9,
                "trades": 19,
                "sharpe_ratio": 1.52,
                "max_drawdown": -3.4,
            },
            {
                "rank": 3,
                "strategy": "ma",
                "display_name": "Moving Average",
                "total_return": 5.2,
                "win_rate": 52.1,
                "trades": 31,
                "sharpe_ratio": 1.23,
                "max_drawdown": -4.7,
            },
            {
                "rank": 4,
                "strategy": "macd",
                "display_name": "MACD Trend",
                "total_return": 3.9,
                "win_rate": 49.6,
                "trades": 27,
                "sharpe_ratio": 0.97,
                "max_drawdown": -5.2,
            },
        ]

        return {
            "leaderboard": leaderboard,
            "period_hours": period_hours,
            "period_description": f"{period_hours // 24} days",
            "total_strategies": len(leaderboard),
            "timestamp": datetime.utcnow().isoformat(),
            "status": "success",
        }

    except Exception as e:
        logger.error(f"Error getting leaderboard: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get strategy leaderboard",
        )

# =============================================================================
# STRATEGY MANAGEMENT
# =============================================================================

@router.post("/{strategy_name}/enable")
async def enable_strategy(
    strategy_name: str,
    config: Dict[str, Any],
    strategy: BaseStrategy = Depends(get_strategy_by_name),
    current_user: dict = Depends(require_authentication),
    rate_limiter=Depends(get_strategy_rate_limiter),
):
    """Enable a trading strategy."""
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


@router.post("/{strategy_name}/disable")
async def disable_strategy(
    strategy_name: str,
    strategy: BaseStrategy = Depends(get_strategy_by_name),
    current_user: dict = Depends(require_authentication),
    rate_limiter=Depends(get_strategy_rate_limiter),
):
    """Disable a trading strategy."""
    try:
        disable_result = await strategy.disable(user_id=current_user["username"])

        if not disable_result.get("success", False):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to disable strategy: {disable_result.get('error')}",
            )

        return {
            "strategy": strategy_name,
            "enabled": False,
            "disabled_by": current_user["username"],
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


@router.put("/{strategy_name}/config")
async def update_strategy_config(
    strategy_name: str,
    config_update: Dict[str, Any],
    strategy: BaseStrategy = Depends(get_strategy_by_name),
    current_user: dict = Depends(require_authentication),
    rate_limiter=Depends(get_strategy_rate_limiter),
):
    """Update strategy configuration."""
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

# =============================================================================
# STRATEGY OPTIMIZATION
# =============================================================================

@router.post("/{strategy_name}/optimize")
async def optimize_strategy_parameters(
    strategy_name: str,
    optimization_config: Dict[str, Any],
    hours: int = Query(168, description="Hours of data for optimization"),
    strategy: BaseStrategy = Depends(get_strategy_by_name),
    current_user: dict = Depends(require_authentication),
    rate_limiter=Depends(get_strategy_rate_limiter),
    validated_hours: int = Depends(validate_timeframe),
):
    """Optimize strategy parameters using historical data."""
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
                detail=optimization_result.get("error", "Parameter optimization failed"),
            )

        # Apply optimized parameters if requested
        if optimization_config.get("auto_apply", False):
            apply_result = await strategy.apply_optimized_parameters(
                optimized_params=optimization_result["best_parameters"],
                user_id=current_user["username"],
            )
            optimization_result["auto_applied"] = apply_result.get("success", False)

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
            detail=f"Optimization failed for {strategy_name}",
        )

# =============================================================================
# STRATEGY SIGNALS
# =============================================================================

@router.get("/{strategy_name}/signals")
async def get_strategy_signals(
    strategy_name: str,
    hours: int = Query(24, description="Hours of signal history"),
    strategy: BaseStrategy = Depends(get_strategy_by_name),
    rate_limiter=Depends(get_strategy_rate_limiter),
    validated_hours: int = Depends(validate_timeframe),
):
    """Get recent trading signals from strategy."""
    try:
        signals = await strategy.get_recent_signals(hours=validated_hours)
        current_signal = await strategy.get_current_signal()

        return {
            "strategy": strategy_name,
            "current_signal": current_signal,
            "recent_signals": signals,
            "signal_count": len(signals) if signals else 0,
            "hours": validated_hours,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "success",
        }

    except Exception as e:
        logger.error(f"Error getting signals for {strategy_name}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get signals for {strategy_name}",
        )


@router.get("/signals/all")
async def get_all_strategy_signals(
    hours: int = Query(24, description="Hours of signal history"),
    ma_strategy: MovingAverageStrategy = Depends(get_ma_strategy),
    rsi_strategy: RSIStrategy = Depends(get_rsi_strategy),
    bb_strategy: BollingerBandsStrategy = Depends(get_bb_strategy),
    macd_strategy: MACDStrategy = Depends(get_macd_strategy),
    rate_limiter=Depends(get_strategy_rate_limiter),
    validated_hours: int = Depends(validate_timeframe),
):
    """Get current signals from all strategies."""
    try:
        strategies = {
            "ma": ma_strategy,
            "rsi": rsi_strategy,
            "bb": bb_strategy,
            "macd": macd_strategy,
        }

        all_signals = {}
        for name, strategy in strategies.items():
            try:
                current_signal = await strategy.get_current_signal()
                all_signals[name] = current_signal
            except Exception as e:
                logger.warning(f"Failed to get signal for {name}: {e}")
                all_signals[name] = {"error": str(e)}

        return {
            "signals": all_signals,
            "strategies_count": len(all_signals),
            "hours": validated_hours,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "success",
        }

    except Exception as e:
        logger.error(f"Error getting all strategy signals: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get strategy signals",
        )