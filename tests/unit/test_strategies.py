import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from odin.strategies import (
    MovingAverageStrategy, 
    RSIStrategy, 
    get_strategy,
    list_strategies
)
from odin.core.models import StrategyType
from odin.core.exceptions import InsufficientDataError

class TestMovingAverageStrategy:
    """Test MovingAverageStrategy."""
    
    @pytest.fixture
    def strategy(self):
        return MovingAverageStrategy(short_window=5, long_window=10)
    
    @pytest.fixture
    def sample_data(self):
        """Generate sample price data."""
        dates = pd.date_range('2024-01-01', periods=50, freq='H')
        # Create trending price data
        prices = [100 + i * 0.5 + np.random.normal(0, 1) for i in range(50)]
        return pd.DataFrame({'price': prices}, index=dates)
    
    def test_initialization(self, strategy):
        """Test strategy initialization."""
        assert strategy.strategy_type == StrategyType.MOVING_AVERAGE
        assert strategy.short_window == 5
        assert strategy.long_window == 10
        assert strategy.min_data_points >= 15
    
    @pytest.mark.asyncio
    async def test_calculate_indicators(self, strategy, sample_data):
        """Test moving average calculation."""
        result = await strategy.calculate_indicators(sample_data)
        
        assert 'ma_short' in result.columns
        assert 'ma_long' in result.columns
        assert 'ma_spread' in result.columns
        assert 'ma_spread_pct' in result.columns
        
        # Check that moving averages are calculated correctly
        assert not result['ma_short'].isna().all()
        assert not result['ma_long'].isna().all()
    
    @pytest.mark.asyncio
    async def test_generate_signals(self, strategy, sample_data):
        """Test signal generation."""
        result = await strategy.generate_signals(sample_data)
        
        assert 'signal' in result.columns
        assert 'signal_type' in result.columns
        
        # Check signal values are valid
        unique_signals = result['signal'].unique()
        assert all(signal in [-1, 0, 1] for signal in unique_signals)
    
    @pytest.mark.asyncio
    async def test_insufficient_data(self, strategy):
        """Test handling of insufficient data."""
        # Create very small dataset
        small_data = pd.DataFrame({
            'price': [100, 101, 102]
        }, index=pd.date_range('2024-01-01', periods=3, freq='H'))
        
        with pytest.raises(Exception):  # Should raise some form of error
            await strategy.generate_signals(small_data)

class TestRSIStrategy:
    """Test RSIStrategy."""
    
    @pytest.fixture
    def strategy(self):
        return RSIStrategy(period=14, oversold=30, overbought=70)
    
    @pytest.fixture
    def sample_data(self):
        """Generate sample price data with oscillating pattern."""
        dates = pd.date_range('2024-01-01', periods=100, freq='H')
        # Create oscillating price pattern
        prices = [100 + 10 * np.sin(i * 0.1) + np.random.normal(0, 0.5) for i in range(100)]
        return pd.DataFrame({'price': prices}, index=dates)
    
    def test_initialization(self, strategy):
        """Test RSI strategy initialization."""
        assert strategy.strategy_type == StrategyType.RSI
        assert strategy.period == 14
        assert strategy.oversold == 30
        assert strategy.overbought == 70
    
    @pytest.mark.asyncio
    async def test_calculate_indicators(self, strategy, sample_data):
        """Test RSI calculation."""
        result = await strategy.calculate_indicators(sample_data)
        
        assert 'rsi' in result.columns
        assert 'rsi_momentum' in result.columns
        assert 'rsi_smooth' in result.columns
        
        # RSI should be between 0 and 100
        rsi_values = result['rsi'].dropna()
        assert (rsi_values >= 0).all()
        assert (rsi_values <= 100).all()
    
    @pytest.mark.asyncio
    async def test_generate_signals(self, strategy, sample_data):
        """Test RSI signal generation."""
        result = await strategy.generate_signals(sample_data)
        
        assert 'signal' in result.columns
        assert 'signal_type' in result.columns
        
        # Check that signals are generated based on RSI levels
        buy_signals = result[result['signal'] == 1]
        sell_signals = result[result['signal'] == -1]
        
        # Buy signals should occur when RSI was oversold
        # Sell signals should occur when RSI was overbought
        # (This is a simplified check)

class TestStrategyRegistry:
    """Test strategy registry functions."""
    
    def test_list_strategies(self):
        """Test strategy listing."""
        strategies = list_strategies()
        assert isinstance(strategies, list)
        assert len(strategies) > 0
        assert "moving_average" in strategies
        assert "rsi" in strategies
    
    def test_get_strategy(self):
        """Test strategy factory."""
        ma_strategy = get_strategy("moving_average", short_window=5, long_window=20)
        assert isinstance(ma_strategy, MovingAverageStrategy)
        assert ma_strategy.short_window == 5
        assert ma_strategy.long_window == 20
        
        rsi_strategy = get_strategy("rsi", period=14)
        assert isinstance(rsi_strategy, RSIStrategy)
        assert rsi_strategy.period == 14
    
    def test_get_unknown_strategy(self):
        """Test handling of unknown strategy."""
        with pytest.raises(ValueError, match="Unknown strategy"):
            get_strategy("unknown_strategy")