# odin/api/routes/strategies/analysis.py
"""
Strategy analysis endpoints
"""

import logging
from datetime import datetime
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, status

from odin.api.dependencies import (
    get_bb_strategy,
    get_ma_strategy,
    get_macd_strategy,
    get_rsi_strategy,
    get_strategy_by_name,
    get_strategy_rate_limiter,
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


@router.get("/list", response_model=Dict[str, Any])
async def list_strategies():
    """Get list of available trading strategies"""
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
            "display_name": "MACD Trend Momentum",
            "description": "MACD(12,26,9) trend momentum",
            "type": "trend_momentum",
            "parameters": {"fast_period": 12, "slow_period": 26, "signal_period": 9},
            "active": True,
            "allocation_percent": 25.0,
        },
    ]

    return {
        "strategies": strategies,
        "count": len(strategies),
        "total_allocation": sum(
            s["allocation_percent"] for s in strategies if s["active"]
        ),
        "status": "success",
    }


@router.get("/analysis", response_model=Dict[str, Any])
async def get_all_strategies_analysis(
    ma_strategy: MovingAverageStrategy = Depends(get_ma_strategy),
    rsi_strategy: RSIStrategy = Depends(get_rsi_strategy),
    bb_strategy: BollingerBandsStrategy = Depends(get_bb_strategy),
    macd_strategy: MACDStrategy = Depends(get_macd_strategy),
    rate_limiter=Depends(get_strategy_rate_limiter),
):
    """Get current analysis from all trading strategies"""
    try:
        strategies_analysis = {}
        strategies = {
            "ma": ma_strategy,
            "rsi": rsi_strategy,
            "bb": bb_strategy,
            "macd": macd_strategy,
        }

        for name, strategy in strategies.items():
            try:
                analysis = await strategy.analyze_current_market()
                strategies_analysis[name] = analysis
            except Exception as e:
                logger.error(f"Error analyzing {name} strategy: {e}")
                strategies_analysis[name] = {
                    "error": f"Analysis failed: {str(e)}",
                    "status": "error",
                }

        # Count active signals ready for execution
        active_signals = {}
        for name, analysis in strategies_analysis.items():
            if "current_signal" in analysis and analysis["current_signal"]:
                signal_type = analysis["current_signal"].get("type", "NONE")
                signal_strength = analysis["current_signal"].get("strength", 0)

                if signal_type in ["BUY", "SELL"] and signal_strength >= 0.7:
                    active_signals[name] = {
                        "type": signal_type,
                        "strength": signal_strength,
                        "price": analysis["current_signal"].get("price"),
                        "confidence": analysis["current_signal"].get("confidence", 0),
                    }

        return {
            "strategies": strategies_analysis,
            "active_signals": active_signals,
            "signal_count": len(active_signals),
            "execution_ready": len(
                [s for s in active_signals.values() if s["strength"] >= 0.8]
            ),
            "timestamp": datetime.utcnow().isoformat(),
            "status": "success",
        }

    except Exception as e:
        logger.error(f"Error getting strategies analysis: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get strategies analysis",
        )


@router.get("/{strategy_name}/analysis", response_model=Dict[str, Any])
async def get_strategy_analysis(
    strategy_name: str,
    strategy: BaseStrategy = Depends(get_strategy_by_name),
    rate_limiter=Depends(get_strategy_rate_limiter),
):
    """Get current market analysis from specific strategy"""
    try:
        analysis = await strategy.analyze_current_market()

        # Add live trading context
        portfolio_manager = PortfolioManager()
        current_position = await portfolio_manager.get_strategy_position(strategy_name)
        available_capital = await portfolio_manager.get_available_capital(strategy_name)

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


@router.get("/{strategy_name}/chart/{hours}", response_model=Dict[str, Any])
async def get_strategy_chart_data(
    strategy_name: str,
    hours: int,
    strategy: BaseStrategy = Depends(get_strategy_by_name),
    rate_limiter=Depends(get_strategy_rate_limiter),
    validated_hours: int = Depends(validate_timeframe),
):
    """Get strategy data formatted for charting"""
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
