# odin/api/routes/strategies/comparison.py
"""
Strategy comparison endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import Dict, Any
import logging
from datetime import datetime

from odin.strategies.moving_average import MovingAverageStrategy
from odin.strategies.rsi import RSIStrategy
from odin.strategies.bollinger_bands import BollingerBandsStrategy
from odin.strategies.macd import MACDStrategy
from odin.api.dependencies import (
    get_ma_strategy,
    get_rsi_strategy,
    get_bb_strategy,
    get_macd_strategy,
    get_strategy_rate_limiter,
    validate_timeframe,
    require_authentication
)
from odin.core.portfolio_manager import PortfolioManager

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/all/{hours}", response_model=Dict[str, Any])
async def compare_all_strategies(
    hours: int,
    initial_balance: float = Query(10000.0, description="Initial balance for comparison"),
    ma_strategy: MovingAverageStrategy = Depends(get_ma_strategy),
    rsi_strategy: RSIStrategy = Depends(get_rsi_strategy),
    bb_strategy: BollingerBandsStrategy = Depends(get_bb_strategy),
    macd_strategy: MACDStrategy = Depends(get_macd_strategy),
    current_user: dict = Depends(require_authentication),
    rate_limiter = Depends(get_strategy_rate_limiter),
    validated_hours: int = Depends(validate_timeframe)
):
    """Compare live performance of all strategies"""
    try:
        strategies = {
            "ma": ma_strategy,
            "rsi": rsi_strategy,
            "bb": bb_strategy,
            "macd": macd_strategy
        }
        
        portfolio_manager = PortfolioManager()
        comparison_results = {}
        live_performance = {}
        
        # Get live performance for each strategy
        for name, strategy in strategies.items():
            try:
                # Live trading results
                live_perf = await portfolio_manager.get_strategy_performance(
                    strategy=name,
                    user_id=current_user["username"],
                    hours=validated_hours
                )
                
                # Backtest for comparison
                backtest_result = await strategy.backtest(
                    hours=validated_hours,
                    initial_balance=initial_balance,
                    include_fees=True,
                    include_slippage=True
                )
                
                if live_perf and "error" not in live_perf:
                    live_performance[name] = live_perf
                    
                    comparison_results[name] = {
                        "live_return_percent": live_perf.get("return_percent", 0),
                        "live_total_trades": live_perf.get("total_trades", 0),
                        "live_win_rate": live_perf.get("win_rate_percent", 0),
                        "live_sharpe_ratio": live_perf.get("sharpe_ratio", 0),
                        "live_max_drawdown": live_perf.get("max_drawdown_percent", 0),
                        "backtest_return_percent": backtest_result.get("total_return_percent", 0),
                        "live_vs_backtest_diff": live_perf.get("return_percent", 0) - backtest_result.get("total_return_percent", 0),
                        "current_allocation": live_perf.get("allocation_percent", 0),
                        "active_positions": live_perf.get("active_positions", 0),
                        "total_fees_paid": live_perf.get("total_fees", 0)
                    }
                
            except Exception as e:
                logger.error(f"Error comparing {name} strategy: {e}")
                comparison_results[name] = {
                    "error": str(e),
                    "live_return_percent": 0,
                    "live_total_trades": 0,
                    "live_win_rate": 0
                }
        
        # Rank strategies by live performance
        strategy_rankings = []
        for name, results in comparison_results.items():
            if "error" not in results:
                strategy_rankings.append({
                    "strategy": name,
                    "live_return_percent": results["live_return_percent"],
                    "live_win_rate": results["live_win_rate"],
                    "live_total_trades": results["live_total_trades"],
                    "live_sharpe_ratio": results["live_sharpe_ratio"],
                    "allocation_percent": results["current_allocation"],
                    "performance_score": (
                        results["live_return_percent"] * 0.4 +
                        results["live_win_rate"] * 0.3 +
                        results["live_sharpe_ratio"] * 10 * 0.3
                    )
                })
        
        # Sort by performance score
        strategy_rankings.sort(key=lambda x: x["performance_score"], reverse=True)
        
        # Add rankings
        for i, strategy in enumerate(strategy_rankings):
            strategy["rank"] = i + 1
        
        # Find top performer
        winner = strategy_rankings[0] if strategy_rankings else None
        
        # Portfolio-level metrics
        total_portfolio_return = sum(
            r["live_return_percent"] * r["allocation_percent"] / 100 
            for r in strategy_rankings
        )
        
        return {
            "live_comparison": comparison_results,
            "rankings": strategy_rankings,
            "winner": winner,
            "portfolio_return": total_portfolio_return,
            "live_performance": live_performance,
            "parameters": {
                "hours": validated_hours,
                "initial_balance": initial_balance,
                "include_live_data": True
            },
            "analyzed_by": current_user["username"],
            "timestamp": datetime.utcnow().isoformat(),
            "status": "success"
        }
        
    except Exception as e:
        logger.error(f"Error comparing strategies: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to compare strategies"
        )


@router.get("/leaderboard", response_model=Dict[str, Any])
async def get_strategy_leaderboard(
    timeframe: str = Query("7d", description="Timeframe for leaderboard (1d, 7d, 30d, 1y)"),
    metric: str = Query("return", description="Ranking metric (return, sharpe, win_rate)"),
    rate_limiter = Depends(get_strategy_rate_limiter)
):
    """Get strategy performance leaderboard"""
    try:
        valid_timeframes = ["1d", "7d", "30d", "1y"]
        valid_metrics = ["return", "sharpe", "win_rate", "trades"]
        
        if timeframe not in valid_timeframes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid timeframe. Must be one of: {', '.join(valid_timeframes)}"
            )
        
        if metric not in valid_metrics:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid metric. Must be one of: {', '.join(valid_metrics)}"
            )
        
        # Convert timeframe to hours
        timeframe_hours = {
            "1d": 24,
            "7d": 168,
            "30d": 720,
            "1y": 8760
        }
        
        hours = timeframe_hours[timeframe]
        
        # Get performance data for all strategies
        strategies = ["ma", "rsi", "bb", "macd"]
        leaderboard = []
        
        for strategy_name in strategies:
            try:
                # Mock performance data - would normally fetch real data
                import random
                performance = {
                    "strategy": strategy_name,
                    "return_percent": round(random.uniform(-5, 15), 2),
                    "sharpe_ratio": round(random.uniform(0.5, 2.5), 2),
                    "win_rate_percent": round(random.uniform(45, 75), 1),
                    "total_trades": random.randint(10, 50),
                    "max_drawdown_percent": round(random.uniform(2, 12), 2),
                    "volatility_percent": round(random.uniform(15, 45), 1)
                }
                leaderboard.append(performance)
                
            except Exception as e:
                logger.error(f"Error getting performance for {strategy_name}: {e}")
        
        # Sort by selected metric
        if metric == "return":
            leaderboard.sort(key=lambda x: x["return_percent"], reverse=True)
        elif metric == "sharpe":
            leaderboard.sort(key=lambda x: x["sharpe_ratio"], reverse=True)
        elif metric == "win_rate":
            leaderboard.sort(key=lambda x: x["win_rate_percent"], reverse=True)
        elif metric == "trades":
            leaderboard.sort(key=lambda x: x["total_trades"], reverse=True)
        
        # Add rankings
        for i, strategy in enumerate(leaderboard):
            strategy["rank"] = i + 1
        
        return {
            "leaderboard": leaderboard,
            "timeframe": timeframe,
            "ranking_metric": metric,
            "total_strategies": len(leaderboard),
            "timestamp": datetime.utcnow().isoformat(),
            "status": "success"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating leaderboard: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate strategy leaderboard"
        )