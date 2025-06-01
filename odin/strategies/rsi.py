"""RSI (Relative Strength Index) strategy implementation."""

from typing import Optional
import pandas as pd
import numpy as np
import structlog

from odin.strategies.base import BaseStrategy, validate_data_columns
from odin.core.models import StrategyAnalysis, StrategyType, TrendType

logger = structlog.get_logger(__name__)


class RSIStrategy(BaseStrategy):
    """RSI momentum trading strategy."""
    
    def __init__(
        self,
        period: Optional[int] = None,
        oversold: Optional[int] = None,
        overbought: Optional[int] = None,
        **kwargs
    ) -> None:
        """Initialize RSI strategy."""
        super().__init__(**kwargs)
        
        self.strategy_type = StrategyType.RSI
        self.period = period or self.settings.rsi_period
        self.oversold = oversold or self.settings.rsi_oversold
        self.overbought = overbought or self.settings.rsi_overbought
        self.min_data_points = max(self.period * 2, 30)
        
        logger.info("RSI strategy initialized",
                   period=self.period,
                   oversold=self.oversold,
                   overbought=self.overbought)
    
    def _calculate_rsi(self, prices: pd.Series, period: int) -> pd.Series:
        """Calculate RSI indicator."""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    async def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate RSI and related indicators."""
        validate_data_columns(data, ['price'])
        
        # Calculate RSI
        data['rsi'] = self._calculate_rsi(data['price'], self.period)
        
        # RSI momentum (rate of change)
        data['rsi_momentum'] = data['rsi'].diff()
        
        # RSI smoothed (3-period SMA of RSI)
        data['rsi_smooth'] = data['rsi'].rolling(window=3).mean()
        
        # Oversold/Overbought levels
        data['rsi_oversold_level'] = self.oversold
        data['rsi_overbought_level'] = self.overbought
        
        return data
    
    async def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """Generate buy/sell signals based on RSI levels."""
        # Calculate indicators first
        data = await self.calculate_indicators(data)
        
        # Initialize signal columns
        data['signal'] = 0
        data['signal_type'] = ''
        
        # Need enough data for reliable signals
        if len(data) < self.period + 5:
            return data
        
        # Generate RSI-based signals
        for i in range(self.period + 1, len(data)):
            current_rsi = data.iloc[i]['rsi']
            prev_rsi = data.iloc[i-1]['rsi']
            
            # Skip if RSI values are NaN
            if pd.isna(current_rsi) or pd.isna(prev_rsi):
                continue
            
            # Buy signal: RSI crosses above oversold level
            if prev_rsi <= self.oversold and current_rsi > self.oversold:
                data.iloc[i, data.columns.get_loc('signal')] = 1
                data.iloc[i, data.columns.get_loc('signal_type')] = 'BUY'
            
            # Sell signal: RSI crosses below overbought level
            elif prev_rsi >= self.overbought and current_rsi < self.overbought:
                data.iloc[i, data.columns.get_loc('signal')] = -1
                data.iloc[i, data.columns.get_loc('signal_type')] = 'SELL'
        
        return data
    
    async def analyze_current_market(self) -> StrategyAnalysis:
        """Analyze current market using RSI strategy."""
        try:
            # Get recent data
            data = await self.get_historical_data(hours=24)
            
            # Generate signals
            data_with_signals = await self.generate_signals(data)
            
            # Get latest values
            latest = data_with_signals.iloc[-1]
            
            # Determine trend based on RSI and price action
            rsi_value = latest['rsi']
            if rsi_value > 50:
                trend = TrendType.BULLISH
            elif rsi_value < 50:
                trend = TrendType.BEARISH
            else:
                trend = TrendType.SIDEWAYS
            
            # Get latest signal
            latest_signal = self._get_latest_signal(data_with_signals)
            
            # Prepare indicators
            indicators = {
                'rsi': float(latest['rsi']),
                'rsi_momentum': float(latest['rsi_momentum']) if pd.notna(latest['rsi_momentum']) else 0.0,
                'rsi_smooth': float(latest['rsi_smooth']) if pd.notna(latest['rsi_smooth']) else float(latest['rsi']),
                'oversold_level': self.oversold,
                'overbought_level': self.overbought,
                'period': self.period,
                'market_condition': (
                    'oversold' if rsi_value <= self.oversold
                    else 'overbought' if rsi_value >= self.overbought
                    else 'neutral'
                ),
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
            logger.error("RSI market analysis failed", error=str(e))
            raise