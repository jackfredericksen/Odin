"""
Strategy Selection Module for Odin Trading Bot

This module provides adaptive strategy selection and management:
- Regime-based strategy mapping
- Dynamic weight optimization
- Performance-based strategy selection
- Risk-adjusted position sizing
"""

from .adaptive_manager import AdaptiveStrategyManager, RegimeType, StrategyConfig

__all__ = [
    "AdaptiveStrategyManager",
    "RegimeType", 
    "StrategyConfig"
]