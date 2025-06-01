"""Custom exceptions for Odin trading bot."""

from typing import Any, Dict, Optional


class OdinException(Exception):
    """Base exception for Odin trading bot."""
    
    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """Initialize exception."""
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary."""
        return {
            "error": self.__class__.__name__,
            "message": self.message,
            "error_code": self.error_code,
            "details": self.details,
        }


class DataCollectionError(OdinException):
    """Raised when data collection fails."""
    pass


class StrategyError(OdinException):
    """Raised when strategy execution fails."""
    pass


class APIError(OdinException):
    """Raised when API operations fail."""
    pass


class DatabaseError(OdinException):
    """Raised when database operations fail."""
    pass


class ValidationError(OdinException):
    """Raised when input validation fails."""
    pass


class ConfigurationError(OdinException):
    """Raised when configuration is invalid."""
    pass


class ExternalAPIError(DataCollectionError):
    """Raised when external API calls fail."""
    
    def __init__(
        self,
        message: str,
        api_name: str,
        status_code: Optional[int] = None,
        response_text: Optional[str] = None
    ) -> None:
        """Initialize external API error."""
        super().__init__(
            message=message,
            error_code="EXTERNAL_API_ERROR",
            details={
                "api_name": api_name,
                "status_code": status_code,
                "response_text": response_text,
            }
        )
        self.api_name = api_name
        self.status_code = status_code
        self.response_text = response_text


class RateLimitError(OdinException):
    """Raised when rate limits are exceeded."""
    
    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: Optional[int] = None
    ) -> None:
        """Initialize rate limit error."""
        super().__init__(
            message=message,
            error_code="RATE_LIMIT_EXCEEDED",
            details={"retry_after": retry_after}
        )
        self.retry_after = retry_after


class InsufficientDataError(StrategyError):
    """Raised when insufficient data is available for strategy calculation."""
    
    def __init__(
        self,
        message: str,
        required_points: int,
        available_points: int
    ) -> None:
        """Initialize insufficient data error."""
        super().__init__(
            message=message,
            error_code="INSUFFICIENT_DATA",
            details={
                "required_points": required_points,
                "available_points": available_points,
            }
        )
        self.required_points = required_points
        self.available_points = available_points