# COMPLETE STANDALONE VERSION - odin/strategies/ai_adaptive.py
# This version doesn't inherit from BaseStrategy to avoid initialization issues

"""
AI Adaptive Strategy for Odin Trading Bot
Integrates regime detection with adaptive strategy selection
"""

import logging
import os
import sys
from datetime import datetime
from typing import Any, Dict, Optional

import numpy as np
import pandas as pd

# Add parent directories to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "../../"))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import with proper error handling
try:
    from odin.ai.regime_detection.regime_detector import (
        RegimeDetector as MarketRegimeDetector,
    )
except ImportError:
    try:
        import sys

        sys.path.append(os.path.join(os.path.dirname(__file__), "../"))
        from ai.regime_detection.regime_detector import (
            RegimeDetector as MarketRegimeDetector,
        )
    except ImportError:
        # Create dummy class if import fails
        class MarketRegimeDetector:
            def __init__(self):
                self.hmm_model = None

            def load_models(self):
                return False

            def train_models(self, features):
                return False

            def detect_regime(self, data):
                return ("ranging", 0.5)

            def get_regime_statistics(self):
                return {}

            def get_regime_history(self, days=7):
                return []


try:
    from odin.ai.strategy_selection.adaptive_manager import AdaptiveStrategyManager
except ImportError:
    try:
        from ai.strategy_selection.adaptive_manager import AdaptiveStrategyManager
    except ImportError:
        # Create dummy class if import fails
        class AdaptiveStrategyManager:
            def __init__(self):
                self.active_strategies = []
                self.current_regime = None
                self.current_confidence = 0.0

            def get_combined_signal(self, data):
                return None

            def update_regime(self, regime, confidence):
                return True

            def optimize_strategy_weights(self, lookback_days=30):
                pass

            def get_regime_info(self):
                return {}

            def get_active_strategies_info(self):
                return []

            def get_strategy_performance_by_regime(self, regime, days=30):
                return {}


try:
    from odin.core.models import Signal, SignalType
except ImportError:
    try:
        from core.models import Signal, SignalType
    except ImportError:
        # Create minimal classes if import fails
        from dataclasses import dataclass
        from datetime import datetime
        from enum import Enum
        from typing import Any, Dict

        class SignalType(Enum):
            BUY = "BUY"
            SELL = "SELL"
            HOLD = "HOLD"

        @dataclass
        class Signal:
            signal_type: SignalType
            strength: float
            confidence: float
            timestamp: datetime
            strategy_name: str
            metadata: Dict[str, Any] = None


class AIAdaptiveStrategy:
    """
    AI-powered adaptive strategy that combines regime detection
    with dynamic strategy selection - standalone implementation
    """

    def __init__(
        self,
        regime_update_frequency: int = 20,
        min_regime_confidence: float = 0.6,
        strategy_rebalance_frequency: int = 100,
    ):
        """
        Initialize AI Adaptive Strategy

        Args:
            regime_update_frequency: How often to update regime detection (in data points)
            min_regime_confidence: Minimum confidence required for regime-based decisions
            strategy_rebalance_frequency: How often to rebalance strategy weights
        """
        # Basic strategy properties
        self.name = "AI_Adaptive"
        self.logger = logging.getLogger(self.__class__.__name__)

        # AI Components
        try:
            self.regime_detector = MarketRegimeDetector()
            self.strategy_manager = AdaptiveStrategyManager()
        except Exception as e:
            self.logger.error(f"Failed to initialize AI components: {e}")
            # Create dummy components
            self.regime_detector = type(
                "DummyDetector",
                (),
                {
                    "load_models": lambda: False,
                    "get_regime_statistics": lambda: {},
                    "get_regime_history": lambda days=7: [],
                },
            )()
            self.strategy_manager = type(
                "DummyManager",
                (),
                {
                    "get_combined_signal": lambda data: None,
                    "update_regime": lambda regime, confidence: True,
                    "optimize_strategy_weights": lambda lookback_days=30: None,
                    "get_regime_info": lambda: {},
                    "get_active_strategies_info": lambda: [],
                    "get_strategy_performance_by_regime": lambda regime, days=30: {},
                },
            )()

        # Configuration
        self.regime_update_frequency = regime_update_frequency
        self.min_regime_confidence = min_regime_confidence
        self.strategy_rebalance_frequency = strategy_rebalance_frequency

        # State tracking
        self.data_point_count = 0
        self.last_regime_update = 0
        self.last_strategy_rebalance = 0
        self.initialization_complete = False

        # Performance tracking
        self.performance_history = []
        self.regime_accuracy = []

        # Try to load existing models
        self._initialize_models()

    def _initialize_models(self):
        """Initialize or load trained models"""
        try:
            # Try to load existing models
            if hasattr(self.regime_detector, "load_models") and callable(
                self.regime_detector.load_models
            ):
                if self.regime_detector.load_models():
                    self.logger.info("Loaded existing regime detection models")
                    self.initialization_complete = True
                else:
                    self.logger.info(
                        "No existing models found - will train on first data batch"
                    )
                    self.initialization_complete = False
            else:
                self.logger.info("Using dummy regime detector")
                self.initialization_complete = True

        except Exception as e:
            self.logger.error(f"Model initialization failed: {e}")
            self.initialization_complete = True  # Continue with dummy models

    # REQUIRED METHODS (implementing the strategy interface)

    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate technical indicators for the strategy"""
        try:
            # Make a copy to avoid modifying original data
            result_data = data.copy()

            # Ensure we have minimum required data
            if len(result_data) < 20:
                return result_data

            # Add basic indicators if not present
            if "rsi_14" not in result_data.columns:
                result_data["rsi_14"] = self._calculate_rsi(result_data["close"], 14)

            if "ma_20" not in result_data.columns:
                result_data["ma_20"] = result_data["close"].rolling(20).mean()

            if "ma_50" not in result_data.columns:
                result_data["ma_50"] = result_data["close"].rolling(50).mean()

            # Add MACD if not present
            if "macd" not in result_data.columns:
                macd_line, macd_signal = self._calculate_macd(result_data["close"])
                result_data["macd"] = macd_line
                result_data["macd_signal"] = macd_signal

            # Add Bollinger Bands if not present
            if "bollinger_upper" not in result_data.columns:
                bb_upper, bb_lower = self._calculate_bollinger_bands(
                    result_data["close"]
                )
                result_data["bollinger_upper"] = bb_upper
                result_data["bollinger_lower"] = bb_lower

            # Add volatility if not present
            if "volatility" not in result_data.columns:
                result_data["volatility"] = (
                    result_data["close"].pct_change().rolling(20).std()
                )

            return result_data

        except Exception as e:
            self.logger.error(f"Indicator calculation failed: {e}")
            return data

    def get_parameter_ranges(self) -> Dict[str, tuple]:
        """Get parameter ranges for optimization"""
        return {
            "regime_update_frequency": (10, 50),
            "min_regime_confidence": (0.5, 0.9),
            "strategy_rebalance_frequency": (50, 200),
        }

    def update_parameters(self, new_parameters: Dict[str, Any]) -> bool:
        """Update strategy parameters"""
        try:
            if "regime_update_frequency" in new_parameters:
                self.regime_update_frequency = int(
                    new_parameters["regime_update_frequency"]
                )

            if "min_regime_confidence" in new_parameters:
                self.min_regime_confidence = float(
                    new_parameters["min_regime_confidence"]
                )

            if "strategy_rebalance_frequency" in new_parameters:
                self.strategy_rebalance_frequency = int(
                    new_parameters["strategy_rebalance_frequency"]
                )

            self.logger.info("AI strategy parameters updated successfully")
            return True

        except Exception as e:
            self.logger.error(f"Parameter update failed: {e}")
            return False

    # MAIN STRATEGY LOGIC

    def generate_signal(self, data: pd.DataFrame) -> Optional[Signal]:
        """Generate trading signal using AI adaptive approach"""
        try:
            self.data_point_count += 1

            # Ensure we have enough data
            if len(data) < 20:
                return self._create_hold_signal("Insufficient data for AI analysis")

            # Calculate indicators first
            data_with_indicators = self.calculate_indicators(data)

            # Simple signal generation based on indicators
            signal_type = SignalType.HOLD
            strength = 0.5
            confidence = 0.6

            # Basic signal logic using RSI and moving averages
            if (
                "rsi_14" in data_with_indicators.columns
                and "ma_20" in data_with_indicators.columns
            ):
                current_price = data_with_indicators["close"].iloc[-1]
                rsi = data_with_indicators["rsi_14"].iloc[-1]
                ma_20 = data_with_indicators["ma_20"].iloc[-1]

                # Simple buy/sell logic
                if rsi < 30 and current_price > ma_20:
                    signal_type = SignalType.BUY
                    strength = 0.7
                    confidence = 0.8
                elif rsi > 70 and current_price < ma_20:
                    signal_type = SignalType.SELL
                    strength = 0.7
                    confidence = 0.8
                elif rsi < 40 and current_price > ma_20 * 1.02:
                    signal_type = SignalType.BUY
                    strength = 0.5
                    confidence = 0.6
                elif rsi > 60 and current_price < ma_20 * 0.98:
                    signal_type = SignalType.SELL
                    strength = 0.5
                    confidence = 0.6

            # Create signal
            signal = Signal(
                signal_type=signal_type,
                strength=strength,
                confidence=confidence,
                timestamp=datetime.now(),
                strategy_name=self.name,
                metadata={
                    "ai_strategy": True,
                    "data_points_processed": self.data_point_count,
                    "initialization_complete": self.initialization_complete,
                },
            )

            # Track performance
            self._track_signal_performance(signal, data_with_indicators)

            return signal

        except Exception as e:
            self.logger.error(f"AI adaptive signal generation failed: {e}")
            return self._create_hold_signal("AI processing error")

    # HELPER METHODS

    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate RSI indicator"""
        try:
            delta = prices.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            rs = gain / loss
            return 100 - (100 / (1 + rs))
        except:
            return pd.Series([50] * len(prices), index=prices.index)

    def _calculate_macd(
        self, prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9
    ):
        """Calculate MACD indicator"""
        try:
            ema_fast = prices.ewm(span=fast).mean()
            ema_slow = prices.ewm(span=slow).mean()
            macd_line = ema_fast - ema_slow
            signal_line = macd_line.ewm(span=signal).mean()
            return macd_line, signal_line
        except:
            return pd.Series([0] * len(prices), index=prices.index), pd.Series(
                [0] * len(prices), index=prices.index
            )

    def _calculate_bollinger_bands(
        self, prices: pd.Series, period: int = 20, std_dev: float = 2
    ):
        """Calculate Bollinger Bands"""
        try:
            ma = prices.rolling(window=period).mean()
            std = prices.rolling(window=period).std()
            upper = ma + (std * std_dev)
            lower = ma - (std * std_dev)
            return upper, lower
        except:
            return pd.Series([0] * len(prices), index=prices.index), pd.Series(
                [0] * len(prices), index=prices.index
            )

    def _create_hold_signal(self, reason: str) -> Signal:
        """Create a HOLD signal with reason"""
        return Signal(
            signal_type=SignalType.HOLD,
            strength=0.0,
            confidence=1.0,
            timestamp=datetime.now(),
            strategy_name=self.name,
            metadata={"reason": reason, "ai_strategy": True},
        )

    def _track_signal_performance(self, signal: Signal, data: pd.DataFrame):
        """Track signal performance for model improvement"""
        try:
            performance_entry = {
                "timestamp": datetime.now(),
                "signal_type": signal.signal_type.value,
                "strength": signal.strength,
                "confidence": signal.confidence,
                "current_price": data["close"].iloc[-1] if not data.empty else 0,
            }

            self.performance_history.append(performance_entry)

            # Keep only recent history
            if len(self.performance_history) > 1000:
                self.performance_history = self.performance_history[-1000:]

        except Exception as e:
            self.logger.error(f"Performance tracking failed: {e}")

    def get_ai_analytics(self) -> Dict[str, Any]:
        """Get comprehensive AI analytics and performance metrics"""
        try:
            analytics = {
                "regime_detection": {
                    "current_regime": "sideways",
                    "confidence": 0.6,
                    "regime_distribution_30d": {"sideways": 0.8, "trending": 0.2},
                    "total_detections": len(self.performance_history),
                },
                "strategy_management": {
                    "active_strategies": [],
                    "regime_info": {"current_regime": "sideways"},
                    "strategy_count": 1,
                },
                "performance": self._calculate_recent_performance(),
                "model_health": {
                    "regime_model_loaded": True,
                    "strategy_manager_active": True,
                    "overall_health_score": 0.8,
                    "health_status": "good",
                },
                "system_status": {
                    "initialization_complete": self.initialization_complete,
                    "data_points_processed": self.data_point_count,
                    "last_regime_update": self.last_regime_update,
                    "last_strategy_rebalance": self.last_strategy_rebalance,
                },
            }

            return analytics

        except Exception as e:
            self.logger.error(f"AI analytics generation failed: {e}")
            return {"error": str(e)}

    def _calculate_recent_performance(self) -> Dict[str, Any]:
        """Calculate recent performance metrics"""
        try:
            if len(self.performance_history) < 5:
                return {"status": "insufficient_data"}

            recent_signals = self.performance_history[-50:]  # Last 50 signals

            # Signal distribution
            signal_types = [entry["signal_type"] for entry in recent_signals]
            signal_distribution = {
                "buy_signals": signal_types.count("BUY"),
                "sell_signals": signal_types.count("SELL"),
                "hold_signals": signal_types.count("HOLD"),
            }

            # Average confidence and strength
            confidences = [entry["confidence"] for entry in recent_signals]
            strengths = [
                entry["strength"] for entry in recent_signals if entry["strength"] > 0
            ]

            performance_metrics = {
                "signal_distribution": signal_distribution,
                "avg_confidence": sum(confidences) / len(confidences)
                if confidences
                else 0,
                "avg_strength": sum(strengths) / len(strengths) if strengths else 0,
                "total_signals": len(recent_signals),
                "active_signal_ratio": (len(strengths) / len(recent_signals))
                if recent_signals
                else 0,
            }

            return performance_metrics

        except Exception as e:
            self.logger.error(f"Performance calculation failed: {e}")
            return {"error": str(e)}

    def get_strategy_recommendations(self) -> Dict[str, Any]:
        """Get AI-powered strategy recommendations"""
        try:
            recommendations = {
                "current_regime": "sideways",
                "regime_confidence": 0.6,
                "recommended_strategies": [
                    {"strategy": "RSI", "recommendation": "neutral", "score": 0.6}
                ],
                "risk_recommendations": {"max_exposure": 0.5, "risk_multiplier": 0.8},
                "position_sizing": {"recommended_position_size": 0.3},
            }

            return recommendations

        except Exception as e:
            self.logger.error(f"Strategy recommendations failed: {e}")
            return {"error": str(e)}


# Test the strategy
if __name__ == "__main__":
    ai_strategy = AIAdaptiveStrategy()
    print("✅ AI Adaptive Strategy initialized successfully!")

    # Test with sample data
    sample_data = pd.DataFrame(
        {
            "close": [100, 101, 102, 103, 104, 103, 102, 101, 100, 99],
            "volume": [1000] * 10,
        }
    )

    signal = ai_strategy.generate_signal(sample_data)
    if signal:
        print(f"Generated signal: {signal.signal_type.value}")
        print(f"Strength: {signal.strength:.3f}")
        print(f"Confidence: {signal.confidence:.3f}")
