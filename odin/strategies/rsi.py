"""
RSI (Relative Strength Index) Strategy

A mean reversion strategy that generates buy/sell signals based on
RSI overbought and oversold conditions. The RSI oscillates between
0 and 100, identifying potential reversal points.

Best For: Sideways/ranging markets with clear support and resistance
Strategy Type: Mean Reversion
Signals: Oversold (buy), Overbought (sell)
"""

from datetime import datetime
from typing import Any, Dict, Tuple

import numpy as np
import pandas as pd

# Import from core models for single source of truth
from ..core.models import SignalType
from .base import Signal, Strategy, StrategyType


class RSIStrategy(Strategy):
    """
    RSI (Relative Strength Index) Strategy Implementation.

    The RSI is a momentum oscillator that measures the speed and
    magnitude of recent price changes to evaluate overbought or
    oversold conditions.

    Signals:
    - BUY: When RSI moves from oversold (< oversold_level) back above it
    - SELL: When RSI moves from overbought (> overbought_level) back below it
    - HOLD: When RSI is in neutral territory
    """

    def __init__(
        self, period: int = 14, oversold: float = 30, overbought: float = 70, **kwargs
    ):
        """
        Initialize RSI strategy.

        Args:
            period: Periods for RSI calculation
            oversold: RSI level considered oversold (buy signal)
            overbought: RSI level considered overbought (sell signal)
            **kwargs: Additional strategy parameters
        """
        super().__init__(
            name="RSI",
            strategy_type=StrategyType.MEAN_REVERSION,
            period=period,
            oversold=oversold,
            overbought=overbought,
            **kwargs,
        )

        self.period = period
        self.oversold = oversold
        self.overbought = overbought

        # Validation
        if period < 2:
            raise ValueError("RSI period must be at least 2")
        if not 0 <= oversold < overbought <= 100:
            raise ValueError("Invalid RSI levels: 0 <= oversold < overbought <= 100")

        # Track previous RSI state for signal generation
        self.previous_rsi_state = "neutral"  # "oversold", "overbought", "neutral"

        self.logger.info(
            f"Initialized RSI strategy: period={period}, "
            f"oversold={oversold}, overbought={overbought}"
        )

    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate RSI and related indicators.

        Args:
            data: Raw OHLCV price data

        Returns:
            Data with additional indicator columns
        """
        df = data.copy()

        # Calculate RSI
        df["rsi"] = self._calculate_rsi(df["close"], self.period)

        # Calculate RSI moving average for smoothing
        df["rsi_ma"] = df["rsi"].rolling(window=3).mean()

        # Calculate price momentum
        df["price_change"] = df["close"].pct_change()
        df["price_momentum"] = df["price_change"].rolling(window=self.period).mean()

        # Calculate RSI divergence indicators
        df["rsi_change"] = df["rsi"].diff()
        df["price_change_abs"] = df["close"].diff()

        # Volume confirmation (if available)
        if "volume" in df.columns:
            df["volume_ma"] = df["volume"].rolling(window=self.period).mean()
            df["volume_ratio"] = df["volume"] / df["volume_ma"]
        else:
            df["volume_ratio"] = 1.0

        # Volatility measure
        df["volatility"] = df["close"].rolling(window=self.period).std()
        df["volatility_norm"] = df["volatility"] / df["close"]

        # Support and resistance levels
        df["price_high"] = df["high"].rolling(window=self.period).max()
        df["price_low"] = df["low"].rolling(window=self.period).min()
        df["price_range"] = df["price_high"] - df["price_low"]
        df["price_position"] = (df["close"] - df["price_low"]) / df["price_range"]

        return df

    def _calculate_rsi(self, prices: pd.Series, period: int) -> pd.Series:
        """
        Calculate Relative Strength Index.

        Args:
            prices: Price series
            period: RSI calculation period

        Returns:
            RSI values
        """
        delta = prices.diff()
        gains = delta.where(delta > 0, 0.0)
        losses = -delta.where(delta < 0, 0.0)

        # Calculate average gains and losses using Wilder's smoothing
        avg_gains = gains.ewm(alpha=1 / period, adjust=False).mean()
        avg_losses = losses.ewm(alpha=1 / period, adjust=False).mean()

        # Calculate relative strength and RSI
        rs = avg_gains / avg_losses
        rsi = 100 - (100 / (1 + rs))

        return rsi

    def generate_signal(self, data: pd.DataFrame) -> Signal:
        """
        Generate trading signal based on RSI levels.

        Args:
            data: OHLCV data with calculated indicators

        Returns:
            Trading signal with confidence and metadata
        """
        if len(data) < self.period + 1:
            return Signal(
                signal=SignalType.HOLD,
                confidence=0.0,
                timestamp=datetime.now(),
                price=data["close"].iloc[-1] if not data.empty else 0.0,
                reasoning="Insufficient data for RSI calculation",
                indicators={},
                risk_score=1.0,
            )

        # Get latest values
        current_row = data.iloc[-1]
        previous_row = data.iloc[-2] if len(data) > 1 else current_row

        current_rsi = current_row["rsi"]
        previous_rsi = previous_row["rsi"]
        current_price = current_row["close"]
        timestamp = (
            current_row.name
            if hasattr(current_row.name, "to_pydatetime")
            else datetime.now()
        )

        # Determine current RSI state
        if current_rsi <= self.oversold:
            current_state = "oversold"
        elif current_rsi >= self.overbought:
            current_state = "overbought"
        else:
            current_state = "neutral"

        # Generate signals based on state transitions
        signal_type = SignalType.HOLD
        reasoning = f"RSI at {current_rsi:.1f} - holding in {current_state} territory"

        # Buy signal: RSI moving up from oversold
        if (
            self.previous_rsi_state == "oversold"
            and current_state == "neutral"
            and current_rsi > previous_rsi
        ):
            signal_type = SignalType.BUY
            reasoning = f"RSI reversal from oversold: {current_rsi:.1f} (was {previous_rsi:.1f})"

        # Sell signal: RSI moving down from overbought
        elif (
            self.previous_rsi_state == "overbought"
            and current_state == "neutral"
            and current_rsi < previous_rsi
        ):
            signal_type = SignalType.SELL
            reasoning = f"RSI reversal from overbought: {current_rsi:.1f} (was {previous_rsi:.1f})"

        # Additional buy signal: Strong oversold bounce
        elif (
            current_rsi <= self.oversold - 5
            and current_rsi > previous_rsi
            and current_row.get("rsi_change", 0) > 2
        ):
            signal_type = SignalType.BUY
            reasoning = f"Strong RSI bounce from extreme oversold: {current_rsi:.1f}"

        # Additional sell signal: Strong overbought rejection
        elif (
            current_rsi >= self.overbought + 5
            and current_rsi < previous_rsi
            and current_row.get("rsi_change", 0) < -2
        ):
            signal_type = SignalType.SELL
            reasoning = (
                f"Strong RSI rejection from extreme overbought: {current_rsi:.1f}"
            )

        # Update state tracking
        self.previous_rsi_state = current_state

        # Calculate confidence score
        confidence = self._calculate_confidence(current_row, signal_type, current_rsi)

        # Calculate risk score
        risk_score = self._calculate_risk_score(current_row, current_rsi)

        # Prepare indicators dictionary
        indicators = {
            "rsi": current_rsi,
            "rsi_ma": current_row.get("rsi_ma", current_rsi),
            "rsi_change": current_row.get("rsi_change", 0),
            "price_momentum": current_row.get("price_momentum", 0),
            "volume_ratio": current_row.get("volume_ratio", 1),
            "price_position": current_row.get("price_position", 0.5),
            "oversold_level": self.oversold,
            "overbought_level": self.overbought,
        }

        signal = Signal(
            signal=signal_type,
            confidence=confidence,
            timestamp=timestamp,
            price=current_price,
            reasoning=reasoning,
            indicators=indicators,
            risk_score=risk_score,
        )

        self.last_signal = signal
        self.signals_history.append(signal)

        self.logger.debug(
            f"Generated signal: {signal_type.value} "
            f"(RSI: {current_rsi:.1f}, confidence: {confidence:.3f})"
        )

        return signal

    def _calculate_confidence(
        self, row: pd.Series, signal_type: SignalType, current_rsi: float
    ) -> float:
        """
        Calculate signal confidence based on various factors.

        Args:
            row: Current data row with indicators
            signal_type: Generated signal type
            current_rsi: Current RSI value

        Returns:
            Confidence score between 0 and 1
        """
        if signal_type == SignalType.HOLD:
            return 0.0

        confidence_factors = []

        # 1. RSI extreme levels (more extreme = higher confidence)
        if signal_type == SignalType.BUY:
            rsi_extreme = max(0, self.oversold - current_rsi) / self.oversold
        else:  # SELL
            rsi_extreme = max(0, current_rsi - self.overbought) / (
                100 - self.overbought
            )

        rsi_confidence = min(rsi_extreme * 2, 1.0)
        confidence_factors.append(rsi_confidence)

        # 2. RSI momentum (stronger momentum = higher confidence)
        rsi_change = abs(row.get("rsi_change", 0))
        momentum_confidence = min(rsi_change / 10.0, 1.0)
        confidence_factors.append(momentum_confidence)

        # 3. Volume confirmation
        volume_ratio = row.get("volume_ratio", 1.0)
        volume_confidence = (
            min((volume_ratio - 1.0) * 2.0, 1.0) if volume_ratio > 1.0 else 0.5
        )
        confidence_factors.append(volume_confidence)

        # 4. Price position in range
        price_position = row.get("price_position", 0.5)
        if signal_type == SignalType.BUY:
            # Want price near bottom of range for buy signal
            position_confidence = 1.0 - price_position
        else:
            # Want price near top of range for sell signal
            position_confidence = price_position
        confidence_factors.append(position_confidence)

        # 5. Divergence factor (price vs RSI momentum)
        price_momentum = row.get("price_momentum", 0)
        rsi_momentum = row.get("rsi_change", 0)

        if signal_type == SignalType.BUY and price_momentum < 0 and rsi_momentum > 0:
            # Bullish divergence
            divergence_confidence = 0.8
        elif signal_type == SignalType.SELL and price_momentum > 0 and rsi_momentum < 0:
            # Bearish divergence
            divergence_confidence = 0.8
        else:
            divergence_confidence = 0.5

        confidence_factors.append(divergence_confidence)

        # Weighted average of confidence factors
        weights = [0.3, 0.25, 0.2, 0.15, 0.1]
        confidence = sum(w * f for w, f in zip(weights, confidence_factors))

        return max(0.0, min(1.0, confidence))

    def _calculate_risk_score(self, row: pd.Series, current_rsi: float) -> float:
        """
        Calculate risk score for the signal.

        Args:
            row: Current data row with indicators
            current_rsi: Current RSI value

        Returns:
            Risk score between 0 and 1 (higher = more risky)
        """
        risk_factors = []

        # 1. Volatility risk
        volatility_norm = row.get("volatility_norm", 0)
        volatility_risk = min(volatility_norm * 20, 1.0)
        risk_factors.append(volatility_risk)

        # 2. RSI neutral zone risk (signals near 50 are less reliable)
        rsi_neutral_distance = abs(current_rsi - 50)
        neutral_risk = max(0, 1.0 - rsi_neutral_distance / 30)
        risk_factors.append(neutral_risk)

        # 3. Volume risk (low volume = higher risk)
        volume_ratio = row.get("volume_ratio", 1.0)
        volume_risk = max(0, 1.0 - volume_ratio) if volume_ratio < 1.0 else 0.0
        risk_factors.append(volume_risk)

        # 4. Range position risk
        price_position = row.get("price_position", 0.5)
        # Risk is higher when price is in middle of range
        range_risk = 1.0 - abs(price_position - 0.5) * 2
        risk_factors.append(range_risk)

        # Average risk score
        risk_score = sum(risk_factors) / len(risk_factors)

        return max(0.0, min(1.0, risk_score))

    def get_parameter_ranges(self) -> Dict[str, Tuple[float, float]]:
        """
        Get parameter ranges for optimization.

        Returns:
            Dictionary mapping parameter names to (min, max) tuples
        """
        return {"period": (5, 30), "oversold": (15, 35), "overbought": (65, 85)}

    def update_parameters(self, parameters: Dict[str, Any]) -> None:
        """
        Update strategy parameters.

        Args:
            parameters: New parameter values
        """
        if "period" in parameters:
            self.period = int(parameters["period"])
            self.parameters["period"] = self.period

        if "oversold" in parameters:
            self.oversold = float(parameters["oversold"])
            self.parameters["oversold"] = self.oversold

        if "overbought" in parameters:
            self.overbought = float(parameters["overbought"])
            self.parameters["overbought"] = self.overbought

        # Validation after update
        if self.period < 2:
            raise ValueError("RSI period must be at least 2")
        if not 0 <= self.oversold < self.overbought <= 100:
            raise ValueError("Invalid RSI levels: 0 <= oversold < overbought <= 100")

        self.logger.info(
            f"Updated parameters: period={self.period}, "
            f"oversold={self.oversold}, overbought={self.overbought}"
        )

    def get_strategy_info(self) -> Dict[str, Any]:
        """
        Get comprehensive strategy information.

        Returns:
            Strategy information dictionary
        """
        return {
            "name": self.name,
            "type": self.strategy_type.value,
            "description": "RSI mean reversion strategy using overbought/oversold signals",
            "parameters": {
                "period": self.period,
                "oversold": self.oversold,
                "overbought": self.overbought,
            },
            "best_for": "Sideways/ranging markets with clear support and resistance",
            "signals": {
                "buy": f"RSI reversal from oversold (< {self.oversold})",
                "sell": f"RSI reversal from overbought (> {self.overbought})",
            },
            "indicators_used": ["RSI", "Volume", "Price Position", "Momentum"],
            "min_data_points": self.period + 1,
        }

    def __str__(self) -> str:
        return f"RSIStrategy(period={self.period}, oversold={self.oversold}, overbought={self.overbought})"
