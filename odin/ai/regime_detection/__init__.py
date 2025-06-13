"""
Regime Detection Module for Odin Trading Bot

This module provides advanced market regime detection capabilities using:
- Hidden Markov Models (HMM)
- Gaussian Mixture Models (GMM)
- Feature engineering from market data
- Real-time regime classification
"""

from .regime_detector import MarketRegimeDetector

__all__ = ["MarketRegimeDetector"]
