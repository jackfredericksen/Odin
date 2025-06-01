"""Trading strategies for Odin trading bot."""

from odin.strategies.base import BaseStrategy
from odin.strategies.moving_average import MovingAverageStrategy
from odin.strategies.rsi import RSIStrategy
from odin.strategies.bollinger_bands import BollingerBandsStrategy
from odin.strategies.macd import MACDStrategy

__all__ = [
    "BaseStrategy",
    "MovingAverageStrategy", 
    "RSIStrategy",
    "BollingerBandsStrategy",
    "MACDStrategy",
]

# Strategy registry for dynamic loading
STRATEGY_REGISTRY = {
    "moving_average": MovingAverageStrategy,
    "rsi": RSIStrategy,
    "bollinger_bands": BollingerBandsStrategy,
    "macd": MACDStrategy,
}

def get_strategy(strategy_name: str, **kwargs) -> BaseStrategy:
    """Get strategy instance by name."""
    if strategy_name not in STRATEGY_REGISTRY:
        raise ValueError(f"Unknown strategy: {strategy_name}")
    
    strategy_class = STRATEGY_REGISTRY[strategy_name]
    return strategy_class(**kwargs)

def list_strategies() -> list[str]:
    """List available strategies."""
    return list(STRATEGY_REGISTRY.keys())