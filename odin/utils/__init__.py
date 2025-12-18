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

# Import validators if they exist
try:
    from odin.utils.validators import *
except ImportError:
    # Validators don't exist yet, that's okay
    pass

__all__ = [
    "get_logger",
    "configure_logging",
    "setup_logging",  # Backward compatibility
    "LogContext",
    "set_correlation_id",
    "get_correlation_id",
]
