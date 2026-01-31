"""
Odin Utils Package - Updated for new logging system
"""

# Import new logging system with backward compatibility
from odin.utils.logging import (
    LogContext,
    configure_logging,
    get_correlation_id,
    get_logger,
    set_correlation_id,
)

# Backward compatibility alias
setup_logging = configure_logging

# HTTP client utilities
from odin.utils.http_client import (
    HTTPClientManager,
    cleanup_http_client,
    fetch_json,
)

# Import validators if they exist
try:
    from odin.utils.validators import validate_price, validate_symbol
except ImportError:
    # Validators don't exist yet, provide stubs
    def validate_price(price: float) -> bool:
        return price > 0

    def validate_symbol(symbol: str) -> bool:
        return bool(symbol and len(symbol) <= 20)

__all__ = [
    "get_logger",
    "configure_logging",
    "setup_logging",  # Backward compatibility
    "LogContext",
    "set_correlation_id",
    "get_correlation_id",
    "HTTPClientManager",
    "fetch_json",
    "cleanup_http_client",
    "validate_price",
    "validate_symbol",
]
