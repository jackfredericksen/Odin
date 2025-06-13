"""
AI Strategy Selector

Intelligent strategy selection system that uses market regime detection,
strategy performance scoring, and ML models to select optimal trading strategies.

File: odin/ai/strategy_selection/ai_strategy_selector.py
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import numpy as np

from ...core.models import PriceData
from ..regime_detection.regime_detector import RegimeDetector
from .strategy_scorer import StrategyScorer

logger = logging.getLogger(__name__)


class AIStrategySelector:
    """
    AI-powered strategy selection system.

    Combines market regime detection with strategy performance analysis
    to intelligently select the optimal trading strategy for current conditions.
    """

    def __init__(
        self, regime_detector: RegimeDetector, strategy_scorer: StrategyScorer
    ):
        """
        Initialize AI strategy selector.

        Args:
            regime_detector: Market regime detection component
            strategy_scorer: Strategy performance scoring component
        """
        self.regime_detector = regime_detector
        self.strategy_scorer = strategy_scorer

        # Strategy-regime compatibility matrix
        self.strategy_regime_matrix = {
            "moving_average": {
                "trending_bullish": 0.9,
                "trending_bearish": 0.9,
                "ranging": 0.4,
                "volatile": 0.3,
                "breakout": 0.8,
            },
            "rsi": {
                "trending_bullish": 0.6,
                "trending_bearish": 0.6,
                "ranging": 0.8,
                "volatile": 0.7,
                "breakout": 0.5,
            },
            "bollinger_bands": {
                "trending_bullish": 0.5,
                "trending_bearish": 0.5,
                "ranging": 0.9,
                "volatile": 0.8,
                "breakout": 0.6,
            },
            "macd": {
                "trending_bullish": 0.8,
                "trending_bearish": 0.8,
                "ranging": 0.5,
                "volatile": 0.4,
                "breakout": 0.7,
            },
            "swing_trading": {
                "trending_bullish": 0.7,
                "trending_bearish": 0.7,
                "ranging": 0.9,
                "volatile": 0.6,
                "breakout": 0.8,
            },
        }

        # Weighting factors for selection
        self.weights = {
            "regime_compatibility": 0.3,
            "recent_performance": 0.4,
            "risk_adjusted_return": 0.2,
            "market_conditions": 0.1,
        }

        self.logger = logging.getLogger(__name__)
        self.logger.info("AI Strategy Selector initialized")

    async def select_optimal_strategy(
        self, price_data: List[PriceData], available_strategies: List[str]
    ) -> Dict[str, Any]:
        """
        Select the optimal strategy based on current market conditions.

        Args:
            price_data: Recent price data for analysis
            available_strategies: List of available strategy IDs

        Returns:
            Dictionary with selected strategy and reasoning
        """
        try:
            # Detect current market regime
            regime_result = await self.regime_detector.detect_regime(price_data)

            # Score all available strategies
            strategy_scores = {}
            detailed_analysis = {}

            for strategy_id in available_strategies:
                try:
                    # Extract strategy type from ID
                    strategy_type = self._extract_strategy_type(strategy_id)

                    # Calculate comprehensive score
                    score_result = await self._calculate_strategy_score(
                        strategy_id, strategy_type, regime_result, price_data
                    )

                    strategy_scores[strategy_id] = score_result["total_score"]
                    detailed_analysis[strategy_id] = score_result["breakdown"]

                except Exception as e:
                    self.logger.warning(f"Error scoring strategy {strategy_id}: {e}")
                    strategy_scores[strategy_id] = 0.0
                    detailed_analysis[strategy_id] = {"error": str(e)}

            # Select best strategy
            if strategy_scores:
                best_strategy = max(strategy_scores.items(), key=lambda x: x[1])
                best_strategy_id = best_strategy[0]
                best_score = best_strategy[1]
            else:
                # Fallback
                best_strategy_id = (
                    available_strategies[0] if available_strategies else None
                )
                best_score = 0.5

            # Generate selection reasoning
            reasoning = self._generate_selection_reasoning(
                best_strategy_id,
                regime_result,
                detailed_analysis.get(best_strategy_id, {}),
            )

            return {
                "strategy_id": best_strategy_id,
                "confidence": best_score,
                "market_regime": regime_result,
                "all_scores": strategy_scores,
                "detailed_analysis": detailed_analysis,
                "reasoning": reasoning,
            }

        except Exception as e:
            self.logger.error(f"Error in strategy selection: {e}")
            return {
                "strategy_id": (
                    available_strategies[0] if available_strategies else None
                ),
                "confidence": 0.1,
                "market_regime": {"current_regime": "unknown", "confidence": 0.0},
                "all_scores": {},
                "detailed_analysis": {},
                "reasoning": f"Error in selection: {str(e)}",
            }

    async def _calculate_strategy_score(
        self,
        strategy_id: str,
        strategy_type: str,
        regime_result: Dict[str, Any],
        price_data: List[PriceData],
    ) -> Dict[str, Any]:
        """Calculate comprehensive score for a strategy."""
        try:
            # Get regime compatibility score
            regime_score = self._get_regime_compatibility_score(
                strategy_type, regime_result
            )

            # Get performance-based scores
            performance_scores = await self.strategy_scorer.calculate_strategy_scores(
                strategy_id, price_data
            )

            # Get market condition adjustments
            market_condition_score = self._calculate_market_condition_score(
                strategy_type, price_data
            )

            # Calculate weighted total score
            total_score = (
                regime_score * self.weights["regime_compatibility"]
                + performance_scores.get("recent_performance", 0.5)
                * self.weights["recent_performance"]
                + performance_scores.get("risk_adjusted_return", 0.5)
                * self.weights["risk_adjusted_return"]
                + market_condition_score * self.weights["market_conditions"]
            )

            # Ensure score is between 0 and 1
            total_score = max(0.0, min(1.0, total_score))

            return {
                "total_score": total_score,
                "breakdown": {
                    "regime_compatibility": regime_score,
                    "recent_performance": performance_scores.get(
                        "recent_performance", 0.5
                    ),
                    "risk_adjusted_return": performance_scores.get(
                        "risk_adjusted_return", 0.5
                    ),
                    "market_conditions": market_condition_score,
                    "performance_details": performance_scores,
                },
            }

        except Exception as e:
            self.logger.error(
                f"Error calculating strategy score for {strategy_id}: {e}"
            )
            return {"total_score": 0.0, "breakdown": {"error": str(e)}}

    def _get_regime_compatibility_score(
        self, strategy_type: str, regime_result: Dict[str, Any]
    ) -> float:
        """Get compatibility score between strategy and current market regime."""
        try:
            current_regime = regime_result.get("current_regime", "unknown")
            regime_confidence = regime_result.get("confidence", 0.0)

            if strategy_type not in self.strategy_regime_matrix:
                return 0.5  # Default neutral score

            # Get base compatibility score
            base_score = self.strategy_regime_matrix[strategy_type].get(
                current_regime, 0.5
            )

            # Adjust by regime confidence
            confidence_adjusted_score = base_score * regime_confidence + 0.5 * (
                1 - regime_confidence
            )

            return confidence_adjusted_score

        except Exception as e:
            self.logger.error(f"Error calculating regime compatibility: {e}")
            return 0.5

    def _calculate_market_condition_score(
        self, strategy_type: str, price_data: List[PriceData]
    ) -> float:
        """Calculate score based on current market conditions."""
        try:
            if len(price_data) < 20:
                return 0.5

            # Extract price series
            prices = [p.price for p in price_data[-20:]]
            volumes = [p.volume for p in price_data[-20:] if p.volume]

            # Calculate market metrics
            price_volatility = np.std(prices) / np.mean(prices) if prices else 0
            price_trend = (
                (prices[-1] - prices[0]) / prices[0] if len(prices) >= 2 else 0
            )

            # Volume analysis
            avg_volume = np.mean(volumes) if volumes else 1000
            recent_volume = volumes[-1] if volumes else 1000
            volume_ratio = recent_volume / avg_volume if avg_volume > 0 else 1

            # Strategy-specific scoring
            score = 0.5  # Base score

            if strategy_type == "moving_average":
                # Favors trending markets with moderate volatility
                if abs(price_trend) > 0.02:  # Strong trend
                    score += 0.3
                if 0.01 < price_volatility < 0.05:  # Moderate volatility
                    score += 0.2

            elif strategy_type == "rsi":
                # Favors ranging markets with higher volatility
                if abs(price_trend) < 0.015:  # Ranging
                    score += 0.2
                if price_volatility > 0.02:  # Higher volatility
                    score += 0.3

            elif strategy_type == "bollinger_bands":
                # Favors volatile, ranging markets
                if price_volatility > 0.025:  # High volatility
                    score += 0.3
                if abs(price_trend) < 0.01:  # Ranging
                    score += 0.2

            elif strategy_type == "swing_trading":
                # Favors markets with clear swings and moderate volatility
                if 0.015 < price_volatility < 0.04:  # Moderate volatility
                    score += 0.3
                if volume_ratio > 1.2:  # Higher volume
                    score += 0.2

            elif strategy_type == "macd":
                # Favors trending markets with momentum
                if abs(price_trend) > 0.01:  # Trending
                    score += 0.2
                if volume_ratio > 1.1:  # Volume confirmation
                    score += 0.3

            return max(0.0, min(1.0, score))

        except Exception as e:
            self.logger.error(f"Error calculating market condition score: {e}")
            return 0.5

    def _extract_strategy_type(self, strategy_id: str) -> str:
        """Extract strategy type from strategy ID."""
        # Assuming strategy IDs are formatted as "type_timestamp"
        try:
            return strategy_id.split("_")[0]
        except:
            return "unknown"

    def _generate_selection_reasoning(
        self,
        selected_strategy: str,
        regime_result: Dict[str, Any],
        analysis: Dict[str, Any],
    ) -> str:
        """Generate human-readable reasoning for strategy selection."""
        try:
            if not selected_strategy:
                return "No strategy could be selected due to insufficient data"

            strategy_type = self._extract_strategy_type(selected_strategy)
            regime = regime_result.get("current_regime", "unknown")
            regime_confidence = regime_result.get("confidence", 0.0)

            reasoning_parts = []

            # Market regime reasoning
            if regime_confidence > 0.7:
                reasoning_parts.append(f"High confidence {regime} market detected")
            elif regime_confidence > 0.5:
                reasoning_parts.append(f"Moderate confidence {regime} market")
            else:
                reasoning_parts.append("Uncertain market conditions")

            # Strategy suitability
            if strategy_type in self.strategy_regime_matrix:
                compatibility = self.strategy_regime_matrix[strategy_type].get(
                    regime, 0.5
                )
                if compatibility > 0.7:
                    reasoning_parts.append(
                        f"{strategy_type} strategy well-suited for {regime} conditions"
                    )
                elif compatibility > 0.5:
                    reasoning_parts.append(
                        f"{strategy_type} strategy moderately suited for current conditions"
                    )
                else:
                    reasoning_parts.append(
                        f"{strategy_type} strategy selected despite regime mismatch due to strong performance"
                    )

            # Performance reasoning
            if "recent_performance" in analysis:
                perf = analysis["recent_performance"]
                if perf > 0.7:
                    reasoning_parts.append("strong recent performance")
                elif perf > 0.5:
                    reasoning_parts.append("solid recent performance")
                else:
                    reasoning_parts.append("performance concerns noted")

            return " - ".join(reasoning_parts)

        except Exception as e:
            return f"Strategy selected with limited analysis: {str(e)}"

    async def get_strategy_recommendations(
        self,
        price_data: List[PriceData],
        available_strategies: List[str],
        top_n: int = 3,
    ) -> List[Dict[str, Any]]:
        """Get top N strategy recommendations with detailed analysis."""
        try:
            selection_result = await self.select_optimal_strategy(
                price_data, available_strategies
            )

            # Sort strategies by score
            sorted_strategies = sorted(
                selection_result["all_scores"].items(), key=lambda x: x[1], reverse=True
            )

            recommendations = []
            for i, (strategy_id, score) in enumerate(sorted_strategies[:top_n]):
                strategy_type = self._extract_strategy_type(strategy_id)
                analysis = selection_result["detailed_analysis"].get(strategy_id, {})

                recommendations.append(
                    {
                        "rank": i + 1,
                        "strategy_id": strategy_id,
                        "strategy_type": strategy_type,
                        "score": round(score, 3),
                        "confidence": (
                            "High"
                            if score > 0.7
                            else "Medium" if score > 0.5 else "Low"
                        ),
                        "analysis": analysis,
                        "recommended": i == 0,
                    }
                )

            return recommendations

        except Exception as e:
            self.logger.error(f"Error generating strategy recommendations: {e}")
            return []

    def update_strategy_regime_matrix(self, updates: Dict[str, Dict[str, float]]):
        """Update the strategy-regime compatibility matrix."""
        try:
            for strategy_type, regime_scores in updates.items():
                if strategy_type in self.strategy_regime_matrix:
                    self.strategy_regime_matrix[strategy_type].update(regime_scores)
                else:
                    self.strategy_regime_matrix[strategy_type] = regime_scores

            self.logger.info("Strategy-regime matrix updated")

        except Exception as e:
            self.logger.error(f"Error updating strategy-regime matrix: {e}")

    def update_selection_weights(self, new_weights: Dict[str, float]):
        """Update the weighting factors for strategy selection."""
        try:
            # Normalize weights to sum to 1.0
            total_weight = sum(new_weights.values())
            if total_weight > 0:
                normalized_weights = {
                    k: v / total_weight for k, v in new_weights.items()
                }
                self.weights.update(normalized_weights)
                self.logger.info(f"Updated selection weights: {self.weights}")

        except Exception as e:
            self.logger.error(f"Error updating selection weights: {e}")

    async def analyze_selection_history(self, hours: int = 24) -> Dict[str, Any]:
        """Analyze recent strategy selection patterns."""
        try:
            # This would analyze historical selections from database
            # For now, return placeholder analysis
            return {
                "total_selections": 0,
                "most_selected_strategy": "swing_trading",
                "selection_frequency": {},
                "regime_distribution": {},
                "average_confidence": 0.75,
                "recommendations": [
                    "Strategy selection showing good diversity",
                    "Market regime detection confidence stable",
                ],
            }

        except Exception as e:
            self.logger.error(f"Error analyzing selection history: {e}")
            return {"error": str(e)}

    def get_configuration(self) -> Dict[str, Any]:
        """Get current AI selector configuration."""
        return {
            "strategy_regime_matrix": self.strategy_regime_matrix,
            "selection_weights": self.weights,
            "supported_regimes": list(
                set().union(
                    *[
                        regime_dict.keys()
                        for regime_dict in self.strategy_regime_matrix.values()
                    ]
                )
            ),
            "supported_strategies": list(self.strategy_regime_matrix.keys()),
        }
