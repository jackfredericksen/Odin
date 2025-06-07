"""
API Routes Package

This package contains all the FastAPI route handlers for the Odin trading bot.
"""

# Import all routers with error handling
try:
    from .data import router as data_router
except ImportError as e:
    print(f"Could not import data router: {e}")
    data_router = None

try:
    from .strategies import router as strategies_router
except ImportError as e:
    print(f"Could not import strategies router: {e}")
    strategies_router = None

try:
    from .trading import router as trading_router
except ImportError as e:
    print(f"Could not import trading router: {e}")
    trading_router = None

try:
    from .portfolio import router as portfolio_router
except ImportError as e:
    print(f"Could not import portfolio router: {e}")
    portfolio_router = None

try:
    from .websockets import router as websocket_router
except ImportError as e:
    print(f"Could not import websocket router: {e}")
    websocket_router = None

__all__ = [
    "data_router",
    "strategies_router", 
    "trading_router",
    "portfolio_router",
    "websocket_router"
]