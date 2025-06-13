"""
Merged Pytest configuration combining existing async fixtures with new basic fixtures.
"""

import sys
import os
import pytest
import asyncio
import tempfile
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timezone, timedelta

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ============================================================================
# EXISTING FIXTURES (for integration/async tests)
# ============================================================================

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def test_settings():
    """Test settings with temporary database."""
    try:
        from odin.config import Settings
        
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test.db"
            
            yield Settings(
                database_url=f"sqlite:///{db_path}",
                data_update_interval=1,
                log_level="DEBUG",
                api_port=5001,  # Different port for testing
            )
    except ImportError:
        # Fallback if Settings not available
        yield None

@pytest.fixture
async def test_database(test_settings):
    """Test database instance."""
    if test_settings is None:
        pytest.skip("Settings not available")
    
    try:
        from odin.core.database import Database
        import odin.config
        
        # Mock the settings
        original_settings = getattr(odin.config, 'settings', None)
        odin.config.settings = test_settings
        
        try:
            db = Database()
            await db.init()
            yield db
        finally:
            # Restore original settings
            if original_settings:
                odin.config.settings = original_settings
    except ImportError:
        pytest.skip("Database not available")

@pytest.fixture
async def test_data_collector(test_database):
    """Test data collector instance."""
    try:
        from odin.core.data_collector import DataCollector
        
        collector = DataCollector()
        await collector.startup()
        yield collector
        await collector.shutdown()
    except ImportError:
        pytest.skip("DataCollector not available")

@pytest.fixture
def sample_price_data_legacy():
    """Sample price data for testing (legacy format)."""
    try:
        from odin.core.models import PriceData
        
        return PriceData(
            timestamp=datetime.utcnow(),
            price=50000.0,
            volume=1000000000.0,
            high=51000.0,
            low=49000.0,
            change_24h=2.5,
            source="test"
        )
    except ImportError:
        pytest.skip("PriceData model not available")

# ============================================================================
# NEW FIXTURES (for basic/unit tests)
# ============================================================================

@pytest.fixture
def sample_price_data():
    """Fixture providing sample price data for testing."""
    dates = pd.date_range(start='2024-01-01', periods=100, freq='1H')
    
    # Generate realistic price movement
    base_price = 50000
    prices = [base_price]
    
    for i in range(1, 100):
        change = np.random.normal(0, 0.01)  # 1% hourly volatility
        new_price = prices[-1] * (1 + change)
        prices.append(max(new_price, 1000))  # Minimum $1000
    
    # Create OHLCV DataFrame
    data = []
    for i, (date, close) in enumerate(zip(dates, prices)):
        open_price = prices[i-1] if i > 0 else close
        high = max(open_price, close) * (1 + abs(np.random.normal(0, 0.005)))
        low = min(open_price, close) * (1 - abs(np.random.normal(0, 0.005)))
        volume = np.random.randint(1000, 5000)
        
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

@pytest.fixture
def sample_ohlc_data():
    """Fixture providing simple OHLC data."""
    return pd.DataFrame({
        'open': [100, 101, 102, 103, 104],
        'high': [102, 103, 104, 105, 106],
        'low': [99, 100, 101, 102, 103],
        'close': [101, 102, 103, 104, 105],
        'volume': [1000, 1100, 1200, 1300, 1400]
    }, index=pd.date_range('2024-01-01', periods=5, freq='1H'))

@pytest.fixture
def mock_strategy():
    """Fixture providing mock strategy for testing."""
    class MockStrategy:
        def __init__(self, name="MockStrategy"):
            self.name = name
            self.parameters = {}
            self.signals_history = []
            self.last_signal = None
        
        def calculate_indicators(self, data):
            data = data.copy()
            data['mock_indicator'] = data['close'].rolling(window=5).mean()
            return data
        
        def generate_signal(self, data):
            from unittest.mock import MagicMock
            
            signal = MagicMock()
            signal.signal = "HOLD"
            signal.confidence = 0.5
            signal.price = data['close'].iloc[-1] if not data.empty else 50000
            signal.timestamp = datetime.now(timezone.utc)
            signal.reasoning = "Mock signal"
            signal.indicators = {}
            signal.risk_score = 0.3
            
            return signal
    
    return MockStrategy()

@pytest.fixture
def test_environment():
    """Fixture setting up test environment variables."""
    original_env = os.environ.copy()
    
    # Set test environment variables
    os.environ['ENVIRONMENT'] = 'test'
    os.environ['LOG_LEVEL'] = 'DEBUG'
    
    yield os.environ
    
    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)

# ============================================================================
# PYTEST CONFIGURATION
# ============================================================================

def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )
    config.addinivalue_line(
        "markers", "async_test: marks tests that require async functionality"
    )
    config.addinivalue_line(
        "markers", "requires_network: marks tests that require network access"
    )

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def create_test_dataframe(length=100, start_price=50000, volatility=0.02):
    """Create test DataFrame with realistic price data."""
    dates = pd.date_range(start='2024-01-01', periods=length, freq='1H')
    
    prices = [start_price]
    for i in range(1, length):
        change = np.random.normal(0, volatility)
        new_price = prices[-1] * (1 + change)
        prices.append(max(new_price, 1000))
    
    return pd.DataFrame({
        'open': prices,
        'high': [p * (1 + abs(np.random.normal(0, 0.005))) for p in prices],
        'low': [p * (1 - abs(np.random.normal(0, 0.005))) for p in prices],
        'close': prices,
        'volume': np.random.randint(1000, 10000, length)
    }, index=dates)

def assert_valid_signal(signal):
    """Assert that a signal object is valid."""
    assert signal is not None
    assert hasattr(signal, 'signal') or hasattr(signal, 'signal_type')
    assert hasattr(signal, 'confidence')
    assert hasattr(signal, 'price')
    
    if hasattr(signal, 'confidence'):
        assert 0 <= signal.confidence <= 1
    
    if hasattr(signal, 'price'):
        assert signal.price > 0

# ============================================================================
# SKIP CONDITIONS
# ============================================================================

skip_if_no_models = pytest.mark.skipif(
    not _can_import('odin.core.models'),
    reason="Core models not available"
)

skip_if_no_strategies = pytest.mark.skipif(
    not _can_import('odin.strategies'),
    reason="Strategies module not available"
)

skip_if_no_async_components = pytest.mark.skipif(
    not _can_import('odin.core.database'),
    reason="Async components not available"
)

def _can_import(module_name):
    """Check if a module can be imported."""
    try:
        __import__(module_name)
        return True
    except ImportError:
        return False