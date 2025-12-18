"""
Odin Core Exceptions - Custom Exception Classes for Error Handling

Comprehensive exception hierarchy for the Odin trading system providing
specific error types for different components and failure scenarios.

Author: Odin Development Team
License: MIT
"""

import logging
from enum import Enum
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


# Error Severity Levels
class ErrorSeverity(Enum):
    """Enumeration of error severity levels."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


# Error Codes
class ErrorCode:
    """Standard error codes for the Odin system."""

    # System Errors
    SYSTEM_ERROR = "SYSTEM_ERROR"
    SYSTEM_STARTUP_FAILED = "SYSTEM_STARTUP_FAILED"
    SYSTEM_CONFIG_INVALID = "SYSTEM_CONFIG_INVALID"
    UNEXPECTED_ERROR = "UNEXPECTED_ERROR"
    CONFIGURATION_ERROR = "CONFIGURATION_ERROR"

    # Trading Errors
    INVALID_ORDER = "INVALID_ORDER"
    ORDER_EXECUTION_FAILED = "ORDER_EXECUTION_FAILED"
    INSUFFICIENT_FUNDS = "INSUFFICIENT_FUNDS"

    # Connection Errors
    EXCHANGE_CONNECTION_FAILED = "EXCHANGE_CONNECTION_FAILED"
    DATABASE_CONNECTION_FAILED = "DATABASE_CONNECTION_FAILED"
    DATABASE_MIGRATION_FAILED = "DATABASE_MIGRATION_FAILED"
    DATABASE_OPERATION_FAILED = "DATABASE_OPERATION_FAILED"
    DATA_INTEGRITY_VIOLATION = "DATA_INTEGRITY_VIOLATION"
    DATA_SOURCE_FAILED = "DATA_SOURCE_FAILED"

    # Risk Management
    RISK_LIMIT_EXCEEDED = "RISK_LIMIT_EXCEEDED"
    DRAWDOWN_LIMIT_EXCEEDED = "DRAWDOWN_LIMIT_EXCEEDED"
    POSITION_SIZE_EXCEEDED = "POSITION_SIZE_EXCEEDED"

    # Data Errors
    MARKET_DATA_ERROR = "MARKET_DATA_ERROR"
    DATA_VALIDATION_FAILED = "DATA_VALIDATION_FAILED"

    # Strategy Errors
    STRATEGY_CONFIG_INVALID = "STRATEGY_CONFIG_INVALID"
    STRATEGY_EXECUTION_FAILED = "STRATEGY_EXECUTION_FAILED"

    # Portfolio Errors
    PORTFOLIO_VALIDATION_FAILED = "PORTFOLIO_VALIDATION_FAILED"
    ALLOCATION_FAILED = "ALLOCATION_FAILED"


# Error Handler
class ErrorHandler:
    """
    Centralized error handling and logging utility.

    Provides structured error handling with context management,
    logging, and error tracking capabilities.
    """

    def __init__(self):
        self.error_count = 0
        self.errors = []

    def handle_error(
        self,
        error: Exception,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        context: Optional[Dict[str, Any]] = None,
        reraise: bool = True,
    ):
        """
        Handle an error with logging and optional re-raising.

        Args:
            error: The exception to handle
            severity: Severity level of the error
            context: Additional context information
            reraise: Whether to re-raise the exception after handling
        """
        self.error_count += 1

        error_data = {
            "error_type": type(error).__name__,
            "error_message": str(error),
            "severity": severity.value,
            "context": context or {},
            "count": self.error_count,
        }

        self.errors.append(error_data)

        # Log based on severity
        if severity == ErrorSeverity.CRITICAL:
            logger.critical(f"Critical error: {error}", extra=error_data)
        elif severity == ErrorSeverity.ERROR:
            logger.error(f"Error: {error}", extra=error_data)
        elif severity == ErrorSeverity.WARNING:
            logger.warning(f"Warning: {error}", extra=error_data)
        else:
            logger.info(f"Info: {error}", extra=error_data)

        if reraise:
            raise error

    def get_error_stats(self) -> Dict[str, Any]:
        """Get error statistics."""
        return {
            "total_errors": self.error_count,
            "recent_errors": self.errors[-10:] if self.errors else [],
        }

    def clear_errors(self):
        """Clear error history."""
        self.error_count = 0
        self.errors = []

    async def handle_exception(
        self,
        exception: Exception,
        context: Optional[Dict[str, Any]] = None,
        reraise: bool = False,
    ):
        """
        Handle an exception asynchronously.

        Args:
            exception: The exception to handle
            context: Additional context information
            reraise: Whether to re-raise the exception after handling
        """
        severity = ErrorSeverity.ERROR
        if isinstance(exception, OdinCoreException):
            # Use context from the exception if available
            context = context or exception.context

        self.handle_error(exception, severity, context, reraise=False)

        if reraise:
            raise exception

    def clear_error_records(self, older_than_hours: int = 24):
        """
        Clear error records older than specified hours.

        Args:
            older_than_hours: Clear errors older than this many hours
        """
        # For now, just clear all errors since we don't track timestamps
        # In a production system, you'd want to add timestamps to errors
        if older_than_hours > 0:
            self.errors = []
            self.error_count = 0


class OdinCoreException(Exception):
    """
    Base exception class for all Odin core errors.

    Provides common functionality for all custom exceptions including
    error codes, context data, and structured logging.
    """

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        original_exception: Optional[Exception] = None,
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.context = context or {}
        self.original_exception = original_exception

        # Log the exception with context
        self._log_exception()

    def _log_exception(self):
        """Log exception with structured context."""
        log_data = {
            "error_code": self.error_code,
            "error_message": self.message,
            "error_context": self.context,
            "exception_type": self.__class__.__name__,
        }

        if self.original_exception:
            log_data["original_exception"] = str(self.original_exception)

        logger.error(f"Odin Core Exception: {self.message}", extra=log_data)

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for API responses."""
        return {
            "error_code": self.error_code,
            "message": self.message,
            "context": self.context,
            "exception_type": self.__class__.__name__,
        }


# Alias for backward compatibility
OdinException = OdinCoreException


# System Exception
class SystemException(OdinCoreException):
    """
    Exception for system-level errors.

    Used for configuration issues, startup failures, and other
    system-wide problems.
    """

    def __init__(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        original_exception: Optional[Exception] = None,
    ):
        super().__init__(
            message=message,
            error_code=ErrorCode.SYSTEM_ERROR,
            context=context,
            original_exception=original_exception,
        )


# Trading Engine Exceptions
class TradingEngineException(OdinCoreException):
    """Base exception for trading engine errors."""

    pass


class InvalidOrderException(TradingEngineException):
    """Raised when an order has invalid parameters."""

    def __init__(self, message: str, order_data: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="INVALID_ORDER",
            context={"order_data": order_data},
        )


class OrderExecutionException(TradingEngineException):
    """Raised when order execution fails."""

    def __init__(
        self,
        message: str,
        order_id: Optional[str] = None,
        exchange_error: Optional[str] = None,
    ):
        super().__init__(
            message=message,
            error_code="ORDER_EXECUTION_FAILED",
            context={"order_id": order_id, "exchange_error": exchange_error},
        )


class InsufficientFundsException(TradingEngineException):
    """Raised when there are insufficient funds for a trade."""

    def __init__(
        self, required_amount: float, available_amount: float, currency: str = "USD"
    ):
        message = f"Insufficient funds: Required {required_amount} {currency}, Available {available_amount} {currency}"
        super().__init__(
            message=message,
            error_code="INSUFFICIENT_FUNDS",
            context={
                "required_amount": required_amount,
                "available_amount": available_amount,
                "currency": currency,
                "deficit": required_amount - available_amount,
            },
        )


class ExchangeConnectionException(TradingEngineException):
    """Raised when exchange connection fails."""

    def __init__(self, exchange_name: str, error_details: Optional[str] = None):
        message = f"Failed to connect to exchange: {exchange_name}"
        super().__init__(
            message=message,
            error_code="EXCHANGE_CONNECTION_FAILED",
            context={"exchange_name": exchange_name, "error_details": error_details},
        )


# Portfolio Manager Exceptions
class PortfolioManagerException(OdinCoreException):
    """Base exception for portfolio manager errors."""

    pass


class PortfolioValidationException(PortfolioManagerException):
    """Raised when portfolio validation fails."""

    def __init__(self, message: str, validation_errors: Optional[list] = None):
        super().__init__(
            message=message,
            error_code="PORTFOLIO_VALIDATION_FAILED",
            context={"validation_errors": validation_errors},
        )


class AllocationException(PortfolioManagerException):
    """Raised when portfolio allocation fails."""

    def __init__(
        self, message: str, target_allocation: Optional[Dict[str, float]] = None
    ):
        super().__init__(
            message=message,
            error_code="ALLOCATION_FAILED",
            context={"target_allocation": target_allocation},
        )


# Risk Manager Exceptions
class RiskManagerException(OdinCoreException):
    """Base exception for risk manager errors."""

    pass


class RiskLimitExceededException(RiskManagerException):
    """Raised when a risk limit is exceeded."""

    def __init__(
        self,
        limit_type: str,
        current_value: float,
        limit_value: float,
        action_blocked: str,
    ):
        message = f"Risk limit exceeded: {limit_type} = {current_value}, Limit = {limit_value}"
        super().__init__(
            message=message,
            error_code="RISK_LIMIT_EXCEEDED",
            context={
                "limit_type": limit_type,
                "current_value": current_value,
                "limit_value": limit_value,
                "action_blocked": action_blocked,
                "excess_percentage": ((current_value / limit_value) - 1) * 100,
            },
        )


class DrawdownLimitException(RiskManagerException):
    """Raised when maximum drawdown limit is exceeded."""

    def __init__(self, current_drawdown: float, max_drawdown: float):
        message = (
            f"Maximum drawdown exceeded: {current_drawdown:.2%} > {max_drawdown:.2%}"
        )
        super().__init__(
            message=message,
            error_code="DRAWDOWN_LIMIT_EXCEEDED",
            context={
                "current_drawdown": current_drawdown,
                "max_drawdown": max_drawdown,
                "excess_drawdown": current_drawdown - max_drawdown,
            },
        )


class PositionSizeException(RiskManagerException):
    """Raised when position size limits are exceeded."""

    def __init__(self, requested_size: float, max_size: float, symbol: str):
        message = (
            f"Position size limit exceeded for {symbol}: {requested_size} > {max_size}"
        )
        super().__init__(
            message=message,
            error_code="POSITION_SIZE_EXCEEDED",
            context={
                "symbol": symbol,
                "requested_size": requested_size,
                "max_size": max_size,
                "excess_size": requested_size - max_size,
            },
        )


# Data Collector Exceptions
class DataCollectorException(OdinCoreException):
    """Base exception for data collector errors."""

    pass


class MarketDataException(DataCollectorException):
    """Raised when market data retrieval fails."""

    def __init__(
        self,
        message: str,
        data_source: Optional[str] = None,
        symbol: Optional[str] = None,
    ):
        super().__init__(
            message=message,
            error_code="MARKET_DATA_ERROR",
            context={"data_source": data_source, "symbol": symbol},
        )


class DataValidationException(DataCollectorException):
    """Raised when data validation fails."""

    def __init__(self, message: str, invalid_data: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="DATA_VALIDATION_FAILED",
            context={"invalid_data": invalid_data},
        )


class DataSourceException(DataCollectorException):
    """Raised when data source is unavailable or fails."""

    def __init__(self, source_name: str, error_details: Optional[str] = None):
        message = f"Data source failed: {source_name}"
        super().__init__(
            message=message,
            error_code="DATA_SOURCE_FAILED",
            context={"source_name": source_name, "error_details": error_details},
        )


# Database Exceptions
class DatabaseException(OdinCoreException):
    """Base exception for database errors."""

    pass


class DatabaseConnectionException(DatabaseException):
    """Raised when database connection fails."""

    def __init__(self, connection_string: str, error_details: Optional[str] = None):
        message = f"Database connection failed: {connection_string}"
        super().__init__(
            message=message,
            error_code="DATABASE_CONNECTION_FAILED",
            context={
                "connection_string": connection_string,
                "error_details": error_details,
            },
        )


class DatabaseOperationException(DatabaseException):
    """Raised when database operations fail."""

    def __init__(
        self,
        operation: str,
        table: Optional[str] = None,
        error_details: Optional[str] = None,
    ):
        message = f"Database operation failed: {operation}"
        super().__init__(
            message=message,
            error_code="DATABASE_OPERATION_FAILED",
            context={
                "operation": operation,
                "table": table,
                "error_details": error_details,
            },
        )


class DataIntegrityException(DatabaseException):
    """Raised when data integrity constraints are violated."""

    def __init__(
        self,
        message: str,
        constraint: Optional[str] = None,
        table: Optional[str] = None,
    ):
        super().__init__(
            message=message,
            error_code="DATA_INTEGRITY_VIOLATION",
            context={"constraint": constraint, "table": table},
        )


# Strategy Exceptions
class StrategyException(OdinCoreException):
    """Base exception for strategy errors."""

    pass


class StrategyConfigurationException(StrategyException):
    """Raised when strategy configuration is invalid."""

    def __init__(self, strategy_name: str, config_errors: Optional[list] = None):
        message = f"Invalid configuration for strategy: {strategy_name}"
        super().__init__(
            message=message,
            error_code="STRATEGY_CONFIG_INVALID",
            context={"strategy_name": strategy_name, "config_errors": config_errors},
        )


class StrategyExecutionException(StrategyException):
    """Raised when strategy execution fails."""

    def __init__(self, strategy_name: str, execution_error: Optional[str] = None):
        message = f"Strategy execution failed: {strategy_name}"
        super().__init__(
            message=message,
            error_code="STRATEGY_EXECUTION_FAILED",
            context={
                "strategy_name": strategy_name,
                "execution_error": execution_error,
            },
        )


# Utility function for exception handling
def handle_core_exception(func):
    """
    Decorator for handling and converting exceptions to OdinCoreException.

    Usage:
        @handle_core_exception
        def some_function():
            # Function implementation
    """

    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except OdinCoreException:
            # Re-raise Odin exceptions as-is
            raise
        except Exception as e:
            # Convert other exceptions to OdinCoreException
            raise OdinCoreException(
                message=f"Unexpected error in {func.__name__}: {str(e)}",
                error_code="UNEXPECTED_ERROR",
                context={
                    "function": func.__name__,
                    "args": str(args),
                    "kwargs": str(kwargs),
                },
                original_exception=e,
            )

    return wrapper


# Exception mapping for HTTP status codes
EXCEPTION_HTTP_STATUS_MAP = {
    InvalidOrderException: 400,
    InsufficientFundsException: 400,
    RiskLimitExceededException: 403,
    DrawdownLimitException: 403,
    PositionSizeException: 403,
    PortfolioValidationException: 400,
    DataValidationException: 400,
    StrategyConfigurationException: 400,
    ExchangeConnectionException: 503,
    DatabaseConnectionException: 503,
    DataSourceException: 503,
    MarketDataException: 503,
    OrderExecutionException: 500,
    DatabaseOperationException: 500,
    DataIntegrityException: 500,
    StrategyExecutionException: 500,
    OdinCoreException: 500,
}


def get_http_status_code(exception: Exception) -> int:
    """Get HTTP status code for exception type."""
    for exc_type, status_code in EXCEPTION_HTTP_STATUS_MAP.items():
        if isinstance(exception, exc_type):
            return status_code
    return 500  # Default to internal server error
