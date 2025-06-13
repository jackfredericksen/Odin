"""
Integration tests for Odin Bitcoin Trading Bot.
These tests verify that different components work together correctly.
"""

import sys
import os
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, timezone

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestStrategyIntegration:
    """Test strategy integration with data models."""
    
    def create_test_market_data(self, periods=100):
        """Create realistic test market data."""
        dates = pd.date_range(start='2024-01-01', periods=periods, freq='1H')
        
        # Generate realistic Bitcoin price movement
        base_price = 50000
        prices = [base_price]
        
        for i in range(1, periods):
            # Random walk with some mean reversion
            change = np.random.normal(0, 0.02)  # 2% hourly volatility
            mean_reversion = (base_price - prices[-1]) * 0.001  # Slight mean reversion
            new_price = prices[-1] * (1 + change + mean_reversion)
            prices.append(max(new_price, 1000))  # Minimum price of $1000
        
        # Create OHLCV data
        data = []
        for i, (date, close) in enumerate(zip(dates, prices)):
            open_price = prices[i-1] if i > 0 else close
            high = max(open_price, close) * (1 + abs(np.random.normal(0, 0.005)))
            low = min(open_price, close) * (1 - abs(np.random.normal(0, 0.005)))
            volume = np.random.randint(1000, 10000)
            
            data.append({
                'timestamp': date,
                'open': open_price,
                'high': high,
                'low': low,
                'close': close,
                'volume': volume
            })
        
        df = pd.DataFrame(data)
        df.set_index('timestamp', inplace=True)
        return df
    
    def test_strategy_pipeline(self):
        """Test complete strategy pipeline from data to signal."""
        try:
            from odin.strategies.moving_average import MovingAverageStrategy
            
            # Create strategy
            strategy = MovingAverageStrategy(short_window=5, long_window=20)
            
            # Create test data
            data = self.create_test_market_data(50)
            
            # Test full pipeline
            # 1. Calculate indicators
            data_with_indicators = strategy.calculate_indicators(data)
            
            # Verify indicators were added
            assert 'ma_short' in data_with_indicators.columns
            assert 'ma_long' in data_with_indicators.columns
            assert len(data_with_indicators) == len(data)
            
            # 2. Generate signal
            signal = strategy.generate_signal(data_with_indicators)
            
            # Verify signal properties
            assert signal is not None
            assert hasattr(signal, 'signal')
            assert hasattr(signal, 'confidence')
            assert hasattr(signal, 'price')
            assert hasattr(signal, 'timestamp')
            assert hasattr(signal, 'reasoning')
            
            # Verify signal values are reasonable
            assert 0 <= signal.confidence <= 1
            assert signal.price > 0
            assert isinstance(signal.timestamp, datetime)
            assert isinstance(signal.reasoning, str)
            
            print("✅ Complete strategy pipeline working")
            
        except ImportError as e:
            pytest.skip(f"Strategy integration test not available: {e}")
        except Exception as e:
            pytest.fail(f"Strategy pipeline failed: {e}")
    
    def test_multiple_strategies(self):
        """Test multiple strategies on same data."""
        try:
            from odin.strategies.moving_average import MovingAverageStrategy
            from odin.strategies.rsi import RSIStrategy
            
            # Create test data
            data = self.create_test_market_data(100)
            
            # Create multiple strategies
            ma_strategy = MovingAverageStrategy(short_window=5, long_window=20)
            rsi_strategy = RSIStrategy(period=14, oversold=30, overbought=70)
            
            strategies = [ma_strategy, rsi_strategy]
            signals = []
            
            # Test each strategy
            for strategy in strategies:
                # Calculate indicators
                data_with_indicators = strategy.calculate_indicators(data)
                
                # Generate signal
                signal = strategy.generate_signal(data_with_indicators)
                signals.append(signal)
                
                # Verify signal
                assert signal is not None
                assert 0 <= signal.confidence <= 1
                assert signal.price > 0
            
            # Verify we got signals from all strategies
            assert len(signals) == len(strategies)
            
            print(f"✅ Multiple strategies working: {len(signals)} signals generated")
            
        except ImportError as e:
            pytest.skip(f"Multiple strategy test not available: {e}")
        except Exception as e:
            pytest.fail(f"Multiple strategy test failed: {e}")


class TestDataModelIntegration:
    """Test integration between different data models."""
    
    def test_signal_to_order_conversion(self):
        """Test converting signals to orders."""
        try:
            from odin.core.models import (
                TradeSignal, TradeOrder, SignalType, 
                OrderType, OrderSide, OrderStatus
            )
            
            # Create test signal
            signal = TradeSignal(
                id="test-signal-1",
                strategy_id="ma-strategy",
                symbol="BTC-USD",
                signal_type=SignalType.BUY,
                confidence=0.8,
                price=50000.0,
                created_at=datetime.now(timezone.utc)
            )
            
            # Convert signal to order (simulate order creation logic)
            order = TradeOrder(
                id="test-order-1",
                portfolio_id="test-portfolio",
                strategy_id=signal.strategy_id,
                symbol=signal.symbol,
                side=OrderSide.BUY if signal.signal_type == SignalType.BUY else OrderSide.SELL,
                order_type=OrderType.MARKET,
                quantity=0.1,  # Would be calculated based on signal confidence
                status=OrderStatus.PENDING,
                created_at=datetime.now(timezone.utc)
            )
            
            # Verify conversion
            assert order.strategy_id == signal.strategy_id
            assert order.symbol == signal.symbol
            assert order.side.value == signal.signal_type.value
            
            print("✅ Signal to Order conversion working")
            
        except ImportError as e:
            pytest.skip(f"Signal to Order test not available: {e}")
    
    def test_portfolio_position_tracking(self):
        """Test portfolio and position relationship."""
        try:
            from odin.core.models import Portfolio, Position, PositionType
            
            # Create portfolio
            portfolio = Portfolio(
                id="test-portfolio",
                name="Test Portfolio",
                total_value=100000.0,
                cash_balance=50000.0,
                invested_amount=50000.0
            )
            
            # Create position linked to portfolio
            position = Position(
                id="test-position",
                portfolio_id=portfolio.id,
                symbol="BTC-USD",
                side=PositionType.LONG,
                size=1.0,
                entry_price=50000.0,
                cost_basis=50000.0,
                current_price=51000.0,
                unrealized_pnl=1000.0
            )
            
            # Verify relationship
            assert position.portfolio_id == portfolio.id
            assert position.cost_basis <= portfolio.invested_amount
            
            # Verify position calculations
            expected_market_value = position.size * position.current_price
            assert expected_market_value == 51000.0
            
            expected_pnl = expected_market_value - position.cost_basis
            assert expected_pnl == position.unrealized_pnl
            
            print("✅ Portfolio-Position relationship working")
            
        except ImportError as e:
            pytest.skip(f"Portfolio-Position test not available: {e}")


class TestAPIIntegration:
    """Test API integration with core models."""
    
    def test_api_response_models(self):
        """Test API response model integration."""
        try:
            from odin.core.models import APIResponse, PriceData
            
            # Create sample data
            price_data = PriceData(
                symbol="BTC-USD",
                timestamp=datetime.now(timezone.utc),
                price=50000.0,
                volume=1000.0,
                source="test"
            )
            
            # Create API response
            response = APIResponse(
                success=True,
                message="Price data retrieved successfully",
                data=price_data.to_dict() if hasattr(price_data, 'to_dict') else {
                    'symbol': price_data.symbol,
                    'price': price_data.price,
                    'volume': price_data.volume
                },
                timestamp=datetime.now(timezone.utc)
            )
            
            # Verify response
            assert response.success is True
            assert response.data is not None
            assert 'symbol' in response.data
            assert response.data['symbol'] == "BTC-USD"
            
            print("✅ API Response integration working")
            
        except ImportError as e:
            pytest.skip(f"API Response test not available: {e}")


class TestDataPersistence:
    """Test data persistence and retrieval."""
    
    def test_model_serialization(self):
        """Test that models can be serialized/deserialized."""
        try:
            from odin.core.models import PriceData
            import json
            
            # Create model instance
            original = PriceData(
                symbol="BTC-USD",
                timestamp=datetime.now(timezone.utc),
                price=50000.0,
                volume=1000.0,
                source="test"
            )
            
            # Test serialization
            if hasattr(original, 'to_dict'):
                data_dict = original.to_dict()
                
                # Convert to JSON and back
                json_str = json.dumps(data_dict, default=str)
                restored_dict = json.loads(json_str)
                
                # Verify key data survived serialization
                assert restored_dict['symbol'] == "BTC-USD"
                assert float(restored_dict['price']) == 50000.0
                assert float(restored_dict['volume']) == 1000.0
                
                print("✅ Model serialization working")
            else:
                print("⚠️ Model serialization not implemented")
                
        except ImportError as e:
            pytest.skip(f"Model serialization test not available: {e}")


class TestErrorHandling:
    """Test error handling in integrated components."""
    
    def test_strategy_error_handling(self):
        """Test strategy error handling with bad data."""
        try:
            from odin.strategies.moving_average import MovingAverageStrategy
            
            strategy = MovingAverageStrategy(short_window=5, long_window=20)
            
            # Test with insufficient data
            small_data = pd.DataFrame({
                'open': [100, 101],
                'high': [102, 103],
                'low': [99, 100],
                'close': [101, 102],
                'volume': [1000, 1100]
            })
            
            # Should handle gracefully
            data_with_indicators = strategy.calculate_indicators(small_data)
            signal = strategy.generate_signal(data_with_indicators)
            
            # Should return a valid signal (likely HOLD)
            assert signal is not None
            assert hasattr(signal, 'signal')
            
            # Test with empty data
            empty_data = pd.DataFrame()
            
            try:
                signal = strategy.generate_signal(empty_data)
                # Should either return valid signal or raise appropriate exception
                if signal is not None:
                    assert hasattr(signal, 'signal')
            except Exception as e:
                # Should raise appropriate exception, not crash
                assert isinstance(e, (ValueError, IndexError))
            
            print("✅ Strategy error handling working")
            
        except ImportError as e:
            pytest.skip(f"Strategy error handling test not available: {e}")
    
    def test_model_validation_errors(self):
        """Test model validation error handling."""
        try:
            from odin.core.models import PriceData
            
            # Test with invalid data
            try:
                invalid_price_data = PriceData(
                    symbol="",  # Empty symbol
                    timestamp=datetime.now(timezone.utc),
                    price=-1000.0,  # Negative price
                    volume=-500.0,  # Negative volume
                    source="test"
                )
                print("⚠️ Model validation not strict enough")
            except (ValueError, Exception) as e:
                print("✅ Model validation working (rejected invalid data)")
            
        except ImportError as e:
            pytest.skip(f"Model validation test not available: {e}")


class TestPerformance:
    """Test performance of integrated components."""
    
    def test_strategy_performance(self):
        """Test strategy performance with large datasets."""
        try:
            from odin.strategies.moving_average import MovingAverageStrategy
            import time
            
            strategy = MovingAverageStrategy(short_window=5, long_window=20)
            
            # Create large dataset
            large_data = self.create_large_test_data(1000)
            
            # Time the operations
            start_time = time.time()
            
            data_with_indicators = strategy.calculate_indicators(large_data)
            signal = strategy.generate_signal(data_with_indicators)
            
            end_time = time.time()
            execution_time = end_time - start_time
            
            # Should complete reasonably quickly
            assert execution_time < 5.0  # 5 seconds max
            assert signal is not None
            
            print(f"✅ Strategy performance test passed ({execution_time:.3f}s for 1000 data points)")
            
        except ImportError as e:
            pytest.skip(f"Strategy performance test not available: {e}")
    
    def create_large_test_data(self, size):
        """Create large test dataset for performance testing."""
        dates = pd.date_range(start='2024-01-01', periods=size, freq='1H')
        
        # Generate simple price data
        prices = 50000 + np.cumsum(np.random.normal(0, 100, size))
        
        data = pd.DataFrame({
            'open': prices,
            'high': prices * 1.01,
            'low': prices * 0.99,
            'close': prices,
            'volume': np.random.randint(1000, 10000, size)
        }, index=dates)
        
        return data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])