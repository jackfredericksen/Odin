# odin/api/routes/market/depth.py
"""
Order book and market depth analysis endpoints
"""

import logging
import random
from datetime import datetime
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, Query, status

from odin.api.dependencies import get_strategy_rate_limiter
from odin.core.data_collector import BitcoinDataCollector

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/", response_model=Dict[str, Any])
async def get_market_depth(
    levels: int = Query(10, description="Number of order book levels"),
    rate_limiter=Depends(get_strategy_rate_limiter),
):
    """Get current market depth and order book data"""
    try:
        # Validate levels parameter
        if levels < 1 or levels > 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Levels must be between 1 and 100",
            )

        data_collector = BitcoinDataCollector()
        current_data = await data_collector.get_current_data()

        if not current_data:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Unable to fetch current market data",
            )

        current_price = current_data.price

        # Generate realistic order book data (in production, fetch from exchange)
        order_book = generate_order_book(current_price, levels)

        # Calculate market depth metrics
        depth_metrics = calculate_depth_metrics(order_book, current_price)

        # Calculate spread metrics
        best_bid = (
            order_book["bids"][0]["price"]
            if order_book["bids"]
            else current_price * 0.999
        )
        best_ask = (
            order_book["asks"][0]["price"]
            if order_book["asks"]
            else current_price * 1.001
        )

        spread_metrics = {
            "bid_ask_spread": best_ask - best_bid,
            "spread_bps": ((best_ask - best_bid) / current_price) * 10000,
            "mid_price": (best_bid + best_ask) / 2,
            "relative_spread": ((best_ask - best_bid) / ((best_bid + best_ask) / 2))
            * 100,
        }

        return {
            "order_book": order_book,
            "depth_metrics": depth_metrics,
            "spread_metrics": spread_metrics,
            "market_price": current_price,
            "levels": levels,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "success",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting market depth: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get market depth",
        )


@router.get("/impact", response_model=Dict[str, Any])
async def get_market_impact(
    trade_sizes: List[float] = Query(
        [1000, 5000, 10000, 25000, 50000], description="Trade sizes in USD"
    ),
    rate_limiter=Depends(get_strategy_rate_limiter),
):
    """Calculate market impact for different trade sizes"""
    try:
        # Validate trade sizes
        for size in trade_sizes:
            if size <= 0 or size > 1000000:  # Max 1M USD
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Trade sizes must be between 0 and 1,000,000 USD",
                )

        data_collector = BitcoinDataCollector()
        current_data = await data_collector.get_current_data()

        if not current_data:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Unable to fetch current market data",
            )

        current_price = current_data.price

        # Generate order book for impact calculation
        order_book = generate_order_book(current_price, 50)

        # Calculate market impact for each trade size
        impact_analysis = {}

        for size_usd in trade_sizes:
            # Calculate impact for both buy and sell orders
            buy_impact = calculate_trade_impact(
                order_book["asks"], size_usd, "buy", current_price
            )
            sell_impact = calculate_trade_impact(
                order_book["bids"], size_usd, "sell", current_price
            )

            impact_analysis[f"{int(size_usd)}_usd"] = {
                "trade_size_usd": size_usd,
                "trade_size_btc": size_usd / current_price,
                "buy_impact": buy_impact,
                "sell_impact": sell_impact,
                "average_impact": (buy_impact["impact_bps"] + sell_impact["impact_bps"])
                / 2,
            }

        # Market impact model parameters
        impact_model = {
            "linear_coefficient": 0.5,  # Impact per $1000 trade
            "square_root_coefficient": 2.0,  # Non-linear impact factor
            "liquidity_score": calculate_liquidity_score(order_book),
            "market_regime": assess_market_regime_for_impact(current_data),
        }

        return {
            "impact_analysis": impact_analysis,
            "impact_model": impact_model,
            "current_price": current_price,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "success",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculating market impact: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to calculate market impact",
        )


@router.get("/liquidity", response_model=Dict[str, Any])
async def get_liquidity_analysis(rate_limiter=Depends(get_strategy_rate_limiter)):
    """Get market liquidity analysis"""
    try:
        data_collector = BitcoinDataCollector()
        current_data = await data_collector.get_current_data()
        recent_data = await data_collector.get_recent_data(limit=100)

        if not current_data or not recent_data:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Unable to fetch market data",
            )

        current_price = current_data.price

        # Generate order book for liquidity analysis
        order_book = generate_order_book(current_price, 25)

        # Calculate liquidity metrics
        liquidity_metrics = calculate_comprehensive_liquidity_metrics(
            order_book, current_data, recent_data
        )

        # Volume-based liquidity indicators
        volumes = [point.volume for point in recent_data if point.volume]
        volume_metrics = {
            "current_volume": (
                current_data.volume_24h if hasattr(current_data, "volume_24h") else 0
            ),
            "average_volume": sum(volumes) / len(volumes) if volumes else 0,
            "volume_volatility": calculate_volume_volatility(volumes),
            "volume_trend": assess_volume_trend(volumes),
        }

        # Liquidity scoring (0-100)
        liquidity_score = calculate_overall_liquidity_score(
            liquidity_metrics, volume_metrics, order_book
        )

        # Liquidity risk assessment
        liquidity_risk = {
            "risk_level": get_liquidity_risk_level(liquidity_score),
            "risk_factors": identify_liquidity_risk_factors(liquidity_metrics),
            "recommendations": generate_liquidity_recommendations(
                liquidity_score, liquidity_metrics
            ),
        }

        return {
            "liquidity_metrics": liquidity_metrics,
            "volume_metrics": volume_metrics,
            "liquidity_score": liquidity_score,
            "liquidity_risk": liquidity_risk,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "success",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing liquidity: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to analyze liquidity",
        )


@router.get("/flow-analysis", response_model=Dict[str, Any])
async def get_order_flow_analysis(
    hours: int = Query(24, description="Hours for order flow analysis"),
    rate_limiter=Depends(get_strategy_rate_limiter),
):
    """Get order flow analysis"""
    try:
        if hours < 1 or hours > 168:  # Max 1 week
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Hours must be between 1 and 168",
            )

        data_collector = BitcoinDataCollector()
        recent_data = await data_collector.get_recent_data(
            limit=hours * 2
        )  # Approximate

        if not recent_data:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Unable to fetch market data",
            )

        # Analyze order flow patterns
        flow_analysis = analyze_order_flow_patterns(recent_data, hours)

        # Buy/sell pressure analysis
        pressure_analysis = calculate_buy_sell_pressure(recent_data)

        # Institutional vs retail flow indicators
        flow_classification = classify_order_flow(recent_data)

        # Flow-based predictions
        flow_signals = generate_flow_based_signals(flow_analysis, pressure_analysis)

        return {
            "flow_analysis": flow_analysis,
            "pressure_analysis": pressure_analysis,
            "flow_classification": flow_classification,
            "flow_signals": flow_signals,
            "hours_analyzed": hours,
            "data_points": len(recent_data),
            "timestamp": datetime.utcnow().isoformat(),
            "status": "success",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing order flow: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to analyze order flow",
        )


# Helper functions


def generate_order_book(current_price: float, levels: int) -> Dict[str, Any]:
    """Generate realistic order book data"""
    bids = []
    asks = []

    # Generate bids (below current price)
    for i in range(levels):
        price = current_price * (1 - (i + 1) * 0.001)  # 0.1% increments
        size = random.uniform(0.1, 2.0) * (1 + random.uniform(0, 1))  # BTC amount
        bids.append(
            {
                "price": round(price, 2),
                "size": round(size, 4),
                "value_usd": round(price * size, 2),
            }
        )

    # Generate asks (above current price)
    for i in range(levels):
        price = current_price * (1 + (i + 1) * 0.001)  # 0.1% increments
        size = random.uniform(0.1, 2.0) * (1 + random.uniform(0, 1))  # BTC amount
        asks.append(
            {
                "price": round(price, 2),
                "size": round(size, 4),
                "value_usd": round(price * size, 2),
            }
        )

    return {
        "bids": sorted(bids, key=lambda x: x["price"], reverse=True),
        "asks": sorted(asks, key=lambda x: x["price"]),
    }


def calculate_depth_metrics(
    order_book: Dict[str, Any], current_price: float
) -> Dict[str, Any]:
    """Calculate order book depth metrics"""
    bids = order_book["bids"]
    asks = order_book["asks"]

    # Calculate depth at different price levels
    depth_levels = [0.001, 0.005, 0.01, 0.02]  # 0.1%, 0.5%, 1%, 2%
    depth_metrics = {}

    for level in depth_levels:
        bid_depth = sum(
            [
                order["value_usd"]
                for order in bids
                if order["price"] >= current_price * (1 - level)
            ]
        )

        ask_depth = sum(
            [
                order["value_usd"]
                for order in asks
                if order["price"] <= current_price * (1 + level)
            ]
        )

        depth_metrics[f"depth_{int(level*1000)}bps"] = {
            "bid_depth_usd": bid_depth,
            "ask_depth_usd": ask_depth,
            "total_depth_usd": bid_depth + ask_depth,
            "depth_imbalance": (
                (bid_depth - ask_depth) / (bid_depth + ask_depth)
                if (bid_depth + ask_depth) > 0
                else 0
            ),
        }

    return depth_metrics


def calculate_trade_impact(
    orders: List[Dict], trade_size_usd: float, side: str, current_price: float
) -> Dict[str, Any]:
    """Calculate market impact for a trade"""
    remaining_size = trade_size_usd
    total_cost = 0
    filled_orders = []

    for order in orders:
        if remaining_size <= 0:
            break

        order_value = order["value_usd"]
        fill_amount = min(remaining_size, order_value)

        total_cost += fill_amount
        filled_orders.append(
            {
                "price": order["price"],
                "filled_usd": fill_amount,
                "remaining_after": remaining_size - fill_amount,
            }
        )

        remaining_size -= fill_amount

    if total_cost > 0:
        average_price = sum(
            [o["price"] * o["filled_usd"] for o in filled_orders]
        ) / sum([o["filled_usd"] for o in filled_orders])
        impact_bps = abs((average_price - current_price) / current_price) * 10000
    else:
        average_price = current_price
        impact_bps = 0

    return {
        "average_fill_price": average_price,
        "impact_bps": impact_bps,
        "total_filled_usd": trade_size_usd - remaining_size,
        "unfilled_usd": remaining_size,
        "fill_ratio": (
            (trade_size_usd - remaining_size) / trade_size_usd
            if trade_size_usd > 0
            else 0
        ),
        "orders_consumed": len(filled_orders),
    }


def calculate_liquidity_score(order_book: Dict[str, Any]) -> float:
    """Calculate overall liquidity score"""
    bids = order_book["bids"]
    asks = order_book["asks"]

    if not bids or not asks:
        return 0

    # Factors for liquidity scoring
    spread = asks[0]["price"] - bids[0]["price"]
    mid_price = (asks[0]["price"] + bids[0]["price"]) / 2
    relative_spread = spread / mid_price

    # Depth within 1%
    total_depth = sum([o["value_usd"] for o in bids[:10]]) + sum(
        [o["value_usd"] for o in asks[:10]]
    )

    # Number of levels
    levels_factor = min(len(bids), len(asks)) / 25  # Normalize to 25 levels

    # Calculate score (0-100)
    spread_score = max(0, 100 - relative_spread * 100000)  # Penalize wide spreads
    depth_score = min(100, total_depth / 1000)  # $100k depth = 100 score
    levels_score = levels_factor * 100

    return spread_score * 0.4 + depth_score * 0.4 + levels_score * 0.2


def assess_market_regime_for_impact(current_data) -> str:
    """Assess market regime for impact modeling"""
    if hasattr(current_data, "change_24h") and current_data.change_24h:
        if abs(current_data.change_24h) > 0.05:
            return "volatile"
        elif abs(current_data.change_24h) < 0.01:
            return "calm"
    return "normal"


def calculate_comprehensive_liquidity_metrics(
    order_book: Dict, current_data, recent_data
) -> Dict[str, Any]:
    """Calculate comprehensive liquidity metrics"""
    bids = order_book["bids"]
    asks = order_book["asks"]

    if not bids or not asks:
        return {}

    # Order book imbalance
    bid_volume = sum([order["size"] for order in bids[:10]])
    ask_volume = sum([order["size"] for order in asks[:10]])
    imbalance = (
        (bid_volume - ask_volume) / (bid_volume + ask_volume)
        if (bid_volume + ask_volume) > 0
        else 0
    )

    # Price levels concentration
    top_3_bids = sum([order["value_usd"] for order in bids[:3]])
    total_bids = sum([order["value_usd"] for order in bids])
    concentration = top_3_bids / total_bids if total_bids > 0 else 0

    return {
        "order_book_imbalance": imbalance,
        "concentration_ratio": concentration,
        "effective_spread_bps": (
            (asks[0]["price"] - bids[0]["price"])
            / ((asks[0]["price"] + bids[0]["price"]) / 2)
        )
        * 10000,
        "depth_1_percent": sum([o["value_usd"] for o in bids[:5]])
        + sum([o["value_usd"] for o in asks[:5]]),
        "resilience_score": calculate_resilience_score(order_book),
    }


def calculate_volume_volatility(volumes: List[float]) -> float:
    """Calculate volume volatility"""
    if len(volumes) < 2:
        return 0

    mean_vol = sum(volumes) / len(volumes)
    variance = sum([(v - mean_vol) ** 2 for v in volumes]) / len(volumes)
    return (variance**0.5) / mean_vol if mean_vol > 0 else 0


def assess_volume_trend(volumes: List[float]) -> str:
    """Assess volume trend"""
    if len(volumes) < 10:
        return "insufficient_data"

    recent_avg = sum(volumes[:5]) / 5
    older_avg = sum(volumes[5:10]) / 5

    if recent_avg > older_avg * 1.2:
        return "increasing"
    elif recent_avg < older_avg * 0.8:
        return "decreasing"
    else:
        return "stable"


def calculate_overall_liquidity_score(
    liquidity_metrics: Dict, volume_metrics: Dict, order_book: Dict
) -> float:
    """Calculate overall liquidity score (0-100)"""
    # Multiple factors contribute to liquidity score
    spread_score = max(0, 100 - liquidity_metrics.get("effective_spread_bps", 50))
    depth_score = min(100, liquidity_metrics.get("depth_1_percent", 0) / 1000)
    volume_score = min(
        100, volume_metrics.get("current_volume", 0) / 1000000
    )  # Normalize to 1M
    resilience_score = liquidity_metrics.get("resilience_score", 50)

    return (
        spread_score * 0.3
        + depth_score * 0.3
        + volume_score * 0.2
        + resilience_score * 0.2
    )


def get_liquidity_risk_level(score: float) -> str:
    """Get liquidity risk level based on score"""
    if score >= 80:
        return "low"
    elif score >= 60:
        return "medium"
    elif score >= 40:
        return "high"
    else:
        return "very_high"


def identify_liquidity_risk_factors(metrics: Dict) -> List[str]:
    """Identify specific liquidity risk factors"""
    risks = []

    if metrics.get("effective_spread_bps", 0) > 50:
        risks.append("wide_spreads")

    if abs(metrics.get("order_book_imbalance", 0)) > 0.3:
        risks.append("order_book_imbalance")

    if metrics.get("concentration_ratio", 0) > 0.7:
        risks.append("concentrated_liquidity")

    if metrics.get("depth_1_percent", 0) < 50000:
        risks.append("shallow_depth")

    return risks


def generate_liquidity_recommendations(score: float, metrics: Dict) -> List[str]:
    """Generate liquidity-based trading recommendations"""
    recommendations = []

    if score < 50:
        recommendations.append("Use limit orders to avoid market impact")
        recommendations.append("Break large orders into smaller sizes")
        recommendations.append("Consider trading during higher volume periods")

    if abs(metrics.get("order_book_imbalance", 0)) > 0.2:
        recommendations.append("Monitor order book imbalance for directional bias")

    if metrics.get("effective_spread_bps", 0) > 30:
        recommendations.append("Wide spreads detected - consider timing trades better")

    return recommendations


def calculate_resilience_score(order_book: Dict) -> float:
    """Calculate order book resilience score"""
    bids = order_book["bids"]
    asks = order_book["asks"]

    if len(bids) < 5 or len(asks) < 5:
        return 0

    # Measure depth distribution
    bid_distribution = [order["value_usd"] for order in bids[:10]]
    ask_distribution = [order["value_usd"] for order in asks[:10]]

    # More evenly distributed = more resilient
    bid_variance = sum(
        [
            (x - sum(bid_distribution) / len(bid_distribution)) ** 2
            for x in bid_distribution
        ]
    )
    ask_variance = sum(
        [
            (x - sum(ask_distribution) / len(ask_distribution)) ** 2
            for x in ask_distribution
        ]
    )

    # Lower variance = higher resilience (more evenly distributed)
    return max(0, 100 - (bid_variance + ask_variance) / 1000000)


def analyze_order_flow_patterns(recent_data: List, hours: int) -> Dict[str, Any]:
    """Analyze order flow patterns"""
    if not recent_data:
        return {}

    # Simplified order flow analysis based on price and volume
    prices = [point.price for point in recent_data]
    volumes = [point.volume for point in recent_data if point.volume]

    # Price momentum
    price_momentum = (
        (prices[0] - prices[-1]) / prices[-1]
        if len(prices) > 1 and prices[-1] != 0
        else 0
    )

    # Volume trend
    if len(volumes) >= 10:
        recent_vol = sum(volumes[:5]) / 5
        older_vol = sum(volumes[5:10]) / 5
        volume_momentum = (recent_vol - older_vol) / older_vol if older_vol != 0 else 0
    else:
        volume_momentum = 0

    return {
        "price_momentum": price_momentum,
        "volume_momentum": volume_momentum,
        "flow_direction": (
            "bullish"
            if price_momentum > 0 and volume_momentum > 0
            else "bearish" if price_momentum < 0 and volume_momentum > 0 else "neutral"
        ),
        "flow_strength": abs(price_momentum) + abs(volume_momentum),
    }


def calculate_buy_sell_pressure(recent_data: List) -> Dict[str, Any]:
    """Calculate buy/sell pressure indicators"""
    if len(recent_data) < 10:
        return {"buy_pressure": 0, "sell_pressure": 0, "net_pressure": 0}

    # Simplified pressure calculation based on price movements and volume
    buy_volume = 0
    sell_volume = 0

    for i in range(1, min(len(recent_data), 20)):
        if recent_data[i - 1].price > recent_data[i].price:  # Price increased
            buy_volume += recent_data[i - 1].volume if recent_data[i - 1].volume else 0
        else:  # Price decreased
            sell_volume += recent_data[i - 1].volume if recent_data[i - 1].volume else 0

    total_volume = buy_volume + sell_volume
    buy_pressure = buy_volume / total_volume if total_volume > 0 else 0.5
    sell_pressure = sell_volume / total_volume if total_volume > 0 else 0.5

    return {
        "buy_pressure": buy_pressure,
        "sell_pressure": sell_pressure,
        "net_pressure": buy_pressure - sell_pressure,
        "pressure_strength": abs(buy_pressure - sell_pressure),
    }


def classify_order_flow(recent_data: List) -> Dict[str, Any]:
    """Classify order flow as institutional vs retail"""
    if not recent_data:
        return {}

    # Simple classification based on volume patterns
    volumes = [point.volume for point in recent_data if point.volume]

    if len(volumes) < 10:
        return {"classification": "insufficient_data"}

    # Large volume spikes suggest institutional activity
    avg_volume = sum(volumes) / len(volumes)
    large_volume_count = len([v for v in volumes if v > avg_volume * 2])

    institutional_score = large_volume_count / len(volumes)

    return {
        "institutional_score": institutional_score,
        "retail_score": 1 - institutional_score,
        "classification": (
            "institutional"
            if institutional_score > 0.3
            else "mixed" if institutional_score > 0.1 else "retail"
        ),
        "large_order_frequency": large_volume_count / len(volumes),
    }


def generate_flow_based_signals(
    flow_analysis: Dict, pressure_analysis: Dict
) -> Dict[str, Any]:
    """Generate trading signals based on order flow"""
    signals = []

    if (
        flow_analysis.get("flow_direction") == "bullish"
        and pressure_analysis.get("net_pressure", 0) > 0.2
    ):
        signals.append(
            {
                "signal": "BUY",
                "strength": min(1.0, flow_analysis.get("flow_strength", 0) * 2),
                "reason": "Strong bullish flow with buy pressure",
            }
        )

    elif (
        flow_analysis.get("flow_direction") == "bearish"
        and pressure_analysis.get("net_pressure", 0) < -0.2
    ):
        signals.append(
            {
                "signal": "SELL",
                "strength": min(1.0, flow_analysis.get("flow_strength", 0) * 2),
                "reason": "Strong bearish flow with sell pressure",
            }
        )

    return {
        "signals": signals,
        "overall_bias": (
            "bullish"
            if pressure_analysis.get("net_pressure", 0) > 0
            else (
                "bearish" if pressure_analysis.get("net_pressure", 0) < 0 else "neutral"
            )
        ),
        "confidence": abs(pressure_analysis.get("net_pressure", 0)),
    }
