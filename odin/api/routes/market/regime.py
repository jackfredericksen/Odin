# odin/api/routes/market/regime.py
"""
Market regime analysis endpoints
"""

import logging
from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from odin.api.dependencies import get_strategy_rate_limiter, validate_timeframe
from odin.core.data_collector import BitcoinDataCollector
from odin.strategies.moving_average import MovingAverageStrategy

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/", response_model=Dict[str, Any])
async def get_market_regime(
    hours: int = Query(168, description="Hours of data for regime analysis"),
    rate_limiter=Depends(get_strategy_rate_limiter),
    validated_hours: int = Depends(validate_timeframe),
):
    """Analyze current market regime and provide trading recommendations"""
    try:
        # Get market data
        data_collector = BitcoinDataCollector()
        market_data = await data_collector.get_price_history(hours=validated_hours)

        if not market_data or len(market_data) < 50:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Insufficient data for regime analysis",
            )

        # Market regime analysis using multiple indicators
        ma_strategy = MovingAverageStrategy()
        regime_analysis = await ma_strategy.analyze_market_regime(hours=validated_hours)

        # Calculate additional regime indicators
        current_price = market_data[0].price
        sma_20 = sum([point.price for point in market_data[:20]]) / 20
        sma_50 = sum([point.price for point in market_data[:50]]) / 50

        # Volatility analysis
        returns = [
            (market_data[i].price / market_data[i + 1].price - 1)
            for i in range(min(30, len(market_data) - 1))
        ]
        volatility = (sum([r**2 for r in returns]) / len(returns)) ** 0.5 * (365**0.5)

        # Trend strength
        trend_strength = abs(current_price - sma_50) / sma_50
        trend_direction = (
            "up"
            if current_price > sma_20 > sma_50
            else "down" if current_price < sma_20 < sma_50 else "sideways"
        )

        # Market regime classification
        regime = "unknown"
        confidence = 0.5

        if volatility < 0.4 and trend_strength < 0.05:
            regime = "low_volatility"
            confidence = 0.8
        elif volatility > 0.8:
            regime = "volatile"
            confidence = 0.9
        elif trend_direction == "up" and trend_strength > 0.1:
            regime = "trending_up"
            confidence = 0.85
        elif trend_direction == "down" and trend_strength > 0.1:
            regime = "trending_down"
            confidence = 0.85
        else:
            regime = "sideways"
            confidence = 0.7

        # Strategy recommendations based on regime
        strategy_recommendations = {
            "trending_up": {
                "primary": ["ma", "macd"],
                "allocation": {"ma": 60, "macd": 40},
                "risk_level": "medium",
            },
            "trending_down": {
                "primary": ["ma", "macd"],
                "allocation": {"ma": 70, "macd": 30},
                "risk_level": "high",
            },
            "sideways": {
                "primary": ["rsi", "bb"],
                "allocation": {"rsi": 50, "bb": 50},
                "risk_level": "low",
            },
            "volatile": {
                "primary": ["bb", "rsi"],
                "allocation": {"bb": 70, "rsi": 30},
                "risk_level": "high",
            },
            "low_volatility": {
                "primary": ["ma", "macd"],
                "allocation": {"ma": 55, "macd": 45},
                "risk_level": "low",
            },
        }

        current_recommendation = strategy_recommendations.get(
            regime, strategy_recommendations["sideways"]
        )

        # Market conditions summary
        market_conditions = {
            "current_price": current_price,
            "sma_20": sma_20,
            "sma_50": sma_50,
            "volatility_annual": volatility,
            "trend_strength": trend_strength,
            "trend_direction": trend_direction,
            "price_vs_sma20": (current_price - sma_20) / sma_20,
            "price_vs_sma50": (current_price - sma_50) / sma_50,
        }

        return {
            "market_regime": {
                "regime": regime,
                "confidence": confidence,
                "description": get_regime_description(regime),
            },
            "market_conditions": market_conditions,
            "strategy_recommendations": current_recommendation,
            "regime_analysis": regime_analysis,
            "hours_analyzed": validated_hours,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "success",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing market regime: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to analyze market regime",
        )


@router.get("/conditions", response_model=Dict[str, Any])
async def get_market_conditions(rate_limiter=Depends(get_strategy_rate_limiter)):
    """Get current market conditions and key metrics"""
    try:
        data_collector = BitcoinDataCollector()

        # Get current market data
        current_data = await data_collector.get_current_data()
        recent_data = await data_collector.get_recent_data(limit=100)

        if not current_data or not recent_data:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Unable to fetch current market data",
            )

        # Calculate market metrics
        prices = [point.price for point in recent_data]
        volumes = [point.volume for point in recent_data if point.volume]

        # Price metrics
        price_metrics = {
            "current_price": current_data.price,
            "24h_change": current_data.change_24h,
            "24h_high": current_data.high_24h,
            "24h_low": current_data.low_24h,
            "24h_range_percent": (
                (
                    (current_data.high_24h - current_data.low_24h)
                    / current_data.low_24h
                    * 100
                )
                if current_data.low_24h
                else 0
            ),
        }

        # Volume metrics
        avg_volume = sum(volumes) / len(volumes) if volumes else 0
        volume_metrics = {
            "current_volume": current_data.volume_24h,
            "average_volume": avg_volume,
            "volume_ratio": (
                current_data.volume_24h / avg_volume if avg_volume > 0 else 1
            ),
            "volume_trend": (
                "high"
                if current_data.volume_24h > avg_volume * 1.5
                else "low" if current_data.volume_24h < avg_volume * 0.5 else "normal"
            ),
        }

        # Volatility analysis
        if len(prices) >= 30:
            returns = [(prices[i] / prices[i + 1] - 1) for i in range(29)]
            realized_vol = (sum([r**2 for r in returns]) / len(returns)) ** 0.5 * (
                365**0.5
            )
            volatility_percentile = calculate_volatility_percentile(realized_vol)
        else:
            realized_vol = 0
            volatility_percentile = 50

        volatility_metrics = {
            "realized_volatility": realized_vol,
            "volatility_percentile": volatility_percentile,
            "volatility_regime": get_volatility_regime(volatility_percentile),
        }

        # Market momentum
        if len(prices) >= 10:
            momentum_short = (prices[0] - prices[4]) / prices[4]  # 5-period
            momentum_long = (prices[0] - prices[9]) / prices[9]  # 10-period
        else:
            momentum_short = 0
            momentum_long = 0

        momentum_metrics = {
            "short_term_momentum": momentum_short,
            "long_term_momentum": momentum_long,
            "momentum_divergence": momentum_short - momentum_long,
            "momentum_strength": "strong" if abs(momentum_short) > 0.05 else "weak",
        }

        # Overall market assessment
        market_sentiment = assess_market_sentiment(
            price_metrics["24h_change"],
            volume_metrics["volume_ratio"],
            volatility_percentile,
            momentum_short,
        )

        return {
            "price_metrics": price_metrics,
            "volume_metrics": volume_metrics,
            "volatility_metrics": volatility_metrics,
            "momentum_metrics": momentum_metrics,
            "market_sentiment": market_sentiment,
            "data_quality": {
                "data_points": len(recent_data),
                "last_update": (
                    current_data.timestamp.isoformat()
                    if hasattr(current_data, "timestamp")
                    else datetime.utcnow().isoformat()
                ),
                "source": (
                    current_data.source
                    if hasattr(current_data, "source")
                    else "unknown"
                ),
            },
            "timestamp": datetime.utcnow().isoformat(),
            "status": "success",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting market conditions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get market conditions",
        )


@router.get("/volatility", response_model=Dict[str, Any])
async def get_volatility_analysis(
    hours: int = Query(168, description="Hours for volatility analysis"),
    rate_limiter=Depends(get_strategy_rate_limiter),
    validated_hours: int = Depends(validate_timeframe),
):
    """Get detailed volatility analysis"""
    try:
        data_collector = BitcoinDataCollector()
        price_data = await data_collector.get_price_history(hours=validated_hours)

        if not price_data or len(price_data) < 30:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Insufficient data for volatility analysis",
            )

        prices = [point.price for point in price_data]

        # Calculate different volatility measures
        returns = [(prices[i] / prices[i + 1] - 1) for i in range(len(prices) - 1)]

        # Realized volatility (different windows)
        vol_1d = calculate_rolling_volatility(returns, 24)
        vol_7d = calculate_rolling_volatility(returns, 168)
        vol_30d = calculate_rolling_volatility(returns, 720)

        # Parkinson volatility (high-low estimator)
        parkinson_vol = 0
        if hasattr(price_data[0], "high") and hasattr(price_data[0], "low"):
            hl_ratios = [
                point.high / point.low
                for point in price_data
                if point.high and point.low
            ]
            if hl_ratios:
                parkinson_vol = (
                    sum([math.log(ratio) ** 2 for ratio in hl_ratios[:30]])
                    / len(hl_ratios[:30])
                ) ** 0.5 * (365**0.5)

        # Volatility clustering analysis
        volatility_clustering = analyze_volatility_clustering(returns)

        # Volatility regime classification
        current_vol = vol_1d[-1] if vol_1d else 0
        vol_percentile = calculate_volatility_percentile(current_vol)
        vol_regime = get_volatility_regime(vol_percentile)

        # GARCH-like volatility forecast
        vol_forecast = forecast_volatility(returns, periods=7)

        volatility_analysis = {
            "current_volatility": {
                "1_day": vol_1d[-1] if vol_1d else 0,
                "7_day": vol_7d[-1] if vol_7d else 0,
                "30_day": vol_30d[-1] if vol_30d else 0,
                "parkinson": parkinson_vol,
            },
            "volatility_trend": {
                "direction": (
                    "increasing"
                    if len(vol_7d) > 1 and vol_7d[-1] > vol_7d[-2]
                    else "decreasing"
                ),
                "rate_of_change": (
                    (vol_7d[-1] - vol_7d[-2]) / vol_7d[-2]
                    if len(vol_7d) > 1 and vol_7d[-2] != 0
                    else 0
                ),
            },
            "volatility_regime": {
                "current_regime": vol_regime,
                "percentile": vol_percentile,
                "clustering_coefficient": volatility_clustering,
            },
            "volatility_forecast": vol_forecast,
            "historical_comparison": {
                "vs_1_month_avg": (
                    (current_vol / (sum(vol_30d) / len(vol_30d)) - 1) if vol_30d else 0
                ),
                "vs_3_month_avg": calculate_vs_historical(current_vol, returns, 720),
                "vs_1_year_avg": calculate_vs_historical(current_vol, returns, 8760),
            },
        }

        return {
            "volatility_analysis": volatility_analysis,
            "hours_analyzed": validated_hours,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "success",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing volatility: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to analyze volatility",
        )


# Helper functions
def get_regime_description(regime: str) -> str:
    """Get human-readable description of market regime"""
    descriptions = {
        "trending_up": "Strong upward trend with momentum",
        "trending_down": "Strong downward trend with momentum",
        "sideways": "Range-bound market with no clear direction",
        "volatile": "High volatility with erratic price movements",
        "low_volatility": "Calm market with low volatility",
        "unknown": "Market regime unclear, mixed signals",
    }
    return descriptions.get(regime, "Unknown market regime")


def calculate_volatility_percentile(volatility: float) -> float:
    """Calculate volatility percentile based on historical Bitcoin data"""
    # Bitcoin historical volatility percentiles (approximate)
    vol_percentiles = {
        0.2: 10,
        0.3: 25,
        0.4: 40,
        0.5: 50,
        0.6: 60,
        0.8: 75,
        1.0: 85,
        1.5: 95,
        2.0: 99,
    }

    for vol_level, percentile in sorted(vol_percentiles.items()):
        if volatility <= vol_level:
            return percentile
    return 99


def get_volatility_regime(percentile: float) -> str:
    """Classify volatility regime based on percentile"""
    if percentile < 25:
        return "low"
    elif percentile < 75:
        return "normal"
    else:
        return "high"


def assess_market_sentiment(
    change_24h: float, volume_ratio: float, vol_percentile: float, momentum: float
) -> Dict[str, Any]:
    """Assess overall market sentiment"""
    sentiment_score = 0

    # Price change component
    if change_24h > 0.05:
        sentiment_score += 2
    elif change_24h > 0.02:
        sentiment_score += 1
    elif change_24h < -0.05:
        sentiment_score -= 2
    elif change_24h < -0.02:
        sentiment_score -= 1

    # Volume component
    if volume_ratio > 1.5:
        sentiment_score += 1
    elif volume_ratio < 0.5:
        sentiment_score -= 1

    # Volatility component (high vol can be negative)
    if vol_percentile > 85:
        sentiment_score -= 1

    # Momentum component
    if momentum > 0.03:
        sentiment_score += 1
    elif momentum < -0.03:
        sentiment_score -= 1

    # Classify sentiment
    if sentiment_score >= 3:
        sentiment = "very_bullish"
    elif sentiment_score >= 1:
        sentiment = "bullish"
    elif sentiment_score <= -3:
        sentiment = "very_bearish"
    elif sentiment_score <= -1:
        sentiment = "bearish"
    else:
        sentiment = "neutral"

    return {
        "sentiment": sentiment,
        "score": sentiment_score,
        "confidence": min(abs(sentiment_score) / 5 * 100, 100),
    }


def calculate_rolling_volatility(returns: list, window: int) -> list:
    """Calculate rolling volatility"""
    if len(returns) < window:
        return []

    rolling_vols = []
    for i in range(window, len(returns)):
        window_returns = returns[i - window : i]
        vol = (sum([r**2 for r in window_returns]) / len(window_returns)) ** 0.5 * (
            365**0.5
        )
        rolling_vols.append(vol)

    return rolling_vols


def analyze_volatility_clustering(returns: list) -> float:
    """Analyze volatility clustering using ARCH effects"""
    if len(returns) < 30:
        return 0

    # Simple volatility clustering measure
    abs_returns = [abs(r) for r in returns[:30]]
    correlations = []

    for lag in range(1, 6):
        if len(abs_returns) > lag:
            x = abs_returns[:-lag]
            y = abs_returns[lag:]
            if len(x) > 0 and len(y) > 0:
                correlation = calculate_correlation(x, y)
                correlations.append(correlation)

    return sum(correlations) / len(correlations) if correlations else 0


def calculate_correlation(x: list, y: list) -> float:
    """Calculate correlation coefficient"""
    if len(x) != len(y) or len(x) == 0:
        return 0

    mean_x = sum(x) / len(x)
    mean_y = sum(y) / len(y)

    numerator = sum([(x[i] - mean_x) * (y[i] - mean_y) for i in range(len(x))])

    sum_sq_x = sum([(xi - mean_x) ** 2 for xi in x])
    sum_sq_y = sum([(yi - mean_y) ** 2 for yi in y])

    denominator = (sum_sq_x * sum_sq_y) ** 0.5

    return numerator / denominator if denominator != 0 else 0


def forecast_volatility(returns: list, periods: int = 7) -> Dict[str, Any]:
    """Simple volatility forecasting"""
    if len(returns) < 30:
        return {"forecast": [], "method": "insufficient_data"}

    # Simple EWMA model
    current_vol = (sum([r**2 for r in returns[:30]]) / 30) ** 0.5
    lambda_param = 0.94  # Decay parameter

    forecast = []
    vol = current_vol

    for i in range(periods):
        vol = (lambda_param * vol**2 + (1 - lambda_param) * returns[0] ** 2) ** 0.5
        forecast.append(vol * (365**0.5))  # Annualized

    return {
        "forecast": forecast,
        "method": "ewma",
        "periods": periods,
        "average_forecast": sum(forecast) / len(forecast),
    }


def calculate_vs_historical(current_vol: float, returns: list, periods: int) -> float:
    """Calculate current volatility vs historical average"""
    if len(returns) < periods:
        return 0

    historical_vols = calculate_rolling_volatility(returns, min(30, len(returns) // 4))
    if not historical_vols:
        return 0

    avg_historical = sum(historical_vols) / len(historical_vols)
    return (current_vol / avg_historical - 1) if avg_historical != 0 else 0


# Import math for logarithmic calculations
import math
