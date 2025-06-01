"""Input validation utilities."""

import re
from typing import Any, List, Optional

from pydantic import validator


def validate_symbol(symbol: str) -> str:
    """Validate cryptocurrency symbol format."""
    if not isinstance(symbol, str):
        raise ValueError("Symbol must be a string")
    
    symbol = symbol.upper().strip()
    
    # Check format (3-5 characters, alphanumeric)
    if not re.match(r'^[A-Z0-9]{2,10}$', symbol):
        raise ValueError("Invalid symbol format")
    
    return symbol


def validate_timeframe(timeframe: str) -> str:
    """Validate timeframe format."""
    valid_timeframes = ["1m", "5m", "15m", "30m", "1h", "4h", "1d", "1w"]
    
    if timeframe not in valid_timeframes:
        raise ValueError(f"Invalid timeframe. Must be one of: {valid_timeframes}")
    
    return timeframe


def validate_positive_number(value: Any, field_name: str = "value") -> float:
    """Validate that a value is a positive number."""
    try:
        num_value = float(value)
    except (ValueError, TypeError):
        raise ValueError(f"{field_name} must be a number")
    
    if num_value <= 0:
        raise ValueError(f"{field_name} must be positive")
    
    return num_value


def validate_percentage(value: Any, field_name: str = "percentage") -> float:
    """Validate percentage value (0-100)."""
    try:
        num_value = float(value)
    except (ValueError, TypeError):
        raise ValueError(f"{field_name} must be a number")
    
    if not 0 <= num_value <= 100:
        raise ValueError(f"{field_name} must be between 0 and 100")
    
    return num_value