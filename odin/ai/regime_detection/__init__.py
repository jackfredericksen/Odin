"""
Market Regime Detection Module.
Fixed imports to match actual class names.
"""

try:
    from .regime_detector import RegimeDetector  # Fixed: was MarketRegimeDetector
except ImportError as e:
    print(f"Warning: Could not import RegimeDetector: {e}")
    RegimeDetector = None

try:
    from .market_states import MarketState
except ImportError as e:
    print(f"Warning: Could not import MarketState: {e}")
    MarketState = None

try:
    from .regime_visualizer import RegimeVisualizer
except ImportError as e:
    print(f"Warning: Could not import RegimeVisualizer: {e}")
    RegimeVisualizer = None

# Export available components
__all__ = []

if RegimeDetector is not None:
    __all__.append("RegimeDetector")
if MarketState is not None:
    __all__.append("MarketState")
if RegimeVisualizer is not None:
    __all__.append("RegimeVisualizer")

# Compatibility alias
MarketRegimeDetector = RegimeDetector  # Alias for backward compatibility
if RegimeDetector is not None:
    __all__.append("MarketRegimeDetector")
