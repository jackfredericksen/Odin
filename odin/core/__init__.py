"""
Odin Core Package - Professional Bitcoin Trading Bot Core Business Logic

This package contains the core business logic for the Odin trading system:
- Trading Engine: Live trade execution and order management
- Portfolio Manager: Portfolio tracking, P&L calculation, and allocation
- Risk Manager: Risk controls, position sizing, and drawdown protection
- Data Collector: Real-time Bitcoin data collection and processing
- Database: SQLAlchemy models and database operations
- Models: Pydantic data models for validation and serialization
- Exceptions: Custom exception classes for error handling

Author: Odin Development Team
License: MIT
"""

"""
Odin Core Package - Enhanced systems with fallbacks
"""

# Try to import new systems, fall back gracefully
try:
    from .config_manager import get_config, get_config_manager
except ImportError:
    print("Enhanced config system not available")

    def get_config():
        class MockConfig:
            class trading:
                enable_live_trading = False

            class logging:
                level = "INFO"

        return MockConfig()

    def get_config_manager():
        return None


try:
    from .repository import get_repository_manager
except ImportError:
    print("Repository system not available")

    def get_repository_manager():
        return None


try:
    from .exceptions import ErrorHandler, OdinException
except ImportError:
    print("Error handler not available")

    class ErrorHandler:
        async def handle_exception(self, e, context=None, **kwargs):
            print(f"Error: {e}")

    class OdinException(Exception):
        pass


__all__ = [
    "get_config",
    "get_config_manager",
    "get_repository_manager",
    "ErrorHandler",
    "OdinException",
]
