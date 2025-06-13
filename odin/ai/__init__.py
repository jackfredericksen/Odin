"""
AI Enhancement Module for Odin Trading Bot.
Fixed imports to match actual class names.
"""

try:
    # Import regime detection components
    from .regime_detection.regime_detector import RegimeDetector  # Fixed: was MarketRegimeDetector
    from .regime_detection.market_states import MarketState
    from .regime_detection.regime_visualizer import RegimeVisualizer
except ImportError as e:
    print(f"Warning: Could not import regime detection components: {e}")
    RegimeDetector = None
    MarketState = None
    RegimeVisualizer = None

try:
    # Import strategy selection components  
    from .strategy_selection.adaptive_manager import AdaptiveManager
    from .strategy_selection.ai_strategy_selector import AIStrategySelector
    from .strategy_selection.strategy_scorer import StrategyScorer
except ImportError as e:
    print(f"Warning: Could not import strategy selection components: {e}")
    AdaptiveManager = None
    AIStrategySelector = None
    StrategyScorer = None

try:
    # Import setup function
    from .setup_ai import setup_ai_components
except ImportError as e:
    print(f"Warning: Could not import AI setup: {e}")
    setup_ai_components = None

# Export available components
__all__ = []

# Add available components to exports
if RegimeDetector is not None:
    __all__.append('RegimeDetector')
if MarketState is not None:
    __all__.append('MarketState')
if RegimeVisualizer is not None:
    __all__.append('RegimeVisualizer')
if AdaptiveManager is not None:
    __all__.append('AdaptiveManager')
if AIStrategySelector is not None:
    __all__.append('AIStrategySelector')
if StrategyScorer is not None:
    __all__.append('StrategyScorer')
if setup_ai_components is not None:
    __all__.append('setup_ai_components')

# Compatibility aliases (in case other code expects the old names)
MarketRegimeDetector = RegimeDetector  # Alias for backward compatibility