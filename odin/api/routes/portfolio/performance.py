# odin/api/routes/portfolio/performance.py
"""
Portfolio performance analytics endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import Dict, Any, Optional
import logging
from datetime import datetime, timedelta

from odin.api.dependencies import (
    get_strategy_rate_limiter,
    require_authentication,
    validate_timeframe
)
from odin.core.portfolio_manager import PortfolioManager

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/{hours}", response_model=Dict[str, Any])
async def get_portfolio_performance(
    hours: int,
    benchmark: str = Query("BTC_HODL", description="Benchmark for comparison"),
    current_user: dict = Depends(require_authentication),
    rate_limiter = Depends(get_strategy_rate_limiter),
    validated_hours: int = Depends(validate_timeframe)
):
    """Get detailed portfolio performance analytics"""
    try:
        portfolio_manager = PortfolioManager()
        
        # Get comprehensive performance metrics
        performance_data = await portfolio_manager.get_performance_metrics(
            user_id=current_user["username"],
            hours=validated_hours
        )
        
        # Calculate key performance indicators
        performance_kpis = {
            "total_return_percent": performance_data.get("total_return_percent", 0),
            "annualized_return": performance_data.get("annualized_return", 0),
            "volatility_percent": performance_data.get("volatility_percent", 0),
            "sharpe_ratio": performance_data.get("sharpe_ratio", 0),
            "sortino_ratio": performance_data.get("sortino_ratio", 0),
            "calmar_ratio": performance_data.get("calmar_ratio", 0),
            "max_drawdown_percent": performance_data.get("max_drawdown_percent", 0),
            "current_drawdown_percent": performance_data.get("current_drawdown_percent", 0),
            "recovery_factor": performance_data.get("recovery_factor", 0),
            "profit_factor": performance_data.get("profit_factor", 0),
            "win_rate_percent": performance_data.get("win_rate_percent", 0),
            "average_win_percent": performance_data.get("average_win_percent", 0),
            "average_loss_percent": performance_data.get("average_loss_percent", 0),
            "largest_win_percent": performance_data.get("largest_win_percent", 0),
            "largest_loss_percent": performance_data.get("largest_loss_percent", 0)
        }
        
        # Benchmark comparison
        benchmark_data = await portfolio_manager.get_benchmark_performance(
            benchmark=benchmark,
            hours=validated_hours
        )
        
        # Calculate relative performance
        relative_performance = {
            "excess_return": performance_kpis["total_return_percent"] - benchmark_data.get("total_return_percent", 0),
            "information_ratio": performance_data.get("information_ratio", 0),
            "tracking_error": performance_data.get("tracking_error", 0),
            "beta": performance_data.get("beta", 1.0),
            "alpha": performance_data.get("alpha", 0),
            "correlation": performance_data.get("correlation", 0)
        }
        
        return {
            "performance_kpis": performance_kpis,
            "benchmark_data": benchmark_data,
            "relative_performance": relative_performance,
            "benchmark": benchmark,
            "hours_analyzed": validated_hours,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "success"
        }
        
    except Exception as e:
        logger.error(f"Error getting portfolio performance: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get portfolio performance"
        )


@router.get("/attribution", response_model=Dict[str, Any])
async def get_returns_attribution(
    hours: int = Query(168, description="Hours for attribution analysis"),
    current_user: dict = Depends(require_authentication),
    rate_limiter = Depends(get_strategy_rate_limiter),
    validated_hours: int = Depends(validate_timeframe)
):
    """Get strategy returns attribution analysis"""
    try:
        portfolio_manager = PortfolioManager()
        
        # Get strategy-level attribution
        strategy_attribution = await portfolio_manager.get_strategy_attribution(
            user_id=current_user["username"],
            hours=validated_hours
        )
        
        # Calculate contribution to total returns
        total_return = sum(attr.get("contribution_percent", 0) for attr in strategy_attribution.values())
        
        attribution_summary = {}
        for strategy, attr in strategy_attribution.items():
            attribution_summary[strategy] = {
                "allocation_percent": attr.get("allocation_percent", 0),
                "strategy_return_percent": attr.get("strategy_return_percent", 0),
                "contribution_percent": attr.get("contribution_percent", 0),
                "contribution_ratio": attr.get("contribution_percent", 0) / total_return if total_return != 0 else 0,
                "active_return": attr.get("active_return", 0),
                "tracking_error": attr.get("tracking_error", 0),
                "information_ratio": attr.get("information_ratio", 0),
                "total_trades": attr.get("total_trades", 0),
                "win_rate": attr.get("win_rate", 0),
                "total_fees": attr.get("total_fees", 0)
            }
        
        # Top contributing strategies
        top_contributors = sorted(
            attribution_summary.items(),
            key=lambda x: x[1]["contribution_percent"],
            reverse=True
        )[:3]
        
        # Worst performing strategies
        worst_performers = sorted(
            attribution_summary.items(),
            key=lambda x: x[1]["contribution_percent"]
        )[:3]
        
        return {
            "strategy_attribution": attribution_summary,
            "top_contributors": dict(top_contributors),
            "worst_performers": dict(worst_performers),
            "total_return_percent": total_return,
            "hours_analyzed": validated_hours,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "success"
        }
        
    except Exception as e:
        logger.error(f"Error getting returns attribution: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get returns attribution"
        )


@router.get("/metrics/live", response_model=Dict[str, Any])
async def get_live_performance_metrics(
    current_user: dict = Depends(require_authentication),
    rate_limiter = Depends(get_strategy_rate_limiter)
):
    """Get real-time performance metrics"""
    try:
        portfolio_manager = PortfolioManager()
        
        # Get current portfolio snapshot
        current_metrics = await portfolio_manager.get_current_performance_snapshot(
            user_id=current_user["username"]
        )
        
        # Performance over different timeframes
        timeframe_performance = {}
        timeframes = [24, 168, 720, 8760]  # 1d, 7d, 30d, 1y
        
        for hours in timeframes:
            try:
                perf = await portfolio_manager.get_performance_summary(
                    user_id=current_user["username"],
                    hours=hours
                )
                timeframe_name = {24: "1d", 168: "7d", 720: "30d", 8760: "1y"}[hours]
                timeframe_performance[timeframe_name] = {
                    "return_percent": perf.get("return_percent", 0),
                    "volatility": perf.get("volatility", 0),
                    "sharpe_ratio": perf.get("sharpe_ratio", 0),
                    "max_drawdown": perf.get("max_drawdown", 0),
                    "win_rate": perf.get("win_rate", 0)
                }
            except Exception as e:
                logger.warning(f"Could not get {hours}h performance: {e}")
                timeframe_name = {24: "1d", 168: "7d", 720: "30d", 8760: "1y"}[hours]
                timeframe_performance[timeframe_name] = None
        
        # Recent trading activity
        recent_activity = await portfolio_manager.get_recent_trading_activity(
            user_id=current_user["username"],
            limit=10
        )
        
        # Current day performance
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_performance = await portfolio_manager.get_performance_since(
            user_id=current_user["username"],
            since=today_start
        )
        
        return {
            "current_metrics": current_metrics,
            "timeframe_performance": timeframe_performance,
            "recent_activity": recent_activity,
            "today_performance": today_performance,
            "last_updated": datetime.utcnow().isoformat(),
            "status": "success"
        }
        
    except Exception as e:
        logger.error(f"Error getting live performance metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get live performance metrics"
        )


@router.get("/drawdown-analysis", response_model=Dict[str, Any])
async def get_drawdown_analysis(
    hours: int = Query(720, description="Hours for drawdown analysis"),
    current_user: dict = Depends(require_authentication),
    rate_limiter = Depends(get_strategy_rate_limiter),
    validated_hours: int = Depends(validate_timeframe)
):
    """Get detailed drawdown analysis"""
    try:
        portfolio_manager = PortfolioManager()
        
        drawdown_data = await portfolio_manager.get_drawdown_analysis(
            user_id=current_user["username"],
            hours=validated_hours
        )
        
        # Drawdown statistics
        drawdown_stats = {
            "max_drawdown_percent": drawdown_data.get("max_drawdown_percent", 0),
            "current_drawdown_percent": drawdown_data.get("current_drawdown_percent", 0),
            "average_drawdown_percent": drawdown_data.get("average_drawdown_percent", 0),
            "drawdown_periods": drawdown_data.get("drawdown_periods", 0),
            "longest_drawdown_days": drawdown_data.get("longest_drawdown_days", 0),
            "current_drawdown_days": drawdown_data.get("current_drawdown_days", 0),
            "recovery_factor": drawdown_data.get("recovery_factor", 0),
            "pain_index": drawdown_data.get("pain_index", 0)
        }
        
        # Historical drawdown periods
        drawdown_periods = drawdown_data.get("historical_periods", [])
        
        # Drawdown severity classification
        current_dd = drawdown_stats["current_drawdown_percent"]
        if current_dd == 0:
            severity = "none"
        elif current_dd < 5:
            severity = "minor"
        elif current_dd < 10:
            severity = "moderate"
        elif current_dd < 20:
            severity = "significant"
        else:
            severity = "severe"
        
        return {
            "drawdown_stats": drawdown_stats,
            "drawdown_periods": drawdown_periods,
            "current_severity": severity,
            "hours_analyzed": validated_hours,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "success"
        }
        
    except Exception as e:
        logger.error(f"Error getting drawdown analysis: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get drawdown analysis"
        )


@router.get("/returns-distribution", response_model=Dict[str, Any])
async def get_returns_distribution(
    hours: int = Query(720, description="Hours for returns analysis"),
    current_user: dict = Depends(require_authentication),
    rate_limiter = Depends(get_strategy_rate_limiter),
    validated_hours: int = Depends(validate_timeframe)
):
    """Get returns distribution analysis"""
    try:
        portfolio_manager = PortfolioManager()
        
        returns_data = await portfolio_manager.get_returns_distribution(
            user_id=current_user["username"],
            hours=validated_hours
        )
        
        # Distribution statistics
        distribution_stats = {
            "mean_return": returns_data.get("mean_return", 0),
            "median_return": returns_data.get("median_return", 0),
            "std_deviation": returns_data.get("std_deviation", 0),
            "skewness": returns_data.get("skewness", 0),
            "kurtosis": returns_data.get("kurtosis", 0),
            "var_95": returns_data.get("var_95", 0),  # Value at Risk 95%
            "var_99": returns_data.get("var_99", 0),  # Value at Risk 99%
            "expected_shortfall_95": returns_data.get("expected_shortfall_95", 0),
            "expected_shortfall_99": returns_data.get("expected_shortfall_99", 0)
        }
        
        # Returns percentiles
        percentiles = returns_data.get("percentiles", {})
        
        # Tail risk analysis
        tail_risk = {
            "positive_tail_ratio": returns_data.get("positive_tail_ratio", 0),
            "negative_tail_ratio": returns_data.get("negative_tail_ratio", 0),
            "tail_ratio": returns_data.get("tail_ratio", 0),
            "extreme_positive_days": returns_data.get("extreme_positive_days", 0),
            "extreme_negative_days": returns_data.get("extreme_negative_days", 0)
        }
        
        return {
            "distribution_stats": distribution_stats,
            "percentiles": percentiles,
            "tail_risk": tail_risk,
            "hours_analyzed": validated_hours,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "success"
        }
        
    except Exception as e:
        logger.error(f"Error getting returns distribution: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get returns distribution"
        )