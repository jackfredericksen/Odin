"""
MACD (Moving Average Convergence Divergence) Strategy

A trend momentum strategy that uses MACD line crossovers, signal line 
crossovers, and histogram analysis to identify trend changes and 
momentum shifts in the market.

Best For: Trend changes and momentum confirmation
Strategy Type: Trend Momentum
Signals: MACD line crossovers, signal line crossovers, histogram divergence
"""

from datetime import datetime
from typing import Dict, Any, Tuple
import pandas as pd
import numpy as np

from .base import Strategy, StrategySignal, StrategyType, Signal


class MACDStrategy(Strategy):
    """
    MACD (Moving Average Convergence Divergence) Strategy Implementation.
    
    MACD consists of:
    - MACD Line: EMA(fast_period) - EMA(slow_period)
    - Signal Line: EMA(macd_line, signal_period)
    - Histogram: MACD Line - Signal Line
    
    Signals:
    - BUY: MACD line crosses above signal line (bullish crossover)
    - SELL: MACD line crosses below signal line (bearish crossover)
    - BUY: MACD line crosses above zero (bullish momentum)
    - SELL: MACD line crosses below zero (bearish momentum)
    """
    
    def __init__(self, fast_period: int = 12, slow_period: int = 26, 
                 signal_period: int = 9, **kwargs):
        """
        Initialize MACD strategy.
        
        Args:
            fast_period: Periods for fast EMA
            slow_period: Periods for slow EMA  
            signal_period: Periods for signal line EMA
            **kwargs: Additional strategy parameters
        """
        super().__init__(
            name="MACD",
            strategy_type=StrategyType.MOMENTUM,
            fast_period=fast_period,
            slow_period=slow_period,
            signal_period=signal_period,
            **kwargs
        )
        
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.signal_period = signal_period
        
        # Validation
        if fast_period >= slow_period:
            raise ValueError("Fast period must be less than slow period")
        if any(p < 1 for p in [fast_period, slow_period, signal_period]):
            raise ValueError("All periods must be positive integers")
            
        # Track previous MACD state for crossover detection
        self.previous_macd_above_signal = None
        self.previous_macd_above_zero = None
        
        self.logger.info(f"Initialized MACD strategy: fast={fast_period}, "
                        f"slow={slow_period}, signal={signal_period}")

    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate MACD and related indicators.
        
        Args:
            data: Raw OHLCV price data
            
        Returns:
            Data with additional indicator columns
        """
        df = data.copy()
        
        # Calculate EMAs
        df['ema_fast'] = df['close'].ewm(span=self.fast_period).mean()
        df['ema_slow'] = df['close'].ewm(span=self.slow_period).mean()
        
        # Calculate MACD line
        df['macd'] = df['ema_fast'] - df['ema_slow']
        
        # Calculate signal line
        df['macd_signal'] = df['macd'].ewm(span=self.signal_period).mean()
        
        # Calculate histogram
        df['macd_histogram'] = df['macd'] - df['macd_signal']
        
        # Calculate additional indicators for confidence scoring
        df['macd_slope'] = df['macd'].diff()
        df['signal_slope'] = df['macd_signal'].diff()
        df['histogram_slope'] = df['macd_histogram'].diff()
        
        # Calculate MACD momentum and strength
        df['macd_momentum'] = df['macd'].diff(3)  # 3-period momentum
        df['macd_strength'] = abs(df['macd'])
        
        # Calculate divergence indicators
        df['price_momentum'] = df['close'].diff(3)
        df['price_slope'] = df['close'].diff()
        
        # Volume analysis (if available)
        if 'volume' in df.columns:
            df['volume_ema'] = df['volume'].ewm(span=self.fast_period).mean()
            df['volume_ratio'] = df['volume'] / df['volume_ema']
        else:
            df['volume_ratio'] = 1.0
        
        # Volatility measures
        df['price_volatility'] = df['close'].rolling(window=self.fast_period).std()
        df['macd_volatility'] = df['macd'].rolling(window=self.fast_period).std()
        
        # Zero line distance
        df['macd_zero_distance'] = abs(df['macd'])
        df['macd_normalized'] = df['macd'] / df['close'] * 100  # Normalize by price
        
        return df

    def generate_signal(self, data: pd.DataFrame) -> Signal:
        """
        Generate trading signal based on MACD analysis.
        
        Args:
            data: OHLCV data with calculated indicators
            
        Returns:
            Trading signal with confidence and metadata
        """
        min_data_points = max(self.slow_period, self.signal_period) + 1
        if len(data) < min_data_points:
            return Signal(
                signal=StrategySignal.HOLD,
                confidence=0.0,
                timestamp=datetime.now(),
                price=data['close'].iloc[-1] if not data.empty else 0.0,
                reasoning="Insufficient data for MACD calculation",
                indicators={},
                risk_score=1.0
            )
        
        # Get latest values
        current_row = data.iloc[-1]
        previous_row = data.iloc[-2] if len(data) > 1 else current_row
        
        current_macd = current_row['macd']
        current_signal = current_row['macd_signal']
        current_histogram = current_row['macd_histogram']
        current_price = current_row['close']
        
        previous_macd = previous_row['macd']
        previous_signal = previous_row['macd_signal']
        
        timestamp = current_row.name if hasattr(current_row.name, 'to_pydatetime') else datetime.now()
        
        # Track crossover states
        current_macd_above_signal = current_macd > current_signal
        current_macd_above_zero = current_macd > 0
        
        # Generate signals
        signal_type, reasoning = self._analyze_macd_signals(
            current_row, previous_row, 
            current_macd_above_signal, current_macd_above_zero
        )
        
        # Update state tracking
        self.previous_macd_above_signal = current_macd_above_signal
        self.previous_macd_above_zero = current_macd_above_zero
        
        # Calculate confidence score
        confidence = self._calculate_confidence(current_row, signal_type)
        
        # Calculate risk score
        risk_score = self._calculate_risk_score(current_row)
        
        # Prepare indicators dictionary
        indicators = {
            'macd': current_macd,
            'macd_signal': current_signal,
            'macd_histogram': current_histogram,
            'macd_slope': current_row.get('macd_slope', 0),
            'histogram_slope': current_row.get('histogram_slope', 0),
            'macd_momentum': current_row.get('macd_momentum', 0),
            'volume_ratio': current_row.get('volume_ratio', 1),
            'macd_normalized': current_row.get('macd_normalized', 0),
            'ema_fast': current_row.get('ema_fast', 0),
            'ema_slow': current_row.get('ema_slow', 0)
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
                         f"(MACD: {current_macd:.6f}, confidence: {confidence:.3f})")
        
        return signal

    def _analyze_macd_signals(self, current_row: pd.Series, previous_row: pd.Series,
                             current_macd_above_signal: bool, 
                             current_macd_above_zero: bool) -> Tuple[StrategySignal, str]:
        """Analyze MACD for trading signals."""
        
        current_macd = current_row['macd']
        current_signal = current_row['macd_signal']
        current_histogram = current_row['macd_histogram']
        previous_histogram = previous_row.get('macd_histogram', 0)
        
        # 1. MACD line crossover signals (primary)
        if (self.previous_macd_above_signal is not None and
            self.previous_macd_above_signal != current_macd_above_signal):
            
            if current_macd_above_signal:
                return (StrategySignal.BUY,
                       f"Bullish MACD crossover: MACD ({current_macd:.6f}) "
                       f"crossed above signal ({current_signal:.6f})")
            else:
                return (StrategySignal.SELL,
                       f"Bearish MACD crossover: MACD ({current_macd:.6f}) "
                       f"crossed below signal ({current_signal:.6f})")
        
        # 2. Zero line crossover signals (secondary)
        if (self.previous_macd_above_zero is not None and
            self.previous_macd_above_zero != current_macd_above_zero):
            
            volume_ratio = current_row.get('volume_ratio', 1.0)
            if volume_ratio > 1.2:  # Require volume confirmation for zero line crosses
                if current_macd_above_zero:
                    return (StrategySignal.BUY,
                           f"Bullish zero line cross: MACD ({current_macd:.6f}) "
                           f"crossed above zero with volume")
                else:
                    return (StrategySignal.SELL,
                           f"Bearish zero line cross: MACD ({current_macd:.6f}) "
                           f"crossed below zero with volume")
        
        # 3. Histogram momentum signals
        histogram_slope = current_row.get('histogram_slope', 0)
        macd_momentum = current_row.get('macd_momentum', 0)
        
        if abs(histogram_slope) > 0.001:  # Significant histogram change
            if (current_histogram > 0 and histogram_slope > 0 and 
                macd_momentum > 0 and current_macd_above_signal):
                return (StrategySignal.BUY,
                       f"Strong bullish momentum: histogram rising ({histogram_slope:.6f})")
            
            elif (current_histogram < 0 and histogram_slope < 0 and 
                  macd_momentum < 0 and not current_macd_above_signal):
                return (StrategySignal.SELL,
                       f"Strong bearish momentum: histogram falling ({histogram_slope:.6f})")
        
        # 4. Divergence signals
        price_momentum = current_row.get('price_momentum', 0)
        if self._detect_divergence(current_row, price_momentum, macd_momentum):
            if macd_momentum > 0 and price_momentum < 0:
                return (StrategySignal.BUY,
                       f"Bullish divergence detected: price falling, MACD rising")
            elif macd_momentum < 0 and price_momentum > 0:
                return (StrategySignal.SELL,
                       f"Bearish divergence detected: price rising, MACD falling")
        
        # No clear signal
        return (StrategySignal.HOLD,
               f"No clear MACD signal - MACD: {current_macd:.6f}, "
               f"Signal: {current_signal:.6f}, Histogram: {current_histogram:.6f}")

    def _detect_divergence(self, row: pd.Series, price_momentum: float, 
                          macd_momentum: float) -> bool:
        """Detect price-MACD divergence."""
        # Simple divergence detection
        divergence_threshold = 0.001
        
        return (abs(price_momentum) > divergence_threshold and 
                abs(macd_momentum) > divergence_threshold and
                (price_momentum * macd_momentum) < 0)  # Opposite signs

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
        
        # 1. MACD line strength
        macd_strength = abs(row.get('macd', 0))
        strength_confidence = min(macd_strength * 1000, 1.0)  # Scale appropriately
        confidence_factors.append(strength_confidence)
        
        # 2. Histogram momentum
        histogram_slope = abs(row.get('histogram_slope', 0))
        momentum_confidence = min(histogram_slope * 5000, 1.0)
        confidence_factors.append(momentum_confidence)
        
        # 3. MACD momentum alignment
        macd_slope = row.get('macd_slope', 0)
        macd_momentum = row.get('macd_momentum', 0)
        
        if signal_type == StrategySignal.BUY:
            momentum_alignment = 1.0 if (macd_slope > 0 and macd_momentum > 0) else 0.3
        else:
            momentum_alignment = 1.0 if (macd_slope < 0 and macd_momentum < 0) else 0.3
        confidence_factors.append(momentum_alignment)
        
        # 4. Volume confirmation
        volume_ratio = row.get('volume_ratio', 1.0)
        volume_confidence = min((volume_ratio - 1.0) * 2.0, 1.0) if volume_ratio > 1.0 else 0.5
        confidence_factors.append(volume_confidence)
        
        # 5. Zero line position
        macd = row.get('macd', 0)
        if signal_type == StrategySignal.BUY:
            zero_confidence = 0.8 if macd > 0 else 0.4
        else:
            zero_confidence = 0.8 if macd < 0 else 0.4
        confidence_factors.append(zero_confidence)
        
        # 6. Signal line separation
        macd_signal_diff = abs(row.get('macd', 0) - row.get('macd_signal', 0))
        separation_confidence = min(macd_signal_diff * 2000, 1.0)
        confidence_factors.append(separation_confidence)
        
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
        
        # 1. MACD volatility risk
        macd_volatility = row.get('macd_volatility', 0)
        volatility_risk = min(macd_volatility * 1000, 1.0)
        risk_factors.append(volatility_risk)
        
        # 2. Signal line proximity risk (signals near crossover are risky)
        macd = row.get('macd', 0)
        macd_signal = row.get('macd_signal', 0)
        proximity_risk = max(0, 1.0 - abs(macd - macd_signal) * 2000)
        risk_factors.append(proximity_risk)
        
        # 3. Zero line proximity risk
        zero_distance = abs(macd)
        zero_risk = max(0, 1.0 - zero_distance * 2000)
        risk_factors.append(zero_risk)
        
        # 4. Volume risk
        volume_ratio = row.get('volume_ratio', 1.0)
        volume_risk = max(0, 1.0 - volume_ratio) if volume_ratio < 1.0 else 0.0
        risk_factors.append(volume_risk)
        
        # 5. Momentum inconsistency risk
        macd_slope = row.get('macd_slope', 0)
        histogram_slope = row.get('histogram_slope', 0)
        
        # Risk is higher when slopes are inconsistent
        if (macd_slope * histogram_slope) < 0:  # Opposite signs
            momentum_risk = 0.7
        else:
            momentum_risk = 0.2
        risk_factors.append(momentum_risk)
        
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
            'fast_period': (8, 16),
            'slow_period': (20, 35),
            'signal_period': (6, 12)
        }

    def update_parameters(self, parameters: Dict[str, Any]) -> None:
        """
        Update strategy parameters.
        
        Args:
            parameters: New parameter values
        """
        if 'fast_period' in parameters:
            self.fast_period = int(parameters['fast_period'])
            self.parameters['fast_period'] = self.fast_period
            
        if 'slow_period' in parameters:
            self.slow_period = int(parameters['slow_period'])
            self.parameters['slow_period'] = self.slow_period
            
        if 'signal_period' in parameters:
            self.signal_period = int(parameters['signal_period'])
            self.parameters['signal_period'] = self.signal_period
            
        # Validation after update
        if self.fast_period >= self.slow_period:
            raise ValueError("Fast period must be less than slow period")
        if any(p < 1 for p in [self.fast_period, self.slow_period, self.signal_period]):
            raise ValueError("All periods must be positive integers")
            
        # Reset state tracking after parameter change
        self.previous_macd_above_signal = None
        self.previous_macd_above_zero = None
            
        self.logger.info(f"Updated parameters: fast={self.fast_period}, "
                        f"slow={self.slow_period}, signal={self.signal_period}")

    def get_strategy_info(self) -> Dict[str, Any]:
        """
        Get comprehensive strategy information.
        
        Returns:
            Strategy information dictionary
        """
        return {
            'name': self.name,
            'type': self.strategy_type.value,
            'description': 'MACD trend momentum strategy using line crossovers and histogram analysis',
            'parameters': {
                'fast_period': self.fast_period,
                'slow_period': self.slow_period,
                'signal_period': self.signal_period
            },
            'best_for': 'Trend changes and momentum confirmation',
            'signals': {
                'buy': 'MACD line crosses above signal line or zero line',
                'sell': 'MACD line crosses below signal line or zero line'
            },
            'indicators_used': ['MACD Line', 'Signal Line', 'Histogram', 'EMAs', 'Volume'],
            'min_data_points': max(self.slow_period, self.signal_period) + 1
        }

    def __str__(self) -> str:
        return f"MACDStrategy(fast={self.fast_period}, slow={self.slow_period}, signal={self.signal_period})"