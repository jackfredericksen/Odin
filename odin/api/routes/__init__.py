"""
API Routes Package

This package contains all the FastAPI route handlers for the Odin trading bot.
"""

# Import all routers for easy access
from .data import router as data_router
from .strategies import router as strategies_router
from .trading import router as trading_router
from .portfolio import router as portfolio_router

__all__ = [
    "data_router",
    "strategies_router", 
    "trading_router",
    "portfolio_router"
]