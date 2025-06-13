"""
Trading Strategies Package

This package contains all trading strategy implementations for the Odin Bitcoin trading bot.
Each strategy inherits from the base Strategy class and implements specific trading logic.

Available Strategies:
- MovingAverageStrategy: Trend following using MA crossovers
- RSIStrategy: Mean reversion using RSI oscillator
- BollingerBandsStrategy: Volatility-based breakout/reversion strategy
- MACDStrategy: Trend momentum using MACD indicator

Usage:
    from odin.strategies import MovingAverageStrategy, RSIStrategy

    ma_strategy = MovingAverageStrategy(short_window=5, long_window=20)
    rsi_strategy = RSIStrategy(period=14, oversold=30, overbought=70)
"""

# Import from core models for single source of truth
from ..core.models import SignalType

# Import strategy components
from .base import Strategy, StrategyType
from .bollinger_bands import BollingerBandsStrategy
from .macd import MACDStrategy
from .moving_average import MovingAverageStrategy
from .rsi import RSIStrategy

# Create alias for backward compatibility
StrategySignal = SignalType

__all__ = [
    "Strategy",
    "SignalType",
    "StrategySignal",  # Backward compatibility alias
    "StrategyType",
    "MovingAverageStrategy",
    "RSIStrategy",
    "BollingerBandsStrategy",
    "MACDStrategy",
]

# Strategy registry for dynamic strategy loading
STRATEGY_REGISTRY = {
    "moving_average": MovingAverageStrategy,
    "rsi": RSIStrategy,
    "bollinger_bands": BollingerBandsStrategy,
    "macd": MACDStrategy,
}


def get_strategy(strategy_name: str) -> type[Strategy]:
    """
    Get strategy class by name.

    Args:
        strategy_name: Name of the strategy

    Returns:
        Strategy class

    Raises:
        ValueError: If strategy name is not found
    """
    if strategy_name not in STRATEGY_REGISTRY:
        available = ", ".join(STRATEGY_REGISTRY.keys())
        raise ValueError(
            f"Strategy '{strategy_name}' not found. Available: {available}"
        )

    return STRATEGY_REGISTRY[strategy_name]


def list_strategies() -> list[str]:
    """
    Get list of available strategy names.

    Returns:
        List of strategy names
    """
    return list(STRATEGY_REGISTRY.keys())
