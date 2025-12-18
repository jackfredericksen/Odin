"""
Odin Structured Logging System - Centralized Logging with Correlation IDs
Provides structured logging with correlation tracking across all operations.
"""

import contextvars
import json
import logging
import logging.handlers
import uuid
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Optional, Union

# Context variable for correlation ID tracking
correlation_id: contextvars.ContextVar[str] = contextvars.ContextVar(
    "correlation_id", default=""
)


class LogLevel(str, Enum):
    """Logging levels."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


@dataclass
class LogContext:
    """Logging context for structured data."""

    component: str
    operation: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    strategy_id: Optional[str] = None
    order_id: Optional[str] = None
    additional_data: Dict[str, Any] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging."""
        result = {"component": self.component, "operation": self.operation}

        if self.user_id:
            result["user_id"] = self.user_id
        if self.session_id:
            result["session_id"] = self.session_id
        if self.strategy_id:
            result["strategy_id"] = self.strategy_id
        if self.order_id:
            result["order_id"] = self.order_id
        if self.additional_data:
            result.update(self.additional_data)

        return result


class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured JSON logging."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as structured JSON."""
        # Base log data
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "correlation_id": correlation_id.get(""),
        }

        # Add file information for debugging
        if record.pathname:
            log_data["file"] = {
                "name": record.filename,
                "line": record.lineno,
                "function": record.funcName,
            }

        # Add exception information if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add structured context if present
        if hasattr(record, "context") and record.context:
            if isinstance(record.context, LogContext):
                log_data["context"] = record.context.to_dict()
            elif isinstance(record.context, dict):
                log_data["context"] = record.context

        # Add extra fields
        extra_fields = {}
        for key, value in record.__dict__.items():
            if key not in [
                "name",
                "msg",
                "args",
                "levelname",
                "levelno",
                "pathname",
                "filename",
                "module",
                "lineno",
                "funcName",
                "created",
                "msecs",
                "relativeCreated",
                "thread",
                "threadName",
                "processName",
                "process",
                "getMessage",
                "exc_info",
                "exc_text",
                "stack_info",
                "context",
            ]:
                extra_fields[key] = value

        if extra_fields:
            log_data["extra"] = extra_fields

        return json.dumps(log_data, default=str, ensure_ascii=False)


class OdinLogger:
    """Enhanced logger with structured logging capabilities."""

    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self.name = name

    def with_context(self, context: Union[LogContext, Dict[str, Any]]) -> "OdinLogger":
        """Create logger with context."""
        new_logger = OdinLogger(self.name)
        new_logger.logger = self.logger
        new_logger._context = context
        return new_logger

    def debug(
        self,
        message: str,
        context: Optional[Union[LogContext, Dict[str, Any]]] = None,
        **kwargs,
    ):
        """Log debug message."""
        self._log(LogLevel.DEBUG, message, context, **kwargs)

    def info(
        self,
        message: str,
        context: Optional[Union[LogContext, Dict[str, Any]]] = None,
        **kwargs,
    ):
        """Log info message."""
        self._log(LogLevel.INFO, message, context, **kwargs)

    def warning(
        self,
        message: str,
        context: Optional[Union[LogContext, Dict[str, Any]]] = None,
        **kwargs,
    ):
        """Log warning message."""
        self._log(LogLevel.WARNING, message, context, **kwargs)

    def error(
        self,
        message: str,
        context: Optional[Union[LogContext, Dict[str, Any]]] = None,
        **kwargs,
    ):
        """Log error message."""
        self._log(LogLevel.ERROR, message, context, **kwargs)

    def critical(
        self,
        message: str,
        context: Optional[Union[LogContext, Dict[str, Any]]] = None,
        **kwargs,
    ):
        """Log critical message."""
        self._log(LogLevel.CRITICAL, message, context, **kwargs)

    def exception(
        self,
        message: str,
        context: Optional[Union[LogContext, Dict[str, Any]]] = None,
        **kwargs,
    ):
        """Log exception with traceback."""
        kwargs["exc_info"] = True
        self._log(LogLevel.ERROR, message, context, **kwargs)

    def _log(
        self,
        level: LogLevel,
        message: str,
        context: Optional[Union[LogContext, Dict[str, Any]]],
        **kwargs,
    ):
        """Internal logging method."""
        # Use provided context or instance context
        log_context = context or getattr(self, "_context", None)

        # Create log record with context
        extra = kwargs.copy()
        if log_context:
            extra["context"] = log_context

        # Map level to logging constant
        level_map = {
            LogLevel.DEBUG: logging.DEBUG,
            LogLevel.INFO: logging.INFO,
            LogLevel.WARNING: logging.WARNING,
            LogLevel.ERROR: logging.ERROR,
            LogLevel.CRITICAL: logging.CRITICAL,
        }

        self.logger.log(level_map[level], message, extra=extra)


class LoggingManager:
    """Centralized logging configuration and management."""

    def __init__(self):
        self.loggers: Dict[str, OdinLogger] = {}
        self.configured = False

    def configure_logging(
        self,
        level: LogLevel = LogLevel.INFO,
        enable_console: bool = True,
        enable_file: bool = True,
        file_path: Optional[str] = None,
        max_file_size: int = 10485760,  # 10MB
        backup_count: int = 5,
        structured_format: bool = True,
    ):
        """Configure logging system."""
        if self.configured:
            return

        # Clear existing handlers
        root_logger = logging.getLogger()
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)

        # Set root level
        level_map = {
            LogLevel.DEBUG: logging.DEBUG,
            LogLevel.INFO: logging.INFO,
            LogLevel.WARNING: logging.WARNING,
            LogLevel.ERROR: logging.ERROR,
            LogLevel.CRITICAL: logging.CRITICAL,
        }
        root_logger.setLevel(level_map[level])

        # Create formatters
        if structured_format:
            formatter = StructuredFormatter()
        else:
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )

        # Console handler
        if enable_console:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            root_logger.addHandler(console_handler)

        # File handler
        if enable_file and file_path:
            # Ensure log directory exists
            log_file = Path(file_path)
            log_file.parent.mkdir(parents=True, exist_ok=True)

            file_handler = logging.handlers.RotatingFileHandler(
                filename=file_path, maxBytes=max_file_size, backupCount=backup_count
            )
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)

        self.configured = True

    def get_logger(self, name: str) -> OdinLogger:
        """Get or create logger instance."""
        if name not in self.loggers:
            self.loggers[name] = OdinLogger(name)
        return self.loggers[name]

    def set_correlation_id(self, corr_id: Optional[str] = None) -> str:
        """Set correlation ID for request tracking."""
        if corr_id is None:
            corr_id = str(uuid.uuid4())

        correlation_id.set(corr_id)
        return corr_id

    def get_correlation_id(self) -> str:
        """Get current correlation ID."""
        return correlation_id.get("")

    def clear_correlation_id(self):
        """Clear correlation ID."""
        correlation_id.set("")


# Global logging manager instance
_logging_manager: Optional[LoggingManager] = None


def get_logging_manager() -> LoggingManager:
    """Get global logging manager instance."""
    global _logging_manager
    if _logging_manager is None:
        _logging_manager = LoggingManager()
    return _logging_manager


def get_logger(name: str) -> OdinLogger:
    """Get logger instance."""
    return get_logging_manager().get_logger(name)


def configure_logging(**kwargs):
    """Configure global logging."""
    get_logging_manager().configure_logging(**kwargs)


def set_correlation_id(corr_id: Optional[str] = None) -> str:
    """Set correlation ID for request tracking."""
    return get_logging_manager().set_correlation_id(corr_id)


def get_correlation_id() -> str:
    """Get current correlation ID."""
    return get_logging_manager().get_correlation_id()


def with_correlation_id(corr_id: Optional[str] = None):
    """Decorator to set correlation ID for function execution."""

    def decorator(func):
        async def async_wrapper(*args, **kwargs):
            old_id = get_correlation_id()
            new_id = set_correlation_id(corr_id)
            try:
                return await func(*args, **kwargs)
            finally:
                correlation_id.set(old_id)

        def sync_wrapper(*args, **kwargs):
            old_id = get_correlation_id()
            new_id = set_correlation_id(corr_id)
            try:
                return func(*args, **kwargs)
            finally:
                correlation_id.set(old_id)

        import asyncio

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


# Convenience functions for common logging patterns
def log_operation_start(logger: OdinLogger, operation: str, **context_data):
    """Log operation start."""
    context = LogContext(
        component=logger.name, operation=operation, additional_data=context_data
    )
    logger.info(f"Starting {operation}", context)


def log_operation_success(
    logger: OdinLogger, operation: str, duration: float = None, **context_data
):
    """Log operation success."""
    additional_data = context_data.copy()
    if duration is not None:
        additional_data["duration_ms"] = duration * 1000

    context = LogContext(
        component=logger.name, operation=operation, additional_data=additional_data
    )
    logger.info(f"Completed {operation}", context)


def log_operation_error(
    logger: OdinLogger, operation: str, error: Exception, **context_data
):
    """Log operation error."""
    additional_data = context_data.copy()
    additional_data["error_type"] = type(error).__name__
    additional_data["error_message"] = str(error)

    context = LogContext(
        component=logger.name, operation=operation, additional_data=additional_data
    )
    logger.exception(f"Failed {operation}", context)


# Example usage patterns
def demo_logging():
    """Demonstrate logging capabilities."""
    # Configure logging
    configure_logging(
        level=LogLevel.INFO,
        enable_file=True,
        file_path="data/logs/odin.log",
        structured_format=True,
    )

    # Get logger
    logger = get_logger("demo")

    # Set correlation ID
    corr_id = set_correlation_id()

    # Basic logging
    logger.info("Application started")

    # Structured logging with context
    context = LogContext(
        component="trading_engine",
        operation="place_order",
        order_id="order_123",
        additional_data={"symbol": "BTC-USD", "quantity": 0.001},
    )
    logger.info("Placing order", context)

    # Logger with persistent context
    trading_logger = logger.with_context(
        LogContext(component="trading_engine", operation="trading_session")
    )
    trading_logger.info("Session started")
    trading_logger.error("Order failed")

    # Operation logging helpers
    log_operation_start(logger, "data_collection", source="coinbase")
    log_operation_success(
        logger, "data_collection", duration=1.5, records_collected=100
    )


if __name__ == "__main__":
    demo_logging()
