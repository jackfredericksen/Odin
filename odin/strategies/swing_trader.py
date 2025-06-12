"""
Enhanced Bitcoin Swing Trading Strategy

Complete implementation with all missing helper methods and AI-optimized
features for intelligent swing trading decisions.

File: odin/strategies/swing_trader.py
"""

from datetime import datetime, timedelta
from typing import Dict, Any, Tuple, List
import pandas as pd
import numpy as np
from scipy.signal import find_peaks
from sklearn.linear_model import LinearRegression

# Import from core models for single source of truth
from ..core.models import SignalType
from .base import Strategy, StrategyType, Signal


class SwingTradingStrategy(Strategy):
    """
    Advanced Bitcoin Swing Trading Strategy Implementation.
    
    This strategy combines multiple timeframes and indicators with complete
    implementation of all helper methods for production use.
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
                 support_resistance_strength: int = 3,
                 fibonacci_levels: List[float] = None,
                 **kwargs):
        """
        Initialize Enhanced Swing Trading strategy.
        """
        super().__init__(
            name="SwingTrading",
            strategy_type=StrategyType.MOMENTUM,
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
            support_resistance_strength=support_resistance_strength,
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
        self.support_resistance_strength = support_resistance_strength
        
        # Fibonacci retracement levels
        self.fibonacci_levels = fibonacci_levels or [0.236, 0.382, 0.500, 0.618, 0.786]
        
        # Swing trading state
        self.current_position = None
        self.entry_price = None
        self.entry_time = None
        self.stop_loss = None
        self.take_profit = None
        self.support_levels = []
        self.resistance_levels = []
        self.fibonacci_retracements = {}
        
        # Market structure tracking
        self.trend_direction = "neutral"  # "bullish", "bearish", "neutral"
        self.market_structure = "ranging"  # "trending", "ranging", "volatile"
        self.current_risk_reward = 0.0
        
        self.logger.info(f"Initialized Enhanced Swing Trading strategy for {primary_timeframe} timeframe")

    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate comprehensive technical indicators for swing trading."""
        df = data.copy()
        
        # Core Moving Averages
        df['ema_fast'] = df['close'].ewm(span=self.ma_fast).mean()
        df['ema_slow'] = df['close'].ewm(span=self.ma_slow).mean()
        df['sma_200'] = df['close'].rolling(window=200).mean()
        
        # RSI with multiple timeframes
        df['rsi'] = self._calculate_rsi(df['close'], self.rsi_period)
        df['rsi_smooth'] = df['rsi'].rolling(window=3).mean()
        
        # Bollinger Bands
        df['bb_middle'] = df['close'].rolling(window=self.bb_period).mean()
        bb_std = df['close'].rolling(window=self.bb_period).std()
        df['bb_upper'] = df['bb_middle'] + (bb_std * self.bb_std)
        df['bb_lower'] = df['bb_middle'] - (bb_std * self.bb_std)
        df['bb_width'] = (df['bb_upper'] - df['bb_lower']) / df['bb_middle']
        df['bb_position'] = (df['close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'])
        
        # MACD
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
        
        # Fibonacci retracement levels
        df = self._calculate_fibonacci_levels(df)
        
        return df

    def generate_signal(self, data: pd.DataFrame) -> Signal:
        """Generate swing trading signal based on comprehensive analysis."""
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
        indicators = self._prepare_indicators_dict(current_row, data)
        
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
        """Analyze potential long swing setup with complete implementation."""
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
        
        # Trend alignment
        if self.trend_direction in ['bullish', 'neutral']:
            confidence_factors.append(0.2)
        else:
            confidence_factors.append(-0.3)
        
        # Support level bounce
        support_distance = self._get_nearest_support_distance(current_row['close'])
        if 0 < support_distance < 0.02:
            reasons.append("near key support level")
            confidence_factors.append(0.3)
        
        # Fibonacci level support
        fib_support = self._check_fibonacci_support(current_row['close'], data)
        if fib_support:
            reasons.append(f"Fibonacci {fib_support} support")
            confidence_factors.append(0.2)
        
        if len(reasons) >= 2 and sum(confidence_factors) > 0.4:
            setup['valid'] = True
            setup['reason'] = " + ".join(reasons)
            setup['confidence'] = min(sum(confidence_factors), 1.0)
        
        return setup

    def _analyze_short_setup(self, current_row: pd.Series, data: pd.DataFrame) -> Dict[str, Any]:
        """Analyze potential short swing setup with complete implementation."""
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
            confidence_factors.append(-0.3)
        
        # Resistance level rejection
        resistance_distance = self._get_nearest_resistance_distance(current_row['close'])
        if 0 < resistance_distance < 0.02:
            reasons.append("near key resistance level")
            confidence_factors.append(0.3)
        
        # Fibonacci level resistance
        fib_resistance = self._check_fibonacci_resistance(current_row['close'], data)
        if fib_resistance:
            reasons.append(f"Fibonacci {fib_resistance} resistance")
            confidence_factors.append(0.2)
        
        if len(reasons) >= 2 and sum(confidence_factors) > 0.4:
            setup['valid'] = True
            setup['reason'] = " + ".join(reasons)
            setup['confidence'] = min(sum(confidence_factors), 1.0)
        
        return setup

    def _calculate_support_resistance(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate support and resistance levels using swing points."""
        try:
            # Get swing highs and lows
            swing_highs = df[df['swing_high'] == True]['high'].values
            swing_lows = df[df['swing_low'] == True]['low'].values
            
            # Calculate resistance levels from swing highs
            if len(swing_highs) > 0:
                resistance_levels = []
                for high in swing_highs[-10:]:  # Last 10 swing highs
                    # Count how many times price touched this level
                    touches = sum(1 for h in swing_highs if abs(h - high) / high < 0.01)
                    if touches >= self.support_resistance_strength:
                        resistance_levels.append(high)
                
                self.resistance_levels = sorted(list(set(resistance_levels)))
            
            # Calculate support levels from swing lows
            if len(swing_lows) > 0:
                support_levels = []
                for low in swing_lows[-10:]:  # Last 10 swing lows
                    # Count how many times price touched this level
                    touches = sum(1 for l in swing_lows if abs(l - low) / low < 0.01)
                    if touches >= self.support_resistance_strength:
                        support_levels.append(low)
                
                self.support_levels = sorted(list(set(support_levels)))
            
            # Add support/resistance distances to dataframe
            current_price = df['close'].iloc[-1]
            df['nearest_support'] = self._get_nearest_support_distance(current_price)
            df['nearest_resistance'] = self._get_nearest_resistance_distance(current_price)
            
            return df
            
        except Exception as e:
            self.logger.error(f"Error calculating support/resistance: {e}")
            return df

    def _calculate_fibonacci_levels(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate Fibonacci retracement levels."""
        try:
            if len(df) < 20:
                return df
            
            # Find recent significant high and low
            recent_data = df.tail(50)
            recent_high = recent_data['high'].max()
            recent_low = recent_data['low'].min()
            
            # Calculate Fibonacci levels
            price_range = recent_high - recent_low
            fib_levels = {}
            
            # For uptrend retracements (from high)
            for level in self.fibonacci_levels:
                fib_price = recent_high - (price_range * level)
                fib_levels[f"fib_{level}"] = fib_price
            
            self.fibonacci_retracements = fib_levels
            
            # Add current price's relation to Fibonacci levels
            current_price = df['close'].iloc[-1]
            df['fib_position'] = self._get_fibonacci_position(current_price)
            
            return df
            
        except Exception as e:
            self.logger.error(f"Error calculating Fibonacci levels: {e}")
            return df

    def _calculate_trend_strength(self, df: pd.DataFrame) -> pd.Series:
        """Calculate trend strength using multiple indicators."""
        try:
            trend_strength = pd.Series(index=df.index, dtype=float)
            
            if len(df) < 20:
                return trend_strength.fillna(0.5)
            
            # EMA alignment
            ema_alignment = np.where(df['ema_fast'] > df['ema_slow'], 1, -1)
            
            # Price vs 200 SMA
            sma_200 = df['sma_200'].fillna(df['close'])
            sma_position = np.where(df['close'] > sma_200, 1, -1)
            
            # MACD trend
            macd_trend = np.where(df['macd'] > df['macd_signal'], 1, -1)
            
            # Combine indicators
            combined_strength = (ema_alignment + sma_position + macd_trend) / 3
            
            # Smooth the result
            trend_strength = pd.Series(combined_strength, index=df.index).rolling(5).mean()
            
            # Normalize to 0-1 range
            trend_strength = (trend_strength + 1) / 2
            
            return trend_strength.fillna(0.5)
            
        except Exception as e:
            self.logger.error(f"Error calculating trend strength: {e}")
            return pd.Series(index=df.index, dtype=float).fillna(0.5)

    def _check_bullish_divergence(self, data: pd.DataFrame) -> bool:
        """Check for bullish RSI divergence."""
        try:
            if len(data) < 20:
                return False
            
            recent_data = data.tail(20)
            
            # Find recent lows in price and RSI
            price_lows = []
            rsi_lows = []
            
            for i in range(5, len(recent_data) - 5):
                if (recent_data['low'].iloc[i] < recent_data['low'].iloc[i-2:i+3].min() and
                    recent_data['low'].iloc[i] == recent_data['low'].iloc[i-2:i+3].min()):
                    price_lows.append((i, recent_data['low'].iloc[i]))
                    rsi_lows.append((i, recent_data['rsi'].iloc[i]))
            
            # Check for divergence (price making lower lows, RSI making higher lows)
            if len(price_lows) >= 2:
                last_price_low = price_lows[-1][1]
                prev_price_low = price_lows[-2][1]
                last_rsi_low = rsi_lows[-1][1]
                prev_rsi_low = rsi_lows[-2][1]
                
                return (last_price_low < prev_price_low and last_rsi_low > prev_rsi_low)
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error checking bullish divergence: {e}")
            return False

    def _check_bearish_divergence(self, data: pd.DataFrame) -> bool:
        """Check for bearish RSI divergence."""
        try:
            if len(data) < 20:
                return False
            
            recent_data = data.tail(20)
            
            # Find recent highs in price and RSI
            price_highs = []
            rsi_highs = []
            
            for i in range(5, len(recent_data) - 5):
                if (recent_data['high'].iloc[i] > recent_data['high'].iloc[i-2:i+3].max() and
                    recent_data['high'].iloc[i] == recent_data['high'].iloc[i-2:i+3].max()):
                    price_highs.append((i, recent_data['high'].iloc[i]))
                    rsi_highs.append((i, recent_data['rsi'].iloc[i]))
            
            # Check for divergence (price making higher highs, RSI making lower highs)
            if len(price_highs) >= 2:
                last_price_high = price_highs[-1][1]
                prev_price_high = price_highs[-2][1]
                last_rsi_high = rsi_highs[-1][1]
                prev_rsi_high = rsi_highs[-2][1]
                
                return (last_price_high > prev_price_high and last_rsi_high < prev_rsi_high)
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error checking bearish divergence: {e}")
            return False

    def _get_nearest_support_distance(self, current_price: float) -> float:
        """Get distance to nearest support level."""
        if not self.support_levels:
            return 1.0  # No support levels identified
        
        # Find nearest support below current price
        supports_below = [s for s in self.support_levels if s < current_price]
        
        if not supports_below:
            return 1.0
        
        nearest_support = max(supports_below)
        return (current_price - nearest_support) / current_price

    def _get_nearest_resistance_distance(self, current_price: float) -> float:
        """Get distance to nearest resistance level."""
        if not self.resistance_levels:
            return 1.0  # No resistance levels identified
        
        # Find nearest resistance above current price
        resistances_above = [r for r in self.resistance_levels if r > current_price]
        
        if not resistances_above:
            return 1.0
        
        nearest_resistance = min(resistances_above)
        return (nearest_resistance - current_price) / current_price

    def _check_fibonacci_support(self, current_price: float, data: pd.DataFrame) -> str:
        """Check if current price is near Fibonacci support level."""
        if not self.fibonacci_retracements:
            return ""
        
        for level_name, level_price in self.fibonacci_retracements.items():
            if abs(current_price - level_price) / current_price < 0.01:  # Within 1%
                if current_price >= level_price:  # Price above fib level (support)
                    return level_name.replace("fib_", "")
        
        return ""

    def _check_fibonacci_resistance(self, current_price: float, data: pd.DataFrame) -> str:
        """Check if current price is near Fibonacci resistance level."""
        if not self.fibonacci_retracements:
            return ""
        
        for level_name, level_price in self.fibonacci_retracements.items():
            if abs(current_price - level_price) / current_price < 0.01:  # Within 1%
                if current_price <= level_price:  # Price below fib level (resistance)
                    return level_name.replace("fib_", "")
        
        return ""

    def _get_fibonacci_position(self, current_price: float) -> float:
        """Get current price position relative to Fibonacci levels."""
        if not self.fibonacci_retracements:
            return 0.5
        
        fib_values = list(self.fibonacci_retracements.values())
        if not fib_values:
            return 0.5
        
        min_fib = min(fib_values)
        max_fib = max(fib_values)
        
        if max_fib == min_fib:
            return 0.5
        
        position = (current_price - min_fib) / (max_fib - min_fib)
        return max(0, min(1, position))

    def _prepare_long_position(self, current_row: pd.Series, setup: Dict[str, Any]):
        """Prepare long position with stop loss and take profit."""
        entry_price = current_row['close']
        
        # Calculate stop loss (below nearest support or recent low)
        support_distance = self._get_nearest_support_distance(entry_price)
        recent_low = current_row['close'] * (1 - support_distance * 0.5)
        
        stop_loss = min(recent_low, entry_price * 0.95)  # Max 5% stop loss
        
        # Calculate take profit based on risk/reward ratio
        risk = entry_price - stop_loss
        take_profit = entry_price + (risk * self.min_risk_reward)
        
        self.current_position = "long"
        self.entry_price = entry_price
        self.entry_time = datetime.now()
        self.stop_loss = stop_loss
        self.take_profit = take_profit
        self.current_risk_reward = (take_profit - entry_price) / risk if risk > 0 else 0

    def _prepare_short_position(self, current_row: pd.Series, setup: Dict[str, Any]):
        """Prepare short position with stop loss and take profit."""
        entry_price = current_row['close']
        
        # Calculate stop loss (above nearest resistance or recent high)
        resistance_distance = self._get_nearest_resistance_distance(entry_price)
        recent_high = current_row['close'] * (1 + resistance_distance * 0.5)
        
        stop_loss = max(recent_high, entry_price * 1.05)  # Max 5% stop loss
        
        # Calculate take profit based on risk/reward ratio
        risk = stop_loss - entry_price
        take_profit = entry_price - (risk * self.min_risk_reward)
        
        self.current_position = "short"
        self.entry_price = entry_price
        self.entry_time = datetime.now()
        self.stop_loss = stop_loss
        self.take_profit = take_profit
        self.current_risk_reward = (entry_price - take_profit) / risk if risk > 0 else 0

    def _check_exit_conditions(self, current_row: pd.Series, data: pd.DataFrame) -> Signal:
        """Check if current position should be exited."""
        if not self.current_position:
            return None
        
        current_price = current_row['close']
        
        # Time-based exit
        if self.entry_time and datetime.now() - self.entry_time > timedelta(days=self.max_hold_days):
            return self._create_exit_signal(current_price, "max hold period reached")
        
        # Stop loss hit
        if ((self.current_position == "long" and current_price <= self.stop_loss) or
            (self.current_position == "short" and current_price >= self.stop_loss)):
            return self._create_exit_signal(current_price, "stop loss triggered")
        
        # Take profit hit
        if ((self.current_position == "long" and current_price >= self.take_profit) or
            (self.current_position == "short" and current_price <= self.take_profit)):
            return self._create_exit_signal(current_price, "take profit reached")
        
        # RSI reversal exit
        rsi = current_row['rsi']
        if ((self.current_position == "long" and rsi > 75) or
            (self.current_position == "short" and rsi < 25)):
            return self._create_exit_signal(current_price, "RSI extreme reversal")
        
        return None

    def _create_exit_signal(self, current_price: float, reason: str) -> Signal:
        """Create exit signal and reset position."""
        if self.current_position == "long":
            signal_type = SignalType.SELL
        else:
            signal_type = SignalType.BUY
        
        # Calculate P&L
        if self.entry_price:
            if self.current_position == "long":
                pnl_pct = (current_price - self.entry_price) / self.entry_price
            else:
                pnl_pct = (self.entry_price - current_price) / self.entry_price
        else:
            pnl_pct = 0
        
        # Reset position
        self.current_position = None
        self.entry_price = None
        self.entry_time = None
        self.stop_loss = None
        self.take_profit = None
        
        return Signal(
            signal=signal_type,
            confidence=0.9,  # High confidence for exit signals
            timestamp=datetime.now(),
            price=current_price,
            reasoning=f"Position exit: {reason} (P&L: {pnl_pct:.2%})",
            indicators={"exit_reason": reason, "pnl_percent": pnl_pct},
            risk_score=0.1
        )

    def _prepare_indicators_dict(self, current_row: pd.Series, data: pd.DataFrame) -> Dict[str, float]:
        """Prepare comprehensive indicators dictionary."""
        return {
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
            'support_distance': self._get_nearest_support_distance(current_row['close']),
            'resistance_distance': self._get_nearest_resistance_distance(current_row['close']),
            'fibonacci_position': current_row.get('fib_position', 0.5),
            'trend_strength': current_row.get('trend_strength', 0.5),
            'market_volatility': current_row.get('market_volatility', 0.02),
            'risk_reward_ratio': getattr(self, 'current_risk_reward', 0),
            'position_status': 'active' if self.current_position else 'none',
            'swing_high': current_row.get('swing_high', False),
            'swing_low': current_row.get('swing_low', False),
            'volume_surge': current_row.get('volume_surge', False)
        }

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
            rsi_confidence = max(0, (self.rsi_oversold - rsi) / self.rsi_oversold) if rsi < self.rsi_oversold else 0
        else:
            rsi_confidence = max(0, (rsi - self.rsi_overbought) / (100 - self.rsi_overbought)) if rsi > self.rsi_overbought else 0
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
        
        # Support/Resistance proximity
        if signal_type == SignalType.BUY:
            support_conf = max(0, 1 - self._get_nearest_support_distance(row['close']) * 10)
            confidence_factors.append(support_conf * 0.1)
        else:
            resistance_conf = max(0, 1 - self._get_nearest_resistance_distance(row['close']) * 10)
            confidence_factors.append(resistance_conf * 0.1)
        
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
        
        # Support/Resistance distance risk
        if signal_type == SignalType.BUY:
            support_risk = self._get_nearest_support_distance(row['close'])
            risk_factors.append(min(support_risk * 5, 0.3))
        else:
            resistance_risk = self._get_nearest_resistance_distance(row['close'])
            risk_factors.append(min(resistance_risk * 5, 0.3))
        
        # Time-based risk (avoid weekend gaps, etc.)
        current_time = datetime.now()
        if current_time.weekday() >= 5:  # Weekend
            risk_factors.append(0.2)
        
        return max(0.0, min(1.0, sum(risk_factors) / len(risk_factors) if risk_factors else 0.0))

    # Helper methods for technical calculations
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
        """Detect swing high points using scipy find_peaks."""
        try:
            peaks, _ = find_peaks(highs.values, distance=window)
            swing_highs = pd.Series(False, index=highs.index)
            if len(peaks) > 0:
                swing_highs.iloc[peaks] = True
            return swing_highs
        except:
            # Fallback method
            swing_highs = pd.Series(False, index=highs.index)
            for i in range(window, len(highs) - window):
                if highs.iloc[i] == highs.iloc[i-window:i+window+1].max():
                    swing_highs.iloc[i] = True
            return swing_highs

    def _detect_swing_lows(self, lows: pd.Series, window: int = 5) -> pd.Series:
        """Detect swing low points using scipy find_peaks."""
        try:
            peaks, _ = find_peaks(-lows.values, distance=window)
            swing_lows = pd.Series(False, index=lows.index)
            if len(peaks) > 0:
                swing_lows.iloc[peaks] = True
            return swing_lows
        except:
            # Fallback method
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
        
        # Determine trend direction using linear regression
        try:
            x = np.arange(len(recent_data)).reshape(-1, 1)
            y = recent_data['close'].values
            model = LinearRegression().fit(x, y)
            slope = model.coef_[0]
            
            # Normalize slope by price level
            slope_normalized = slope / recent_data['close'].mean()
            
            if slope_normalized > 0.001:  # 0.1% per period
                self.trend_direction = 'bullish'
            elif slope_normalized < -0.001:
                self.trend_direction = 'bearish'
            else:
                self.trend_direction = 'neutral'
        except:
            # Fallback to simple price change
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
            'min_risk_reward': (1.5, 3.0),
            'support_resistance_strength': (2, 5)
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
            'description': 'Advanced Bitcoin swing trading with AI-enhanced multi-timeframe analysis',
            'parameters': {
                'timeframe': self.primary_timeframe,
                'rsi_period': self.rsi_period,
                'rsi_levels': f"{self.rsi_oversold}/{self.rsi_overbought}",
                'moving_averages': f"{self.ma_fast}/{self.ma_slow}",
                'bollinger_bands': f"{self.bb_period}({self.bb_std})",
                'min_risk_reward': self.min_risk_reward,
                'max_hold_days': self.max_hold_days,
                'support_resistance_strength': self.support_resistance_strength
            },
            'best_for': 'Bitcoin swing trading with 1-7 day holding periods',
            'signals': {
                'buy': 'Multi-timeframe bullish confluence with support and Fibonacci levels',
                'sell': 'Multi-timeframe bearish confluence with resistance and Fibonacci levels'
            },
            'indicators_used': [
                'RSI with divergence detection', 'EMA Fast/Slow crossover', 'Bollinger Bands',
                'MACD momentum', 'Volume surge analysis', 'Support/Resistance levels', 
                'Fibonacci retracements', 'Market structure analysis', 'Swing point detection'
            ],
            'features': [
                'Bullish/Bearish divergence detection',
                'Dynamic support/resistance calculation',
                'Fibonacci retracement levels',
                'Risk/reward ratio optimization',
                'Market regime awareness',
                'Position management with stop-loss/take-profit',
                'Multi-timeframe confluence'
            ],
            'min_data_points': max(self.ma_slow, self.bb_period, 50),
            'current_state': {
                'position': self.current_position,
                'entry_price': self.entry_price,
                'stop_loss': self.stop_loss,
                'take_profit': self.take_profit,
                'trend_direction': self.trend_direction,
                'market_structure': self.market_structure,
                'support_levels_count': len(self.support_levels),
                'resistance_levels_count': len(self.resistance_levels),
                'fibonacci_levels_count': len(self.fibonacci_retracements)
            },
            'performance_metrics': {
                'signals_generated': len(self.signals_history),
                'last_signal': self.last_signal.signal.value if self.last_signal else None,
                'last_signal_time': self.last_signal.timestamp if self.last_signal else None
            }
        }

    def get_current_levels(self) -> Dict[str, Any]:
        """Get current support, resistance, and Fibonacci levels."""
        return {
            'support_levels': self.support_levels,
            'resistance_levels': self.resistance_levels,
            'fibonacci_retracements': self.fibonacci_retracements,
            'trend_direction': self.trend_direction,
            'market_structure': self.market_structure
        }

    def reset_position(self):
        """Reset current position state."""
        self.current_position = None
        self.entry_price = None
        self.entry_time = None
        self.stop_loss = None
        self.take_profit = None
        self.current_risk_reward = 0.0
        self.logger.info("Position state reset")

    def __str__(self) -> str:
        return (f"EnhancedSwingTradingStrategy(timeframe={self.primary_timeframe}, "
                f"rsi={self.rsi_period}, ma={self.ma_fast}/{self.ma_slow}, "
                f"position={self.current_position})")

    def __repr__(self) -> str:
        return self.__str__()