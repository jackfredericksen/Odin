"""
Odin AI Module - Market Regime Detection & Adaptive Strategies
"""

from .regime_detection.regime_detector import MarketRegimeDetector
from .strategy_selection.adaptive_manager import AdaptiveStrategyManager

__version__ = "1.0.0"
__author__ = "Odin Trading Bot"
__description__ = "AI-powered market regime detection and adaptive strategy selection"

__all__ = ["MarketRegimeDetector", "AdaptiveStrategyManager"]
