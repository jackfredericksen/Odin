"""Strategy endpoints for Odin trading bot."""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
import structlog

from odin.api.dependencies import get_database
from odin.core.models import APIResponse, StrategyType
from odin.core.exceptions import StrategyError, InsufficientDataError
from odin.strategies import (
    get_strategy, 
    list_strategies,
    MovingAverageStrategy,
    RSIStrategy,
    BollingerBandsStrategy,
    MACDStrategy
)

logger = structlog.get_logger(__name__)
router = APIRouter()


@router.get("/strategies", response_model=APIResponse)
async def get_available_strategies():
    """Get list of available trading strategies."""
    try:
        strategies = list_strategies()
        
        strategy_info = {
            "moving_average": {
                "name": "Moving Average Crossover",
                "description": "MA(5,20) crossover signals for trend following",
                "type": "trend_following",
                "timeframe": "medium_term"
            },
            "rsi": {
                "name": "RSI Strategy",
                "description": "RSI(14) momentum oscillator for overbought/oversold signals",
                "type": "mean_reversion",
                "timeframe": "short_term"
            },
            "bollinger_bands": {
                "name": "Bollinger Bands",
                "description": "BB(20,2) volatility-based mean reversion strategy",
                "type": "volatility",
                "timeframe": "medium_term"
            },
            "macd": {
                "name": "MACD Strategy",
                "description": "MACD(12,26,9) trend momentum with multiple signal types",
                "type": "momentum",
                "timeframe": "medium_term"
            }
        }
        
        return APIResponse.success_response(
            data={
                "strategies": strategies,
                "strategy_info": strategy_info,
                "count": len(strategies)
            },
            message="Available strategies retrieved"
        )
        
    except Exception as e:
        logger.error("Failed to get strategies", error=str(e))
        return APIResponse.error_response(
            message="Failed to retrieve strategies",
            error_details={"error": str(e)}
        )


@router.get("/strategy/{strategy_name}/analysis", response_model=APIResponse)
async def get_strategy_analysis(
    strategy_name: str,
    database=Depends(get_database)
):
    """Get current market analysis for a specific strategy."""
    try:
        if strategy_name not in list_strategies():
            raise HTTPException(status_code=404, detail="Strategy not found")
        
        # Create strategy instance
        strategy = get_strategy(strategy_name)
        await strategy.initialize()
        
        # Perform analysis
        analysis = await strategy.analyze_current_market()
        
        return APIResponse.success_response(
            data=analysis.dict(),
            message=f"{strategy_name} analysis completed"
        )
        
    except InsufficientDataError as e:
        return APIResponse.error_response(
            message="Insufficient data for analysis",
            error_details={
                "required_points": e.required_points,
                "available_points": e.available_points
            }
        )
    except Exception as e:
        logger.error("Strategy analysis failed", 
                    strategy=strategy_name, error=str(e))
        return APIResponse.error_response(
            message="Strategy analysis failed",
            error_details={"error": str(e)}
        )


@router.get("/strategy/{strategy_name}/backtest/{hours}", response_model=APIResponse)
async def get_strategy_backtest(
    strategy_name: str,
    hours: int = Query(..., ge=24, le=720, description="Hours to backtest"),
    initial_balance: float = Query(10000.0, ge=1000.0, description="Initial balance"),
    database=Depends(get_database)
):
    """Get backtest results for a specific strategy."""
    try:
        if strategy_name not in list_strategies():
            raise HTTPException(status_code=404, detail="Strategy not found")
        
        # Create strategy instance
        strategy = get_strategy(strategy_name)
        await strategy.initialize()
        
        # Run backtest
        backtest_result = await strategy.backtest(
            hours=hours, 
            initial_balance=initial_balance
        )
        
        return APIResponse.success_response(
            data=backtest_result.dict(),
            message=f"{strategy_name} backtest completed"
        )
        
    except InsufficientDataError as e:
        return APIResponse.error_response(
            message="Insufficient data for backtesting",
            error_details={
                "required_points": e.required_points,
                "available_points": e.available_points
            }
        )
    except Exception as e:
        logger.error("Strategy backtest failed", 
                    strategy=strategy_name, error=str(e))
        return APIResponse.error_response(
            message="Strategy backtest failed",
            error_details={"error": str(e)}
        )


@router.get("/strategy/{strategy_name}/chart/{hours}", response_model=APIResponse)
async def get_strategy_chart_data(
    strategy_name: str,
    hours: int = Query(..., ge=1, le=168, description="Hours of chart data"),
    database=Depends(get_database)
):
    """Get strategy data formatted for charting."""
    try:
        if strategy_name not in list_strategies():
            raise HTTPException(status_code=404, detail="Strategy not found")
        
        # Create strategy instance
        strategy = get_strategy(strategy_name)
        await strategy.initialize()
        
        # Get chart data
        chart_data = await strategy.get_strategy_data_for_chart(hours=hours)
        
        if chart_data is None:
            return APIResponse.error_response(
                message="Insufficient data for chart",
                error_details={"hours": hours}
            )
        
        return APIResponse.success_response(
            data={
                "chart_data": chart_data,
                "strategy": strategy_name,
                "hours": hours,
                "data_points": len(chart_data)
            },
            message=f"{strategy_name} chart data retrieved"
        )
        
    except Exception as e:
        logger.error("Strategy chart data failed", 
                    strategy=strategy_name, error=str(e))
        return APIResponse.error_response(
            message="Failed to get chart data",
            error_details={"error": str(e)}
        )


@router.get("/strategies/compare/{hours}", response_model=APIResponse)
async def compare_all_strategies(
    hours: int = Query(..., ge=24, le=720, description="Hours to compare"),
    initial_balance: float = Query(10000.0, ge=1000.0, description="Initial balance"),
    database=Depends(get_database)
):
    """Compare performance of all strategies."""
    try:
        strategies = list_strategies()
        comparison_results = {}
        
        for strategy_name in strategies:
            try:
                strategy = get_strategy(strategy_name)
                await strategy.initialize()
                
                # Get both analysis and backtest
                analysis = await strategy.analyze_current_market()
                backtest = await strategy.backtest(hours=hours, initial_balance=initial_balance)
                
                comparison_results[strategy_name] = {
                    "analysis": analysis.dict(),
                    "backtest": backtest.dict(),
                    "performance_score": backtest.total_return_percent * (backtest.win_rate_percent / 100)
                }
                
            except InsufficientDataError:
                comparison_results[strategy_name] = {
                    "error": "Insufficient data",
                    "performance_score": -999
                }
            except Exception as e:
                logger.warning("Strategy comparison failed", 
                              strategy=strategy_name, error=str(e))
                comparison_results[strategy_name] = {
                    "error": str(e),
                    "performance_score": -999
                }
        
        # Rank strategies by performance
        valid_strategies = {
            name: data for name, data in comparison_results.items()
            if "error" not in data
        }
        
        if valid_strategies:
            ranked_strategies = sorted(
                valid_strategies.items(),
                key=lambda x: x[1]["performance_score"],
                reverse=True
            )
            
            winner = ranked_strategies[0][0] if ranked_strategies else None
        else:
            ranked_strategies = []
            winner = None
        
        return APIResponse.success_response(
            data={
                "comparison": comparison_results,
                "ranked_strategies": [{"strategy": name, **data} for name, data in ranked_strategies],
                "winner": winner,
                "period_hours": hours,
                "strategies_compared": len(strategies)
            },
            message="Strategy comparison completed"
        )
        
    except Exception as e:
        logger.error("Strategy comparison failed", error=str(e))
        return APIResponse.error_response(
            message="Strategy comparison failed",
            error_details={"error": str(e)}
        )