"""
Moving Average Crossover Strategy

A trend-following strategy that generates buy/sell signals based on 
moving average crossovers. Uses Golden Cross (short MA > long MA) 
for buy signals and Death Cross (short MA < long MA) for sell signals.

Best For: Trending markets with clear directional movement
Strategy Type: Trend Following
Signals: Golden Cross (buy), Death Cross (sell)
"""

from datetime import datetime
from typing import Dict, Any, Tuple
import pandas as pd
import numpy as np

from .base import Strategy, StrategySignal, StrategyType, Signal


class MovingAverageStrategy(Strategy):
    """
    Moving Average Crossover Strategy Implementation.
    
    This strategy uses two moving averages:
    - Short-term MA (faster): Default 5 periods
    - Long-term MA (slower): Default 20 periods
    
    Signals:
    - BUY: When short MA crosses above long MA (Golden Cross)
    - SELL: When short MA crosses below long MA (Death Cross)
    - HOLD: When no crossover occurs
    """
    
    def __init__(self, short_window: int = 5, long_window: int = 20, **kwargs):
        """
        Initialize Moving Average strategy.
        
        Args:
            short_window: Periods for short-term moving average
            long_window: Periods for long-term moving average
            **kwargs: Additional strategy parameters
        """
        super().__init__(
            name="MovingAverage",
            strategy_type=StrategyType.TREND_FOLLOWING,
            short_window=short_window,
            long_window=long_window,
            **kwargs
        )
        
        self.short_window = short_window
        self.long_window = long_window
        
        # Validation
        if short_window >= long_window:
            raise ValueError("Short window must be less than long window")
        if short_window < 1 or long_window < 2:
            raise ValueError("Windows must be positive integers")
            
        self.logger.info(f"Initialized MA strategy: short={short_window}, long={long_window}")

    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate moving averages and related indicators.
        
        Args:
            data: Raw OHLCV price data
            
        Returns:
            Data with additional indicator columns
        """
        df = data.copy()
        
        # Calculate moving averages
        df['ma_short'] = df['close'].rolling(window=self.short_window).mean()
        df['ma_long'] = df['close'].rolling(window=self.long_window).mean()
        
        # Calculate additional indicators for confidence scoring
        df['ma_diff'] = df['ma_short'] - df['ma_long']
        df['ma_diff_pct'] = (df['ma_diff'] / df['ma_long']) * 100
        
        # Calculate trend strength
        df['trend_strength'] = abs(df['ma_diff_pct'])
        
        # Calculate price position relative to MAs
        df['price_vs_ma_short'] = (df['close'] - df['ma_short']) / df['ma_short'] * 100
        df['price_vs_ma_long'] = (df['close'] - df['ma_long']) / df['ma_long'] * 100
        
        # Volume trend (if available)
        if 'volume' in df.columns:
            df['volume_ma'] = df['volume'].rolling(window=self.short_window).mean()
            df['volume_ratio'] = df['volume'] / df['volume_ma']
        else:
            df['volume_ratio'] = 1.0
        
        # Volatility measure
        df['volatility'] = df['close'].rolling(window=self.short_window).std()
        df['volatility_norm'] = df['volatility'] / df['close']
        
        return df

    def generate_signal(self, data: pd.DataFrame) -> Signal:
        """
        Generate trading signal based on MA crossover.
        
        Args:
            data: OHLCV data with calculated indicators
            
        Returns:
            Trading signal with confidence and metadata
        """
        if len(data) < max(self.short_window, self.long_window):
            return Signal(
                signal=StrategySignal.HOLD,
                confidence=0.0,
                timestamp=datetime.now(),
                price=data['close'].iloc[-1] if not data.empty else 0.0,
                reasoning="Insufficient data for MA calculation",
                indicators={},
                risk_score=1.0
            )
        
        # Get latest values
        current_row = data.iloc[-1]
        previous_row = data.iloc[-2] if len(data) > 1 else current_row
        
        ma_short_current = current_row['ma_short']
        ma_long_current = current_row['ma_long']
        ma_short_previous = previous_row['ma_short']
        ma_long_previous = previous_row['ma_long']
        
        current_price = current_row['close']
        timestamp = current_row.name if hasattr(current_row.name, 'to_pydatetime') else datetime.now()
        
        # Check for crossover
        signal_type = StrategySignal.HOLD
        reasoning = "No crossover detected"
        
        # Golden Cross (buy signal)
        if (ma_short_previous <= ma_long_previous and 
            ma_short_current > ma_long_current):
            signal_type = StrategySignal.BUY
            reasoning = f"Golden Cross: Short MA ({ma_short_current:.2f}) crossed above Long MA ({ma_long_current:.2f})"
            
        # Death Cross (sell signal)
        elif (ma_short_previous >= ma_long_previous and 
              ma_short_current < ma_long_current):
            signal_type = StrategySignal.SELL
            reasoning = f"Death Cross: Short MA ({ma_short_current:.2f}) crossed below Long MA ({ma_long_current:.2f})"
        
        # Calculate confidence score
        confidence = self._calculate_confidence(current_row, signal_type)
        
        # Calculate risk score
        risk_score = self._calculate_risk_score(current_row)
        
        # Prepare indicators dictionary
        indicators = {
            'ma_short': ma_short_current,
            'ma_long': ma_long_current,
            'ma_diff_pct': current_row.get('ma_diff_pct', 0),
            'trend_strength': current_row.get('trend_strength', 0),
            'volume_ratio': current_row.get('volume_ratio', 1),
            'volatility_norm': current_row.get('volatility_norm', 0)
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
        
        self.logger.debug(f"Generated signal: {signal_type.value} "
                         f"(confidence: {confidence:.3f}, risk: {risk_score:.3f})")
        
        return signal

    def _calculate_confidence(self, row: pd.Series, signal_type: StrategySignal) -> float:
        """
        Calculate signal confidence based on various factors.
        
        Args:
            row: Current data row with indicators
            signal_type: Generated signal type
            
        Returns:
            Confidence score between 0 and 1
        """
        if signal_type == StrategySignal.HOLD:
            return 0.0
        
        confidence_factors = []
        
        # 1. Trend strength (larger MA separation = higher confidence)
        trend_strength = abs(row.get('ma_diff_pct', 0))
        trend_confidence = min(trend_strength / 2.0, 1.0)  # Normalize to 0-1
        confidence_factors.append(trend_confidence)
        
        # 2. Price momentum (price direction relative to MAs)
        if signal_type == StrategySignal.BUY:
            price_momentum = max(0, row.get('price_vs_ma_short', 0)) / 5.0  # Normalize
        else:
            price_momentum = max(0, -row.get('price_vs_ma_short', 0)) / 5.0
        
        price_confidence = min(price_momentum, 1.0)
        confidence_factors.append(price_confidence)
        
        # 3. Volume confirmation
        volume_ratio = row.get('volume_ratio', 1.0)
        volume_confidence = min((volume_ratio - 1.0) * 2.0, 1.0) if volume_ratio > 1.0 else 0.5
        confidence_factors.append(volume_confidence)
        
        # 4. Volatility factor (lower volatility = higher confidence for trend signals)
        volatility_norm = row.get('volatility_norm', 0)
        volatility_confidence = max(0, 1.0 - volatility_norm * 50)  # Inverse relationship
        confidence_factors.append(volatility_confidence)
        
        # Weighted average of confidence factors
        weights = [0.4, 0.3, 0.2, 0.1]  # Trend strength weighted most heavily
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
        
        # 1. Volatility risk
        volatility_norm = row.get('volatility_norm', 0)
        volatility_risk = min(volatility_norm * 20, 1.0)
        risk_factors.append(volatility_risk)
        
        # 2. Trend uncertainty (small MA separation)
        trend_strength = abs(row.get('ma_diff_pct', 0))
        trend_risk = max(0, 1.0 - trend_strength / 2.0)
        risk_factors.append(trend_risk)
        
        # 3. Volume risk (low volume = higher risk)
        volume_ratio = row.get('volume_ratio', 1.0)
        volume_risk = max(0, 1.0 - volume_ratio) if volume_ratio < 1.0 else 0.0
        risk_factors.append(volume_risk)
        
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
            'short_window': (3, 15),
            'long_window': (10, 50)
        }

    def update_parameters(self, parameters: Dict[str, Any]) -> None:
        """
        Update strategy parameters.
        
        Args:
            parameters: New parameter values
        """
        if 'short_window' in parameters:
            self.short_window = int(parameters['short_window'])
            self.parameters['short_window'] = self.short_window
            
        if 'long_window' in parameters:
            self.long_window = int(parameters['long_window'])
            self.parameters['long_window'] = self.long_window
            
        # Validation after update
        if self.short_window >= self.long_window:
            raise ValueError("Short window must be less than long window")
            
        self.logger.info(f"Updated parameters: short={self.short_window}, long={self.long_window}")

    def get_strategy_info(self) -> Dict[str, Any]:
        """
        Get comprehensive strategy information.
        
        Returns:
            Strategy information dictionary
        """
        return {
            'name': self.name,
            'type': self.strategy_type.value,
            'description': 'Moving Average crossover strategy using Golden/Death Cross signals',
            'parameters': {
                'short_window': self.short_window,
                'long_window': self.long_window
            },
            'best_for': 'Trending markets with clear directional movement',
            'signals': {
                'buy': 'Golden Cross - Short MA crosses above Long MA',
                'sell': 'Death Cross - Short MA crosses below Long MA'
            },
            'indicators_used': ['Simple Moving Average', 'Volume', 'Volatility'],
            'min_data_points': max(self.short_window, self.long_window)
        }

    def __str__(self) -> str:
        return f"MovingAverageStrategy(short={self.short_window}, long={self.long_window})"