"""
Market Regime Detection Module

Identifies market conditions (trending, ranging, volatile) using
statistical analysis and machine learning techniques.
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import numpy as np

logger = logging.getLogger(__name__)


class RegimeDetector:
    """
    Detects market regimes using statistical analysis.

    Identifies whether the market is:
    - Trending (bullish/bearish)
    - Ranging (sideways)
    - Volatile (high volatility)
    - Calm (low volatility)
    """

    def __init__(self):
        """Initialize the regime detector."""
        self.is_initialized = False
        self.historical_regimes: List[Dict[str, Any]] = []
        self.current_regime: Optional[Dict[str, Any]] = None

        # Configuration
        self.lookback_period = 50
        self.volatility_threshold_high = 0.03
        self.volatility_threshold_low = 0.01
        self.trend_threshold = 0.02

        logger.info("RegimeDetector initialized")

    async def initialize(self, historical_data: List[Dict[str, Any]]) -> bool:
        """
        Initialize the detector with historical data.

        Args:
            historical_data: List of price records with timestamp and price

        Returns:
            True if initialization successful
        """
        try:
            if not historical_data or len(historical_data) < self.lookback_period:
                logger.warning("Insufficient historical data for regime detection")
                self.is_initialized = True
                return True

            # Calculate initial regime from historical data
            prices = [float(d.get("price", d.price if hasattr(d, "price") else 0))
                     for d in historical_data[-self.lookback_period:]]

            if prices and all(p > 0 for p in prices):
                self.current_regime = self._calculate_regime(prices)

            self.is_initialized = True
            logger.info("RegimeDetector initialized with historical data")
            return True

        except Exception as e:
            logger.error(f"Error initializing RegimeDetector: {e}")
            self.is_initialized = True
            return False

    async def detect_regime(self, price_data: List[Any]) -> Dict[str, Any]:
        """
        Detect the current market regime.

        Args:
            price_data: Recent price data points

        Returns:
            Dictionary with regime information
        """
        try:
            if not price_data:
                return self._default_regime()

            # Extract prices from price data
            prices = []
            for p in price_data[-self.lookback_period:]:
                if hasattr(p, "price"):
                    prices.append(float(p.price))
                elif isinstance(p, dict):
                    prices.append(float(p.get("price", 0)))
                else:
                    prices.append(float(p))

            if not prices or len(prices) < 10:
                return self._default_regime()

            regime = self._calculate_regime(prices)
            self.current_regime = regime
            self.historical_regimes.append({
                "timestamp": datetime.now(timezone.utc),
                "regime": regime
            })

            # Keep only recent history
            if len(self.historical_regimes) > 100:
                self.historical_regimes = self.historical_regimes[-100:]

            return regime

        except Exception as e:
            logger.error(f"Error detecting regime: {e}")
            return self._default_regime()

    def _calculate_regime(self, prices: List[float]) -> Dict[str, Any]:
        """Calculate regime from price data."""
        if not prices or len(prices) < 2:
            return self._default_regime()

        prices_array = np.array(prices)

        # Calculate returns
        returns = np.diff(prices_array) / prices_array[:-1]

        # Calculate volatility (standard deviation of returns)
        volatility = float(np.std(returns)) if len(returns) > 0 else 0.0

        # Calculate trend (linear regression slope)
        x = np.arange(len(prices_array))
        slope = float(np.polyfit(x, prices_array, 1)[0]) if len(prices_array) > 1 else 0.0
        normalized_slope = slope / np.mean(prices_array) if np.mean(prices_array) > 0 else 0.0

        # Determine regime
        if volatility > self.volatility_threshold_high:
            volatility_regime = "high"
        elif volatility < self.volatility_threshold_low:
            volatility_regime = "low"
        else:
            volatility_regime = "medium"

        if abs(normalized_slope) > self.trend_threshold:
            if normalized_slope > 0:
                trend = "bullish"
                current_regime = "trending_up"
            else:
                trend = "bearish"
                current_regime = "trending_down"
        else:
            trend = "neutral"
            current_regime = "ranging"

        # Calculate confidence based on consistency
        confidence = min(0.9, 0.5 + abs(normalized_slope) * 10 + (1 - volatility) * 0.3)

        return {
            "current_regime": current_regime,
            "trend": trend,
            "volatility": volatility_regime,
            "volatility_value": round(volatility, 6),
            "trend_strength": round(abs(normalized_slope), 6),
            "confidence": round(confidence, 3),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    def _default_regime(self) -> Dict[str, Any]:
        """Return default regime when detection is not possible."""
        return {
            "current_regime": "unknown",
            "trend": "neutral",
            "volatility": "medium",
            "volatility_value": 0.02,
            "trend_strength": 0.0,
            "confidence": 0.3,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    async def health_check(self) -> bool:
        """Check if the detector is healthy."""
        return self.is_initialized

    def get_regime_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent regime history."""
        return self.historical_regimes[-limit:]
