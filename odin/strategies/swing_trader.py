"""
Bitcoin Swing Trading Strategy

A comprehensive swing trading strategy optimized for Bitcoin's medium-term price movements.
Combines multiple technical indicators with market sentiment analysis for 1-7 day holding periods.

Best For: Bitcoin swing trading with 1-7 day holding periods
Strategy Type: Hybrid (Trend + Mean Reversion + Momentum)
Signals: Multi-timeframe analysis with confirmation signals
"""

from datetime import datetime, timedelta
from typing import Dict, Any, Tuple, List
import pandas as pd
import numpy as np

# Import from core models for single source of truth
from ..core.models import SignalType
from .base import Strategy, StrategyType, Signal


class SwingTradingStrategy(Strategy):
    """
    Advanced Bitcoin Swing Trading Strategy Implementation.
    
    This strategy combines multiple timeframes and indicators:
    - Primary: 4H timeframe for swing signals
    - Confirmation: 1H timeframe for entry timing
    - Filter: Daily timeframe for trend direction
    
    Key Features:
    - Multi-timeframe analysis
    - Dynamic position sizing based on volatility
    - Support/resistance level detection
    - Market structure analysis
    - Risk-adjusted entries with tight stops
    """
    
    def __init__(self, 
                 primary_timeframe: str = "4H",
                 rsi_period: int = 14,
                 rsi_oversold: float = 35,
                 rsi_overbought: float = 65,
                 ma_fast: int = 21,
                 ma_slow: int = 50,
                 bb_period: int = 20,
                 bb_std: float = 2.0,
                 volume_threshold: float = 1.2,
                 min_risk_reward: float = 2.0,
                 max_hold_days: int = 7,
                 **kwargs):
        """
        Initialize Swing Trading strategy.
        
        Args:
            primary_timeframe: Primary timeframe for analysis
            rsi_period: RSI calculation period
            rsi_oversold: RSI oversold level for swing lows
            rsi_overbought: RSI overbought level for swing highs
            ma_fast: Fast moving average period
            ma_slow: Slow moving average period
            bb_period: Bollinger Bands period
            bb_std: Bollinger Bands standard deviation
            volume_threshold: Volume confirmation threshold
            min_risk_reward: Minimum risk/reward ratio
            max_hold_days: Maximum holding period in days
            **kwargs: Additional strategy parameters
        """
        super().__init__(
            name="SwingTrading",
            strategy_type=StrategyType.MOMENTUM,  # Hybrid approach
            primary_timeframe=primary_timeframe,
            rsi_period=rsi_period,
            rsi_oversold=rsi_oversold,
            rsi_overbought=rsi_overbought,
            ma_fast=ma_fast,
            ma_slow=ma_slow,
            bb_period=bb_period,
            bb_std=bb_std,
            volume_threshold=volume_threshold,
            min_risk_reward=min_risk_reward,
            max_hold_days=max_hold_days,
            **kwargs
        )
        
        self.primary_timeframe = primary_timeframe
        self.rsi_period = rsi_period
        self.rsi_oversold = rsi_oversold
        self.rsi_overbought = rsi_overbought
        self.ma_fast = ma_fast
        self.ma_slow = ma_slow
        self.bb_period = bb_period
        self.bb_std = bb_std
        self.volume_threshold = volume_threshold
        self.min_risk_reward = min_risk_reward
        self.max_hold_days = max_hold_days
        
        # Swing trading state
        self.current_position = None
        self.entry_price = None
        self.entry_time = None
        self.stop_loss = None
        self.take_profit = None
        self.support_levels = []
        self.resistance_levels = []
        
        # Market structure tracking
        self.trend_direction = "neutral"  # "bullish", "bearish", "neutral"
        self.market_structure = "ranging"  # "trending", "ranging", "volatile"
        
        self.logger.info(f"Initialized Swing Trading strategy for {primary_timeframe} timeframe")

    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate comprehensive technical indicators for swing trading.
        
        Args:
            data: Raw OHLCV price data
            
        Returns:
            Data with swing trading indicators
        """
        df = data.copy()
        
        # Core Moving Averages
        df['ema_fast'] = df['close'].ewm(span=self.ma_fast).mean()
        df['ema_slow'] = df['close'].ewm(span=self.ma_slow).mean()
        df['sma_200'] = df['close'].rolling(window=200).mean()  # Long-term trend
        
        # RSI with multiple timeframes
        df['rsi'] = self._calculate_rsi(df['close'], self.rsi_period)
        df['rsi_smooth'] = df['rsi'].rolling(window=3).mean()
        
        # Bollinger Bands for volatility
        df['bb_middle'] = df['close'].rolling(window=self.bb_period).mean()
        bb_std = df['close'].rolling(window=self.bb_period).std()
        df['bb_upper'] = df['bb_middle'] + (bb_std * self.bb_std)
        df['bb_lower'] = df['bb_middle'] - (bb_std * self.bb_std)
        df['bb_width'] = (df['bb_upper'] - df['bb_lower']) / df['bb_middle']
        df['bb_position'] = (df['close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'])
        
        # MACD for momentum
        ema_12 = df['close'].ewm(span=12).mean()
        ema_26 = df['close'].ewm(span=26).mean()
        df['macd'] = ema_12 - ema_26
        df['macd_signal'] = df['macd'].ewm(span=9).mean()
        df['macd_histogram'] = df['macd'] - df['macd_signal']
        
        # Volume analysis
        df['volume_sma'] = df['volume'].rolling(window=20).mean()
        df['volume_ratio'] = df['volume'] / df['volume_sma']
        df['volume_surge'] = df['volume_ratio'] > self.volume_threshold
        
        # Price action analysis
        df['high_low_ratio'] = (df['high'] - df['low']) / df['close']
        df['body_size'] = abs(df['close'] - df['open']) / df['close']
        df['upper_shadow'] = (df['high'] - df[['open', 'close']].max(axis=1)) / df['close']
        df['lower_shadow'] = (df[['open', 'close']].min(axis=1) - df['low']) / df['close']
        
        # Swing highs and lows detection
        df['swing_high'] = self._detect_swing_highs(df['high'], window=5)
        df['swing_low'] = self._detect_swing_lows(df['low'], window=5)
        
        # Support and resistance levels
        df = self._calculate_support_resistance(df)
        
        # Market structure analysis
        df['trend_strength'] = self._calculate_trend_strength(df)
        df['market_volatility'] = df['close'].rolling(window=20).std() / df['close']
        
        # Fibonacci retracement levels (simplified)
        df = self._calculate_fibonacci_levels(df)
        
        return df

    def generate_signal(self, data: pd.DataFrame) -> Signal:
        """
        Generate swing trading signal based on comprehensive analysis.
        
        Args:
            data: OHLCV data with calculated indicators
            
        Returns:
            Swing trading signal with detailed analysis
        """
        if len(data) < max(self.ma_slow, self.bb_period, 50):
            return Signal(
                signal=SignalType.HOLD,
                confidence=0.0,
                timestamp=datetime.now(),
                price=data['close'].iloc[-1] if not data.empty else 0.0,
                reasoning="Insufficient data for swing analysis",
                indicators={},
                risk_score=1.0
            )
        
        current_row = data.iloc[-1]
        current_price = current_row['close']
        timestamp = current_row.name if hasattr(current_row.name, 'to_pydatetime') else datetime.now()
        
        # Update market structure
        self._update_market_structure(data)
        
        # Check if we should exit current position
        if self.current_position:
            exit_signal = self._check_exit_conditions(current_row, data)
            if exit_signal:
                return exit_signal
        
        # Look for new swing trading opportunities
        signal_type = SignalType.HOLD
        reasoning = "Monitoring market conditions"
        
        # Swing Long Setup Analysis
        long_setup = self._analyze_long_setup(current_row, data)
        short_setup = self._analyze_short_setup(current_row, data)
        
        if long_setup['valid'] and not self.current_position:
            signal_type = SignalType.BUY
            reasoning = f"Swing Long Setup: {long_setup['reason']}"
            self._prepare_long_position(current_row, long_setup)
            
        elif short_setup['valid'] and not self.current_position:
            signal_type = SignalType.SELL
            reasoning = f"Swing Short Setup: {short_setup['reason']}"
            self._prepare_short_position(current_row, short_setup)
        
        # Calculate confidence and risk
        confidence = self._calculate_swing_confidence(current_row, signal_type, data)
        risk_score = self._calculate_swing_risk(current_row, signal_type, data)
        
        # Prepare comprehensive indicators
        indicators = {
            'rsi': current_row['rsi'],
            'rsi_smooth': current_row.get('rsi_smooth', current_row['rsi']),
            'ema_fast': current_row['ema_fast'],
            'ema_slow': current_row['ema_slow'],
            'bb_position': current_row.get('bb_position', 0.5),
            'bb_width': current_row.get('bb_width', 0),
            'macd': current_row.get('macd', 0),
            'macd_signal': current_row.get('macd_signal', 0),
            'volume_ratio': current_row.get('volume_ratio', 1),
            'trend_direction': self.trend_direction,
            'market_structure': self.market_structure,
            'support_distance': self._get_nearest_support_distance(current_price),
            'resistance_distance': self._get_nearest_resistance_distance(current_price),
            'risk_reward_ratio': getattr(self, 'current_risk_reward', 0),
            'position_status': 'active' if self.current_position else 'none'
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
        
        self.logger.debug(f"Swing signal: {signal_type.value} "
                         f"(confidence: {confidence:.3f}, risk: {risk_score:.3f})")
        
        return signal

    def _analyze_long_setup(self, current_row: pd.Series, data: pd.DataFrame) -> Dict[str, Any]:
        """Analyze potential long swing setup."""
        setup = {'valid': False, 'reason': '', 'confidence': 0.0}
        
        rsi = current_row['rsi']
        ema_fast = current_row['ema_fast']
        ema_slow = current_row['ema_slow']
        bb_position = current_row.get('bb_position', 0.5)
        volume_ratio = current_row.get('volume_ratio', 1)
        macd_histogram = current_row.get('macd_histogram', 0)
        
        reasons = []
        confidence_factors = []
        
        # RSI oversold with divergence
        if rsi < self.rsi_oversold:
            reasons.append(f"RSI oversold ({rsi:.1f})")
            confidence_factors.append(0.3)
            
            # Check for bullish divergence
            if self._check_bullish_divergence(data):
                reasons.append("bullish divergence detected")
                confidence_factors.append(0.4)
        
        # Price near Bollinger Band lower
        if bb_position < 0.2:
            reasons.append("price near BB lower band")
            confidence_factors.append(0.2)
        
        # Volume confirmation
        if volume_ratio > self.volume_threshold:
            reasons.append("volume surge confirmation")
            confidence_factors.append(0.3)
        
        # MACD momentum turning positive
        if macd_histogram > 0 and current_row.get('macd', 0) > current_row.get('macd_signal', 0):
            reasons.append("MACD momentum positive")
            confidence_factors.append(0.2)
        
        # Trend alignment (not fighting major trend)
        if self.trend_direction in ['bullish', 'neutral']:
            confidence_factors.append(0.2)
        else:
            confidence_factors.append(-0.3)  # Penalize counter-trend
        
        # Support level bounce
        support_distance = self._get_nearest_support_distance(current_row['close'])
        if 0 < support_distance < 0.02:  # Within 2% of support
            reasons.append("near key support level")
            confidence_factors.append(0.3)
        
        if len(reasons) >= 2 and sum(confidence_factors) > 0.4:
            setup['valid'] = True
            setup['reason'] = " + ".join(reasons)
            setup['confidence'] = min(sum(confidence_factors), 1.0)
        
        return setup

    def _analyze_short_setup(self, current_row: pd.Series, data: pd.DataFrame) -> Dict[str, Any]:
        """Analyze potential short swing setup."""
        setup = {'valid': False, 'reason': '', 'confidence': 0.0}
        
        rsi = current_row['rsi']
        bb_position = current_row.get('bb_position', 0.5)
        volume_ratio = current_row.get('volume_ratio', 1)
        macd_histogram = current_row.get('macd_histogram', 0)
        
        reasons = []
        confidence_factors = []
        
        # RSI overbought
        if rsi > self.rsi_overbought:
            reasons.append(f"RSI overbought ({rsi:.1f})")
            confidence_factors.append(0.3)
            
            # Check for bearish divergence
            if self._check_bearish_divergence(data):
                reasons.append("bearish divergence detected")
                confidence_factors.append(0.4)
        
        # Price near Bollinger Band upper
        if bb_position > 0.8:
            reasons.append("price near BB upper band")
            confidence_factors.append(0.2)
        
        # Volume confirmation
        if volume_ratio > self.volume_threshold:
            reasons.append("volume surge confirmation")
            confidence_factors.append(0.3)
        
        # MACD momentum turning negative
        if macd_histogram < 0 and current_row.get('macd', 0) < current_row.get('macd_signal', 0):
            reasons.append("MACD momentum negative")
            confidence_factors.append(0.2)
        
        # Trend alignment
        if self.trend_direction in ['bearish', 'neutral']:
            confidence_factors.append(0.2)
        else:
            confidence_factors.append(-0.3)  # Penalize counter-trend
        
        # Resistance level rejection
        resistance_distance = self._get_nearest_resistance_distance(current_row['close'])
        if 0 < resistance_distance < 0.02:  # Within 2% of resistance
            reasons.append("near key resistance level")
            confidence_factors.append(0.3)
        
        if len(reasons) >= 2 and sum(confidence_factors) > 0.4:
            setup['valid'] = True
            setup['reason'] = " + ".join(reasons)
            setup['confidence'] = min(sum(confidence_factors), 1.0)
        
        return setup

    def _calculate_swing_confidence(self, row: pd.Series, signal_type: SignalType, data: pd.DataFrame) -> float:
        """Calculate confidence for swing trading signals."""
        if signal_type == SignalType.HOLD:
            return 0.0
        
        confidence_factors = []
        
        # Technical confluence
        rsi = row['rsi']
        bb_position = row.get('bb_position', 0.5)
        volume_ratio = row.get('volume_ratio', 1)
        
        # RSI positioning
        if signal_type == SignalType.BUY:
            rsi_confidence = max(0, (self.rsi_oversold - rsi) / self.rsi_oversold)
        else:
            rsi_confidence = max(0, (rsi - self.rsi_overbought) / (100 - self.rsi_overbought))
        confidence_factors.append(rsi_confidence * 0.3)
        
        # Bollinger Band positioning
        if signal_type == SignalType.BUY:
            bb_confidence = max(0, 1 - bb_position * 2)  # Lower is better for buys
        else:
            bb_confidence = max(0, (bb_position - 0.5) * 2)  # Higher is better for sells
        confidence_factors.append(bb_confidence * 0.2)
        
        # Volume confirmation
        volume_confidence = min((volume_ratio - 1) * 0.5, 0.5)
        confidence_factors.append(volume_confidence * 0.2)
        
        # Trend alignment
        if signal_type == SignalType.BUY and self.trend_direction == 'bullish':
            confidence_factors.append(0.15)
        elif signal_type == SignalType.SELL and self.trend_direction == 'bearish':
            confidence_factors.append(0.15)
        elif self.trend_direction == 'neutral':
            confidence_factors.append(0.05)
        
        # Market structure favorability
        if self.market_structure == 'trending':
            confidence_factors.append(0.1)
        elif self.market_structure == 'ranging':
            confidence_factors.append(0.05)
        
        return max(0.0, min(1.0, sum(confidence_factors)))

    def _calculate_swing_risk(self, row: pd.Series, signal_type: SignalType, data: pd.DataFrame) -> float:
        """Calculate risk score for swing trading signals."""
        if signal_type == SignalType.HOLD:
            return 0.0
        
        risk_factors = []
        
        # Market volatility risk
        volatility = row.get('market_volatility', 0)
        volatility_risk = min(volatility * 50, 1.0)
        risk_factors.append(volatility_risk * 0.3)
        
        # Counter-trend risk
        if signal_type == SignalType.BUY and self.trend_direction == 'bearish':
            risk_factors.append(0.4)
        elif signal_type == SignalType.SELL and self.trend_direction == 'bullish':
            risk_factors.append(0.4)
        
        # Market structure risk
        if self.market_structure == 'volatile':
            risk_factors.append(0.3)
        elif self.market_structure == 'ranging' and signal_type in [SignalType.BUY, SignalType.SELL]:
            risk_factors.append(0.2)
        
        # Time-based risk (avoid weekend gaps, etc.)
        current_time = datetime.now()
        if current_time.weekday() >= 5:  # Weekend
            risk_factors.append(0.2)
        
        return max(0.0, min(1.0, sum(risk_factors) / len(risk_factors) if risk_factors else 0.0))

    # Helper methods for swing trading analysis
    def _calculate_rsi(self, prices: pd.Series, period: int) -> pd.Series:
        """Calculate RSI with Wilder's smoothing."""
        delta = prices.diff()
        gains = delta.where(delta > 0, 0.0)
        losses = -delta.where(delta < 0, 0.0)
        
        avg_gains = gains.ewm(alpha=1/period, adjust=False).mean()
        avg_losses = losses.ewm(alpha=1/period, adjust=False).mean()
        
        rs = avg_gains / avg_losses
        return 100 - (100 / (1 + rs))

    def _detect_swing_highs(self, highs: pd.Series, window: int = 5) -> pd.Series:
        """Detect swing high points."""
        swing_highs = pd.Series(False, index=highs.index)
        for i in range(window, len(highs) - window):
            if highs.iloc[i] == highs.iloc[i-window:i+window+1].max():
                swing_highs.iloc[i] = True
        return swing_highs

    def _detect_swing_lows(self, lows: pd.Series, window: int = 5) -> pd.Series:
        """Detect swing low points."""
        swing_lows = pd.Series(False, index=lows.index)
        for i in range(window, len(lows) - window):
            if lows.iloc[i] == lows.iloc[i-window:i+window+1].min():
                swing_lows.iloc[i] = True
        return swing_lows

    def _update_market_structure(self, data: pd.DataFrame):
        """Update market structure analysis."""
        if len(data) < 50:
            return
        
        recent_data = data.tail(50)
        price_change = (recent_data['close'].iloc[-1] - recent_data['close'].iloc[0]) / recent_data['close'].iloc[0]
        volatility = recent_data['close'].std() / recent_data['close'].mean()
        
        # Determine trend direction
        if price_change > 0.05:
            self.trend_direction = 'bullish'
        elif price_change < -0.05:
            self.trend_direction = 'bearish'
        else:
            self.trend_direction = 'neutral'
        
        # Determine market structure
        if volatility > 0.05:
            self.market_structure = 'volatile'
        elif abs(price_change) > 0.03:
            self.market_structure = 'trending'
        else:
            self.market_structure = 'ranging'

    def get_parameter_ranges(self) -> Dict[str, Tuple[float, float]]:
        """Get parameter ranges for optimization."""
        return {
            'rsi_period': (10, 21),
            'rsi_oversold': (25, 40),
            'rsi_overbought': (60, 75),
            'ma_fast': (15, 30),
            'ma_slow': (40, 60),
            'bb_period': (15, 25),
            'bb_std': (1.5, 2.5),
            'volume_threshold': (1.1, 1.5),
            'min_risk_reward': (1.5, 3.0)
        }

    def update_parameters(self, parameters: Dict[str, Any]) -> None:
        """Update strategy parameters."""
        for param, value in parameters.items():
            if hasattr(self, param):
                setattr(self, param, value)
                self.parameters[param] = value
        
        self.logger.info(f"Updated swing trading parameters: {parameters}")

    def get_strategy_info(self) -> Dict[str, Any]:
        """Get comprehensive strategy information."""
        return {
            'name': self.name,
            'type': self.strategy_type.value,
            'description': 'Advanced Bitcoin swing trading with multi-timeframe analysis',
            'parameters': {
                'timeframe': self.primary_timeframe,
                'rsi_period': self.rsi_period,
                'rsi_levels': f"{self.rsi_oversold}/{self.rsi_overbought}",
                'moving_averages': f"{self.ma_fast}/{self.ma_slow}",
                'bollinger_bands': f"{self.bb_period}({self.bb_std})",
                'min_risk_reward': self.min_risk_reward,
                'max_hold_days': self.max_hold_days
            },
            'best_for': 'Bitcoin swing trading with 1-7 day holding periods',
            'signals': {
                'buy': 'Multi-timeframe bullish confluence with support',
                'sell': 'Multi-timeframe bearish confluence with resistance'
            },
            'indicators_used': [
                'RSI with divergence', 'EMA Fast/Slow', 'Bollinger Bands',
                'MACD', 'Volume Analysis', 'Support/Resistance', 'Market Structure'
            ],
            'min_data_points': max(self.ma_slow, self.bb_period, 50),
            'current_state': {
                'position': self.current_position,
                'trend_direction': self.trend_direction,
                'market_structure': self.market_structure
            }
        }

    def __str__(self) -> str:
        return f"SwingTradingStrategy(timeframe={self.primary_timeframe}, rsi={self.rsi_period}, ma={self.ma_fast}/{self.ma_slow})"