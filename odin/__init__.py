"""
Odin Trading Bot - Advanced cryptocurrency trading bot with real-time data collection.

A professional-grade trading bot featuring:
- Multiple trading strategies (MA, RSI, Bollinger Bands, MACD)
- Real-time data collection with multi-source fallback
- RESTful API with FastAPI
- Professional web dashboard
- Comprehensive backtesting and performance analysis
"""

__version__ = "2.0.0"
__author__ = "Jack Fredericksen"
__email__ = "your.email@example.com"
__description__ = "Advanced cryptocurrency trading bot with real-time data collection"

from odin.config import settings

__all__ = ["settings", "__version__", "__author__", "__email__", "__description__"]