# odin/ai/strategy_selection/adaptive_manager.py
"""
Adaptive Strategy Management System for Odin Trading Bot
Automatically selects and configures strategies based on detected market regimes
"""

import json
import logging
import os

# Import existing Odin strategies
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "../../../"))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

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


# Import strategies with fallback
try:
    from odin.strategies.bollinger_bands import BollingerBandsStrategy
    from odin.strategies.macd import MACDStrategy
    from odin.strategies.moving_average import MovingAverageStrategy
    from odin.strategies.rsi import RSIStrategy
except ImportError:
    try:
        from strategies.bollinger_bands import BollingerBandsStrategy
        from strategies.macd import MACDStrategy
        from strategies.moving_average import MovingAverageStrategy
        from strategies.rsi import RSIStrategy
    except ImportError:
        # Create dummy strategy classes if imports fail
        class DummyStrategy:
            def __init__(self, **kwargs):
                self.params = kwargs

            def generate_signal(self, data):
                return Signal(
                    signal_type=SignalType.HOLD,
                    strength=0.0,
                    confidence=0.5,
                    timestamp=datetime.now(),
                    strategy_name=self.__class__.__name__,
                )

        class BollingerBandsStrategy(DummyStrategy):
            pass

        class MACDStrategy(DummyStrategy):
            pass

        class MovingAverageStrategy(DummyStrategy):
            pass

        class RSIStrategy(DummyStrategy):
            pass


class RegimeType(Enum):
    BULL_TRENDING = "bull_trending"
    BEAR_TRENDING = "bear_trending"
    SIDEWAYS = "sideways"
    HIGH_VOLATILITY = "high_volatility"
    CRISIS = "crisis"


@dataclass
class StrategyConfig:
    """Configuration for a trading strategy"""

    strategy_class: str
    parameters: Dict[str, Any]
    weight: float
    min_confidence: float
    max_position_size: float


@dataclass
class RegimeStrategyMapping:
    """Mapping of strategies to market regimes"""

    regime: RegimeType
    primary_strategies: List[StrategyConfig]
    secondary_strategies: List[StrategyConfig]
    risk_multiplier: float
    max_exposure: float


class AdaptiveStrategyManager:
    """
    Manages strategy selection and configuration based on market regimes
    """

    def __init__(self, config_path: str = "data/strategy_configs/"):
        self.config_path = config_path
        self.logger = self._setup_logging()

        # Strategy instances
        self.strategy_instances = {}
        self.active_strategies = []

        # Performance tracking
        self.strategy_performance = {}
        self.regime_performance = {}

        # Current state
        self.current_regime = None
        self.current_confidence = 0.0
        self.last_regime_change = None

        # Initialize strategy mappings
        self.regime_strategy_map = self._initialize_strategy_mappings()

        # Ensure config directory exists
        os.makedirs(config_path, exist_ok=True)

        # Load existing performance data
        self._load_performance_data()

    def _setup_logging(self):
        logging.basicConfig(level=logging.INFO)
        return logging.getLogger(__name__)

    def _initialize_strategy_mappings(self) -> Dict[RegimeType, RegimeStrategyMapping]:
        """Initialize default strategy mappings for each regime"""

        mappings = {
            RegimeType.BULL_TRENDING: RegimeStrategyMapping(
                regime=RegimeType.BULL_TRENDING,
                primary_strategies=[
                    StrategyConfig(
                        strategy_class="MovingAverageStrategy",
                        parameters={"short_period": 5, "long_period": 20},
                        weight=0.6,
                        min_confidence=0.7,
                        max_position_size=0.8,
                    ),
                    StrategyConfig(
                        strategy_class="MACDStrategy",
                        parameters={
                            "fast_period": 8,
                            "slow_period": 21,
                            "signal_period": 9,
                        },
                        weight=0.4,
                        min_confidence=0.6,
                        max_position_size=0.6,
                    ),
                ],
                secondary_strategies=[
                    StrategyConfig(
                        strategy_class="RSIStrategy",
                        parameters={"period": 14, "oversold": 25, "overbought": 75},
                        weight=0.2,
                        min_confidence=0.8,
                        max_position_size=0.3,
                    )
                ],
                risk_multiplier=1.2,  # More aggressive in bull markets
                max_exposure=0.9,
            ),
            RegimeType.BEAR_TRENDING: RegimeStrategyMapping(
                regime=RegimeType.BEAR_TRENDING,
                primary_strategies=[
                    StrategyConfig(
                        strategy_class="RSIStrategy",
                        parameters={"period": 14, "oversold": 35, "overbought": 65},
                        weight=0.5,
                        min_confidence=0.8,
                        max_position_size=0.4,
                    ),
                    StrategyConfig(
                        strategy_class="MovingAverageStrategy",
                        parameters={"short_period": 10, "long_period": 30},
                        weight=0.5,
                        min_confidence=0.7,
                        max_position_size=0.5,
                    ),
                ],
                secondary_strategies=[],
                risk_multiplier=0.6,  # Conservative in bear markets
                max_exposure=0.5,
            ),
            RegimeType.SIDEWAYS: RegimeStrategyMapping(
                regime=RegimeType.SIDEWAYS,
                primary_strategies=[
                    StrategyConfig(
                        strategy_class="RSIStrategy",
                        parameters={"period": 14, "oversold": 30, "overbought": 70},
                        weight=0.4,
                        min_confidence=0.6,
                        max_position_size=0.6,
                    ),
                    StrategyConfig(
                        strategy_class="BollingerBandsStrategy",
                        parameters={"period": 20, "std_dev": 2.0},
                        weight=0.6,
                        min_confidence=0.7,
                        max_position_size=0.7,
                    ),
                ],
                secondary_strategies=[
                    StrategyConfig(
                        strategy_class="MACDStrategy",
                        parameters={
                            "fast_period": 12,
                            "slow_period": 26,
                            "signal_period": 9,
                        },
                        weight=0.3,
                        min_confidence=0.8,
                        max_position_size=0.4,
                    )
                ],
                risk_multiplier=0.8,
                max_exposure=0.7,
            ),
            RegimeType.HIGH_VOLATILITY: RegimeStrategyMapping(
                regime=RegimeType.HIGH_VOLATILITY,
                primary_strategies=[
                    StrategyConfig(
                        strategy_class="BollingerBandsStrategy",
                        parameters={"period": 15, "std_dev": 2.5},
                        weight=0.7,
                        min_confidence=0.8,
                        max_position_size=0.5,
                    ),
                    StrategyConfig(
                        strategy_class="RSIStrategy",
                        parameters={"period": 10, "oversold": 20, "overbought": 80},
                        weight=0.3,
                        min_confidence=0.9,
                        max_position_size=0.3,
                    ),
                ],
                secondary_strategies=[],
                risk_multiplier=0.5,  # Very conservative
                max_exposure=0.4,
            ),
            RegimeType.CRISIS: RegimeStrategyMapping(
                regime=RegimeType.CRISIS,
                primary_strategies=[],  # No active trading in crisis
                secondary_strategies=[],
                risk_multiplier=0.0,  # Cash position
                max_exposure=0.1,  # Minimal exposure
            ),
        }

        return mappings

    def update_regime(self, regime: str, confidence: float) -> bool:
        """
        Update current market regime and adapt strategies

        Args:
            regime: Detected market regime
            confidence: Confidence score for the regime

        Returns:
            bool: Whether strategy adaptation was successful
        """
        try:
            # Convert string to enum
            try:
                new_regime = RegimeType(regime)
            except ValueError:
                self.logger.warning(f"Unknown regime: {regime}")
                return False

            # Check if regime actually changed
            regime_changed = self.current_regime != new_regime

            if regime_changed:
                self.logger.info(
                    f"Regime change detected: {self.current_regime} -> {new_regime}"
                )
                self.last_regime_change = datetime.now()

                # Adapt strategies for new regime
                success = self._adapt_strategies_for_regime(new_regime, confidence)

                if success:
                    self.current_regime = new_regime
                    self.current_confidence = confidence

                    # Log regime change
                    self._log_regime_change(new_regime, confidence)

                return success
            else:
                # Same regime, just update confidence
                self.current_confidence = confidence
                return True

        except Exception as e:
            self.logger.error(f"Regime update failed: {e}")
            return False

    def _adapt_strategies_for_regime(
        self, regime: RegimeType, confidence: float
    ) -> bool:
        """
        Adapt active strategies based on the new regime

        Args:
            regime: New market regime
            confidence: Confidence in regime detection

        Returns:
            bool: Success status
        """
        try:
            # Get strategy mapping for this regime
            regime_mapping = self.regime_strategy_map.get(regime)
            if not regime_mapping:
                self.logger.warning(f"No strategy mapping for regime: {regime}")
                return False

            # Clear current active strategies
            self.active_strategies = []

            # Handle crisis regime (go to cash)
            if regime == RegimeType.CRISIS:
                self.logger.info("Crisis regime detected - moving to cash position")
                return self._implement_crisis_mode()

            # Activate primary strategies
            for strategy_config in regime_mapping.primary_strategies:
                if confidence >= strategy_config.min_confidence:
                    strategy_instance = self._get_strategy_instance(
                        strategy_config.strategy_class, strategy_config.parameters
                    )

                    if strategy_instance:
                        self.active_strategies.append(
                            {
                                "strategy": strategy_instance,
                                "config": strategy_config,
                                "type": "primary",
                            }
                        )

                        self.logger.info(
                            f"Activated primary strategy: {strategy_config.strategy_class} "
                            f"(weight: {strategy_config.weight})"
                        )

            # Activate secondary strategies if confidence is high enough
            if confidence > 0.8:
                for strategy_config in regime_mapping.secondary_strategies:
                    if confidence >= strategy_config.min_confidence:
                        strategy_instance = self._get_strategy_instance(
                            strategy_config.strategy_class, strategy_config.parameters
                        )

                        if strategy_instance:
                            self.active_strategies.append(
                                {
                                    "strategy": strategy_instance,
                                    "config": strategy_config,
                                    "type": "secondary",
                                }
                            )

                            self.logger.info(
                                f"Activated secondary strategy: {strategy_config.strategy_class}"
                            )

            self.logger.info(
                f"Activated {len(self.active_strategies)} strategies for {regime.value}"
            )
            return True

        except Exception as e:
            self.logger.error(f"Strategy adaptation failed: {e}")
            return False

    def _get_strategy_instance(self, strategy_class: str, parameters: Dict[str, Any]):
        """Get or create strategy instance with given parameters"""
        try:
            # Create unique key for this strategy configuration
            param_key = json.dumps(parameters, sort_keys=True)
            instance_key = f"{strategy_class}_{hash(param_key)}"

            # Return existing instance if available
            if instance_key in self.strategy_instances:
                return self.strategy_instances[instance_key]

            # Create new instance
            if strategy_class == "MovingAverageStrategy":
                strategy = MovingAverageStrategy(
                    short_period=parameters.get("short_period", 5),
                    long_period=parameters.get("long_period", 20),
                )
            elif strategy_class == "RSIStrategy":
                strategy = RSIStrategy(
                    period=parameters.get("period", 14),
                    oversold=parameters.get("oversold", 30),
                    overbought=parameters.get("overbought", 70),
                )
            elif strategy_class == "BollingerBandsStrategy":
                strategy = BollingerBandsStrategy(
                    period=parameters.get("period", 20),
                    std_dev=parameters.get("std_dev", 2.0),
                )
            elif strategy_class == "MACDStrategy":
                strategy = MACDStrategy(
                    fast_period=parameters.get("fast_period", 12),
                    slow_period=parameters.get("slow_period", 26),
                    signal_period=parameters.get("signal_period", 9),
                )
            else:
                self.logger.warning(f"Unknown strategy class: {strategy_class}")
                return None

            # Store instance for reuse
            self.strategy_instances[instance_key] = strategy
            return strategy

        except Exception as e:
            self.logger.error(f"Strategy instance creation failed: {e}")
            return None

    def _implement_crisis_mode(self) -> bool:
        """Implement crisis mode - move to cash position"""
        try:
            # In crisis mode, we don't activate any strategies
            # This should trigger the portfolio manager to move to cash
            self.logger.info("Crisis mode implemented - all strategies deactivated")
            return True

        except Exception as e:
            self.logger.error(f"Crisis mode implementation failed: {e}")
            return False

    def generate_signals(self, market_data: pd.DataFrame) -> List[Dict]:
        """
        Generate trading signals from all active strategies

        Args:
            market_data: Current market data

        Returns:
            List of weighted signals from active strategies
        """
        try:
            if not self.active_strategies:
                return []

            signals = []

            for strategy_info in self.active_strategies:
                strategy = strategy_info["strategy"]
                config = strategy_info["config"]
                strategy_type = strategy_info["type"]

                try:
                    # Generate signal from strategy
                    signal = strategy.generate_signal(market_data)

                    if signal and signal.signal_type != SignalType.HOLD:
                        # Apply regime-specific adjustments
                        adjusted_signal = self._adjust_signal_for_regime(signal, config)

                        signals.append(
                            {
                                "signal": adjusted_signal,
                                "strategy_name": strategy.__class__.__name__,
                                "weight": config.weight,
                                "type": strategy_type,
                                "confidence": config.min_confidence,
                                "max_position_size": config.max_position_size,
                            }
                        )

                except Exception as e:
                    self.logger.warning(
                        f"Signal generation failed for {strategy.__class__.__name__}: {e}"
                    )
                    continue

            return signals

        except Exception as e:
            self.logger.error(f"Signal generation failed: {e}")
            return []

    def _adjust_signal_for_regime(
        self, signal: Signal, config: StrategyConfig
    ) -> Signal:
        """Adjust signal strength based on current regime"""
        try:
            # Get regime multiplier
            regime_mapping = self.regime_strategy_map.get(self.current_regime)
            if not regime_mapping:
                return signal

            # Apply risk multiplier to signal strength
            adjusted_strength = signal.strength * regime_mapping.risk_multiplier
            adjusted_strength = max(
                0.1, min(1.0, adjusted_strength)
            )  # Clamp between 0.1 and 1.0

            # Apply position size limit
            max_position = min(config.max_position_size, regime_mapping.max_exposure)

            # Create adjusted signal
            adjusted_signal = Signal(
                signal_type=signal.signal_type,
                strength=adjusted_strength,
                confidence=signal.confidence * self.current_confidence,
                timestamp=signal.timestamp,
                strategy_name=signal.strategy_name,
                metadata={
                    **signal.metadata,
                    "regime": (
                        self.current_regime.value if self.current_regime else "unknown"
                    ),
                    "regime_confidence": self.current_confidence,
                    "max_position_size": max_position,
                    "risk_multiplier": regime_mapping.risk_multiplier,
                },
            )

            return adjusted_signal

        except Exception as e:
            self.logger.error(f"Signal adjustment failed: {e}")
            return signal

    def get_combined_signal(self, market_data: pd.DataFrame) -> Optional[Dict]:
        """
        Get combined signal from all active strategies

        Args:
            market_data: Current market data

        Returns:
            Combined signal with weighted average
        """
        try:
            signals = self.generate_signals(market_data)

            if not signals:
                return None

            # Separate buy and sell signals
            buy_signals = [
                s for s in signals if s["signal"].signal_type == SignalType.BUY
            ]
            sell_signals = [
                s for s in signals if s["signal"].signal_type == SignalType.SELL
            ]

            # Calculate weighted averages
            combined_signal = self._calculate_weighted_signal(buy_signals, sell_signals)

            return combined_signal

        except Exception as e:
            self.logger.error(f"Combined signal calculation failed: {e}")
            return None

    def _calculate_weighted_signal(
        self, buy_signals: List[Dict], sell_signals: List[Dict]
    ) -> Dict:
        """Calculate weighted average of signals"""

        if not buy_signals and not sell_signals:
            return {
                "signal_type": SignalType.HOLD,
                "strength": 0.0,
                "confidence": 0.0,
                "position_size": 0.0,
                "contributing_strategies": [],
            }

        # Calculate weighted buy strength
        buy_weight_sum = sum(s["weight"] for s in buy_signals)
        buy_strength = sum(s["signal"].strength * s["weight"] for s in buy_signals)

        # Calculate weighted sell strength
        sell_weight_sum = sum(s["weight"] for s in sell_signals)
        sell_strength = sum(s["signal"].strength * s["weight"] for s in sell_signals)

        # Determine final signal
        if buy_weight_sum > sell_weight_sum:
            final_signal_type = SignalType.BUY
            final_strength = buy_strength / max(buy_weight_sum, 0.001)
            contributing_strategies = [s["strategy_name"] for s in buy_signals]
        elif sell_weight_sum > buy_weight_sum:
            final_signal_type = SignalType.SELL
            final_strength = sell_strength / max(sell_weight_sum, 0.001)
            contributing_strategies = [s["strategy_name"] for s in sell_signals]
        else:
            final_signal_type = SignalType.HOLD
            final_strength = 0.0
            contributing_strategies = []

        # Calculate position size based on regime constraints
        regime_mapping = self.regime_strategy_map.get(self.current_regime)
        max_position = regime_mapping.max_exposure if regime_mapping else 0.5

        position_size = final_strength * max_position

        # Calculate confidence
        all_signals = buy_signals + sell_signals
        avg_confidence = (
            sum(s["confidence"] for s in all_signals) / len(all_signals)
            if all_signals
            else 0
        )

        return {
            "signal_type": final_signal_type,
            "strength": final_strength,
            "confidence": avg_confidence * self.current_confidence,
            "position_size": position_size,
            "contributing_strategies": contributing_strategies,
            "regime": self.current_regime.value if self.current_regime else "unknown",
            "regime_confidence": self.current_confidence,
            "active_strategy_count": len(self.active_strategies),
        }

    def update_strategy_performance(
        self, strategy_name: str, performance_metrics: Dict
    ):
        """Update performance tracking for a strategy"""
        try:
            if strategy_name not in self.strategy_performance:
                self.strategy_performance[strategy_name] = []

            performance_entry = {
                "timestamp": datetime.now(),
                "regime": (
                    self.current_regime.value if self.current_regime else "unknown"
                ),
                "metrics": performance_metrics,
            }

            self.strategy_performance[strategy_name].append(performance_entry)

            # Keep only recent performance data (last 1000 entries)
            if len(self.strategy_performance[strategy_name]) > 1000:
                self.strategy_performance[strategy_name] = self.strategy_performance[
                    strategy_name
                ][-1000:]

            # Save performance data
            self._save_performance_data()

        except Exception as e:
            self.logger.error(f"Performance update failed: {e}")

    def get_strategy_performance_by_regime(
        self, regime: RegimeType, days: int = 30
    ) -> Dict:
        """Get strategy performance statistics for a specific regime"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            regime_performance = {}

            for strategy_name, performance_history in self.strategy_performance.items():
                regime_entries = [
                    entry
                    for entry in performance_history
                    if entry["regime"] == regime.value
                    and entry["timestamp"] > cutoff_date
                ]

                if regime_entries:
                    # Calculate average metrics
                    metrics = regime_entries[0]["metrics"].keys()
                    avg_metrics = {}

                    for metric in metrics:
                        values = [
                            entry["metrics"][metric]
                            for entry in regime_entries
                            if metric in entry["metrics"]
                        ]
                        if values:
                            avg_metrics[metric] = sum(values) / len(values)

                    regime_performance[strategy_name] = {
                        "avg_metrics": avg_metrics,
                        "sample_count": len(regime_entries),
                        "regime": regime.value,
                    }

            return regime_performance

        except Exception as e:
            self.logger.error(f"Performance analysis failed: {e}")
            return {}

    def optimize_strategy_weights(self, lookback_days: int = 30):
        """Optimize strategy weights based on recent performance"""
        try:
            if not self.current_regime:
                return

            # Get recent performance for current regime
            regime_performance = self.get_strategy_performance_by_regime(
                self.current_regime, lookback_days
            )

            if not regime_performance:
                return

            # Calculate performance scores
            strategy_scores = {}
            for strategy_name, perf_data in regime_performance.items():
                metrics = perf_data["avg_metrics"]

                # Simple scoring based on return and Sharpe ratio
                returns = metrics.get("total_return", 0)
                sharpe = metrics.get("sharpe_ratio", 0)
                win_rate = metrics.get("win_rate", 0.5)

                # Combined score
                score = (returns * 0.4) + (sharpe * 0.4) + (win_rate * 0.2)
                strategy_scores[strategy_name] = max(
                    0.1, score
                )  # Minimum weight of 0.1

            # Update weights in current regime mapping
            if strategy_scores:
                self._update_regime_strategy_weights(strategy_scores)
                self.logger.info(
                    f"Updated strategy weights for {self.current_regime.value}"
                )

        except Exception as e:
            self.logger.error(f"Weight optimization failed: {e}")

    def _update_regime_strategy_weights(self, strategy_scores: Dict[str, float]):
        """Update strategy weights based on performance scores"""
        try:
            regime_mapping = self.regime_strategy_map.get(self.current_regime)
            if not regime_mapping:
                return

            # Normalize scores to sum to 1
            total_score = sum(strategy_scores.values())
            normalized_scores = {k: v / total_score for k, v in strategy_scores.items()}

            # Update primary strategy weights
            for strategy_config in regime_mapping.primary_strategies:
                strategy_class = strategy_config.strategy_class
                if strategy_class in normalized_scores:
                    strategy_config.weight = normalized_scores[strategy_class]

            # Update secondary strategy weights (scaled down)
            for strategy_config in regime_mapping.secondary_strategies:
                strategy_class = strategy_config.strategy_class
                if strategy_class in normalized_scores:
                    strategy_config.weight = normalized_scores[strategy_class] * 0.5

        except Exception as e:
            self.logger.error(f"Weight update failed: {e}")

    def get_active_strategies_info(self) -> List[Dict]:
        """Get information about currently active strategies"""
        return [
            {
                "strategy_name": strategy_info["strategy"].__class__.__name__,
                "type": strategy_info["type"],
                "weight": strategy_info["config"].weight,
                "min_confidence": strategy_info["config"].min_confidence,
                "max_position_size": strategy_info["config"].max_position_size,
                "parameters": strategy_info["config"].parameters,
            }
            for strategy_info in self.active_strategies
        ]

    def get_regime_info(self) -> Dict:
        """Get current regime information"""
        return {
            "current_regime": (
                self.current_regime.value if self.current_regime else "unknown"
            ),
            "confidence": self.current_confidence,
            "last_change": (
                self.last_regime_change.isoformat() if self.last_regime_change else None
            ),
            "active_strategy_count": len(self.active_strategies),
            "regime_risk_multiplier": (
                self.regime_strategy_map[self.current_regime].risk_multiplier
                if self.current_regime
                else 1.0
            ),
            "max_exposure": (
                self.regime_strategy_map[self.current_regime].max_exposure
                if self.current_regime
                else 0.5
            ),
        }

    def _log_regime_change(self, new_regime: RegimeType, confidence: float):
        """Log regime change for analysis"""
        try:
            regime_change_entry = {
                "timestamp": datetime.now(),
                "from_regime": (
                    self.current_regime.value if self.current_regime else "unknown"
                ),
                "to_regime": new_regime.value,
                "confidence": confidence,
            }

            # Store in regime performance tracking
            if "regime_changes" not in self.regime_performance:
                self.regime_performance["regime_changes"] = []

            self.regime_performance["regime_changes"].append(regime_change_entry)

            # Keep only recent changes
            if len(self.regime_performance["regime_changes"]) > 1000:
                self.regime_performance["regime_changes"] = self.regime_performance[
                    "regime_changes"
                ][-1000:]

        except Exception as e:
            self.logger.error(f"Regime change logging failed: {e}")

    def _save_performance_data(self):
        """Save performance data to disk"""
        try:
            performance_file = os.path.join(
                self.config_path, "strategy_performance.json"
            )

            # Convert datetime objects to strings for JSON serialization
            serializable_data = {}
            for strategy, history in self.strategy_performance.items():
                serializable_history = []
                for entry in history:
                    serializable_entry = entry.copy()
                    serializable_entry["timestamp"] = entry["timestamp"].isoformat()
                    serializable_history.append(serializable_entry)
                serializable_data[strategy] = serializable_history

            with open(performance_file, "w") as f:
                json.dump(serializable_data, f, indent=2)

        except Exception as e:
            self.logger.error(f"Performance data save failed: {e}")

    def _load_performance_data(self):
        """Load performance data from disk"""
        try:
            performance_file = os.path.join(
                self.config_path, "strategy_performance.json"
            )

            if os.path.exists(performance_file):
                with open(performance_file, "r") as f:
                    data = json.load(f)

                # Convert timestamp strings back to datetime objects
                for strategy, history in data.items():
                    converted_history = []
                    for entry in history:
                        converted_entry = entry.copy()
                        converted_entry["timestamp"] = datetime.fromisoformat(
                            entry["timestamp"]
                        )
                        converted_history.append(converted_entry)
                    self.strategy_performance[strategy] = converted_history

                self.logger.info("Performance data loaded successfully")

        except Exception as e:
            self.logger.error(f"Performance data load failed: {e}")


# Example usage
if __name__ == "__main__":
    # Test the adaptive strategy manager
    manager = AdaptiveStrategyManager()

    print("Testing adaptive strategy manager...")

    # Simulate regime change
    success = manager.update_regime("bull_trending", 0.85)
    print(f"Regime update success: {success}")

    # Get regime info
    regime_info = manager.get_regime_info()
    print(f"Regime info: {regime_info}")

    # Get active strategies
    active_strategies = manager.get_active_strategies_info()
    print(f"Active strategies: {active_strategies}")

    # Create sample market data
    sample_data = pd.DataFrame(
        {
            "close": [100, 101, 102, 103, 104],
            "volume": [1000, 1100, 1200, 1300, 1400],
            "rsi_14": [45, 50, 55, 60, 65],
            "ma_20": [99, 100, 101, 102, 103],
            "ma_50": [95, 96, 97, 98, 99],
        }
    )

    # Generate combined signal
    combined_signal = manager.get_combined_signal(sample_data)
    print(f"Combined signal: {combined_signal}")
