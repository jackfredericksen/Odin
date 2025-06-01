"""Bollinger Bands strategy implementation."""

from typing import Optional
import pandas as pd
import numpy as np
import structlog

from odin.strategies.base import BaseStrategy, validate_data_columns
from odin.core.models import StrategyAnalysis, StrategyType, TrendType

logger = structlog.get_logger(__name__)


class BollingerBandsStrategy(BaseStrategy):
    """Bollinger Bands volatility trading strategy."""
    
    def __init__(
        self,
        period: Optional[int] = None,
        std_dev: Optional[float] = None,
        **kwargs
    ) -> None:
        """Initialize Bollinger Bands strategy."""
        super().__init__(**kwargs)
        
        self.strategy_type = StrategyType.BOLLINGER_BANDS
        self.period = period or self.settings.bb_period
        self.std_dev = std_dev or self.settings.bb_std_dev
        self.min_data_points = max(self.period + 10, 30)
        
        logger.info("Bollinger Bands strategy initialized",
                   period=self.period,
                   std_dev=self.std_dev)
    
    async def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate Bollinger Bands indicators."""
        validate_data_columns(data, ['price'])
        
        # Calculate middle band (SMA)
        data['bb_middle'] = data['price'].rolling(window=self.period).mean()
        
        # Calculate standard deviation
        data['bb_std'] = data['price'].rolling(window=self.period).std()
        
        # Calculate upper and lower bands
        data['bb_upper'] = data['bb_middle'] + (data['bb_std'] * self.std_dev)
        data['bb_lower'] = data['bb_middle'] - (data['bb_std'] * self.std_dev)
        
        # Calculate %B (position within bands)
        data['bb_percent_b'] = (data['price'] - data['bb_lower']) / (data['bb_upper'] - data['bb_lower'])
        
        # Calculate bandwidth (volatility measure)
        data['bb_bandwidth'] = (data['bb_upper'] - data['bb_lower']) / data['bb_middle']
        
        return data
    
    async def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """Generate buy/sell signals based on Bollinger Bands."""
        # Calculate indicators first
        data = await self.calculate_indicators(data)
        
        # Initialize signal columns
        data['signal'] = 0
        data['signal_type'] = ''
        
        # Need enough data for reliable signals
        if len(data) < self.period + 5:
            return data
        
        # Generate Bollinger Bands signals
        for i in range(self.period + 1, len(data)):
            current_price = data.iloc[i]['price']
            current_lower = data.iloc[i]['bb_lower']
            current_upper = data.iloc[i]['bb_upper']
            current_percent_b = data.iloc[i]['bb_percent_b']
            
            # Skip if any values are NaN
            if pd.isna([current_price, current_lower, current_upper, current_percent_b]).any():
                continue
            
            # Buy signal: Price touches or goes below lower band (%B <= 0)
            if current_percent_b <= 0.05:  # Small buffer to avoid noise
                data.iloc[i, data.columns.get_loc('signal')] = 1
                data.iloc[i, data.columns.get_loc('signal_type')] = 'BUY'
            
            # Sell signal: Price touches or goes above upper band (%B >= 1)
            elif current_percent_b >= 0.95:  # Small buffer to avoid noise
                data.iloc[i, data.columns.get_loc('signal')] = -1
                data.iloc[i, data.columns.get_loc('signal_type')] = 'SELL'
        
        return data
    
    async def analyze_current_market(self) -> StrategyAnalysis:
        """Analyze current market using Bollinger Bands strategy."""
        try:
            # Get recent data
            data = await self.get_historical_data(hours=24)
            
            # Generate signals
            data_with_signals = await self.generate_signals(data)
            
            # Get latest values
            latest = data_with_signals.iloc[-1]
            
            # Determine trend based on position within bands and bandwidth
            percent_b = latest['bb_percent_b']
            bandwidth = latest['bb_bandwidth']
            
            if percent_b > 0.7:
                trend = TrendType.BULLISH
            elif percent_b < 0.3:
                trend = TrendType.BEARISH
            else:
                trend = TrendType.SIDEWAYS
            
            # Get latest signal
            latest_signal = self._get_latest_signal(data_with_signals)
            
            # Determine market condition
            if bandwidth > 0.1:  # High volatility
                market_condition = "high_volatility"
            elif bandwidth < 0.05:  # Low volatility
                market_condition = "low_volatility" 
            else:
                market_condition = "normal_volatility"
            
            # Prepare indicators
            indicators = {
                'bb_upper': float(latest['bb_upper']),
                'bb_middle': float(latest['bb_middle']),
                'bb_lower': float(latest['bb_lower']),
                'bb_percent_b': float(latest['bb_percent_b']),
                'bb_bandwidth': float(latest['bb_bandwidth']),
                'period': self.period,
                'std_dev': self.std_dev,
                'market_condition': market_condition,
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
            logger.error("Bollinger Bands market analysis failed", error=str(e))
            raise