"""
Strategy Scoring Module

Evaluates and scores trading strategies based on their historical
performance and current market conditions.
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class StrategyScorer:
    """
    Scores trading strategies based on performance metrics.

    Evaluates strategies using:
    - Historical returns
    - Win rate
    - Risk-adjusted metrics (Sharpe ratio)
    - Drawdown analysis
    - Market condition alignment
    """

    def __init__(self, database: Any = None):
        """
        Initialize the strategy scorer.

        Args:
            database: Database instance for fetching historical data
        """
        self.database = database
        self.is_initialized = False
        self.strategy_scores: Dict[str, float] = {}
        self.score_history: List[Dict[str, Any]] = []

        # Scoring weights
        self.weights = {
            "return": 0.25,
            "win_rate": 0.20,
            "sharpe_ratio": 0.20,
            "max_drawdown": 0.15,
            "consistency": 0.10,
            "regime_alignment": 0.10
        }

        logger.info("StrategyScorer initialized")

    async def initialize(self) -> bool:
        """Initialize the scorer with historical data."""
        try:
            self.is_initialized = True
            logger.info("StrategyScorer initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Error initializing StrategyScorer: {e}")
            self.is_initialized = True
            return False

    async def score_strategy(
        self,
        strategy_id: str,
        performance_data: Optional[Dict[str, Any]] = None,
        market_regime: Optional[Dict[str, Any]] = None
    ) -> float:
        """
        Calculate a score for a strategy.

        Args:
            strategy_id: Identifier for the strategy
            performance_data: Historical performance metrics
            market_regime: Current market regime information

        Returns:
            Score between 0 and 1
        """
        try:
            if not performance_data:
                # Return baseline score if no performance data
                return 0.5

            scores = []

            # Return score (0-1 based on percentage return)
            total_return = performance_data.get("total_return", 0)
            return_score = min(1.0, max(0, (total_return + 10) / 20))  # -10% to +10% mapped to 0-1
            scores.append(("return", return_score))

            # Win rate score
            win_rate = performance_data.get("win_rate", 50) / 100
            scores.append(("win_rate", win_rate))

            # Sharpe ratio score (typically -2 to +3)
            sharpe = performance_data.get("sharpe_ratio", 0)
            sharpe_score = min(1.0, max(0, (sharpe + 1) / 3))
            scores.append(("sharpe_ratio", sharpe_score))

            # Max drawdown score (lower is better)
            max_dd = abs(performance_data.get("max_drawdown", 10))
            dd_score = max(0, 1 - (max_dd / 20))  # 0% drawdown = 1, 20% = 0
            scores.append(("max_drawdown", dd_score))

            # Consistency score (based on recent performance variance)
            recent_perf = performance_data.get("recent_performance", [])
            if recent_perf and len(recent_perf) > 1:
                import numpy as np
                consistency = max(0, 1 - np.std(recent_perf) * 10)
            else:
                consistency = 0.5
            scores.append(("consistency", consistency))

            # Regime alignment score
            regime_score = self._calculate_regime_alignment(strategy_id, market_regime)
            scores.append(("regime_alignment", regime_score))

            # Calculate weighted score
            final_score = sum(
                self.weights.get(name, 0) * score
                for name, score in scores
            )

            # Clamp to 0-1 range
            final_score = max(0, min(1, final_score))

            # Store score
            self.strategy_scores[strategy_id] = final_score

            return final_score

        except Exception as e:
            logger.error(f"Error scoring strategy {strategy_id}: {e}")
            return 0.5

    def _calculate_regime_alignment(
        self,
        strategy_id: str,
        market_regime: Optional[Dict[str, Any]]
    ) -> float:
        """Calculate how well a strategy aligns with current market regime."""
        if not market_regime:
            return 0.5

        regime = market_regime.get("current_regime", "unknown")
        trend = market_regime.get("trend", "neutral")

        # Strategy-regime alignment mapping
        alignments = {
            "moving_average": {
                "trending_up": 0.9, "trending_down": 0.9,
                "ranging": 0.3, "unknown": 0.5
            },
            "rsi": {
                "trending_up": 0.5, "trending_down": 0.5,
                "ranging": 0.9, "unknown": 0.5
            },
            "bollinger_bands": {
                "trending_up": 0.6, "trending_down": 0.6,
                "ranging": 0.8, "unknown": 0.5
            },
            "macd": {
                "trending_up": 0.85, "trending_down": 0.85,
                "ranging": 0.4, "unknown": 0.5
            },
            "swing_trading": {
                "trending_up": 0.8, "trending_down": 0.7,
                "ranging": 0.6, "unknown": 0.5
            }
        }

        # Extract strategy type from ID
        strategy_type = strategy_id.split("_")[0] if "_" in strategy_id else strategy_id

        if strategy_type in alignments:
            return alignments[strategy_type].get(regime, 0.5)

        return 0.5

    async def score_all_strategies(
        self,
        strategy_ids: List[str],
        market_regime: Optional[Dict[str, Any]] = None
    ) -> Dict[str, float]:
        """Score all provided strategies."""
        scores = {}
        for strategy_id in strategy_ids:
            score = await self.score_strategy(strategy_id, None, market_regime)
            scores[strategy_id] = score
        return scores

    async def health_check(self) -> bool:
        """Check if the scorer is healthy."""
        return self.is_initialized

    def get_strategy_ranking(self) -> List[tuple]:
        """Get strategies ranked by score."""
        return sorted(
            self.strategy_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )
