"""
API routes package - organized and modular
"""

from . import data, health
from .strategies import router as strategies_router
from .trading import router as trading_router
from .portfolio import router as portfolio_router
from .market import router as market_router

__all__ = [
    "data",
    "health", 
    "strategies_router",
    "trading_router",
    "portfolio_router",
    "market_router"
]