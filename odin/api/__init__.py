"""
FastAPI web layer for Odin Bitcoin Trading Bot
"""

__version__ = "1.0.0"

from .app import create_app
from .dependencies import get_database, get_current_user
from .middleware import setup_middleware

__all__ = [
    "create_app",
    "get_database", 
    "get_current_user",
    "setup_middleware"
]