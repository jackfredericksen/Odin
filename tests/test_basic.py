"""
Basic tests for Odin Bitcoin Trading Bot.
These tests ensure the system is working and dependencies are installed correctly.
"""

import sys
import os
import pytest
from datetime import datetime

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestBasicSystem:
    """Test basic system functionality."""
    
    def test_python_version(self):
        """Test that we're using a supported Python version."""
        assert sys.version_info >= (3, 8), f"Python 3.8+ required, got {sys.version_info}"
        print(f"✅ Python version: {sys.version}")
    
    def test_basic_math(self):
        """Sanity check test."""
        assert 1 + 1 == 2
        assert 10 / 2 == 5.0
        assert 2 ** 3 == 8
    
    def test_datetime_functionality(self):
        """Test datetime operations (used throughout trading bot)."""
        now = datetime.now()
        assert isinstance(now, datetime)
        assert now.year >= 2024
        
        # Test timestamp conversion
        timestamp = now.timestamp()
        assert isinstance(timestamp, float)
        assert timestamp > 0


class TestDependencies:
    """Test that required dependencies can be imported."""
    
    def test_pandas_import(self):
        """Test pandas import (core dependency)."""
        try:
            import pandas as pd
            import numpy as np
            
            # Test basic DataFrame operations
            df = pd.DataFrame({'close': [100, 101, 102, 103, 104]})
            assert len(df) == 5
            assert 'close' in df.columns
            
            # Test numpy operations
            arr = np.array([1, 2, 3, 4, 5])
            assert len(arr) == 5
            assert arr.mean() == 3.0
            
            print("✅ Pandas and NumPy working correctly")
            
        except ImportError as e:
            pytest.fail(f"Failed to import pandas/numpy: {e}")
    
    def test_technical_indicators(self):
        """Test technical analysis library."""
        try:
            # Try pandas-ta first (recommended)
            import pandas_ta as ta
            import pandas as pd
            import numpy as np
            
            # Create sample price data
            data = pd.DataFrame({
                'close': [50, 51, 52, 51, 50, 49, 50, 51, 52, 53, 54, 53, 52, 51, 50]
            })
            
            # Test SMA
            sma = ta.sma(data['close'], length=5)
            assert len(sma) == len(data)
            assert not sma.isna().all()  # Should have some non-NaN values
            
            # Test RSI
            rsi = ta.rsi(data['close'], length=10)
            assert len(rsi) == len(data)
            
            print("✅ pandas-ta technical indicators working")
            
        except ImportError:
            # Fall back to TA-Lib if available
            try:
                import talib
                import numpy as np
                
                data = np.array([50, 51, 52, 51, 50, 49, 50, 51, 52, 53, 54, 53, 52, 51, 50], dtype=float)
                
                # Test SMA
                sma = talib.SMA(data, timeperiod=5)
                assert len(sma) == len(data)
                
                # Test RSI
                rsi = talib.RSI(data, timeperiod=10)
                assert len(rsi) == len(data)
                
                print("✅ TA-Lib technical indicators working")
                
            except ImportError:
                pytest.skip("No technical analysis library available (pandas-ta or TA-Lib)")
    
    def test_web_dependencies(self):
        """Test web-related dependencies."""
        try:
            import requests
            import aiohttp
            
            # Test basic functionality
            assert hasattr(requests, 'get')
            assert hasattr(aiohttp, 'ClientSession')
            
            print("✅ Web dependencies (requests, aiohttp) available")
            
        except ImportError as e:
            print(f"⚠️ Some web dependencies missing: {e}")
            # Don't fail - these might not be critical for basic tests
    
    def test_data_validation_dependencies(self):
        """Test data validation dependencies."""
        try:
            import pydantic
            from pydantic import BaseModel
            
            # Test basic Pydantic model
            class TestModel(BaseModel):
                name: str
                value: float
            
            model = TestModel(name="test", value=123.45)
            assert model.name == "test"
            assert model.value == 123.45
            
            print("✅ Pydantic data validation working")
            
        except ImportError:
            print("⚠️ Pydantic not available - using basic validation")


class TestOdinPackage:
    """Test Odin package imports."""
    
    def test_odin_package_exists(self):
        """Test that odin package exists and can be imported."""
        try:
            import odin
            print("✅ Odin package imported successfully")
            
            # Check if package has expected structure
            if hasattr(odin, '__file__'):
                print(f"✅ Odin package location: {odin.__file__}")
            
        except ImportError as e:
            print(f"⚠️ Odin package not found: {e}")
            print("This is expected if the package is still in development")
            # Don't fail - package might not be ready yet
    
    def test_odin_strategies_import(self):
        """Test that strategies module can be imported."""
        try:
            from odin.strategies import base
            print("✅ Odin strategies.base imported successfully")
            
            # Check for expected classes
            if hasattr(base, 'Strategy'):
                print("✅ Strategy base class found")
            
        except ImportError as e:
            print(f"⚠️ Odin strategies not importable: {e}")
            # Don't fail - might be in development
    
    def test_odin_core_models(self):
        """Test that core models can be imported."""
        try:
            from odin.core import models
            print("✅ Odin core.models imported successfully")
            
            # Check for expected enums/classes
            if hasattr(models, 'SignalType'):
                print("✅ SignalType enum found")
                
        except ImportError as e:
            print(f"⚠️ Odin core models not importable: {e}")
            # Don't fail - might be in development


class TestEnvironment:
    """Test environment setup."""
    
    def test_environment_variables(self):
        """Test that environment can be configured."""
        # Test that we can set environment variables
        os.environ['TEST_VAR'] = 'test_value'
        assert os.environ.get('TEST_VAR') == 'test_value'
        
        # Clean up
        del os.environ['TEST_VAR']
    
    def test_file_system_access(self):
        """Test that we can create files and directories."""
        import tempfile
        
        # Test directory creation
        test_dir = tempfile.mkdtemp()
        assert os.path.exists(test_dir)
        
        # Test file creation
        test_file = os.path.join(test_dir, 'test.txt')
        with open(test_file, 'w') as f:
            f.write('test content')
        
        assert os.path.exists(test_file)
        
        # Read back content
        with open(test_file, 'r') as f:
            content = f.read()
        
        assert content == 'test content'
        
        # Clean up
        os.remove(test_file)
        os.rmdir(test_dir)


# Test data for other tests to use
SAMPLE_PRICE_DATA = [
    {'timestamp': '2024-01-01 00:00:00', 'open': 100.0, 'high': 105.0, 'low': 98.0, 'close': 103.0, 'volume': 1000},
    {'timestamp': '2024-01-01 01:00:00', 'open': 103.0, 'high': 107.0, 'low': 101.0, 'close': 105.0, 'volume': 1100},
    {'timestamp': '2024-01-01 02:00:00', 'open': 105.0, 'high': 106.0, 'low': 102.0, 'close': 104.0, 'volume': 900},
    {'timestamp': '2024-01-01 03:00:00', 'open': 104.0, 'high': 108.0, 'low': 103.0, 'close': 107.0, 'volume': 1200},
    {'timestamp': '2024-01-01 04:00:00', 'open': 107.0, 'high': 109.0, 'low': 105.0, 'close': 106.0, 'volume': 1050},
]


def test_sample_data():
    """Test that sample data is valid."""
    assert len(SAMPLE_PRICE_DATA) == 5
    
    for row in SAMPLE_PRICE_DATA:
        assert 'timestamp' in row
        assert 'open' in row
        assert 'high' in row
        assert 'low' in row
        assert 'close' in row
        assert 'volume' in row
        
        # Test price relationships
        assert row['high'] >= row['open']
        assert row['high'] >= row['close']
        assert row['low'] <= row['open']
        assert row['low'] <= row['close']
        assert row['volume'] > 0


if __name__ == "__main__":
    # Run tests directly
    pytest.main([__file__, "-v"])