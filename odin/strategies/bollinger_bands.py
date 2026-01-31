"""
Bollinger Bands Strategy

A volatility-based strategy that uses Bollinger Bands to identify
potential breakout and mean reversion opportunities. Bollinger Bands
consist of a moving average with upper and lower bands based on
standard deviation.

Best For: Breakouts and reversions in volatile markets
Strategy Type: Volatility
Signals: Band touches, squeezes, and breakouts
"""

from datetime import datetime
from typing import Any, Dict, Tuple

import numpy as np
import pandas as pd

from .base import Signal, SignalType, Strategy, StrategyType


class BollingerBandsStrategy(Strategy):
    """
    Bollinger Bands Strategy Implementation.

    Bollinger Bands consist of:
    - Middle Band: Simple Moving Average (SMA)
    - Upper Band: SMA + (Standard Deviation × multiplier)
    - Lower Band: SMA - (Standard Deviation × multiplier)

    Signals:
    - BUY: Price touches or bounces off lower band (oversold)
    - SELL: Price touches or bounces off upper band (overbought)
    - BUY: Breakout above upper band with volume (momentum)
    - SELL: Breakdown below lower band with volume (momentum)
    """

    def __init__(
        self,
        period: int = 20,
        std_dev: float = 2.0,
        breakout_mode: bool = False,
        **kwargs,
    ):
        """
        Initialize Bollinger Bands strategy.

        Args:
            period: Periods for moving average calculation
            std_dev: Standard deviation multiplier for bands
            breakout_mode: If True, use breakout strategy; if False, use mean reversion
            **kwargs: Additional strategy parameters
        """
        super().__init__(
            name="BollingerBands",
            strategy_type=StrategyType.VOLATILITY,
            period=period,
            std_dev=std_dev,
            breakout_mode=breakout_mode,
            **kwargs,
        )

        self.period = period
        self.std_dev = std_dev
        self.breakout_mode = breakout_mode

        # Validation
        if period < 2:
            raise ValueError("Period must be at least 2")
        if std_dev <= 0:
            raise ValueError("Standard deviation multiplier must be positive")

        # Track band squeeze conditions
        self.squeeze_threshold = 0.1  # Percentage threshold for squeeze detection

        self.logger.info(
            f"Initialized Bollinger Bands strategy: period={period}, "
            f"std_dev={std_dev}, breakout_mode={breakout_mode}"
        )

    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate Bollinger Bands and related indicators.

        Args:
            data: Raw OHLCV price data

        Returns:
            Data with additional indicator columns
        """
        df = data.copy()

        # Calculate Bollinger Bands
        df["bb_middle"] = df["close"].rolling(window=self.period).mean()
        bb_std = df["close"].rolling(window=self.period).std()
        df["bb_upper"] = df["bb_middle"] + (bb_std * self.std_dev)
        df["bb_lower"] = df["bb_middle"] - (bb_std * self.std_dev)

        # Calculate band width and position
        df["bb_width"] = (df["bb_upper"] - df["bb_lower"]) / df["bb_middle"]
        df["bb_position"] = (df["close"] - df["bb_lower"]) / (
            df["bb_upper"] - df["bb_lower"]
        )

        # Calculate %B (position within bands)
        df["percent_b"] = (df["close"] - df["bb_lower"]) / (
            df["bb_upper"] - df["bb_lower"]
        )

        # Band squeeze detection
        df["bb_width_sma"] = df["bb_width"].rolling(window=self.period).mean()
        df["bb_squeeze"] = df["bb_width"] < (
            df["bb_width_sma"] * (1 - self.squeeze_threshold)
        )

        # Price distance from bands
        df["distance_to_upper"] = (df["bb_upper"] - df["close"]) / df["close"]
        df["distance_to_lower"] = (df["close"] - df["bb_lower"]) / df["close"]

        # Band slope (trend direction)
        df["bb_middle_slope"] = df["bb_middle"].diff()
        df["bb_trend"] = np.where(
            df["bb_middle_slope"] > 0, 1, np.where(df["bb_middle_slope"] < 0, -1, 0)
        )

        # Volume analysis (if available)
        if "volume" in df.columns:
            df["volume_sma"] = df["volume"].rolling(window=self.period).mean()
            df["volume_ratio"] = df["volume"] / df["volume_sma"]
        else:
            df["volume_ratio"] = 1.0

        # Volatility measures
        df["price_volatility"] = (
            df["close"].rolling(window=self.period).std() / df["close"]
        )
        df["bb_volatility"] = bb_std / df["bb_middle"]

        # Band touch detection
        df["touching_upper"] = df["close"] >= df["bb_upper"]
        df["touching_lower"] = df["close"] <= df["bb_lower"]

        return df

    def generate_signal(self, data: pd.DataFrame) -> Signal:
        """
        Generate trading signal based on Bollinger Bands.

        Args:
            data: OHLCV data with calculated indicators

        Returns:
            Trading signal with confidence and metadata
        """
        if len(data) < self.period:
            return Signal(
                signal=SignalType.HOLD,
                confidence=0.0,
                timestamp=datetime.now(),
                price=data["close"].iloc[-1] if not data.empty else 0.0,
                reasoning="Insufficient data for Bollinger Bands calculation",
                indicators={},
                risk_score=1.0,
            )

        # Get latest values
        current_row = data.iloc[-1]
        previous_row = data.iloc[-2] if len(data) > 1 else current_row

        current_price = current_row["close"]
        bb_upper = current_row["bb_upper"]
        bb_lower = current_row["bb_lower"]
        bb_middle = current_row["bb_middle"]
        percent_b = current_row["percent_b"]

        timestamp = (
            current_row.name
            if hasattr(current_row.name, "to_pydatetime")
            else datetime.now()
        )

        # Generate signals based on strategy mode
        if self.breakout_mode:
            signal_type, reasoning = self._generate_breakout_signal(
                current_row, previous_row
            )
        else:
            signal_type, reasoning = self._generate_mean_reversion_signal(
                current_row, previous_row
            )

        # Calculate confidence score
        confidence = self._calculate_confidence(current_row, signal_type)

        # Calculate risk score
        risk_score = self._calculate_risk_score(current_row)

        # Prepare indicators dictionary
        indicators = {
            "bb_upper": bb_upper,
            "bb_middle": bb_middle,
            "bb_lower": bb_lower,
            "bb_width": current_row.get("bb_width", 0),
            "percent_b": percent_b,
            "bb_squeeze": current_row.get("bb_squeeze", False),
            "volume_ratio": current_row.get("volume_ratio", 1),
            "bb_trend": current_row.get("bb_trend", 0),
            "distance_to_upper": current_row.get("distance_to_upper", 0),
            "distance_to_lower": current_row.get("distance_to_lower", 0),
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
            f"(%B: {percent_b:.3f}, confidence: {confidence:.3f})"
        )

        return signal

    def _generate_breakout_signal(
        self, current_row: pd.Series, previous_row: pd.Series
    ) -> Tuple[SignalType, str]:
        """Generate breakout-based signals."""
        current_price = current_row["close"]
        previous_price = previous_row["close"]
        bb_upper = current_row["bb_upper"]
        bb_lower = current_row["bb_lower"]
        volume_ratio = current_row.get("volume_ratio", 1.0)
        bb_squeeze = current_row.get("bb_squeeze", False)

        # Breakout above upper band with volume
        if (
            current_price > bb_upper
            and previous_row["close"] <= previous_row["bb_upper"]
            and volume_ratio > 1.2
        ):
            return (
                SignalType.BUY,
                f"Bullish breakout above upper band at {current_price:.2f} "
                f"(band: {bb_upper:.2f}) with volume",
            )

        # Breakdown below lower band with volume
        elif (
            current_price < bb_lower
            and previous_row["close"] >= previous_row["bb_lower"]
            and volume_ratio > 1.2
        ):
            return (
                SignalType.SELL,
                f"Bearish breakdown below lower band at {current_price:.2f} "
                f"(band: {bb_lower:.2f}) with volume",
            )

        # Squeeze breakout preparation
        elif bb_squeeze and volume_ratio > 1.5:
            bb_trend = current_row.get("bb_trend", 0)
            if bb_trend > 0:
                return (
                    SignalType.BUY,
                    f"Squeeze breakout preparation - uptrend with volume",
                )
            elif bb_trend < 0:
                return (
                    SignalType.SELL,
                    f"Squeeze breakout preparation - downtrend with volume",
                )

        return (
            SignalType.HOLD,
            f"No breakout signal - price at {current_price:.2f}, "
            f"bands: {bb_lower:.2f}-{bb_upper:.2f}",
        )

    def _generate_mean_reversion_signal(
        self, current_row: pd.Series, previous_row: pd.Series
    ) -> Tuple[SignalType, str]:
        """Generate mean reversion signals."""
        current_price = current_row["close"]
        percent_b = current_row["percent_b"]
        bb_middle = current_row["bb_middle"]
        bb_trend = current_row.get("bb_trend", 0)

        # Buy signal: Price near lower band (oversold)
        if percent_b <= 0.1 and current_price < bb_middle:
            return (
                SignalType.BUY,
                f"Oversold bounce from lower band - %B: {percent_b:.3f}",
            )

        # Sell signal: Price near upper band (overbought)
        elif percent_b >= 0.9 and current_price > bb_middle:
            return (
                SignalType.SELL,
                f"Overbought rejection from upper band - %B: {percent_b:.3f}",
            )

        # Enhanced signals with trend confirmation
        elif 0.1 < percent_b <= 0.3 and bb_trend > 0:
            return (SignalType.BUY, f"Buy the dip in uptrend - %B: {percent_b:.3f}")

        elif 0.7 <= percent_b < 0.9 and bb_trend < 0:
            return (
                SignalType.SELL,
                f"Sell the rally in downtrend - %B: {percent_b:.3f}",
            )

        return (
            SignalType.HOLD,
            f"Neutral position - %B: {percent_b:.3f}, trend: {bb_trend}",
        )

    def _calculate_confidence(self, row: pd.Series, signal_type: SignalType) -> float:
        """
        Calculate signal confidence based on various factors.

        Args:
            row: Current data row with indicators
            signal_type: Generated signal type

        Returns:
            Confidence score between 0 and 1
        """
        if signal_type == SignalType.HOLD:
            return 0.0

        confidence_factors = []

        # 1. Band position extremity
        percent_b = row.get("percent_b", 0.5)
        if signal_type == SignalType.BUY:
            position_confidence = max(
                0, 1.0 - percent_b * 2
            )  # Lower %B = higher confidence
        else:
            position_confidence = max(
                0, (percent_b - 0.5) * 2
            )  # Higher %B = higher confidence
        confidence_factors.append(position_confidence)

        # 2. Band width (volatility)
        bb_width = row.get("bb_width", 0)
        width_confidence = min(bb_width * 10, 1.0)  # Wider bands = higher confidence
        confidence_factors.append(width_confidence)

        # 3. Volume confirmation
        volume_ratio = row.get("volume_ratio", 1.0)
        volume_confidence = (
            min((volume_ratio - 1.0) * 2.0, 1.0) if volume_ratio > 1.0 else 0.5
        )
        confidence_factors.append(volume_confidence)

        # 4. Trend alignment
        bb_trend = row.get("bb_trend", 0)
        if (signal_type == SignalType.BUY and bb_trend >= 0) or (
            signal_type == SignalType.SELL and bb_trend <= 0
        ):
            trend_confidence = 0.8
        else:
            trend_confidence = 0.3
        confidence_factors.append(trend_confidence)

        # 5. Squeeze factor
        bb_squeeze = row.get("bb_squeeze", False)
        squeeze_confidence = 0.9 if bb_squeeze else 0.6
        confidence_factors.append(squeeze_confidence)

        # 6. Distance from middle band
        distance_factor = abs(percent_b - 0.5) * 2  # 0.5 = middle, 0/1 = extreme
        confidence_factors.append(distance_factor)

        # Weighted average of confidence factors
        weights = [0.25, 0.2, 0.2, 0.15, 0.1, 0.1]
        confidence = sum(w * f for w, f in zip(weights, confidence_factors))

        return max(0.0, min(1.0, confidence))

    def _calculate_risk_score(self, row: pd.Series) -> float:
        """
        Calculate risk score for the signal.

        Args:
            row: Current data row with indicators

        Returns:
            Risk score between 0 and 1 (higher = more risky)
        """
        risk_factors = []

        # 1. Band width risk (narrow bands = higher risk)
        bb_width = row.get("bb_width", 0)
        width_risk = max(0, 1.0 - bb_width * 20)
        risk_factors.append(width_risk)

        # 2. Middle band position risk
        percent_b = row.get("percent_b", 0.5)
        middle_risk = 1.0 - abs(percent_b - 0.5) * 2  # Higher risk near middle
        risk_factors.append(middle_risk)

        # 3. Volume risk
        volume_ratio = row.get("volume_ratio", 1.0)
        volume_risk = max(0, 1.0 - volume_ratio) if volume_ratio < 1.0 else 0.0
        risk_factors.append(volume_risk)

        # 4. Volatility risk
        price_volatility = row.get("price_volatility", 0)
        volatility_risk = min(price_volatility * 50, 1.0)
        risk_factors.append(volatility_risk)

        # 5. Squeeze risk (false breakouts during squeeze)
        bb_squeeze = row.get("bb_squeeze", False)
        squeeze_risk = 0.7 if bb_squeeze else 0.3
        risk_factors.append(squeeze_risk)

        # Average risk score
        risk_score = sum(risk_factors) / len(risk_factors)

        return max(0.0, min(1.0, risk_score))

    def get_parameter_ranges(self) -> Dict[str, Tuple[float, float]]:
        """
        Get parameter ranges for optimization.

        Returns:
            Dictionary mapping parameter names to (min, max) tuples
        """
        return {
            "period": (10, 30),
            "std_dev": (1.5, 2.5),
            "breakout_mode": (0, 1),  # Boolean: 0=False, 1=True
        }

    def update_parameters(self, parameters: Dict[str, Any]) -> None:
        """
        Update strategy parameters.

        Args:
            parameters: New parameter values
        """
        if "period" in parameters:
            self.period = int(parameters["period"])
            self.parameters["period"] = self.period

        if "std_dev" in parameters:
            self.std_dev = float(parameters["std_dev"])
            self.parameters["std_dev"] = self.std_dev

        if "breakout_mode" in parameters:
            self.breakout_mode = bool(parameters["breakout_mode"])
            self.parameters["breakout_mode"] = self.breakout_mode

        # Validation after update
        if self.period < 2:
            raise ValueError("Period must be at least 2")
        if self.std_dev <= 0:
            raise ValueError("Standard deviation multiplier must be positive")

        self.logger.info(
            f"Updated parameters: period={self.period}, "
            f"std_dev={self.std_dev}, breakout_mode={self.breakout_mode}"
        )

    def get_strategy_info(self) -> Dict[str, Any]:
        """
        Get comprehensive strategy information.

        Returns:
            Strategy information dictionary
        """
        mode = "Breakout" if self.breakout_mode else "Mean Reversion"
        return {
            "name": self.name,
            "type": self.strategy_type.value,
            "description": f"Bollinger Bands {mode.lower()} strategy using volatility bands",
            "parameters": {
                "period": self.period,
                "std_dev": self.std_dev,
                "breakout_mode": self.breakout_mode,
            },
            "best_for": "Breakouts and reversions in volatile markets",
            "signals": {
                "buy": f"{mode} buy signals based on band interaction",
                "sell": f"{mode} sell signals based on band interaction",
            },
            "indicators_used": ["Bollinger Bands", "Volume", "%B", "Band Width"],
            "min_data_points": self.period,
            "mode": mode,
        }

    def __str__(self) -> str:
        mode = "Breakout" if self.breakout_mode else "MeanReversion"
        return f"BollingerBandsStrategy(period={self.period}, std_dev={self.std_dev}, mode={mode})"
