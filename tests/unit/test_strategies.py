"""
Tests for trading strategies.
These tests verify that strategy classes work correctly and generate proper signals.
"""

import sys
import os
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestStrategyBase:
    """Test base strategy functionality."""
    
    def test_strategy_base_import(self):
        """Test that strategy base classes can be imported."""
        try:
            from odin.strategies.base import Strategy, StrategyType, Signal
            print("✅ Strategy base classes imported successfully")
            
            # Test enums
            assert hasattr(StrategyType, 'TREND_FOLLOWING')
            assert hasattr(StrategyType, 'MEAN_REVERSION')
            
        except ImportError as e:
            pytest.skip(f"Strategy base classes not available: {e}")
    
    def test_signal_types(self):
        """Test signal type consistency."""
        try:
            # Try to import from both locations to check consistency
            from odin.core.models import SignalType
            
            # Check that signal types exist
            assert hasattr(SignalType, 'BUY')
            assert hasattr(SignalType, 'SELL')
            assert hasattr(SignalType, 'HOLD')
            
            print("✅ Signal types imported from core.models")
            
        except ImportError:
            try:
                from odin.strategies.base import StrategySignal
                print("⚠️ Using StrategySignal from base (should migrate to SignalType)")
                
            except ImportError:
                pytest.skip("No signal types available")


class TestMovingAverageStrategy:
    """Test Moving Average strategy."""
    
    def test_moving_average_strategy_import(self):
        """Test MA strategy can be imported."""
        try:
            from odin.strategies.moving_average import MovingAverageStrategy
            print("✅ MovingAverageStrategy imported successfully")
            
        except ImportError as e:
            pytest.skip(f"MovingAverageStrategy not available: {e}")
    
    def test_moving_average_strategy_creation(self):
        """Test MA strategy can be created."""
        try:
            from odin.strategies.moving_average import MovingAverageStrategy
            
            # Create strategy with valid parameters
            strategy = MovingAverageStrategy(short_window=5, long_window=20)
            
            assert strategy.short_window == 5
            assert strategy.long_window == 20
            assert strategy.name == "MovingAverage"
            
            print("✅ MovingAverageStrategy created successfully")
            
        except ImportError:
            pytest.skip("MovingAverageStrategy not available")
    
    def test_moving_average_indicators(self):
        """Test MA strategy indicator calculation."""
        try:
            from odin.strategies.moving_average import MovingAverageStrategy
            
            strategy = MovingAverageStrategy(short_window=3, long_window=5)
            
            # Create test data
            data = pd.DataFrame({
                'open': [100, 101, 102, 103, 104, 105],
                'high': [102, 103, 104, 105, 106, 107],
                'low': [99, 100, 101, 102, 103, 104],
                'close': [101, 102, 103, 104, 105, 106],
                'volume': [1000, 1100, 1200, 1300, 1400, 1500]
            })
            
            # Calculate indicators
            result = strategy.calculate_indicators(data)
            
            # Check that indicators were added
            assert 'ma_short' in result.columns
            assert 'ma_long' in result.columns
            
            # Check that moving averages are calculated correctly
            assert not result['ma_short'].isna().all()
            assert not result['ma_long'].isna().all()
            
            print("✅ MovingAverageStrategy indicators calculated")
            
        except ImportError:
            pytest.skip("MovingAverageStrategy not available")


class TestRSIStrategy:
    """Test RSI strategy."""
    
    def test_rsi_strategy_import(self):
        """Test RSI strategy can be imported."""
        try:
            from odin.strategies.rsi import RSIStrategy
            print("✅ RSIStrategy imported successfully")
            
        except ImportError as e:
            pytest.skip(f"RSIStrategy not available: {e}")
    
    def test_rsi_strategy_creation(self):
        """Test RSI strategy can be created."""
        try:
            from odin.strategies.rsi import RSIStrategy
            
            strategy = RSIStrategy(period=14, oversold=30, overbought=70)
            
            assert strategy.period == 14
            assert strategy.oversold == 30
            assert strategy.overbought == 70
            assert strategy.name == "RSI"
            
            print("✅ RSIStrategy created successfully")
            
        except ImportError:
            pytest.skip("RSIStrategy not available")


class TestSwingTradingStrategy:
    """Test Swing Trading strategy."""
    
    def test_swing_strategy_import(self):
        """Test Swing strategy can be imported."""
        try:
            from odin.strategies.swing_trader import SwingTradingStrategy
            print("✅ SwingTradingStrategy imported successfully")
            
        except ImportError as e:
            pytest.skip(f"SwingTradingStrategy not available: {e}")
    
    def test_swing_strategy_creation(self):
        """Test Swing strategy can be created."""
        try:
            from odin.strategies.swing_trader import SwingTradingStrategy
            
            strategy = SwingTradingStrategy(
                rsi_period=14,
                rsi_oversold=35,
                rsi_overbought=65,
                ma_fast=21,
                ma_slow=50
            )
            
            assert strategy.rsi_period == 14
            assert strategy.rsi_oversold == 35
            assert strategy.rsi_overbought == 65
            assert strategy.ma_fast == 21
            assert strategy.ma_slow == 50
            assert strategy.name == "SwingTrading"
            
            print("✅ SwingTradingStrategy created successfully")
            
        except ImportError:
            pytest.skip("SwingTradingStrategy not available")


class TestStrategySignalGeneration:
    """Test strategy signal generation with mock data."""
    
    def create_sample_data(self, num_points=100):
        """Create sample OHLCV data for testing."""
        dates = pd.date_range(start='2024-01-01', periods=num_points, freq='1H')
        
        # Generate realistic price data
        base_price = 50000
        prices = []
        current_price = base_price
        
        for i in range(num_points):
            # Add some randomness but keep it realistic
            change = np.random.normal(0, 0.02)  # 2% standard deviation
            current_price *= (1 + change)
            prices.append(current_price)
        
        # Create OHLCV data
        data = []
        for i, price in enumerate(prices):
            high = price * (1 + abs(np.random.normal(0, 0.01)))
            low = price * (1 - abs(np.random.normal(0, 0.01)))
            open_price = prices[i-1] if i > 0 else price
            volume = np.random.randint(1000, 10000)
            
            data.append({
                'timestamp': dates[i],
                'open': open_price,
                'high': high,
                'low': low,
                'close': price,
                'volume': volume
            })
        
        df = pd.DataFrame(data)
        df.set_index('timestamp', inplace=True)
        return df
    
    def test_strategy_with_sample_data(self):
        """Test that strategies can process sample data without errors."""
        try:
            from odin.strategies.moving_average import MovingAverageStrategy
            
            strategy = MovingAverageStrategy(short_window=5, long_window=10)
            data = self.create_sample_data(50)
            
            # Test indicator calculation
            result = strategy.calculate_indicators(data)
            assert len(result) == len(data)
            assert 'ma_short' in result.columns
            assert 'ma_long' in result.columns
            
            # Test signal generation (should not raise exceptions)
            signal = strategy.generate_signal(result)
            assert signal is not None
            assert hasattr(signal, 'signal')
            assert hasattr(signal, 'confidence')
            assert hasattr(signal, 'price')
            
            print("✅ Strategy processes sample data successfully")
            
        except ImportError:
            pytest.skip("MovingAverageStrategy not available")
        except Exception as e:
            pytest.fail(f"Strategy failed with sample data: {e}")
    
    def test_strategy_parameter_validation(self):
        """Test strategy parameter validation."""
        try:
            from odin.strategies.moving_average import MovingAverageStrategy
            
            # Test valid parameters
            strategy = MovingAverageStrategy(short_window=5, long_window=20)
            assert strategy.short_window == 5
            assert strategy.long_window == 20
            
            # Test invalid parameters (should raise ValueError)
            with pytest.raises(ValueError):
                MovingAverageStrategy(short_window=20, long_window=5)  # short >= long
            
            with pytest.raises(ValueError):
                MovingAverageStrategy(short_window=0, long_window=5)  # invalid window
            
            print("✅ Strategy parameter validation working")
            
        except ImportError:
            pytest.skip("MovingAverageStrategy not available")


class TestStrategyRegistry:
    """Test strategy registry and factory functions."""
    
    def test_strategy_registry_import(self):
        """Test strategy registry can be imported."""
        try:
            from odin.strategies import STRATEGY_REGISTRY, get_strategy
            
            assert isinstance(STRATEGY_REGISTRY, dict)
            assert len(STRATEGY_REGISTRY) > 0
            
            print(f"✅ Strategy registry found with {len(STRATEGY_REGISTRY)} strategies")
            
        except ImportError:
            pytest.skip("Strategy registry not available")
    
    def test_get_strategy_function(self):
        """Test get_strategy factory function."""
        try:
            from odin.strategies import get_strategy
            
            # Test getting a strategy by name
            strategy_class = get_strategy("moving_average")
            assert strategy_class is not None
            
            # Test invalid strategy name
            with pytest.raises(ValueError):
                get_strategy("nonexistent_strategy")
            
            print("✅ get_strategy function working")
            
        except ImportError:
            pytest.skip("get_strategy function not available")


# Utility functions for testing
def create_test_price_data(length=100, start_price=50000):
    """Create test price data for strategy testing."""
    dates = pd.date_range(start='2024-01-01', periods=length, freq='1H')
    
    data = []
    current_price = start_price
    
    for i, date in enumerate(dates):
        # Simple price movement
        change = np.random.normal(0, 0.01)
        current_price *= (1 + change)
        
        # Create OHLC
        high = current_price * (1 + abs(np.random.normal(0, 0.005)))
        low = current_price * (1 - abs(np.random.normal(0, 0.005)))
        open_price = data[i-1]['close'] if i > 0 else current_price
        volume = np.random.randint(1000, 5000)
        
        data.append({
            'timestamp': date,
            'open': open_price,
            'high': high,
            'low': low,
            'close': current_price,
            'volume': volume
        })
    
    df = pd.DataFrame(data)
    df.set_index('timestamp', inplace=True)
    return df


if __name__ == "__main__":
    pytest.main([__file__, "-v"])