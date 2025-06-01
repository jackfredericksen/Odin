# odin/api/routes/market/fees.py
"""
Trading fee analysis endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import Dict, Any, List, Optional
import logging
from datetime import datetime, timedelta

from odin.api.dependencies import (
    get_strategy_rate_limiter,
    require_authentication
)
from odin.core.portfolio_manager import PortfolioManager

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/", response_model=Dict[str, Any])
async def get_trading_fees(
    period: str = Query("30d", description="Period for fee analysis (7d, 30d, 90d, 1y)"),
    current_user: dict = Depends(require_authentication),
    rate_limiter = Depends(get_strategy_rate_limiter)
):
    """Get comprehensive trading fees analysis"""
    try:
        valid_periods = ["7d", "30d", "90d", "1y"]
        if period not in valid_periods:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid period. Must be one of: {valid_periods}"
            )
        
        # Convert period to hours
        period_hours = {"7d": 168, "30d": 720, "90d": 2160, "1y": 8760}
        hours = period_hours[period]
        
        portfolio_manager = PortfolioManager()
        
        # Get fee analysis data
        fee_analysis = await portfolio_manager.get_fee_analysis(
            user_id=current_user["username"],
            hours=hours
        )
        
        # Calculate fee metrics
        fee_metrics = calculate_fee_metrics(fee_analysis, period)
        
        # Get exchange fee structure
        exchange_fees = get_exchange_fee_structure()
        
        # Calculate fee efficiency
        fee_efficiency = calculate_fee_efficiency(fee_analysis, exchange_fees)
        
        # Fee optimization suggestions
        optimization_suggestions = generate_fee_optimization_suggestions(
            fee_analysis, fee_metrics, exchange_fees
        )
        
        # Fee comparison with benchmarks
        fee_benchmarks = get_fee_benchmarks(fee_analysis)
        
        return {
            "fee_analysis": fee_analysis,
            "fee_metrics": fee_metrics,
            "exchange_fees": exchange_fees,
            "fee_efficiency": fee_efficiency,
            "optimization_suggestions": optimization_suggestions,
            "fee_benchmarks": fee_benchmarks,
            "period": period,
            "period_hours": hours,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "success"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting trading fees analysis: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get trading fees analysis"
        )


@router.get("/optimization", response_model=Dict[str, Any])
async def get_fee_optimization(
    trade_size: float = Query(1000, description="Typical trade size in USD"),
    frequency: int = Query(10, description="Trades per month"),
    current_user: dict = Depends(require_authentication),
    rate_limiter = Depends(get_strategy_rate_limiter)
):
    """Get fee optimization recommendations"""
    try:
        if trade_size <= 0 or trade_size > 1000000:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Trade size must be between 0 and 1,000,000 USD"
            )
        
        if frequency <= 0 or frequency > 1000:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Frequency must be between 0 and 1000 trades per month"
            )
        
        # Calculate optimization scenarios
        optimization_scenarios = calculate_optimization_scenarios(trade_size, frequency)
        
        # Order type recommendations
        order_type_analysis = analyze_order_type_efficiency(trade_size, frequency)
        
        # Exchange comparison
        exchange_comparison = compare_exchange_fees(trade_size, frequency)
        
        # VIP tier analysis
        vip_tier_analysis = analyze_vip_tier_benefits(trade_size, frequency)
        
        # Potential savings calculation
        potential_savings = calculate_potential_savings(
            optimization_scenarios, order_type_analysis, vip_tier_analysis
        )
        
        return {
            "optimization_scenarios": optimization_scenarios,
            "order_type_analysis": order_type_analysis,
            "exchange_comparison": exchange_comparison,
            "vip_tier_analysis": vip_tier_analysis,
            "potential_savings": potential_savings,
            "trade_parameters": {
                "trade_size_usd": trade_size,
                "monthly_frequency": frequency,
                "monthly_volume": trade_size * frequency
            },
            "timestamp": datetime.utcnow().isoformat(),
            "status": "success"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting fee optimization: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get fee optimization"
        )


@router.get("/comparison", response_model=Dict[str, Any])
async def get_fee_comparison(
    exchanges: Optional[List[str]] = Query(None, description="Exchanges to compare"),
    current_user: dict = Depends(require_authentication),
    rate_limiter = Depends(get_strategy_rate_limiter)
):
    """Compare fees across different exchanges"""
    try:
        # Default exchanges if none specified
        if not exchanges:
            exchanges = ["binance", "coinbase_pro", "kraken", "bitfinex", "ftx"]
        
        # Validate exchanges
        valid_exchanges = ["binance", "coinbase_pro", "kraken", "bitfinex", "ftx", "bitstamp", "gemini"]
        for exchange in exchanges:
            if exchange not in valid_exchanges:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid exchange '{exchange}'. Valid exchanges: {valid_exchanges}"
                )
        
        # Get user's trading profile for comparison
        portfolio_manager = PortfolioManager()
        trading_profile = await portfolio_manager.get_trading_profile(
            user_id=current_user["username"]
        )
        
        # Compare fees across exchanges
        exchange_comparison = {}
        
        for exchange in exchanges:
            fee_structure = get_exchange_fee_structure(exchange)
            
            # Calculate fees for user's typical trading pattern
            estimated_fees = calculate_estimated_fees(
                fee_structure, trading_profile
            )
            
            exchange_comparison[exchange] = {
                "fee_structure": fee_structure,
                "estimated_monthly_fees": estimated_fees["monthly_fees"],
                "estimated_annual_fees": estimated_fees["annual_fees"],
                "maker_taker_ratio": fee_structure.get("maker_taker_ratio", 0.5),
                "vip_benefits": fee_structure.get("vip_benefits", {}),
                "withdrawal_fees": fee_structure.get("withdrawal_fees", {}),
                "deposit_fees": fee_structure.get("deposit_fees", 0)
            }
        
        # Rank exchanges by cost efficiency
        ranking = rank_exchanges_by_cost(exchange_comparison, trading_profile)
        
        # Savings opportunities
        current_exchange = trading_profile.get("current_exchange", "unknown")
        savings_opportunities = calculate_exchange_savings(
            exchange_comparison, current_exchange, trading_profile
        )
        
        return {
            "exchange_comparison": exchange_comparison,
            "ranking": ranking,
            "savings_opportunities": savings_opportunities,
            "trading_profile": trading_profile,
            "compared_exchanges": exchanges,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "success"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error comparing exchange fees: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to compare exchange fees"
        )


@router.get("/breakdown", response_model=Dict[str, Any])
async def get_fee_breakdown(
    period: str = Query("30d", description="Period for breakdown analysis"),
    current_user: dict = Depends(require_authentication),
    rate_limiter = Depends(get_strategy_rate_limiter)
):
    """Get detailed fee breakdown by category"""
    try:
        valid_periods = ["7d", "30d", "90d", "1y"]
        if period not in valid_periods:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid period. Must be one of: {valid_periods}"
            )
        
        portfolio_manager = PortfolioManager()
        
        # Get detailed fee breakdown
        fee_breakdown = await portfolio_manager.get_detailed_fee_breakdown(
            user_id=current_user["username"],
            period=period
        )
        
        # Categorize fees
        fee_categories = {
            "trading_fees": {
                "maker_fees": fee_breakdown.get("maker_fees", 0),
                "taker_fees": fee_breakdown.get("taker_fees", 0),
                "total": fee_breakdown.get("maker_fees", 0) + fee_breakdown.get("taker_fees", 0)
            },
            "funding_fees": {
                "deposit_fees": fee_breakdown.get("deposit_fees", 0),
                "withdrawal_fees": fee_breakdown.get("withdrawal_fees", 0),
                "transfer_fees": fee_breakdown.get("transfer_fees", 0),
                "total": fee_breakdown.get("deposit_fees", 0) + fee_breakdown.get("withdrawal_fees", 0) + fee_breakdown.get("transfer_fees", 0)
            },
            "financing_fees": {
                "margin_fees": fee_breakdown.get("margin_fees", 0),
                "borrowing_fees": fee_breakdown.get("borrowing_fees", 0),
                "funding_rate_fees": fee_breakdown.get("funding_rate_fees", 0),
                "total": fee_breakdown.get("margin_fees", 0) + fee_breakdown.get("borrowing_fees", 0) + fee_breakdown.get("funding_rate_fees", 0)
            },
            "other_fees": {
                "api_fees": fee_breakdown.get("api_fees", 0),
                "inactivity_fees": fee_breakdown.get("inactivity_fees", 0),
                "conversion_fees": fee_breakdown.get("conversion_fees", 0),
                "total": fee_breakdown.get("api_fees", 0) + fee_breakdown.get("inactivity_fees", 0) + fee_breakdown.get("conversion_fees", 0)
            }
        }
        
        # Calculate percentages
        total_fees = sum([cat["total"] for cat in fee_categories.values()])
        fee_percentages = {}
        
        for category, data in fee_categories.items():
            fee_percentages[category] = {
                "percentage": (data["total"] / total_fees * 100) if total_fees > 0 else 0,
                "amount": data["total"]
            }
        
        # Fee trends over time
        fee_trends = await portfolio_manager.get_fee_trends(
            user_id=current_user["username"],
            period=period
        )
        
        # Cost per trade analysis
        trade_count = fee_breakdown.get("total_trades", 0)
        cost_per_trade = total_fees / trade_count if trade_count > 0 else 0
        
        cost_analysis = {
            "total_fees": total_fees,
            "total_trades": trade_count,
            "cost_per_trade": cost_per_trade,
            "fees_as_percent_of_volume": (total_fees / fee_breakdown.get("total_volume", 1)) * 100 if fee_breakdown.get("total_volume", 0) > 0 else 0
        }
        
        return {
            "fee_categories": fee_categories,
            "fee_percentages": fee_percentages,
            "fee_trends": fee_trends,
            "cost_analysis": cost_analysis,
            "period": period,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "success"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting fee breakdown: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get fee breakdown"
        )


# Helper functions

def calculate_fee_metrics(fee_analysis: Dict[str, Any], period: str) -> Dict[str, Any]:
    """Calculate comprehensive fee metrics"""
    total_fees = fee_analysis.get("total_fees", 0)
    total_volume = fee_analysis.get("total_volume", 0)
    total_trades = fee_analysis.get("total_trades", 0)
    total_profit = fee_analysis.get("total_profit", 0)
    
    return {
        "total_fees": total_fees,
        "average_fee_rate": (total_fees / total_volume * 100) if total_volume > 0 else 0,
        "fees_per_trade": total_fees / total_trades if total_trades > 0 else 0,
        "fees_as_percent_of_profit": (total_fees / total_profit * 100) if total_profit > 0 else 0,
        "maker_ratio": fee_analysis.get("maker_ratio", 0),
        "taker_ratio": 1 - fee_analysis.get("maker_ratio", 0),
        "period_analyzed": period
    }


def get_exchange_fee_structure(exchange: str = "binance") -> Dict[str, Any]:
    """Get fee structure for different exchanges"""
    fee_structures = {
        "binance": {
            "maker_fee": 0.001,  # 0.1%
            "taker_fee": 0.001,  # 0.1%
            "vip_tiers": {
                "vip_1": {"maker": 0.0009, "taker": 0.001, "volume_required": 100000},
                "vip_2": {"maker": 0.0008, "taker": 0.001, "volume_required": 500000},
                "vip_3": {"maker": 0.0007, "taker": 0.0009, "volume_required": 1000000}
            },
            "withdrawal_fees": {"btc": 0.0005, "eth": 0.005, "usdt": 1},
            "deposit_fees": 0,
            "maker_taker_ratio": 0.6
        },
        "coinbase_pro": {
            "maker_fee": 0.005,  # 0.5%
            "taker_fee": 0.005,  # 0.5%
            "vip_tiers": {
                "tier_1": {"maker": 0.004, "taker": 0.006, "volume_required": 10000},
                "tier_2": {"maker": 0.0035, "taker": 0.0055, "volume_required": 50000},
                "tier_3": {"maker": 0.003, "taker": 0.005, "volume_required": 100000}
            },
            "withdrawal_fees": {"btc": 0, "eth": 0, "usdt": 0},
            "deposit_fees": 0,
            "maker_taker_ratio": 0.4
        },
        "kraken": {
            "maker_fee": 0.0016,  # 0.16%
            "taker_fee": 0.0026,  # 0.26%
            "vip_tiers": {
                "tier_1": {"maker": 0.0014, "taker": 0.0024, "volume_required": 50000},
                "tier_2": {"maker": 0.0012, "taker": 0.0022, "volume_required": 100000},
                "tier_3": {"maker": 0.001, "taker": 0.002, "volume_required": 250000}
            },
            "withdrawal_fees": {"btc": 0.00015, "eth": 0.0025, "usdt": 5},
            "deposit_fees": 0,
            "maker_taker_ratio": 0.5
        }
    }
    
    return fee_structures.get(exchange, fee_structures["binance"])


def calculate_fee_efficiency(fee_analysis: Dict[str, Any], exchange_fees: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate fee efficiency metrics"""
    actual_rate = fee_analysis.get("average_fee_rate", 0)
    expected_rate = (exchange_fees["maker_fee"] + exchange_fees["taker_fee"]) / 2 * 100
    
    efficiency = (expected_rate - actual_rate) / expected_rate * 100 if expected_rate > 0 else 0
    
    return {
        "actual_average_rate": actual_rate,
        "expected_average_rate": expected_rate,
        "efficiency_score": max(0, efficiency),
        "efficiency_grade": get_efficiency_grade(efficiency),
        "maker_usage_optimization": fee_analysis.get("maker_ratio", 0) * 100
    }


def get_efficiency_grade(efficiency: float) -> str:
    """Convert efficiency score to letter grade"""
    if efficiency >= 90:
        return "A+"
    elif efficiency >= 80:
        return "A"
    elif efficiency >= 70:
        return "B+"
    elif efficiency >= 60:
        return "B"
    elif efficiency >= 50:
        return "C+"
    elif efficiency >= 40:
        return "C"
    else:
        return "D"


def generate_fee_optimization_suggestions(
    fee_analysis: Dict[str, Any], 
    fee_metrics: Dict[str, Any], 
    exchange_fees: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """Generate fee optimization suggestions"""
    suggestions = []
    
    # Maker ratio optimization
    if fee_metrics.get("maker_ratio", 0) < 0.6:
        suggestions.append({
            "type": "order_type",
            "priority": "high",
            "title": "Increase Maker Order Usage",
            "description": f"Your maker ratio is {fee_metrics.get('maker_ratio', 0)*100:.1f}%. Increase limit orders to reduce fees.",
            "potential_savings_percent": 15
        })
    
    # VIP tier opportunity
    monthly_volume = fee_analysis.get("total_volume", 0)
    for tier, requirements in exchange_fees.get("vip_tiers", {}).items():
        if monthly_volume >= requirements["volume_required"] * 0.8:
            potential_savings = (exchange_fees["taker_fee"] - requirements["taker"]) * monthly_volume
            suggestions.append({
                "type": "vip_tier",
                "priority": "medium",
                "title": f"Qualify for {tier.upper()}",
                "description": f"You're close to {tier} benefits. Potential savings: ${potential_savings:.2f}/month",
                "potential_savings_usd": potential_savings
            })
            break
    
    # High fee percentage
    if fee_metrics.get("fees_as_percent_of_profit", 0) > 30:
        suggestions.append({
            "type": "strategy",
            "priority": "high",
            "title": "High Fee Impact on Profits",
            "description": f"Fees are {fee_metrics.get('fees_as_percent_of_profit', 0):.1f}% of profits. Consider reducing trade frequency.",
            "potential_savings_percent": 25
        })
    
    return suggestions


def get_fee_benchmarks(fee_analysis: Dict[str, Any]) -> Dict[str, Any]:
    """Get fee benchmarks for comparison"""
    actual_rate = fee_analysis.get("average_fee_rate", 0)
    
    benchmarks = {
        "retail_trader": {"rate": 0.25, "description": "Typical retail trader"},
        "active_trader": {"rate": 0.15, "description": "Active trader with some optimization"},
        "professional": {"rate": 0.08, "description": "Professional trader"},
        "institutional": {"rate": 0.05, "description": "Institutional level"}
    }
    
    # Find user's category
    user_category = "retail_trader"
    for category, data in benchmarks.items():
        if actual_rate <= data["rate"]:
            user_category = category
            break
    
    return {
        "benchmarks": benchmarks,
        "user_category": user_category,
        "percentile": calculate_fee_percentile(actual_rate)
    }


def calculate_fee_percentile(fee_rate: float) -> float:
    """Calculate what percentile the user's fee rate represents"""
    # Simplified percentile calculation
    if fee_rate <= 0.05:
        return 95  # Top 5%
    elif fee_rate <= 0.08:
        return 85  # Top 15%
    elif fee_rate <= 0.15:
        return 70  # Top 30%
    elif fee_rate <= 0.25:
        return 50  # Median
    else:
        return 25  # Below median


def calculate_optimization_scenarios(trade_size: float, frequency: int) -> Dict[str, Any]:
    """Calculate different optimization scenarios"""
    monthly_volume = trade_size * frequency
    
    scenarios = {
        "current": {
            "description": "Current trading pattern",
            "monthly_fees": monthly_volume * 0.001,  # Assume 0.1% fee
            "annual_fees": monthly_volume * 0.001 * 12
        },
        "optimized_maker": {
            "description": "80% maker orders",
            "monthly_fees": monthly_volume * (0.8 * 0.0005 + 0.2 * 0.001),  # 80% maker, 20% taker
            "annual_fees": monthly_volume * (0.8 * 0.0005 + 0.2 * 0.001) * 12
        },
        "vip_tier": {
            "description": "VIP tier benefits",
            "monthly_fees": monthly_volume * 0.0008,  # VIP rate
            "annual_fees": monthly_volume * 0.0008 * 12
        }
    }
    
    # Calculate savings
    current_fees = scenarios["current"]["monthly_fees"]
    for scenario in ["optimized_maker", "vip_tier"]:
        savings = current_fees - scenarios[scenario]["monthly_fees"]
        scenarios[scenario]["monthly_savings"] = savings
        scenarios[scenario]["annual_savings"] = savings * 12
        scenarios[scenario]["savings_percent"] = (savings / current_fees * 100) if current_fees > 0 else 0
    
    return scenarios


def analyze_order_type_efficiency(trade_size: float, frequency: int) -> Dict[str, Any]:
    """Analyze efficiency of different order types"""
    monthly_volume = trade_size * frequency
    
    order_types = {
        "market_only": {
            "fee_rate": 0.001,  # 0.1% taker
            "execution_rate": 1.0,
            "slippage": 0.0005  # 0.05% average slippage
        },
        "limit_only": {
            "fee_rate": 0.0005,  # 0.05% maker
            "execution_rate": 0.7,  # 70% fill rate
            "slippage": 0
        },
        "mixed_strategy": {
            "fee_rate": 0.00075,  # Mix of maker/taker
            "execution_rate": 0.9,
            "slippage": 0.0002
        }
    }
    
    # Calculate total costs including fees and slippage
    for order_type, data in order_types.items():
        total_cost_rate = data["fee_rate"] + data["slippage"]
        data["monthly_cost"] = monthly_volume * total_cost_rate
        data["annual_cost"] = data["monthly_cost"] * 12
        data["effectiveness_score"] = data["execution_rate"] / total_cost_rate
    
    return order_types


def compare_exchange_fees(trade_size: float, frequency: int) -> Dict[str, Any]:
    """Compare fees across exchanges for given trading pattern"""
    monthly_volume = trade_size * frequency
    exchanges = ["binance", "coinbase_pro", "kraken"]
    
    comparison = {}
    for exchange in exchanges:
        fee_structure = get_exchange_fee_structure(exchange)
        
        # Assume 60% maker, 40% taker
        effective_rate = 0.6 * fee_structure["maker_fee"] + 0.4 * fee_structure["taker_fee"]
        monthly_fees = monthly_volume * effective_rate
        
        comparison[exchange] = {
            "effective_rate": effective_rate,
            "monthly_fees": monthly_fees,
            "annual_fees": monthly_fees * 12
        }
    
    # Find cheapest
    cheapest = min(comparison.items(), key=lambda x: x[1]["monthly_fees"])
    
    return {
        "comparison": comparison,
        "cheapest_exchange": cheapest[0],
        "max_monthly_savings": max([data["monthly_fees"] for data in comparison.values()]) - cheapest[1]["monthly_fees"]
    }


def analyze_vip_tier_benefits(trade_size: float, frequency: int) -> Dict[str, Any]:
    """Analyze VIP tier benefits and requirements"""
    monthly_volume = trade_size * frequency
    
    vip_analysis = {
        "current_volume": monthly_volume,
        "tier_progress": {},
        "recommendations": []
    }
    
    # Check progress toward different VIP tiers
    fee_structure = get_exchange_fee_structure()
    for tier, requirements in fee_structure.get("vip_tiers", {}).items():
        required_volume = requirements["volume_required"]
        progress = min(100, (monthly_volume / required_volume) * 100)
        
        vip_analysis["tier_progress"][tier] = {
            "progress_percent": progress,
            "volume_needed": max(0, required_volume - monthly_volume),
            "potential_savings": (fee_structure["taker_fee"] - requirements["taker"]) * monthly_volume
        }
        
        # Add recommendation if close to tier
        if 80 <= progress < 100:
            vip_analysis["recommendations"].append({
                "tier": tier,
                "volume_needed": required_volume - monthly_volume,
                "potential_monthly_savings": (fee_structure["taker_fee"] - requirements["taker"]) * monthly_volume
            })
    
    return vip_analysis


def calculate_potential_savings(
    optimization_scenarios: Dict,
    order_type_analysis: Dict, 
    vip_tier_analysis: Dict
) -> Dict[str, Any]:
    """Calculate total potential savings from all optimizations"""
    
    # Get maximum savings from each category
    scenario_savings = max([
        scenario.get("monthly_savings", 0) 
        for scenario in optimization_scenarios.values() 
        if "monthly_savings" in scenario
    ])
    
    current_cost = min([data["monthly_cost"] for data in order_type_analysis.values()])
    order_type_savings = max([data["monthly_cost"] for data in order_type_analysis.values()]) - current_cost
    
    vip_savings = max([
        tier.get("potential_savings", 0) 
        for tier in vip_tier_analysis.get("tier_progress", {}).values()
    ])
    
    total_monthly_savings = scenario_savings + order_type_savings + vip_savings
    
    return {
        "monthly_savings": {
            "optimization_scenarios": scenario_savings,
            "order_type_efficiency": order_type_savings,
            "vip_tier_benefits": vip_savings,
            "total": total_monthly_savings
        },
        "annual_savings": {
            "total": total_monthly_savings * 12
        },
        "payback_period_months": 0,  # Immediate savings
        "roi_percent": float('inf') if total_monthly_savings > 0 else 0
    }


def rank_exchanges_by_cost(exchange_comparison: Dict, trading_profile: Dict) -> List[Dict[str, Any]]:
    """Rank exchanges by total cost efficiency"""
    rankings = []
    
    for exchange, data in exchange_comparison.items():
        total_monthly_cost = (
            data["estimated_monthly_fees"] + 
            data.get("withdrawal_fees", {}).get("btc", 0) * trading_profile.get("monthly_withdrawals", 1) * 50000 +  # Assume $50k BTC
            data.get("deposit_fees", 0) * trading_profile.get("monthly_deposits", 1)
        )
        
        rankings.append({
            "exchange": exchange,
            "total_monthly_cost": total_monthly_cost,
            "trading_fees": data["estimated_monthly_fees"],
            "other_fees": total_monthly_cost - data["estimated_monthly_fees"]
        })
    
    return sorted(rankings, key=lambda x: x["total_monthly_cost"])


def calculate_exchange_savings(
    exchange_comparison: Dict, 
    current_exchange: str, 
    trading_profile: Dict
) -> Dict[str, Any]:
    """Calculate savings from switching exchanges"""
    if current_exchange == "unknown":
        return {"message": "Current exchange unknown, cannot calculate savings"}
    
    current_fees = exchange_comparison.get(current_exchange, {}).get("estimated_monthly_fees", 0)
    
    savings_opportunities = {}
    for exchange, data in exchange_comparison.items():
        if exchange != current_exchange:
            monthly_savings = current_fees - data["estimated_monthly_fees"]
            if monthly_savings > 0:
                savings_opportunities[exchange] = {
                    "monthly_savings": monthly_savings,
                    "annual_savings": monthly_savings * 12,
                    "savings_percent": (monthly_savings / current_fees * 100) if current_fees > 0 else 0
                }
    
    return savings_opportunities


def calculate_estimated_fees(fee_structure: Dict, trading_profile: Dict) -> Dict[str, Any]:
    """Calculate estimated fees based on trading profile"""
    monthly_volume = trading_profile.get("monthly_volume", 10000)
    maker_ratio = trading_profile.get("maker_ratio", 0.6)
    
    monthly_fees = (
        monthly_volume * maker_ratio * fee_structure["maker_fee"] +
        monthly_volume * (1 - maker_ratio) * fee_structure["taker_fee"]
    )
    
    return {
        "monthly_fees": monthly_fees,
        "annual_fees": monthly_fees * 12
    }