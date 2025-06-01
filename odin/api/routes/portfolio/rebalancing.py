# odin/api/routes/portfolio/rebalancing.py
"""
Portfolio rebalancing endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import Dict, Any, List
import logging
from datetime import datetime

from odin.api.dependencies import (
    get_strategy_rate_limiter,
    require_authentication
)
from odin.core.portfolio_manager import PortfolioManager
from odin.core.risk_manager import RiskManager

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/", response_model=Dict[str, Any])
async def rebalance_portfolio(
    rebalance_config: Dict[str, Any],
    current_user: dict = Depends(require_authentication),
    rate_limiter = Depends(get_strategy_rate_limiter)
):
    """Execute portfolio rebalancing according to target allocations"""
    try:
        # Validate rebalancing configuration
        required_fields = ["target_allocations"]
        for field in required_fields:
            if field not in rebalance_config:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Missing required field: {field}"
                )
        
        target_allocations = rebalance_config["target_allocations"]
        
        # Validate allocations sum to 100%
        total_allocation = sum(target_allocations.values())
        if abs(total_allocation - 100) > 0.01:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Target allocations must sum to 100%, got {total_allocation}%"
            )
        
        # Validate strategy names
        valid_strategies = ["ma", "rsi", "bb", "macd", "cash"]
        for strategy in target_allocations.keys():
            if strategy not in valid_strategies:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid strategy '{strategy}'. Valid strategies: {valid_strategies}"
                )
        
        portfolio_manager = PortfolioManager()
        
        # Get current allocations
        current_allocations = await portfolio_manager.get_current_allocations(
            user_id=current_user["username"]
        )
        
        # Calculate rebalancing trades needed
        rebalancing_plan = await portfolio_manager.calculate_rebalancing_trades(
            current_allocations=current_allocations,
            target_allocations=target_allocations,
            threshold=rebalance_config.get("threshold", 0.05),  # 5% threshold
            min_trade_size=rebalance_config.get("min_trade_size", 100)  # $100 minimum
        )
        
        # Risk check for rebalancing
        risk_manager = RiskManager()
        risk_assessment = await risk_manager.assess_rebalancing_risk(
            rebalancing_plan=rebalancing_plan,
            user_id=current_user["username"]
        )
        
        if not risk_assessment["approved"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Rebalancing rejected by risk management: {risk_assessment['reason']}"
            )
        
        # Execute rebalancing if requested
        execute = rebalance_config.get("execute", False)
        if execute:
            execution_result = await portfolio_manager.execute_rebalancing(
                rebalancing_plan=rebalancing_plan,
                user_id=current_user["username"]
            )
        else:
            execution_result = {"simulated": True, "message": "Dry run - no trades executed"}
        
        # Calculate expected impact
        expected_impact = {
            "total_trades": len(rebalancing_plan.get("trades", [])),
            "estimated_fees": rebalancing_plan.get("estimated_fees", 0),
            "largest_trade_usd": max([trade.get("amount_usd", 0) for trade in rebalancing_plan.get("trades", [])], default=0),
            "total_turnover_usd": sum([trade.get("amount_usd", 0) for trade in rebalancing_plan.get("trades", [])]),
            "estimated_slippage": rebalancing_plan.get("estimated_slippage", 0)
        }
        
        logger.info(f"Portfolio rebalancing {'executed' if execute else 'simulated'} for {current_user['username']}")
        
        return {
            "target_allocations": target_allocations,
            "current_allocations": current_allocations,
            "rebalancing_plan": rebalancing_plan,
            "risk_assessment": risk_assessment,
            "execution_result": execution_result,
            "expected_impact": expected_impact,
            "executed": execute,
            "rebalanced_by": current_user["username"],
            "timestamp": datetime.utcnow().isoformat(),
            "status": "executed" if execute else "simulated"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error rebalancing portfolio: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to rebalance portfolio"
        )


@router.get("/recommendations", response_model=Dict[str, Any])
async def get_rebalancing_recommendations(
    current_user: dict = Depends(require_authentication),
    rate_limiter = Depends(get_strategy_rate_limiter)
):
    """Get portfolio rebalancing recommendations"""
    try:
        portfolio_manager = PortfolioManager()
        
        # Get current portfolio state
        current_allocations = await portfolio_manager.get_current_allocations(
            user_id=current_user["username"]
        )
        
        # Get strategy performance metrics
        strategy_performance = await portfolio_manager.get_strategy_performance_metrics(
            hours=168  # 1 week
        )
        
        # Generate recommendations based on performance and market conditions
        recommendations = await portfolio_manager.generate_rebalancing_recommendations(
            current_allocations=current_allocations,
            performance_metrics=strategy_performance,
            user_id=current_user["username"]
        )
        
        # Categorize recommendations
        recommendation_categories = {
            "immediate": [r for r in recommendations if r.get("urgency") == "high"],
            "suggested": [r for r in recommendations if r.get("urgency") == "medium"],
            "optional": [r for r in recommendations if r.get("urgency") == "low"]
        }
        
        # Calculate potential impact
        potential_impact = {}
        for category, recs in recommendation_categories.items():
            if recs:
                potential_impact[category] = {
                    "total_changes": len(recs),
                    "max_allocation_change": max([abs(r.get("allocation_change", 0)) for r in recs]),
                    "estimated_improvement": sum([r.get("expected_improvement", 0) for r in recs])
                }
        
        return {
            "current_allocations": current_allocations,
            "recommendations": recommendations,
            "recommendation_categories": recommendation_categories,
            "potential_impact": potential_impact,
            "last_rebalancing": await portfolio_manager.get_last_rebalancing_date(current_user["username"]),
            "timestamp": datetime.utcnow().isoformat(),
            "status": "success"
        }
        
    except Exception as e:
        logger.error(f"Error getting rebalancing recommendations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get rebalancing recommendations"
        )


@router.post("/allocation/update", response_model=Dict[str, Any])
async def update_target_allocation(
    allocation_update: Dict[str, Any],
    current_user: dict = Depends(require_authentication),
    rate_limiter = Depends(get_strategy_rate_limiter)
):
    """Update target portfolio allocation"""
    try:
        required_fields = ["target_allocations"]
        for field in required_fields:
            if field not in allocation_update:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Missing required field: {field}"
                )
        
        target_allocations = allocation_update["target_allocations"]
        
        # Validate allocations
        total_allocation = sum(target_allocations.values())
        if abs(total_allocation - 100) > 0.01:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Target allocations must sum to 100%, got {total_allocation}%"
            )
        
        portfolio_manager = PortfolioManager()
        
        # Update target allocations
        update_result = await portfolio_manager.update_target_allocations(
            user_id=current_user["username"],
            target_allocations=target_allocations,
            auto_rebalance=allocation_update.get("auto_rebalance", False),
            rebalance_threshold=allocation_update.get("rebalance_threshold", 0.05)
        )
        
        # Calculate deviation from current allocations
        current_allocations = await portfolio_manager.get_current_allocations(
            user_id=current_user["username"]
        )
        
        allocation_deviations = {}
        for strategy, target in target_allocations.items():
            current = current_allocations.get(strategy, 0)
            allocation_deviations[strategy] = {
                "current": current,
                "target": target,
                "deviation": target - current,
                "rebalancing_needed": abs(target - current) > allocation_update.get("rebalance_threshold", 0.05) * 100
            }
        
        return {
            "target_allocations": target_allocations,
            "current_allocations": current_allocations,
            "allocation_deviations": allocation_deviations,
            "update_result": update_result,
            "auto_rebalance_enabled": allocation_update.get("auto_rebalance", False),
            "rebalance_threshold": allocation_update.get("rebalance_threshold", 0.05),
            "updated_by": current_user["username"],
            "timestamp": datetime.utcnow().isoformat(),
            "status": "success"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating target allocation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update target allocation"
        )


@router.get("/history", response_model=Dict[str, Any])
async def get_rebalancing_history(
    limit: int = Query(20, description="Number of rebalancing events to return"),
    current_user: dict = Depends(require_authentication),
    rate_limiter = Depends(get_strategy_rate_limiter)
):
    """Get portfolio rebalancing history"""
    try:
        portfolio_manager = PortfolioManager()
        
        rebalancing_history = await portfolio_manager.get_rebalancing_history(
            user_id=current_user["username"],
            limit=limit
        )
        
        # Calculate summary statistics
        if rebalancing_history:
            total_rebalances = len(rebalancing_history)
            total_fees_paid = sum([event.get("total_fees", 0) for event in rebalancing_history])
            average_turnover = sum([event.get("total_turnover", 0) for event in rebalancing_history]) / total_rebalances
            
            # Performance impact analysis
            performance_impact = []
            for event in rebalancing_history:
                if event.get("performance_before") and event.get("performance_after"):
                    impact = event["performance_after"] - event["performance_before"]
                    performance_impact.append(impact)
            
            avg_performance_impact = sum(performance_impact) / len(performance_impact) if performance_impact else 0
            
            summary_stats = {
                "total_rebalances": total_rebalances,
                "total_fees_paid": total_fees_paid,
                "average_turnover": average_turnover,
                "average_performance_impact": avg_performance_impact,
                "successful_rebalances": sum([1 for event in rebalancing_history if event.get("status") == "completed"]),
                "failed_rebalances": sum([1 for event in rebalancing_history if event.get("status") == "failed"])
            }
        else:
            summary_stats = {
                "total_rebalances": 0,
                "total_fees_paid": 0,
                "average_turnover": 0,
                "average_performance_impact": 0,
                "successful_rebalances": 0,
                "failed_rebalances": 0
            }
        
        return {
            "rebalancing_history": rebalancing_history,
            "summary_stats": summary_stats,
            "count": len(rebalancing_history),
            "limit": limit,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "success"
        }
        
    except Exception as e:
        logger.error(f"Error getting rebalancing history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get rebalancing history"
        )


@router.post("/auto-rebalance/configure", response_model=Dict[str, Any])
async def configure_auto_rebalancing(
    auto_config: Dict[str, Any],
    current_user: dict = Depends(require_authentication),
    rate_limiter = Depends(get_strategy_rate_limiter)
):
    """Configure automatic rebalancing settings"""
    try:
        required_fields = ["enabled", "threshold", "frequency"]
        for field in required_fields:
            if field not in auto_config:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Missing required field: {field}"
                )
        
        # Validate configuration
        if auto_config["threshold"] < 0.01 or auto_config["threshold"] > 0.5:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Threshold must be between 1% and 50%"
            )
        
        valid_frequencies = ["daily", "weekly", "monthly"]
        if auto_config["frequency"] not in valid_frequencies:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid frequency. Must be one of: {valid_frequencies}"
            )
        
        portfolio_manager = PortfolioManager()
        
        config_result = await portfolio_manager.configure_auto_rebalancing(
            user_id=current_user["username"],
            enabled=auto_config["enabled"],
            threshold=auto_config["threshold"],
            frequency=auto_config["frequency"],
            max_trades_per_rebalance=auto_config.get("max_trades_per_rebalance", 10),
            min_trade_size=auto_config.get("min_trade_size", 100)
        )
        
        return {
            "auto_rebalancing_config": auto_config,
            "config_result": config_result,
            "configured_by": current_user["username"],
            "timestamp": datetime.utcnow().isoformat(),
            "status": "success"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error configuring auto-rebalancing: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to configure auto-rebalancing"
        )