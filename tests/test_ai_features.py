import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from odin.ai.regime_detection.regime_detector import MarketRegimeDetector
from odin.ai.strategy_selection.adaptive_manager import AdaptiveStrategyManager
from odin.strategies.ai_adaptive import AIAdaptiveStrategy

@pytest.fixture
def sample_market_data():
    '''Create sample market data for testing'''
    dates = pd.date_range(start='2024-01-01', end='2024-06-01', freq='D')
    data = pd.DataFrame({
        'close': np.random.randn(len(dates)).cumsum() + 50000,
        'high': np.random.randn(len(dates)).cumsum() + 51000,
        'low': np.random.randn(len(dates)).cumsum() + 49000,
        'volume': np.random.randint(1000, 10000, len(dates)),
        'rsi_14': np.random.uniform(20, 80, len(dates)),
        'ma_20': np.random.randn(len(dates)).cumsum() + 49500,
        'ma_50': np.random.randn(len(dates)).cumsum() + 49000,
    }, index=dates)
    return data

def test_regime_detector_initialization():
    '''Test regime detector can be initialized'''
    detector = MarketRegimeDetector()
    assert detector is not None
    assert detector.regime_map is not None

def test_feature_preparation(sample_market_data):
    '''Test feature preparation for regime detection'''
    detector = MarketRegimeDetector()
    features = detector.prepare_features(sample_market_data)
    
    assert not features.empty
    assert len(features) > 0
    assert 'returns_1d' in features.columns

def test_adaptive_strategy_manager():
    '''Test adaptive strategy manager initialization'''
    manager = AdaptiveStrategyManager()
    assert manager is not None
    assert manager.regime_strategy_map is not None

def test_ai_adaptive_strategy(sample_market_data):
    '''Test AI adaptive strategy signal generation'''
    strategy = AIAdaptiveStrategy()
    
    # Generate signal (may return HOLD if models not trained)
    signal = strategy.generate_signal(sample_market_data)
    
    assert signal is not None
    assert hasattr(signal, 'signal_type')
    assert hasattr(signal, 'confidence')

def test_ai_analytics():
    '''Test AI analytics generation'''
    strategy = AIAdaptiveStrategy()
    analytics = strategy.get_ai_analytics()
    
    assert isinstance(analytics, dict)
    assert 'system_status' in analytics