# odin/api/routes/portfolio/risk.py
"""
Portfolio risk management endpoints
"""

import logging
from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from odin.api.dependencies import (
    get_strategy_rate_limiter,
    require_authentication,
    validate_timeframe,
)
from odin.core.portfolio_manager import PortfolioManager
from odin.core.risk_manager import RiskManager

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/metrics", response_model=Dict[str, Any])
async def get_risk_metrics(
    hours: int = Query(168, description="Hours for risk calculation"),
    current_user: dict = Depends(require_authentication),
    rate_limiter=Depends(get_strategy_rate_limiter),
    validated_hours: int = Depends(validate_timeframe),
):
    """Get comprehensive portfolio risk metrics"""
    try:
        risk_manager = RiskManager()
        portfolio_manager = PortfolioManager()

        # Portfolio-level risk metrics
        portfolio_risk = await risk_manager.calculate_portfolio_risk(
            user_id=current_user["username"], hours=validated_hours
        )

        # Value at Risk calculations
        var_metrics = {
            "var_95_1d": portfolio_risk.get("var_95_1d", 0),  # 1-day 95% VaR
            "var_99_1d": portfolio_risk.get("var_99_1d", 0),  # 1-day 99% VaR
            "var_95_1w": portfolio_risk.get("var_95_1w", 0),  # 1-week 95% VaR
            "var_99_1w": portfolio_risk.get("var_99_1w", 0),  # 1-week 99% VaR
            "expected_shortfall_95": portfolio_risk.get("expected_shortfall_95", 0),
            "expected_shortfall_99": portfolio_risk.get("expected_shortfall_99", 0),
        }

        # Volatility and correlation metrics
        volatility_metrics = {
            "daily_volatility": portfolio_risk.get("daily_volatility", 0),
            "annual_volatility": portfolio_risk.get("annual_volatility", 0),
            "downside_volatility": portfolio_risk.get("downside_volatility", 0),
            "correlation_with_btc": portfolio_risk.get("correlation_with_btc", 0),
            "beta_to_btc": portfolio_risk.get("beta_to_btc", 0),
            "tracking_error": portfolio_risk.get("tracking_error", 0),
        }

        # Drawdown metrics
        drawdown_metrics = {
            "max_drawdown": portfolio_risk.get("max_drawdown", 0),
            "current_drawdown": portfolio_risk.get("current_drawdown", 0),
            "average_drawdown": portfolio_risk.get("average_drawdown", 0),
            "drawdown_duration_days": portfolio_risk.get("drawdown_duration_days", 0),
            "recovery_factor": portfolio_risk.get("recovery_factor", 0),
            "pain_index": portfolio_risk.get("pain_index", 0),
        }

        # Risk-adjusted performance
        risk_adjusted_metrics = {
            "sharpe_ratio": portfolio_risk.get("sharpe_ratio", 0),
            "sortino_ratio": portfolio_risk.get("sortino_ratio", 0),
            "calmar_ratio": portfolio_risk.get("calmar_ratio", 0),
            "information_ratio": portfolio_risk.get("information_ratio", 0),
            "treynor_ratio": portfolio_risk.get("treynor_ratio", 0),
        }

        # Overall risk score (0-100, where 100 is highest risk)
        risk_score = portfolio_risk.get("risk_score", 50)
        risk_level = (
            "low" if risk_score < 30 else "medium" if risk_score < 70 else "high"
        )

        return {
            "var_metrics": var_metrics,
            "volatility_metrics": volatility_metrics,
            "drawdown_metrics": drawdown_metrics,
            "risk_adjusted_metrics": risk_adjusted_metrics,
            "risk_score": risk_score,
            "risk_level": risk_level,
            "hours_analyzed": validated_hours,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "success",
        }

    except Exception as e:
        logger.error(f"Error calculating risk metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to calculate risk metrics",
        )


@router.get("/exposure", response_model=Dict[str, Any])
async def get_exposure_analysis(
    current_user: dict = Depends(require_authentication),
    rate_limiter=Depends(get_strategy_rate_limiter),
):
    """Get current portfolio exposure analysis"""
    try:
        risk_manager = RiskManager()
        portfolio_manager = PortfolioManager()

        # Get current positions and exposures
        exposure_data = await risk_manager.get_exposure_analysis(
            user_id=current_user["username"]
        )

        # Strategy exposure breakdown
        strategy_exposure = {}
        for strategy in ["ma", "rsi", "bb", "macd"]:
            exposure = await risk_manager.get_strategy_exposure(
                strategy=strategy, user_id=current_user["username"]
            )
            strategy_exposure[strategy] = {
                "allocation_percent": exposure.get("allocation_percent", 0),
                "position_value_usd": exposure.get("position_value_usd", 0),
                "unrealized_pnl": exposure.get("unrealized_pnl", 0),
                "risk_contribution": exposure.get("risk_contribution", 0),
                "leverage": exposure.get("leverage", 1.0),
                "margin_used": exposure.get("margin_used", 0),
            }

        # Market exposure
        market_exposure = {
            "btc_exposure_percent": exposure_data.get("btc_exposure_percent", 0),
            "cash_percent": exposure_data.get("cash_percent", 0),
            "net_exposure": exposure_data.get("net_exposure", 0),
            "gross_exposure": exposure_data.get("gross_exposure", 0),
            "leverage_ratio": exposure_data.get("leverage_ratio", 1.0),
            "margin_utilization": exposure_data.get("margin_utilization", 0),
        }

        # Concentration risk
        concentration_risk = {
            "largest_position_percent": max(
                [exp["allocation_percent"] for exp in strategy_exposure.values()]
            ),
            "top_3_concentration": sum(
                sorted(
                    [exp["allocation_percent"] for exp in strategy_exposure.values()],
                    reverse=True,
                )[:3]
            ),
            "herfindahl_index": sum(
                [exp["allocation_percent"] ** 2 for exp in strategy_exposure.values()]
            )
            / 10000,
            "effective_strategies": (
                1
                / sum(
                    [
                        exp["allocation_percent"] ** 2
                        for exp in strategy_exposure.values()
                    ]
                )
                * 10000
                if any(exp["allocation_percent"] for exp in strategy_exposure.values())
                else 0
            ),
        }

        # Risk limits check
        risk_limits = await risk_manager.get_risk_limits(current_user["username"])
        limit_violations = await risk_manager.check_limit_violations(
            current_user["username"], exposure_data
        )

        return {
            "strategy_exposure": strategy_exposure,
            "market_exposure": market_exposure,
            "concentration_risk": concentration_risk,
            "risk_limits": risk_limits,
            "limit_violations": limit_violations,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "success",
        }

    except Exception as e:
        logger.error(f"Error getting exposure analysis: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get exposure analysis",
        )


@router.post("/limits/update", response_model=Dict[str, Any])
async def update_risk_limits(
    limits_update: Dict[str, Any],
    current_user: dict = Depends(require_authentication),
    rate_limiter=Depends(get_strategy_rate_limiter),
):
    """Update portfolio risk limits"""
    try:
        # Validate risk limits
        valid_limits = {
            "max_portfolio_var_percent": (0.01, 0.50),  # 1% to 50%
            "max_strategy_allocation_percent": (0.05, 1.00),  # 5% to 100%
            "max_drawdown_percent": (0.05, 0.50),  # 5% to 50%
            "max_leverage": (1.0, 10.0),  # 1x to 10x
            "min_cash_percent": (0.0, 0.50),  # 0% to 50%
            "max_concentration_percent": (0.10, 1.00),  # 10% to 100%
        }

        for limit_name, limit_value in limits_update.items():
            if limit_name in valid_limits:
                min_val, max_val = valid_limits[limit_name]
                if not min_val <= limit_value <= max_val:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"{limit_name} must be between {min_val} and {max_val}",
                    )

        risk_manager = RiskManager()

        # Update risk limits
        update_result = await risk_manager.update_risk_limits(
            user_id=current_user["username"], limits=limits_update
        )

        # Check if current positions violate new limits
        current_violations = await risk_manager.check_limit_violations(
            user_id=current_user["username"]
        )

        # Generate recommendations if violations exist
        recommendations = []
        if current_violations:
            recommendations = await risk_manager.generate_compliance_recommendations(
                violations=current_violations, user_id=current_user["username"]
            )

        return {
            "updated_limits": limits_update,
            "update_result": update_result,
            "current_violations": current_violations,
            "compliance_recommendations": recommendations,
            "updated_by": current_user["username"],
            "timestamp": datetime.utcnow().isoformat(),
            "status": "success",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating risk limits: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update risk limits",
        )


@router.get("/stress-test", response_model=Dict[str, Any])
async def run_stress_test(
    scenario: str = Query("market_crash", description="Stress test scenario"),
    current_user: dict = Depends(require_authentication),
    rate_limiter=Depends(get_strategy_rate_limiter),
):
    """Run portfolio stress test scenarios"""
    try:
        valid_scenarios = [
            "market_crash",
            "volatility_spike",
            "correlation_breakdown",
            "flash_crash",
            "prolonged_bear",
            "black_swan",
        ]

        if scenario not in valid_scenarios:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid scenario. Must be one of: {valid_scenarios}",
            )

        risk_manager = RiskManager()

        # Run stress test
        stress_results = await risk_manager.run_stress_test(
            user_id=current_user["username"], scenario=scenario
        )

        # Scenario definitions
        scenario_definitions = {
            "market_crash": "Bitcoin drops 50% in 24 hours",
            "volatility_spike": "Volatility increases 300% for 1 week",
            "correlation_breakdown": "Strategy correlations increase to 0.9+",
            "flash_crash": "5% drop in 1 hour with recovery",
            "prolonged_bear": "Gradual 70% decline over 6 months",
            "black_swan": "Extreme tail event (-8 sigma)",
        }

        # Risk metrics under stress
        stressed_metrics = {
            "projected_loss_usd": stress_results.get("projected_loss_usd", 0),
            "projected_loss_percent": stress_results.get("projected_loss_percent", 0),
            "stressed_var_95": stress_results.get("stressed_var_95", 0),
            "stressed_var_99": stress_results.get("stressed_var_99", 0),
            "time_to_recovery_days": stress_results.get("time_to_recovery_days", 0),
            "margin_call_risk": stress_results.get("margin_call_risk", False),
            "liquidation_risk": stress_results.get("liquidation_risk", False),
        }

        # Strategy-specific impact
        strategy_impact = stress_results.get("strategy_impact", {})

        # Risk mitigation suggestions
        mitigation_suggestions = (
            await risk_manager.generate_stress_mitigation_suggestions(
                stress_results=stress_results, scenario=scenario
            )
        )

        return {
            "scenario": scenario,
            "scenario_description": scenario_definitions[scenario],
            "stressed_metrics": stressed_metrics,
            "strategy_impact": strategy_impact,
            "mitigation_suggestions": mitigation_suggestions,
            "test_timestamp": datetime.utcnow().isoformat(),
            "status": "success",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error running stress test: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to run stress test",
        )


@router.get("/correlation-analysis", response_model=Dict[str, Any])
async def get_correlation_analysis(
    hours: int = Query(720, description="Hours for correlation analysis"),
    current_user: dict = Depends(require_authentication),
    rate_limiter=Depends(get_strategy_rate_limiter),
    validated_hours: int = Depends(validate_timeframe),
):
    """Get strategy correlation analysis"""
    try:
        risk_manager = RiskManager()

        # Calculate correlation matrix
        correlation_data = await risk_manager.calculate_strategy_correlations(
            user_id=current_user["username"], hours=validated_hours
        )

        # Correlation matrix between strategies
        correlation_matrix = correlation_data.get("correlation_matrix", {})

        # Rolling correlation analysis
        rolling_correlations = correlation_data.get("rolling_correlations", {})

        # Correlation with Bitcoin
        btc_correlations = {}
        for strategy in ["ma", "rsi", "bb", "macd"]:
            btc_correlations[strategy] = correlation_data.get(
                f"{strategy}_btc_correlation", 0
            )

        # Diversification metrics
        diversification_metrics = {
            "average_correlation": correlation_data.get("average_correlation", 0),
            "max_correlation": correlation_data.get("max_correlation", 0),
            "min_correlation": correlation_data.get("min_correlation", 0),
            "diversification_ratio": correlation_data.get("diversification_ratio", 1.0),
            "effective_strategies": correlation_data.get("effective_strategies", 1.0),
        }

        # Correlation risk assessment
        correlation_risk = "low"
        avg_corr = diversification_metrics["average_correlation"]
        if avg_corr > 0.8:
            correlation_risk = "high"
        elif avg_corr > 0.6:
            correlation_risk = "medium"

        # Portfolio concentration due to correlation
        concentration_effect = {
            "correlation_adjusted_diversification": diversification_metrics[
                "diversification_ratio"
            ],
            "concentration_risk_level": correlation_risk,
            "recommended_action": (
                "reduce_correlation" if correlation_risk == "high" else "maintain"
            ),
        }

        return {
            "correlation_matrix": correlation_matrix,
            "btc_correlations": btc_correlations,
            "rolling_correlations": rolling_correlations,
            "diversification_metrics": diversification_metrics,
            "concentration_effect": concentration_effect,
            "hours_analyzed": validated_hours,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "success",
        }

    except Exception as e:
        logger.error(f"Error getting correlation analysis: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get correlation analysis",
        )


@router.get("/risk-attribution", response_model=Dict[str, Any])
async def get_risk_attribution(
    hours: int = Query(168, description="Hours for risk attribution"),
    current_user: dict = Depends(require_authentication),
    rate_limiter=Depends(get_strategy_rate_limiter),
    validated_hours: int = Depends(validate_timeframe),
):
    """Get risk attribution analysis across strategies"""
    try:
        risk_manager = RiskManager()

        # Calculate risk attribution
        risk_attribution = await risk_manager.calculate_risk_attribution(
            user_id=current_user["username"], hours=validated_hours
        )

        # Strategy risk contributions
        strategy_risk_contributions = {}
        total_portfolio_risk = risk_attribution.get("total_portfolio_var", 0)

        for strategy in ["ma", "rsi", "bb", "macd"]:
            strategy_data = risk_attribution.get(f"{strategy}_attribution", {})
            strategy_risk_contributions[strategy] = {
                "standalone_var": strategy_data.get("standalone_var", 0),
                "marginal_var": strategy_data.get("marginal_var", 0),
                "component_var": strategy_data.get("component_var", 0),
                "risk_contribution_percent": (
                    (strategy_data.get("component_var", 0) / total_portfolio_risk * 100)
                    if total_portfolio_risk > 0
                    else 0
                ),
                "diversification_benefit": strategy_data.get(
                    "diversification_benefit", 0
                ),
            }

        # Risk factor analysis
        risk_factors = {
            "market_risk": risk_attribution.get("market_risk_percent", 0),
            "strategy_specific_risk": risk_attribution.get("strategy_risk_percent", 0),
            "correlation_risk": risk_attribution.get("correlation_risk_percent", 0),
            "concentration_risk": risk_attribution.get("concentration_risk_percent", 0),
        }

        # Risk budget utilization
        risk_budget = await risk_manager.get_risk_budget_utilization(
            user_id=current_user["username"]
        )

        return {
            "strategy_risk_contributions": strategy_risk_contributions,
            "risk_factors": risk_factors,
            "risk_budget_utilization": risk_budget,
            "total_portfolio_var": total_portfolio_risk,
            "hours_analyzed": validated_hours,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "success",
        }

    except Exception as e:
        logger.error(f"Error getting risk attribution: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get risk attribution",
        )
