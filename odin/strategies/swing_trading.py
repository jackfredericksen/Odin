"""
Swing Trading Strategy

A multi-timeframe swing trading strategy that combines trend analysis
with momentum indicators to capture medium-term price swings.

Best For: Medium-term trades (days to weeks)
Strategy Type: Swing Trading / Trend Following
Signals: Multi-timeframe alignment, momentum confirmation
"""

import logging
from datetime import datetime
from typing import Any, Dict, Optional, Tuple

import numpy as np
import pandas as pd

from ..core.models import SignalType
from .base import Signal, Strategy, StrategyType

logger = logging.getLogger(__name__)


class SwingTradingStrategy(Strategy):
    """
    Advanced Swing Trading Strategy Implementation.

    Combines multiple indicators and timeframe analysis to identify
    high-probability swing trading opportunities.

    Features:
    - Multi-timeframe trend alignment
    - RSI for momentum confirmation
    - Moving average crossovers for trend direction
    - Support/resistance level detection
    - Risk/reward ratio filtering
    """

    def __init__(
        self,
        primary_timeframe: str = "4H",
        rsi_period: int = 14,
        rsi_oversold: int = 35,
        rsi_overbought: int = 65,
        ma_fast: int = 21,
        ma_slow: int = 50,
        min_risk_reward: float = 2.0,
        **kwargs
    ):
        """
        Initialize Swing Trading strategy.

        Args:
            primary_timeframe: Primary analysis timeframe
            rsi_period: Period for RSI calculation
            rsi_oversold: RSI oversold threshold
            rsi_overbought: RSI overbought threshold
            ma_fast: Fast moving average period
            ma_slow: Slow moving average period
            min_risk_reward: Minimum risk/reward ratio for trades
            **kwargs: Additional strategy parameters
        """
        super().__init__(
            name="SwingTrading",
            strategy_type=StrategyType.SWING,
            primary_timeframe=primary_timeframe,
            rsi_period=rsi_period,
            rsi_oversold=rsi_oversold,
            rsi_overbought=rsi_overbought,
            ma_fast=ma_fast,
            ma_slow=ma_slow,
            min_risk_reward=min_risk_reward,
            **kwargs
        )

        self.primary_timeframe = primary_timeframe
        self.rsi_period = rsi_period
        self.rsi_oversold = rsi_oversold
        self.rsi_overbought = rsi_overbought
        self.ma_fast = ma_fast
        self.ma_slow = ma_slow
        self.min_risk_reward = min_risk_reward

        # Validation
        if rsi_period < 2:
            raise ValueError("RSI period must be at least 2")
        if ma_fast >= ma_slow:
            raise ValueError("Fast MA must be smaller than slow MA")
        if min_risk_reward < 1.0:
            raise ValueError("Minimum risk/reward must be at least 1.0")

        # Track swing points
        self.recent_highs = []
        self.recent_lows = []
        self.swing_points = []

        self.logger.info(
            f"Initialized Swing Trading strategy: "
            f"RSI({rsi_period}), MA({ma_fast}/{ma_slow}), R:R={min_risk_reward}"
        )

    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate all indicators needed for swing trading.

        Args:
            data: Raw OHLCV price data

        Returns:
            Data with additional indicator columns
        """
        df = data.copy()

        # Moving Averages
        df["ma_fast"] = df["close"].rolling(window=self.ma_fast).mean()
        df["ma_slow"] = df["close"].rolling(window=self.ma_slow).mean()
        df["ma_trend"] = np.where(df["ma_fast"] > df["ma_slow"], 1, -1)

        # RSI
        df["rsi"] = self._calculate_rsi(df["close"], self.rsi_period)

        # ATR for volatility and stop placement
        df["atr"] = self._calculate_atr(df, period=14)

        # Swing highs and lows
        df["swing_high"] = self._detect_swing_highs(df["high"])
        df["swing_low"] = self._detect_swing_lows(df["low"])

        # Support and resistance levels
        df["nearest_support"] = self._find_nearest_support(df)
        df["nearest_resistance"] = self._find_nearest_resistance(df)

        # Trend strength (ADX simplified)
        df["trend_strength"] = self._calculate_trend_strength(df)

        # Price position relative to MAs
        df["price_vs_fast_ma"] = (df["close"] - df["ma_fast"]) / df["ma_fast"]
        df["price_vs_slow_ma"] = (df["close"] - df["ma_slow"]) / df["ma_slow"]

        # Momentum
        df["momentum"] = df["close"].pct_change(periods=5)

        # Volume analysis
        if "volume" in df.columns:
            df["volume_sma"] = df["volume"].rolling(window=20).mean()
            df["volume_ratio"] = df["volume"] / df["volume_sma"]
        else:
            df["volume_ratio"] = 1.0

        return df

    def generate_signal(self, data: pd.DataFrame) -> Signal:
        """
        Generate trading signal based on swing trading criteria.

        Args:
            data: OHLCV data with calculated indicators

        Returns:
            Trading signal with confidence and metadata
        """
        min_periods = max(self.ma_slow, self.rsi_period) + 5

        if len(data) < min_periods:
            return Signal(
                signal=SignalType.HOLD,
                confidence=0.0,
                timestamp=datetime.now(),
                price=data["close"].iloc[-1] if not data.empty else 0.0,
                reasoning="Insufficient data for swing trading analysis",
                indicators={},
                risk_score=1.0
            )

        # Get current values
        current = data.iloc[-1]
        previous = data.iloc[-2] if len(data) > 1 else current

        current_price = current["close"]
        rsi = current["rsi"]
        ma_trend = current["ma_trend"]
        ma_fast = current["ma_fast"]
        ma_slow = current["ma_slow"]

        timestamp = (
            current.name
            if hasattr(current.name, "to_pydatetime")
            else datetime.now()
        )

        # Generate signal
        signal_type, reasoning = self._evaluate_swing_opportunity(
            current, previous, data
        )

        # Calculate confidence
        confidence = self._calculate_confidence(current, signal_type)

        # Calculate risk score
        risk_score = self._calculate_risk_score(current)

        # Prepare indicators
        indicators = {
            "rsi": rsi,
            "ma_fast": ma_fast,
            "ma_slow": ma_slow,
            "ma_trend": ma_trend,
            "atr": current.get("atr", 0),
            "trend_strength": current.get("trend_strength", 0),
            "nearest_support": current.get("nearest_support", 0),
            "nearest_resistance": current.get("nearest_resistance", 0),
            "volume_ratio": current.get("volume_ratio", 1),
            "momentum": current.get("momentum", 0)
        }

        signal = Signal(
            signal=signal_type,
            confidence=confidence,
            timestamp=timestamp,
            price=current_price,
            reasoning=reasoning,
            indicators=indicators,
            risk_score=risk_score
        )

        self.last_signal = signal
        self.signals_history.append(signal)

        self.logger.debug(
            f"Generated signal: {signal_type.value} "
            f"(RSI: {rsi:.1f}, trend: {ma_trend}, confidence: {confidence:.3f})"
        )

        return signal

    def _evaluate_swing_opportunity(
        self,
        current: pd.Series,
        previous: pd.Series,
        data: pd.DataFrame
    ) -> Tuple[SignalType, str]:
        """Evaluate swing trading opportunity."""
        rsi = current["rsi"]
        ma_trend = current["ma_trend"]
        ma_fast = current["ma_fast"]
        ma_slow = current["ma_slow"]
        price = current["close"]
        trend_strength = current.get("trend_strength", 0)
        volume_ratio = current.get("volume_ratio", 1)

        # Check for MA crossover
        prev_ma_trend = previous["ma_trend"]
        ma_crossover_bull = ma_trend == 1 and prev_ma_trend == -1
        ma_crossover_bear = ma_trend == -1 and prev_ma_trend == 1

        # Bullish swing entry conditions
        if (
            ma_trend == 1 and  # Uptrend
            rsi < self.rsi_overbought and  # Not overbought
            rsi > self.rsi_oversold and  # Not oversold (avoiding falling knives)
            price > ma_fast  # Price above fast MA (pullback complete)
        ):
            if ma_crossover_bull:
                return (
                    SignalType.BUY,
                    f"Bullish MA crossover with RSI at {rsi:.1f} - swing entry"
                )
            elif rsi < 50 and trend_strength > 0.5:
                return (
                    SignalType.BUY,
                    f"Pullback in uptrend - RSI at {rsi:.1f}, strong trend"
                )

        # Bearish swing entry conditions
        elif (
            ma_trend == -1 and  # Downtrend
            rsi > self.rsi_oversold and  # Not oversold
            rsi < self.rsi_overbought and  # Not overbought (avoiding squeezes)
            price < ma_fast  # Price below fast MA (bounce complete)
        ):
            if ma_crossover_bear:
                return (
                    SignalType.SELL,
                    f"Bearish MA crossover with RSI at {rsi:.1f} - swing entry"
                )
            elif rsi > 50 and trend_strength > 0.5:
                return (
                    SignalType.SELL,
                    f"Bounce in downtrend - RSI at {rsi:.1f}, strong trend"
                )

        # Extreme conditions
        if rsi < self.rsi_oversold and ma_trend == 1:
            return (
                SignalType.BUY,
                f"Oversold in uptrend - RSI at {rsi:.1f}, potential bounce"
            )

        if rsi > self.rsi_overbought and ma_trend == -1:
            return (
                SignalType.SELL,
                f"Overbought in downtrend - RSI at {rsi:.1f}, potential reversal"
            )

        return (
            SignalType.HOLD,
            f"No clear swing setup - RSI: {rsi:.1f}, trend: {ma_trend}"
        )

    def _calculate_rsi(self, prices: pd.Series, period: int) -> pd.Series:
        """Calculate RSI indicator."""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))

        return rsi.fillna(50)

    def _calculate_atr(self, data: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calculate Average True Range."""
        high = data["high"]
        low = data["low"]
        close = data["close"]

        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())

        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean()

        return atr.fillna(0)

    def _detect_swing_highs(self, highs: pd.Series, lookback: int = 5) -> pd.Series:
        """Detect swing high points."""
        swing_highs = pd.Series(index=highs.index, dtype=float)

        for i in range(lookback, len(highs) - lookback):
            if highs.iloc[i] == max(highs.iloc[i-lookback:i+lookback+1]):
                swing_highs.iloc[i] = highs.iloc[i]

        return swing_highs

    def _detect_swing_lows(self, lows: pd.Series, lookback: int = 5) -> pd.Series:
        """Detect swing low points."""
        swing_lows = pd.Series(index=lows.index, dtype=float)

        for i in range(lookback, len(lows) - lookback):
            if lows.iloc[i] == min(lows.iloc[i-lookback:i+lookback+1]):
                swing_lows.iloc[i] = lows.iloc[i]

        return swing_lows

    def _find_nearest_support(self, data: pd.DataFrame) -> pd.Series:
        """Find nearest support level."""
        current_price = data["close"]
        swing_lows = data["swing_low"].dropna()

        nearest_support = pd.Series(index=data.index, dtype=float)

        for i in range(len(data)):
            price = current_price.iloc[i]
            relevant_lows = swing_lows[swing_lows.index < data.index[i]]
            below_price = relevant_lows[relevant_lows < price]

            if len(below_price) > 0:
                nearest_support.iloc[i] = below_price.iloc[-1]
            else:
                nearest_support.iloc[i] = price * 0.95  # Default 5% below

        return nearest_support

    def _find_nearest_resistance(self, data: pd.DataFrame) -> pd.Series:
        """Find nearest resistance level."""
        current_price = data["close"]
        swing_highs = data["swing_high"].dropna()

        nearest_resistance = pd.Series(index=data.index, dtype=float)

        for i in range(len(data)):
            price = current_price.iloc[i]
            relevant_highs = swing_highs[swing_highs.index < data.index[i]]
            above_price = relevant_highs[relevant_highs > price]

            if len(above_price) > 0:
                nearest_resistance.iloc[i] = above_price.iloc[-1]
            else:
                nearest_resistance.iloc[i] = price * 1.05  # Default 5% above

        return nearest_resistance

    def _calculate_trend_strength(self, data: pd.DataFrame) -> pd.Series:
        """Calculate trend strength (simplified ADX)."""
        ma_diff = abs(data["ma_fast"] - data["ma_slow"])
        ma_avg = (data["ma_fast"] + data["ma_slow"]) / 2
        trend_strength = (ma_diff / ma_avg).fillna(0)

        # Normalize to 0-1 range
        return trend_strength.clip(0, 0.1) * 10

    def _calculate_confidence(self, row: pd.Series, signal_type: SignalType) -> float:
        """Calculate signal confidence."""
        if signal_type == SignalType.HOLD:
            return 0.0

        confidence_factors = []

        # Trend alignment
        ma_trend = row.get("ma_trend", 0)
        if (signal_type == SignalType.BUY and ma_trend == 1) or \
           (signal_type == SignalType.SELL and ma_trend == -1):
            confidence_factors.append(0.8)
        else:
            confidence_factors.append(0.4)

        # RSI positioning
        rsi = row.get("rsi", 50)
        if signal_type == SignalType.BUY:
            rsi_conf = max(0, (self.rsi_overbought - rsi) / self.rsi_overbought)
        else:
            rsi_conf = max(0, (rsi - self.rsi_oversold) / (100 - self.rsi_oversold))
        confidence_factors.append(rsi_conf)

        # Trend strength
        trend_strength = row.get("trend_strength", 0.5)
        confidence_factors.append(min(1.0, trend_strength))

        # Volume confirmation
        volume_ratio = row.get("volume_ratio", 1)
        vol_conf = min(1.0, volume_ratio / 1.5) if volume_ratio > 1 else 0.5
        confidence_factors.append(vol_conf)

        return sum(confidence_factors) / len(confidence_factors)

    def _calculate_risk_score(self, row: pd.Series) -> float:
        """Calculate risk score."""
        risk_factors = []

        # ATR-based volatility risk
        atr = row.get("atr", 0)
        price = row.get("close", 1)
        if price > 0:
            atr_pct = atr / price
            risk_factors.append(min(1.0, atr_pct * 20))
        else:
            risk_factors.append(0.5)

        # RSI extreme risk
        rsi = row.get("rsi", 50)
        rsi_risk = abs(rsi - 50) / 50
        risk_factors.append(rsi_risk)

        # Trend clarity risk
        trend_strength = row.get("trend_strength", 0.5)
        risk_factors.append(1 - trend_strength)

        return sum(risk_factors) / len(risk_factors)

    def get_parameter_ranges(self) -> Dict[str, Tuple[float, float]]:
        """Get parameter ranges for optimization."""
        return {
            "rsi_period": (7, 21),
            "rsi_oversold": (20, 40),
            "rsi_overbought": (60, 80),
            "ma_fast": (10, 30),
            "ma_slow": (30, 100),
            "min_risk_reward": (1.5, 3.0)
        }

    def update_parameters(self, parameters: Dict[str, Any]) -> None:
        """Update strategy parameters."""
        if "rsi_period" in parameters:
            self.rsi_period = int(parameters["rsi_period"])
        if "rsi_oversold" in parameters:
            self.rsi_oversold = int(parameters["rsi_oversold"])
        if "rsi_overbought" in parameters:
            self.rsi_overbought = int(parameters["rsi_overbought"])
        if "ma_fast" in parameters:
            self.ma_fast = int(parameters["ma_fast"])
        if "ma_slow" in parameters:
            self.ma_slow = int(parameters["ma_slow"])
        if "min_risk_reward" in parameters:
            self.min_risk_reward = float(parameters["min_risk_reward"])

        # Validate
        if self.ma_fast >= self.ma_slow:
            raise ValueError("Fast MA must be smaller than slow MA")

        self.parameters.update(parameters)
        self.logger.info(f"Updated parameters: {parameters}")

    def get_strategy_info(self) -> Dict[str, Any]:
        """Get comprehensive strategy information."""
        return {
            "name": self.name,
            "type": self.strategy_type.value,
            "description": "Multi-timeframe swing trading strategy for medium-term positions",
            "parameters": {
                "primary_timeframe": self.primary_timeframe,
                "rsi_period": self.rsi_period,
                "rsi_oversold": self.rsi_oversold,
                "rsi_overbought": self.rsi_overbought,
                "ma_fast": self.ma_fast,
                "ma_slow": self.ma_slow,
                "min_risk_reward": self.min_risk_reward
            },
            "best_for": "Medium-term trades (days to weeks)",
            "signals": {
                "buy": "Bullish swing setups with trend alignment",
                "sell": "Bearish swing setups with trend alignment"
            },
            "indicators_used": ["RSI", "Moving Averages", "ATR", "Swing Points"],
            "min_data_points": self.ma_slow + 10
        }

    def __str__(self) -> str:
        return f"SwingTradingStrategy(RSI={self.rsi_period}, MA={self.ma_fast}/{self.ma_slow})"
