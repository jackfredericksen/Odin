"""
Bitcoin Swing Trading Strategy - Part 1: Core Class & Initialization

A comprehensive swing trading strategy optimized for Bitcoin's medium-term price movements.
Combines multiple technical indicators with market sentiment analysis for 1-7 day holding periods.

Best For: Bitcoin swing trading with 1-7 day holding periods
Strategy Type: Hybrid (Trend + Mean Reversion + Momentum)
Signals: Multi-timeframe analysis with confirmation signals
"""

from datetime import datetime, timedelta
from typing import Dict, Any, Tuple, List, Optional
import pandas as pd
import numpy as np
import logging

# Import from base strategy and models (using correct imports from codebase)
from .base import Strategy, StrategyType, SignalType, Signal
from ..core.models import SignalType


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
                 stop_loss_pct: float = 0.03,
                 take_profit_pct: float = 0.06,
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
            stop_loss_pct: Stop loss percentage
            take_profit_pct: Take profit percentage
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
            stop_loss_pct=stop_loss_pct,
            take_profit_pct=take_profit_pct,
            **kwargs
        )
        
        # Strategy parameters
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
        self.stop_loss_pct = stop_loss_pct
        self.take_profit_pct = take_profit_pct
        
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
        
        # Performance tracking
        self.swing_signals_count = 0
        self.successful_swings = 0
        self.current_risk_reward = 0
        
        self.logger.info(f"Initialized Swing Trading strategy for {primary_timeframe} timeframe")
        self.logger.info(f"RSI levels: {rsi_oversold}/{rsi_overbought}, MA: {ma_fast}/{ma_slow}")

    def __str__(self) -> str:
        return f"SwingTradingStrategy(timeframe={self.primary_timeframe}, rsi={self.rsi_period}, ma={self.ma_fast}/{self.ma_slow})"
        
    def __repr__(self) -> str:
        return self.__str__()

    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate comprehensive technical indicators for swing trading.
        
        Args:
            data: Raw OHLCV price data
            
        Returns:
            Data with swing trading indicators
        """
        df = data.copy()
        
        # Ensure we have required columns
        required_cols = ['open', 'high', 'low', 'close', 'volume']
        for col in required_cols:
            if col not in df.columns:
                self.logger.warning(f"Missing required column: {col}")
                return df
        
        # Core Moving Averages
        df['ema_fast'] = df['close'].ewm(span=self.ma_fast, adjust=False).mean()
        df['ema_slow'] = df['close'].ewm(span=self.ma_slow, adjust=False).mean()
        df['sma_200'] = df['close'].rolling(window=200, min_periods=1).mean()  # Long-term trend
        
        # RSI with multiple timeframes
        df['rsi'] = self._calculate_rsi(df['close'], self.rsi_period)
        df['rsi_smooth'] = df['rsi'].rolling(window=3, min_periods=1).mean()
        
        # Bollinger Bands for volatility
        df['bb_middle'] = df['close'].rolling(window=self.bb_period, min_periods=1).mean()
        bb_std = df['close'].rolling(window=self.bb_period, min_periods=1).std()
        df['bb_upper'] = df['bb_middle'] + (bb_std * self.bb_std)
        df['bb_lower'] = df['bb_middle'] - (bb_std * self.bb_std)
        df['bb_width'] = (df['bb_upper'] - df['bb_lower']) / df['bb_middle']
        df['bb_position'] = (df['close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'])
        
        # Handle division by zero
        df['bb_width'] = df['bb_width'].fillna(0)
        df['bb_position'] = df['bb_position'].fillna(0.5)
        
        # MACD for momentum
        ema_12 = df['close'].ewm(span=12, adjust=False).mean()
        ema_26 = df['close'].ewm(span=26, adjust=False).mean()
        df['macd'] = ema_12 - ema_26
        df['macd_signal'] = df['macd'].ewm(span=9, adjust=False).mean()
        df['macd_histogram'] = df['macd'] - df['macd_signal']
        
        # Volume analysis
        df['volume_sma'] = df['volume'].rolling(window=20, min_periods=1).mean()
        df['volume_ratio'] = df['volume'] / df['volume_sma']
        df['volume_surge'] = df['volume_ratio'] > self.volume_threshold
        
        # Handle division by zero for volume
        df['volume_ratio'] = df['volume_ratio'].fillna(1.0)
        df['volume_surge'] = df['volume_surge'].fillna(False)
        
        # Price action analysis
        df['high_low_ratio'] = (df['high'] - df['low']) / df['close']
        df['body_size'] = abs(df['close'] - df['open']) / df['close']
        df['upper_shadow'] = (df['high'] - df[['open', 'close']].max(axis=1)) / df['close']
        df['lower_shadow'] = (df[['open', 'close']].min(axis=1) - df['low']) / df['close']
        
        # Fill any NaN values
        df['high_low_ratio'] = df['high_low_ratio'].fillna(0)
        df['body_size'] = df['body_size'].fillna(0)
        df['upper_shadow'] = df['upper_shadow'].fillna(0)
        df['lower_shadow'] = df['lower_shadow'].fillna(0)
        
        # Swing highs and lows detection
        df['swing_high'] = self._detect_swing_highs(df['high'], window=5)
        df['swing_low'] = self._detect_swing_lows(df['low'], window=5)
        
        # Support and resistance levels
        df = self._calculate_support_resistance(df)
        
        # Market structure analysis
        df['trend_strength'] = self._calculate_trend_strength(df)
        df['market_volatility'] = df['close'].rolling(window=20, min_periods=1).std() / df['close']
        df['market_volatility'] = df['market_volatility'].fillna(0)
        
        # Fibonacci retracement levels (simplified)
        df = self._calculate_fibonacci_levels(df)
        
        # Additional momentum indicators
        df['price_change'] = df['close'].pct_change()
        df['momentum'] = df['close'] / df['close'].shift(self.rsi_period) - 1
        df['price_change'] = df['price_change'].fillna(0)
        df['momentum'] = df['momentum'].fillna(0)
        
        return df

    def _calculate_rsi(self, prices: pd.Series, period: int) -> pd.Series:
        """Calculate RSI with Wilder's smoothing."""
        delta = prices.diff()
        gains = delta.where(delta > 0, 0.0)
        losses = -delta.where(delta < 0, 0.0)
        
        avg_gains = gains.ewm(alpha=1/period, adjust=False).mean()
        avg_losses = losses.ewm(alpha=1/period, adjust=False).mean()
        
        # Avoid division by zero
        rs = avg_gains / avg_losses.replace(0, np.nan)
        rsi = 100 - (100 / (1 + rs))
        
        return rsi.fillna(50)  # Fill NaN with neutral RSI

    def _detect_swing_highs(self, highs: pd.Series, window: int = 5) -> pd.Series:
        """Detect swing high points."""
        swing_highs = pd.Series(False, index=highs.index)
        
        if len(highs) < window * 2 + 1:
            return swing_highs
            
        for i in range(window, len(highs) - window):
            if highs.iloc[i] == highs.iloc[i-window:i+window+1].max():
                swing_highs.iloc[i] = True
        return swing_highs

    def _detect_swing_lows(self, lows: pd.Series, window: int = 5) -> pd.Series:
        """Detect swing low points."""
        swing_lows = pd.Series(False, index=lows.index)
        
        if len(lows) < window * 2 + 1:
            return swing_lows
            
        for i in range(window, len(lows) - window):
            if lows.iloc[i] == lows.iloc[i-window:i+window+1].min():
                swing_lows.iloc[i] = True
        return swing_lows

    def _calculate_support_resistance(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate support and resistance levels."""
        df['support_level'] = 0.0
        df['resistance_level'] = 0.0
        df['support_distance'] = 1.0
        df['resistance_distance'] = 1.0
        
        if len(df) < 50:
            return df
        
        # Use swing highs/lows for S/R calculation
        swing_highs = df[df['swing_high'] == True]['high'].values
        swing_lows = df[df['swing_low'] == True]['low'].values
        
        if len(swing_highs) > 0:
            self.resistance_levels = list(swing_highs[-10:])  # Keep last 10
        if len(swing_lows) > 0:
            self.support_levels = list(swing_lows[-10:])  # Keep last 10
        
        # Calculate nearest support/resistance distances
        for i in range(len(df)):
            current_price = df['close'].iloc[i]
            
            # Find nearest support below current price
            supports_below = [s for s in self.support_levels if s < current_price]
            if supports_below:
                nearest_support = max(supports_below)
                df.iloc[i, df.columns.get_loc('support_level')] = nearest_support
                df.iloc[i, df.columns.get_loc('support_distance')] = (current_price - nearest_support) / current_price
            
            # Find nearest resistance above current price
            resistances_above = [r for r in self.resistance_levels if r > current_price]
            if resistances_above:
                nearest_resistance = min(resistances_above)
                df.iloc[i, df.columns.get_loc('resistance_level')] = nearest_resistance
                df.iloc[i, df.columns.get_loc('resistance_distance')] = (nearest_resistance - current_price) / current_price
        
        return df

    def _calculate_trend_strength(self, df: pd.DataFrame) -> pd.Series:
        """Calculate trend strength indicator."""
        if len(df) < self.ma_slow:
            return pd.Series(0, index=df.index)
        
        # Use EMA relationship for trend strength
        ema_diff = (df['ema_fast'] - df['ema_slow']) / df['ema_slow']
        
        # Normalize to -1 to 1 range
        trend_strength = np.tanh(ema_diff * 10)  # Scale and limit
        
        return pd.Series(trend_strength, index=df.index).fillna(0)

    def _calculate_fibonacci_levels(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate simplified Fibonacci retracement levels."""
        df['fib_23.6'] = 0.0
        df['fib_38.2'] = 0.0
        df['fib_50.0'] = 0.0
        df['fib_61.8'] = 0.0
        
        if len(df) < 20:
            return df
        
        # Calculate over rolling 20-period window
        for i in range(20, len(df)):
            window_data = df.iloc[i-20:i]
            high = window_data['high'].max()
            low = window_data['low'].min()
            
            # Calculate Fibonacci levels
            diff = high - low
            df.iloc[i, df.columns.get_loc('fib_23.6')] = high - (diff * 0.236)
            df.iloc[i, df.columns.get_loc('fib_38.2')] = high - (diff * 0.382)
            df.iloc[i, df.columns.get_loc('fib_50.0')] = high - (diff * 0.500)
            df.iloc[i, df.columns.get_loc('fib_61.8')] = high - (diff * 0.618)
        
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
        
        # Handle timestamp properly
        if hasattr(current_row.name, 'to_pydatetime'):
            timestamp = current_row.name.to_pydatetime()
        elif isinstance(current_row.name, datetime):
            timestamp = current_row.name
        else:
            timestamp = datetime.now()
        
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
            'rsi': float(current_row.get('rsi', 50)),
            'rsi_smooth': float(current_row.get('rsi_smooth', current_row.get('rsi', 50))),
            'ema_fast': float(current_row.get('ema_fast', current_price)),
            'ema_slow': float(current_row.get('ema_slow', current_price)),
            'bb_position': float(current_row.get('bb_position', 0.5)),
            'bb_width': float(current_row.get('bb_width', 0)),
            'macd': float(current_row.get('macd', 0)),
            'macd_signal': float(current_row.get('macd_signal', 0)),
            'volume_ratio': float(current_row.get('volume_ratio', 1)),
            'trend_direction': self.trend_direction,
            'market_structure': self.market_structure,
            'support_distance': self._get_nearest_support_distance(current_price),
            'resistance_distance': self._get_nearest_resistance_distance(current_price),
            'risk_reward_ratio': float(getattr(self, 'current_risk_reward', 0)),
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
        
        # Update tracking
        self.last_signal = signal
        self.signals_history.append(signal)
        
        if signal_type != SignalType.HOLD:
            self.swing_signals_count += 1
        
        self.logger.debug(f"Swing signal: {signal_type.value} "
                         f"(confidence: {confidence:.3f}, risk: {risk_score:.3f})")
        
        return signal

    def _check_exit_conditions(self, current_row: pd.Series, data: pd.DataFrame) -> Optional[Signal]:
        """Check if current position should be exited."""
        if not self.current_position or not self.entry_time:
            return None
        
        current_price = current_row['close']
        current_time = datetime.now()
        
        # Time-based exit
        if self.entry_time and (current_time - self.entry_time).days >= self.max_hold_days:
            return Signal(
                signal=SignalType.SELL if self.current_position == 'long' else SignalType.BUY,
                confidence=0.8,
                timestamp=current_time,
                price=current_price,
                reasoning=f"Time-based exit after {self.max_hold_days} days",
                indicators={},
                risk_score=0.3
            )
        
        # Stop loss hit
        if self.stop_loss:
            if (self.current_position == 'long' and current_price <= self.stop_loss) or \
               (self.current_position == 'short' and current_price >= self.stop_loss):
                self._close_position()
                return Signal(
                    signal=SignalType.SELL if self.current_position == 'long' else SignalType.BUY,
                    confidence=0.9,
                    timestamp=current_time,
                    price=current_price,
                    reasoning="Stop loss triggered",
                    indicators={},
                    risk_score=0.2
                )
        
        # Take profit hit
        if self.take_profit:
            if (self.current_position == 'long' and current_price >= self.take_profit) or \
               (self.current_position == 'short' and current_price <= self.take_profit):
                self._close_position()
                return Signal(
                    signal=SignalType.SELL if self.current_position == 'long' else SignalType.BUY,
                    confidence=0.9,
                    timestamp=current_time,
                    price=current_price,
                    reasoning="Take profit reached",
                    indicators={},
                    risk_score=0.1
                )
        
        # Technical exit conditions
        rsi = current_row.get('rsi', 50)
        if self.current_position == 'long' and rsi > 75:
            return Signal(
                signal=SignalType.SELL,
                confidence=0.7,
                timestamp=current_time,
                price=current_price,
                reasoning="RSI overbought exit for long position",
                indicators={'rsi': rsi},
                risk_score=0.4
            )
        elif self.current_position == 'short' and rsi < 25:
            return Signal(
                signal=SignalType.BUY,
                confidence=0.7,
                timestamp=current_time,
                price=current_price,
                reasoning="RSI oversold exit for short position",
                indicators={'rsi': rsi},
                risk_score=0.4
            )
        
        return None

    def _analyze_long_setup(self, current_row: pd.Series, data: pd.DataFrame) -> Dict[str, Any]:
        """Analyze potential long swing setup."""
        setup = {'valid': False, 'reason': '', 'confidence': 0.0}
        
        rsi = current_row.get('rsi', 50)
        ema_fast = current_row.get('ema_fast', 0)
        ema_slow = current_row.get('ema_slow', 0)
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
        
        # MACD momentum turning negative
        if macd_histogram < 0:
            macd = current_row.get('macd', 0)
            macd_signal = current_row.get('macd_signal', 0)
            if macd < macd_signal:
                reasons.append("MACD momentum negative")
                confidence_factors.append(0.2)
        
        # EMA alignment
        if ema_fast < ema_slow * 1.001:  # Allow small tolerance
            reasons.append("EMA alignment bearish")
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
        
        return setup.append(0.3)
        
        # MACD momentum turning positive
        if macd_histogram > 0:
            macd = current_row.get('macd', 0)
            macd_signal = current_row.get('macd_signal', 0)
            if macd > macd_signal:
                reasons.append("MACD momentum positive")
                confidence_factors.append(0.2)
        
        # EMA alignment
        if ema_fast > ema_slow * 0.999:  # Allow small tolerance
            reasons.append("EMA alignment bullish")
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
        
        rsi = current_row.get('rsi', 50)
        ema_fast = current_row.get('ema_fast', 0)
        ema_slow = current_row.get('ema_slow', 0)
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
            confidence_factors
    def _prepare_long_position(self, current_row: pd.Series, setup: Dict[str, Any]):
        """Prepare for long position entry."""
        current_price = current_row['close']
        
        self.current_position = 'long'
        self.entry_price = current_price
        self.entry_time = datetime.now()
        
        # Calculate stop loss and take profit
        self.stop_loss = current_price * (1 - self.stop_loss_pct)
        self.take_profit = current_price * (1 + self.take_profit_pct)
        
        # Calculate risk/reward ratio
        risk = self.stop_loss_pct
        reward = self.take_profit_pct
        self.current_risk_reward = reward / risk if risk > 0 else 0
        
        self.logger.info(f"Prepared long position at {current_price:.2f}, "
                        f"SL: {self.stop_loss:.2f}, TP: {self.take_profit:.2f}, "
                        f"R/R: {self.current_risk_reward:.2f}")

    def _prepare_short_position(self, current_row: pd.Series, setup: Dict[str, Any]):
        """Prepare for short position entry."""
        current_price = current_row['close']
        
        self.current_position = 'short'
        self.entry_price = current_price
        self.entry_time = datetime.now()
        
        # Calculate stop loss and take profit
        self.stop_loss = current_price * (1 + self.stop_loss_pct)
        self.take_profit = current_price * (1 - self.take_profit_pct)
        
        # Calculate risk/reward ratio
        risk = self.stop_loss_pct
        reward = self.take_profit_pct
        self.current_risk_reward = reward / risk if risk > 0 else 0
        
        self.logger.info(f"Prepared short position at {current_price:.2f}, "
                        f"SL: {self.stop_loss:.2f}, TP: {self.take_profit:.2f}, "
                        f"R/R: {self.current_risk_reward:.2f}")

    def _close_position(self):
        """Close current position."""
        if self.current_position:
            self.logger.info(f"Closing {self.current_position} position at {self.entry_price}")
            
        self.current_position = None
        self.entry_price = None
        self.entry_time = None
        self.stop_loss = None
        self.take_profit = None
        self.current_risk_reward = 0

    def _calculate_swing_confidence(self, row: pd.Series, signal_type: SignalType, data: pd.DataFrame) -> float:
        """Calculate confidence for swing trading signals."""
        if signal_type == SignalType.HOLD:
            return 0.0
        
        confidence_factors = []
        
        # Technical confluence
        rsi = row.get('rsi', 50)
        bb_position = row.get('bb_position', 0.5)
        volume_ratio = row.get('volume_ratio', 1)
        
        # RSI positioning
        if signal_type == SignalType.BUY:
            rsi_confidence = max(0, (self.rsi_oversold - rsi) / self.rsi_oversold) if self.rsi_oversold > 0 else 0
        else:
            rsi_confidence = max(0, (rsi - self.rsi_overbought) / (100 - self.rsi_overbought)) if self.rsi_overbought < 100 else 0
        confidence_factors.append(rsi_confidence * 0.3)
        
        # Bollinger Band positioning
        if signal_type == SignalType.BUY:
            bb_confidence = max(0, 1 - bb_position * 2)  # Lower is better for buys
        else:
            bb_confidence = max(0, (bb_position - 0.5) * 2)  # Higher is better for sells
        confidence_factors.append(bb_confidence * 0.2)
        
        # Volume confirmation
        volume_confidence = min((volume_ratio - 1) * 0.5, 0.5) if volume_ratio > 1 else 0
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
        volatility_risk = min(volatility * 50, 1.0) if volatility > 0 else 0
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
        
        # Position concentration risk
        if self.current_position:
            risk_factors.append(0.3)  # Already in position
        
        return max(0.0, min(1.0, sum(risk_factors) / len(risk_factors) if risk_factors else 0.0))

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

    def _check_bullish_divergence(self, data: pd.DataFrame) -> bool:
        """Check for bullish RSI divergence."""
        if len(data) < 20:
            return False
        
        recent = data.tail(20)
        
        # Look for lower lows in price but higher lows in RSI
        price_lows = recent['low'].rolling(window=5).min()
        rsi_lows = recent['rsi'].rolling(window=5).min()
        
        if len(price_lows) < 10 or len(rsi_lows) < 10:
            return False
        
        # Simple divergence check
        price_trend = price_lows.iloc[-1] < price_lows.iloc[-10]
        rsi_trend = rsi_lows.iloc[-1] > rsi_lows.iloc[-10]
        
        return price_trend and rsi_trend

    def _check_bearish_divergence(self, data: pd.DataFrame) -> bool:
        """Check for bearish RSI divergence."""
        if len(data) < 20:
            return False
        
        recent = data.tail(20)
        
        # Look for higher highs in price but lower highs in RSI
        price_highs = recent['high'].rolling(window=5).max()
        rsi_highs = recent['rsi'].rolling(window=5).max()
        
        if len(price_highs) < 10 or len(rsi_highs) < 10:
            return False
        
        # Simple divergence check
        price_trend = price_highs.iloc[-1] > price_highs.iloc[-10]
        rsi_trend = rsi_highs.iloc[-1] < rsi_highs.iloc[-10]
        
        return price_trend and rsi_trend

    def _get_nearest_support_distance(self, current_price: float) -> float:
        """Get distance to nearest support level."""
        if not self.support_levels:
            return 1.0
        
        supports_below = [s for s in self.support_levels if s < current_price]
        if not supports_below:
            return 1.0
        
        nearest_support = max(supports_below)
        return (current_price - nearest_support) / current_price

    def _get_nearest_resistance_distance(self, current_price: float) -> float:
        """Get distance to nearest resistance level."""
        if not self.resistance_levels:
            return 1.0
        
        resistances_above = [r for r in self.resistance_levels if r > current_price]
        if not resistances_above:
            return 1.0
        
        nearest_resistance = min(resistances_above)
        return (nearest_resistance - current_price) / current_price
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
            'min_risk_reward': (1.5, 3.0),
            'stop_loss_pct': (0.02, 0.05),
            'take_profit_pct': (0.04, 0.10)
        }

    def update_parameters(self, parameters: Dict[str, Any]) -> None:
        """Update strategy parameters."""
        for param, value in parameters.items():
            if hasattr(self, param):
                old_value = getattr(self, param)
                setattr(self, param, value)
                self.parameters[param] = value
                self.logger.debug(f"Updated {param}: {old_value} -> {value}")
        
        self.logger.info(f"Updated swing trading parameters: {list(parameters.keys())}")

    def get_strategy_info(self) -> Dict[str, Any]:
        """Get comprehensive strategy information."""
        return {
            'name': self.name,
            'type': self.strategy_type.value,
            'description': 'Advanced Bitcoin swing trading with multi-timeframe analysis',
            'version': '2.0',
            'parameters': {
                'timeframe': self.primary_timeframe,
                'rsi_period': self.rsi_period,
                'rsi_levels': f"{self.rsi_oversold}/{self.rsi_overbought}",
                'moving_averages': f"{self.ma_fast}/{self.ma_slow}",
                'bollinger_bands': f"{self.bb_period}({self.bb_std})",
                'volume_threshold': self.volume_threshold,
                'min_risk_reward': self.min_risk_reward,
                'max_hold_days': self.max_hold_days,
                'stop_loss_pct': f"{self.stop_loss_pct*100:.1f}%",
                'take_profit_pct': f"{self.take_profit_pct*100:.1f}%"
            },
            'best_for': 'Bitcoin swing trading with 1-7 day holding periods',
            'market_conditions': {
                'optimal': ['trending', 'moderate volatility'],
                'avoid': ['high volatility', 'low volume'],
                'neutral': ['ranging', 'consolidation']
            },
            'signals': {
                'buy': 'Multi-timeframe bullish confluence with support',
                'sell': 'Multi-timeframe bearish confluence with resistance',
                'hold': 'Insufficient confluence or existing position'
            },
            'indicators_used': [
                'RSI with divergence detection',
                'EMA Fast/Slow crossover',
                'Bollinger Bands positioning',
                'MACD momentum',
                'Volume surge analysis',
                'Support/Resistance levels',
                'Market structure analysis',
                'Fibonacci retracements'
            ],
            'risk_management': {
                'stop_loss': f"{self.stop_loss_pct*100:.1f}%",
                'take_profit': f"{self.take_profit_pct*100:.1f}%",
                'max_hold': f"{self.max_hold_days} days",
                'min_risk_reward': self.min_risk_reward,
                'position_sizing': 'Confidence and volatility adjusted'
            },
            'performance_tracking': {
                'signals_generated': self.swing_signals_count,
                'successful_swings': self.successful_swings,
                'success_rate': f"{(self.successful_swings/max(self.swing_signals_count,1)*100):.1f}%"
            },
            'min_data_points': max(self.ma_slow, self.bb_period, 50),
            'current_state': {
                'position': self.current_position,
                'entry_price': self.entry_price,
                'entry_time': self.entry_time.isoformat() if self.entry_time else None,
                'stop_loss': self.stop_loss,
                'take_profit': self.take_profit,
                'trend_direction': self.trend_direction,
                'market_structure': self.market_structure,
                'risk_reward_ratio': self.current_risk_reward
            },
            'optimization': {
                'optimizable_parameters': list(self.get_parameter_ranges().keys()),
                'optimization_target': 'Sharpe ratio',
                'backtest_period': 'Minimum 6 months recommended'
            }
        }

    def get_current_status(self) -> Dict[str, Any]:
        """Get current strategy status."""
        return {
            'strategy_name': self.name,
            'enabled': self.is_enabled,
            'position': {
                'active': self.current_position is not None,
                'type': self.current_position,
                'entry_price': self.entry_price,
                'entry_time': self.entry_time.isoformat() if self.entry_time else None,
                'stop_loss': self.stop_loss,
                'take_profit': self.take_profit,
                'risk_reward': self.current_risk_reward
            },
            'market_analysis': {
                'trend_direction': self.trend_direction,
                'market_structure': self.market_structure,
                'support_levels': len(self.support_levels),
                'resistance_levels': len(self.resistance_levels)
            },
            'performance': {
                'total_signals': self.swing_signals_count,
                'successful_swings': self.successful_swings,
                'last_signal': {
                    'type': self.last_signal.signal.value if self.last_signal else 'none',
                    'confidence': self.last_signal.confidence if self.last_signal else 0,
                    'timestamp': self.last_signal.timestamp.isoformat() if self.last_signal else None
                }
            }
        }

    def reset_strategy(self):
        """Reset strategy state."""
        self._close_position()
        self.support_levels = []
        self.resistance_levels = []
        self.trend_direction = "neutral"
        self.market_structure = "ranging"
        self.swing_signals_count = 0
        self.successful_swings = 0
        self.current_risk_reward = 0
        self.signals_history = []
        self.trades_history = []
        self.last_signal = None
        
        self.logger.info("Strategy state reset")

    def validate_parameters(self) -> bool:
        """Validate strategy parameters."""
        try:
            assert 0 < self.rsi_period <= 50, "RSI period must be between 1 and 50"
            assert 0 < self.rsi_oversold < 50, "RSI oversold must be between 0 and 50"
            assert 50 < self.rsi_overbought < 100, "RSI overbought must be between 50 and 100"
            assert self.rsi_oversold < self.rsi_overbought, "RSI oversold must be less than overbought"
            assert 0 < self.ma_fast < self.ma_slow, "Fast MA must be less than slow MA"
            assert self.ma_slow <= 200, "Slow MA should not exceed 200"
            assert 0 < self.bb_period <= 50, "BB period must be between 1 and 50"
            assert 0.5 <= self.bb_std <= 3.0, "BB std must be between 0.5 and 3.0"
            assert 1.0 <= self.volume_threshold <= 5.0, "Volume threshold must be between 1.0 and 5.0"
            assert 1.0 <= self.min_risk_reward <= 10.0, "Min risk/reward must be between 1.0 and 10.0"
            assert 1 <= self.max_hold_days <= 30, "Max hold days must be between 1 and 30"
            assert 0.005 <= self.stop_loss_pct <= 0.20, "Stop loss must be between 0.5% and 20%"
            assert 0.01 <= self.take_profit_pct <= 0.50, "Take profit must be between 1% and 50%"
            
            return True
            
        except AssertionError as e:
            self.logger.error(f"Parameter validation failed: {e}")
            return False

    def get_optimization_suggestions(self, performance_data: Optional[Dict] = None) -> List[str]:
        """Get optimization suggestions based on performance."""
        suggestions = []
        
        if performance_data:
            win_rate = performance_data.get('win_rate', 0)
            avg_trade_duration = performance_data.get('avg_trade_duration_hours', 0)
            max_drawdown = performance_data.get('max_drawdown', 0)
            
            if win_rate < 0.4:
                suggestions.append("Consider tightening entry criteria - low win rate detected")
                suggestions.append("Try adjusting RSI levels or requiring more confirmations")
            
            if win_rate > 0.8:
                suggestions.append("Win rate very high - consider loosening criteria for more opportunities")
            
            if avg_trade_duration > self.max_hold_days * 20:  # hours
                suggestions.append("Trades holding too long - consider tighter profit targets")
            
            if max_drawdown > 0.15:
                suggestions.append("High drawdown detected - consider smaller position sizes")
                suggestions.append("Review stop loss levels")
        
        # General suggestions
        if self.swing_signals_count > 0:
            success_rate = self.successful_swings / self.swing_signals_count
            if success_rate < 0.5:
                suggestions.append("Low success rate - review entry/exit logic")
        
        if not suggestions:
            suggestions.append("Strategy parameters appear well-balanced")
            suggestions.append("Consider backtesting on different market periods")
        
        return suggestions