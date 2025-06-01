"""Moving Average Crossover strategy implementation."""

from typing import Dict, Optional
import pandas as pd
import numpy as np
import structlog

from odin.strategies.base import BaseStrategy, validate_data_columns
from odin.core.models import StrategyAnalysis, StrategyType, TrendType

logger = structlog.get_logger(__name__)


class MovingAverageStrategy(BaseStrategy):
    """Moving Average Crossover trading strategy."""
    
    def __init__(
        self, 
        short_window: Optional[int] = None,
        long_window: Optional[int] = None,
        **kwargs
    ) -> None:
        """Initialize Moving Average strategy."""
        super().__init__(**kwargs)
        
        self.strategy_type = StrategyType.MOVING_AVERAGE
        self.short_window = short_window or self.settings.ma_short_period
        self.long_window = long_window or self.settings.ma_long_period
        self.min_data_points = max(self.long_window + 5, 25)
        
        logger.info("Moving Average strategy initialized",
                   short_window=self.short_window,
                   long_window=self.long_window)
    
    async def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate moving averages."""
        validate_data_columns(data, ['price'])
        
        # Calculate moving averages
        data['ma_short'] = data['price'].rolling(window=self.short_window, min_periods=1).mean()
        data['ma_long'] = data['price'].rolling(window=self.long_window, min_periods=1).mean()
        
        # Calculate MA spread for additional insight
        data['ma_spread'] = data['ma_short'] - data['ma_long']
        data['ma_spread_pct'] = (data['ma_spread'] / data['ma_long']) * 100
        
        return data
    
    async def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """Generate buy/sell signals based on MA crossover."""
        # Calculate indicators first
        data = await self.calculate_indicators(data)
        
        # Initialize signal columns
        data['signal'] = 0
        data['signal_type'] = ''
        
        # Need enough data for reliable signals
        if len(data) < self.long_window + 1:
            return data
        
        # Generate crossover signals
        for i in range(self.long_window, len(data)):
            current_short = data.iloc[i]['ma_short']
            current_long = data.iloc[i]['ma_long']
            prev_short = data.iloc[i-1]['ma_short']
            prev_long = data.iloc[i-1]['ma_long']
            
            # Skip if any values are NaN
            if pd.isna([current_short, current_long, prev_short, prev_long]).any():
                continue
            
            # Buy signal: short MA crosses above long MA (golden cross)
            if prev_short <= prev_long and current_short > current_long:
                data.iloc[i, data.columns.get_loc('signal')] = 1
                data.iloc[i, data.columns.get_loc('signal_type')] = 'BUY'
            
            # Sell signal: short MA crosses below long MA (death cross)
            elif prev_short >= prev_long and current_short < current_long:
                data.iloc[i, data.columns.get_loc('signal')] = -1
                data.iloc[i, data.columns.get_loc('signal_type')] = 'SELL'
        
        return data
    
    async def analyze_current_market(self) -> StrategyAnalysis:
        """Analyze current market using MA strategy."""
        try:
            # Get recent data
            data = await self.get_historical_data(hours=24)
            
            # Generate signals
            data_with_signals = await self.generate_signals(data)
            
            # Get latest values
            latest = data_with_signals.iloc[-1]
            
            # Determine trend
            trend = TrendType.BULLISH if latest['ma_short'] > latest['ma_long'] else TrendType.BEARISH
            
            # Get latest signal
            latest_signal = self._get_latest_signal(data_with_signals)
            
            # Prepare indicators
            indicators = {
                'ma_short': float(latest['ma_short']),
                'ma_long': float(latest['ma_long']),
                'ma_spread': float(latest['ma_spread']),
                'ma_spread_pct': float(latest['ma_spread_pct']),
                'short_window': self.short_window,
                'long_window': self.long_window,
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
            logger.error("Market analysis failed", error=str(e))
            raise