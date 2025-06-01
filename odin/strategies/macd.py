"""MACD (Moving Average Convergence Divergence) strategy implementation."""

from typing import Optional
import pandas as pd
import numpy as np
import structlog

from odin.strategies.base import BaseStrategy, validate_data_columns, safe_divide
from odin.core.models import StrategyAnalysis, StrategyType, TrendType

logger = structlog.get_logger(__name__)


class MACDStrategy(BaseStrategy):
    """MACD trend momentum trading strategy."""
    
    def __init__(
        self,
        fast_period: Optional[int] = None,
        slow_period: Optional[int] = None,
        signal_period: Optional[int] = None,
        **kwargs
    ) -> None:
        """Initialize MACD strategy."""
        super().__init__(**kwargs)
        
        self.strategy_type = StrategyType.MACD
        self.fast_period = fast_period or self.settings.macd_fast
        self.slow_period = slow_period or self.settings.macd_slow
        self.signal_period = signal_period or self.settings.macd_signal
        self.min_data_points = max(self.slow_period + self.signal_period + 5, 40)
        
        logger.info("MACD strategy initialized",
                   fast_period=self.fast_period,
                   slow_period=self.slow_period,
                   signal_period=self.signal_period)
    
    def _calculate_ema(self, prices: pd.Series, period: int) -> pd.Series:
        """Calculate Exponential Moving Average."""
        return prices.ewm(span=period, adjust=False).mean()
    
    async def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate MACD indicators."""
        validate_data_columns(data, ['price'])
        
        # Calculate EMAs
        data['ema_fast'] = self._calculate_ema(data['price'], self.fast_period)
        data['ema_slow'] = self._calculate_ema(data['price'], self.slow_period)
        
        # Calculate MACD line
        data['macd_line'] = data['ema_fast'] - data['ema_slow']
        
        # Calculate signal line
        data['macd_signal'] = self._calculate_ema(data['macd_line'], self.signal_period)
        
        # Calculate histogram
        data['macd_histogram'] = data['macd_line'] - data['macd_signal']
        
        # Calculate MACD momentum (rate of change)
        data['macd_momentum'] = data['macd_line'].diff()
        
        return data
    
    async def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """Generate buy/sell signals based on MACD."""
        # Calculate indicators first
        data = await self.calculate_indicators(data)
        
        # Initialize signal columns
        data['signal'] = 0
        data['signal_type'] = ''
        
        # Need enough data for reliable signals
        min_required = self.slow_period + self.signal_period + 2
        if len(data) < min_required:
            return data
        
        # Generate MACD signals
        for i in range(min_required, len(data)):
            current_macd = data.iloc[i]['macd_line']
            current_signal = data.iloc[i]['macd_signal']
            current_histogram = data.iloc[i]['macd_histogram']
            
            prev_macd = data.iloc[i-1]['macd_line']
            prev_signal = data.iloc[i-1]['macd_signal']
            prev_histogram = data.iloc[i-1]['macd_histogram']
            
            # Skip if any values are NaN
            if pd.isna([current_macd, current_signal, prev_macd, prev_signal]).any():
                continue
            
            # Buy signals
            # 1. MACD line crosses above signal line (bullish crossover)
            if prev_macd <= prev_signal and current_macd > current_signal:
                data.iloc[i, data.columns.get_loc('signal')] = 1
                data.iloc[i, data.columns.get_loc('signal_type')] = 'BUY'
            
            # 2. MACD crosses above zero line (momentum confirmation)
            elif prev_macd <= 0 and current_macd > 0:
                data.iloc[i, data.columns.get_loc('signal')] = 1
                data.iloc[i, data.columns.get_loc('signal_type')] = 'BUY'
            
            # Sell signals
            # 1. MACD line crosses below signal line (bearish crossover)
            elif prev_macd >= prev_signal and current_macd < current_signal:
                data.iloc[i, data.columns.get_loc('signal')] = -1
                data.iloc[i, data.columns.get_loc('signal_type')] = 'SELL'
            
            # 2. MACD crosses below zero line (momentum confirmation)
            elif prev_macd >= 0 and current_macd < 0:
                data.iloc[i, data.columns.get_loc('signal')] = -1
                data.iloc[i, data.columns.get_loc('signal_type')] = 'SELL'
        
        return data
    
    async def analyze_current_market(self) -> StrategyAnalysis:
        """Analyze current market using MACD strategy."""
        try:
            # Get recent data
            data = await self.get_historical_data(hours=24)
            
            # Generate signals
            data_with_signals = await self.generate_signals(data)
            
            # Get latest values
            latest = data_with_signals.iloc[-1]
            
            # Determine trend based on MACD position and histogram
            macd_line = latest['macd_line']
            macd_signal = latest['macd_signal']
            histogram = latest['macd_histogram']
            
            if macd_line > 0 and histogram > 0:
                trend = TrendType.BULLISH
            elif macd_line < 0 and histogram < 0:
                trend = TrendType.BEARISH
            else:
                trend = TrendType.SIDEWAYS
            
            # Get latest signal
            latest_signal = self._get_latest_signal(data_with_signals)
            
            # Determine momentum condition
            if abs(histogram) > abs(latest['macd_line']) * 0.1:
                momentum_condition = "strong"
            elif abs(histogram) < abs(latest['macd_line']) * 0.05:
                momentum_condition = "weak"
            else:
                momentum_condition = "moderate"
            
            # Prepare indicators
            indicators = {
                'macd_line': float(latest['macd_line']),
                'macd_signal': float(latest['macd_signal']),
                'macd_histogram': float(latest['macd_histogram']),
                'macd_momentum': float(latest['macd_momentum']) if pd.notna(latest['macd_momentum']) else 0.0,
                'ema_fast': float(latest['ema_fast']),
                'ema_slow': float(latest['ema_slow']),
                'fast_period': self.fast_period,
                'slow_period': self.slow_period,
                'signal_period': self.signal_period,
                'momentum_condition': momentum_condition,
            }
            
            return StrategyAnalysis(
                strategy=self.strategy_type,
                current_price=float(latest['price']),
                trend=trend,
                signal=latest_signal,
                indicators=indicators,
                data_points=len(data_with_signals),
                timestamp=latest.name,
            )
            
        except Exception as e:
            logger.error("MACD market analysis failed", error=str(e))
            raise
