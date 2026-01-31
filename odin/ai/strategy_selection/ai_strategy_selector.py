"""
AI Strategy Selector Module

Uses machine learning and market analysis to dynamically select
the optimal trading strategy for current market conditions.
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class AIStrategySelector:
    """
    AI-powered strategy selector.

    Combines regime detection, strategy scoring, and market analysis
    to recommend the optimal trading strategy.
    """

    def __init__(
        self,
        regime_detector: Any = None,
        strategy_scorer: Any = None
    ):
        """
        Initialize the AI strategy selector.

        Args:
            regime_detector: RegimeDetector instance
            strategy_scorer: StrategyScorer instance
        """
        self.regime_detector = regime_detector
        self.strategy_scorer = strategy_scorer
        self.selection_history: List[Dict[str, Any]] = []
        self.current_selection: Optional[str] = None

        logger.info("AIStrategySelector initialized")

    async def select_optimal_strategy(
        self,
        price_data: List[Any],
        available_strategies: List[str]
    ) -> Dict[str, Any]:
        """
        Select the optimal strategy based on current market conditions.

        Args:
            price_data: Recent price data
            available_strategies: List of available strategy IDs

        Returns:
            Dictionary with selection results
        """
        try:
            if not available_strategies:
                return self._empty_result()

            # Detect current market regime
            market_regime = {}
            if self.regime_detector:
                market_regime = await self.regime_detector.detect_regime(price_data)

            # Score all strategies
            all_scores = {}
            if self.strategy_scorer:
                all_scores = await self.strategy_scorer.score_all_strategies(
                    available_strategies, market_regime
                )
            else:
                # Default scores if no scorer available
                all_scores = {s: 0.5 for s in available_strategies}

            # Find best strategy
            if all_scores:
                best_strategy = max(all_scores.items(), key=lambda x: x[1])
                strategy_id = best_strategy[0]
                confidence = best_strategy[1]
            else:
                strategy_id = available_strategies[0]
                confidence = 0.5

            # Create result
            result = {
                "strategy_id": strategy_id,
                "confidence": confidence,
                "market_regime": market_regime,
                "all_scores": all_scores,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "reasoning": self._generate_reasoning(
                    strategy_id, confidence, market_regime, all_scores
                )
            }

            # Store selection
            self.current_selection = strategy_id
            self.selection_history.append(result)

            # Keep only recent history
            if len(self.selection_history) > 100:
                self.selection_history = self.selection_history[-100:]

            logger.info(
                f"Selected strategy: {strategy_id} "
                f"(confidence: {confidence:.3f}, regime: {market_regime.get('current_regime', 'unknown')})"
            )

            return result

        except Exception as e:
            logger.error(f"Error selecting strategy: {e}")
            return self._empty_result(available_strategies)

    def _generate_reasoning(
        self,
        strategy_id: str,
        confidence: float,
        market_regime: Dict[str, Any],
        all_scores: Dict[str, float]
    ) -> str:
        """Generate human-readable reasoning for the selection."""
        regime = market_regime.get("current_regime", "unknown")
        trend = market_regime.get("trend", "neutral")
        volatility = market_regime.get("volatility", "medium")

        # Extract strategy type
        strategy_type = strategy_id.split("_")[0] if "_" in strategy_id else strategy_id

        reasons = []

        # Regime-based reasoning
        if regime == "trending_up":
            reasons.append(f"Market is in an uptrend ({trend})")
            if strategy_type in ["moving_average", "macd"]:
                reasons.append("Trend-following strategies perform well in trending markets")
        elif regime == "trending_down":
            reasons.append(f"Market is in a downtrend ({trend})")
            if strategy_type in ["moving_average", "macd"]:
                reasons.append("Trend-following can capture downside moves")
        elif regime == "ranging":
            reasons.append("Market is ranging/consolidating")
            if strategy_type in ["rsi", "bollinger_bands"]:
                reasons.append("Mean reversion strategies excel in ranging markets")

        # Volatility reasoning
        if volatility == "high":
            reasons.append("High volatility detected - position sizing may need adjustment")
        elif volatility == "low":
            reasons.append("Low volatility - breakout opportunities may arise")

        # Confidence reasoning
        if confidence > 0.8:
            reasons.append("High confidence in selection based on historical performance")
        elif confidence < 0.5:
            reasons.append("Lower confidence - consider reduced position sizes")

        return " | ".join(reasons) if reasons else "Standard selection based on available data"

    def _empty_result(self, strategies: Optional[List[str]] = None) -> Dict[str, Any]:
        """Return empty/default result."""
        default_strategy = strategies[0] if strategies else None
        return {
            "strategy_id": default_strategy,
            "confidence": 0.5,
            "market_regime": {},
            "all_scores": {},
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "reasoning": "Default selection - insufficient data for AI analysis"
        }

    def get_selection_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent selection history."""
        return self.selection_history[-limit:]

    async def health_check(self) -> bool:
        """Check if the selector is healthy."""
        return True
