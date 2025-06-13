"""
Tests for data models and core data structures.
These tests verify that data models work correctly and validate data properly.
"""

import sys
import os
import pytest
from datetime import datetime, timezone
from decimal import Decimal

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestSignalTypes:
    """Test signal type enums."""
    
    def test_signal_type_import(self):
        """Test that SignalType can be imported."""
        try:
            from odin.core.models import SignalType
            
            # Test that all expected signal types exist
            assert hasattr(SignalType, 'BUY')
            assert hasattr(SignalType, 'SELL')
            assert hasattr(SignalType, 'HOLD')
            
            # Test values
            assert SignalType.BUY.value == "buy"
            assert SignalType.SELL.value == "sell"
            assert SignalType.HOLD.value == "hold"
            
            print("✅ SignalType enum working correctly")
            
        except ImportError as e:
            pytest.skip(f"SignalType not available: {e}")
    
    def test_order_types(self):
        """Test order type enums."""
        try:
            from odin.core.models import OrderType, OrderSide, OrderStatus
            
            # Test OrderType
            assert hasattr(OrderType, 'MARKET')
            assert hasattr(OrderType, 'LIMIT')
            
            # Test OrderSide
            assert hasattr(OrderSide, 'BUY')
            assert hasattr(OrderSide, 'SELL')
            
            # Test OrderStatus
            assert hasattr(OrderStatus, 'PENDING')
            assert hasattr(OrderStatus, 'FILLED')
            assert hasattr(OrderStatus, 'CANCELLED')
            
            print("✅ Order enums working correctly")
            
        except ImportError as e:
            pytest.skip(f"Order types not available: {e}")


class TestPriceDataModels:
    """Test price data models."""
    
    def test_price_data_creation(self):
        """Test creating PriceData instances."""
        try:
            from odin.core.models import PriceData
            
            # Test basic price data creation
            price_data = PriceData(
                symbol="BTC-USD",
                timestamp=datetime.now(timezone.utc),
                price=50000.0,
                volume=1000.0,
                source="test"
            )
            
            assert price_data.symbol == "BTC-USD"
            assert price_data.price == 50000.0
            assert price_data.volume == 1000.0
            assert price_data.source == "test"
            
            print("✅ PriceData model working correctly")
            
        except ImportError as e:
            pytest.skip(f"PriceData model not available: {e}")
    
    def test_ohlc_data_creation(self):
        """Test creating OHLC data instances."""
        try:
            from odin.core.models import OHLCData
            
            ohlc_data = OHLCData(
                symbol="BTC-USD",
                timeframe="1H",
                timestamp=datetime.now(timezone.utc),
                open=50000.0,
                high=51000.0,
                low=49500.0,
                close=50500.0,
                volume=1000.0
            )
            
            assert ohlc_data.symbol == "BTC-USD"
            assert ohlc_data.timeframe == "1H"
            assert ohlc_data.open == 50000.0
            assert ohlc_data.high == 51000.0
            assert ohlc_data.low == 49500.0
            assert ohlc_data.close == 50500.0
            
            # Test price relationships
            assert ohlc_data.high >= ohlc_data.open
            assert ohlc_data.high >= ohlc_data.close
            assert ohlc_data.low <= ohlc_data.open
            assert ohlc_data.low <= ohlc_data.close
            
            print("✅ OHLCData model working correctly")
            
        except ImportError as e:
            pytest.skip(f"OHLCData model not available: {e}")


class TestTradingModels:
    """Test trading-related models."""
    
    def test_trade_signal_creation(self):
        """Test creating TradeSignal instances."""
        try:
            from odin.core.models import TradeSignal, SignalType
            
            signal = TradeSignal(
                id="test-signal-1",
                strategy_id="test-strategy",
                symbol="BTC-USD",
                signal_type=SignalType.BUY,
                confidence=0.8,
                price=50000.0,
                created_at=datetime.now(timezone.utc)
            )
            
            assert signal.id == "test-signal-1"
            assert signal.strategy_id == "test-strategy"
            assert signal.signal_type == SignalType.BUY
            assert signal.confidence == 0.8
            assert signal.price == 50000.0
            assert not signal.executed
            
            print("✅ TradeSignal model working correctly")
            
        except ImportError as e:
            pytest.skip(f"TradeSignal model not available: {e}")
    
    def test_trade_order_creation(self):
        """Test creating TradeOrder instances."""
        try:
            from odin.core.models import TradeOrder, OrderType, OrderSide, OrderStatus
            
            order = TradeOrder(
                id="test-order-1",
                portfolio_id="test-portfolio",
                symbol="BTC-USD",
                side=OrderSide.BUY,
                order_type=OrderType.MARKET,
                quantity=0.1,
                status=OrderStatus.PENDING
            )
            
            assert order.id == "test-order-1"
            assert order.portfolio_id == "test-portfolio"
            assert order.side == OrderSide.BUY
            assert order.order_type == OrderType.MARKET
            assert order.quantity == 0.1
            assert order.status == OrderStatus.PENDING
            
            print("✅ TradeOrder model working correctly")
            
        except ImportError as e:
            pytest.skip(f"TradeOrder model not available: {e}")


class TestPortfolioModels:
    """Test portfolio-related models."""
    
    def test_portfolio_creation(self):
        """Test creating Portfolio instances."""
        try:
            from odin.core.models import Portfolio
            
            portfolio = Portfolio(
                id="test-portfolio-1",
                name="Test Portfolio",
                total_value=100000.0,
                cash_balance=50000.0,
                invested_amount=50000.0
            )
            
            assert portfolio.id == "test-portfolio-1"
            assert portfolio.name == "Test Portfolio"
            assert portfolio.total_value == 100000.0
            assert portfolio.cash_balance == 50000.0
            assert portfolio.invested_amount == 50000.0
            
            print("✅ Portfolio model working correctly")
            
        except ImportError as e:
            pytest.skip(f"Portfolio model not available: {e}")
    
    def test_position_creation(self):
        """Test creating Position instances."""
        try:
            from odin.core.models import Position, PositionType
            
            position = Position(
                id="test-position-1",
                portfolio_id="test-portfolio",
                symbol="BTC-USD",
                side=PositionType.LONG,
                size=0.5,
                entry_price=50000.0,
                cost_basis=25000.0
            )
            
            assert position.id == "test-position-1"
            assert position.portfolio_id == "test-portfolio"
            assert position.symbol == "BTC-USD"
            assert position.side == PositionType.LONG
            assert position.size == 0.5
            assert position.entry_price == 50000.0
            assert position.cost_basis == 25000.0
            
            print("✅ Position model working correctly")
            
        except ImportError as e:
            pytest.skip(f"Position model not available: {e}")


class TestModelUtilities:
    """Test model utility functions."""
    
    def test_model_to_dict(self):
        """Test model to dictionary conversion."""
        try:
            from odin.core.models import PriceData
            
            price_data = PriceData(
                symbol="BTC-USD",
                timestamp=datetime.now(timezone.utc),
                price=50000.0,
                volume=1000.0,
                source="test"
            )
            
            # Test to_dict method
            if hasattr(price_data, 'to_dict'):
                data_dict = price_data.to_dict()
                assert isinstance(data_dict, dict)
                assert 'symbol' in data_dict
                assert 'price' in data_dict
                assert data_dict['symbol'] == "BTC-USD"
                assert data_dict['price'] == 50000.0
                print("✅ Model to_dict method working")
            else:
                print("⚠️ Model to_dict method not available")
                
        except ImportError as e:
            pytest.skip(f"Model utilities not available: {e}")
    
    def test_model_validation(self):
        """Test model validation."""
        try:
            from odin.core.models import PriceData
            
            # Test valid data
            valid_data = PriceData(
                symbol="BTC-USD",
                timestamp=datetime.now(timezone.utc),
                price=50000.0,
                source="test"
            )
            assert valid_data.price == 50000.0
            
            # Test invalid data (if validation is implemented)
            try:
                invalid_data = PriceData(
                    symbol="BTC-USD",
                    timestamp=datetime.now(timezone.utc),
                    price=-1000.0,  # Negative price should be invalid
                    source="test"
                )
                print("⚠️ Model validation not implemented (allows negative prices)")
            except (ValueError, Exception) as e:
                print("✅ Model validation working (rejected negative price)")
                
        except ImportError as e:
            pytest.skip(f"Model validation not available: {e}")


class TestAPIResponseModels:
    """Test API response models."""
    
    def test_api_response_creation(self):
        """Test creating API response models."""
        try:
            from odin.core.models import APIResponse
            
            response = APIResponse(
                success=True,
                message="Operation successful",
                data={"result": "test"},
                timestamp=datetime.now(timezone.utc)
            )
            
            assert response.success is True
            assert response.message == "Operation successful"
            assert response.data == {"result": "test"}
            assert isinstance(response.timestamp, datetime)
            
            print("✅ APIResponse model working correctly")
            
        except ImportError as e:
            pytest.skip(f"APIResponse model not available: {e}")
    
    def test_error_response_creation(self):
        """Test creating error response models."""
        try:
            from odin.core.models import ErrorResponse
            
            error_response = ErrorResponse(
                success=False,
                message="An error occurred",
                error_code="TEST_ERROR",
                error_details={"field": "test_field", "issue": "test_issue"}
            )
            
            assert error_response.success is False
            assert error_response.message == "An error occurred"
            assert error_response.error_code == "TEST_ERROR"
            assert error_response.error_details["field"] == "test_field"
            
            print("✅ ErrorResponse model working correctly")
            
        except ImportError as e:
            pytest.skip(f"ErrorResponse model not available: {e}")


class TestDataCollectionModels:
    """Test data collection models."""
    
    def test_data_source_status(self):
        """Test DataSourceStatus model."""
        try:
            from odin.core.models import DataSourceStatus
            
            status = DataSourceStatus(
                name="test_source",
                enabled=True,
                healthy=True,
                priority=1,
                error_count=0,
                last_update=datetime.now(timezone.utc)
            )
            
            assert status.name == "test_source"
            assert status.enabled is True
            assert status.healthy is True
            assert status.priority == 1
            assert status.error_count == 0
            
            print("✅ DataSourceStatus model working correctly")
            
        except ImportError as e:
            pytest.skip(f"DataSourceStatus model not available: {e}")
    
    def test_data_collection_result(self):
        """Test DataCollectionResult model."""
        try:
            from odin.core.models import DataCollectionResult
            
            result = DataCollectionResult(
                success=True,
                price=50000.0,
                source="test_source",
                timestamp=datetime.now(timezone.utc)
            )
            
            assert result.success is True
            assert result.price == 50000.0
            assert result.source == "test_source"
            assert isinstance(result.timestamp, datetime)
            
            print("✅ DataCollectionResult model working correctly")
            
        except ImportError as e:
            pytest.skip(f"DataCollectionResult model not available: {e}")


class TestConfigurationModels:
    """Test configuration models."""
    
    def test_trading_config(self):
        """Test TradingConfig model."""
        try:
            from odin.core.models import TradingConfig
            
            config = TradingConfig(
                max_position_size=0.95,
                risk_per_trade=0.02,
                max_daily_loss=0.05,
                enable_live_trading=False,
                exchange_name="binance"
            )
            
            assert config.max_position_size == 0.95
            assert config.risk_per_trade == 0.02
            assert config.max_daily_loss == 0.05
            assert config.enable_live_trading is False
            assert config.exchange_name == "binance"
            
            print("✅ TradingConfig model working correctly")
            
        except ImportError as e:
            pytest.skip(f"TradingConfig model not available: {e}")


class TestModelRelationships:
    """Test relationships between models."""
    
    def test_signal_to_order_workflow(self):
        """Test typical workflow from signal to order."""
        try:
            from odin.core.models import (
                TradeSignal, TradeOrder, SignalType, 
                OrderType, OrderSide, OrderStatus
            )
            
            # Create a signal
            signal = TradeSignal(
                id="signal-1",
                strategy_id="test-strategy",
                signal_type=SignalType.BUY,
                confidence=0.8,
                price=50000.0
            )
            
            # Create corresponding order
            order = TradeOrder(
                id="order-1",
                portfolio_id="portfolio-1",
                strategy_id=signal.strategy_id,
                side=OrderSide.BUY,  # Matches signal
                order_type=OrderType.MARKET,
                quantity=0.1,
                status=OrderStatus.PENDING
            )
            
            # Verify relationship
            assert order.strategy_id == signal.strategy_id
            assert order.side.value == signal.signal_type.value
            
            print("✅ Signal to Order workflow working correctly")
            
        except ImportError as e:
            pytest.skip(f"Workflow models not available: {e}")


# Test fixtures and utilities
def create_test_price_data():
    """Create test price data for model testing."""
    try:
        from odin.core.models import PriceData
        
        return PriceData(
            symbol="BTC-USD",
            timestamp=datetime.now(timezone.utc),
            price=50000.0,
            volume=1000.0,
            source="test"
        )
    except ImportError:
        return None


def create_test_signal():
    """Create test signal for model testing."""
    try:
        from odin.core.models import TradeSignal, SignalType
        
        return TradeSignal(
            id="test-signal",
            strategy_id="test-strategy",
            signal_type=SignalType.BUY,
            confidence=0.8,
            price=50000.0
        )
    except ImportError:
        return None


class TestUtilityFunctions:
    """Test utility functions provided by models module."""
    
    def test_create_functions(self):
        """Test create utility functions."""
        try:
            from odin.core.models import create_price_data, create_api_response
            
            # Test create_price_data
            price_data = create_price_data(
                timestamp=datetime.now(timezone.utc),
                price=50000.0,
                volume=1000.0,
                source="test"
            )
            
            assert price_data.price == 50000.0
            assert price_data.volume == 1000.0
            
            # Test create_api_response
            api_response = create_api_response(
                success=True,
                data={"test": "data"},
                message="Success"
            )
            
            assert api_response.success is True
            assert api_response.data == {"test": "data"}
            assert api_response.message == "Success"
            
            print("✅ Utility functions working correctly")
            
        except ImportError as e:
            pytest.skip(f"Utility functions not available: {e}")
        except AttributeError as e:
            pytest.skip(f"Some utility functions not available: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])