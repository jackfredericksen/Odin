"""
Strategy Performance Scorer

Evaluates trading strategy performance using multiple metrics including
returns, risk-adjusted performance, consistency, and market adaptability.

File: odin/ai/strategy_selection/strategy_scorer.py
"""

import logging
from datetime import datetime, timedelta, timezone
from statistics import mean, stdev
from typing import Any, Dict, List, Optional

import numpy as np

from ...core.database import Database
from ...core.models import PriceData

logger = logging.getLogger(__name__)


class StrategyScorer:
    """
    Comprehensive strategy performance scoring system.

    Evaluates strategies across multiple dimensions to provide
    accurate performance assessments for AI-driven selection.
    """

    def __init__(self, database: Database):
        """
        Initialize strategy scorer.

        Args:
            database: Database instance for accessing historical data
        """
        self.database = database

        # Scoring weights for different metrics
        self.metric_weights = {
            "returns": 0.25,
            "consistency": 0.20,
            "risk_adjusted": 0.25,
            "drawdown": 0.15,
            "win_rate": 0.15,
        }

        # Performance thresholds
        self.thresholds = {
            "excellent_return": 0.05,  # 5% return threshold
            "good_return": 0.02,  # 2% return threshold
            "excellent_sharpe": 1.5,  # Sharpe ratio threshold
            "good_sharpe": 1.0,
            "max_acceptable_drawdown": 0.15,  # 15% max drawdown
            "min_win_rate": 0.45,  # 45% minimum win rate
        }

        # Cache for performance data
        self.performance_cache: Dict[str, Dict[str, Any]] = {}
        self.cache_expiry: Dict[str, datetime] = {}
        self.cache_duration = timedelta(minutes=10)

        self.logger = logging.getLogger(__name__)

    async def initialize(self):
        """Initialize the scorer with historical data."""
        try:
            self.logger.info("Strategy scorer initialized")
        except Exception as e:
            self.logger.error(f"Error initializing strategy scorer: {e}")

    async def calculate_strategy_scores(
        self, strategy_id: str, price_data: List[PriceData]
    ) -> Dict[str, float]:
        """
        Calculate comprehensive performance scores for a strategy.

        Args:
            strategy_id: Strategy identifier
            price_data: Recent market data for context

        Returns:
            Dictionary of performance scores
        """
        try:
            # Check cache first
            if self._is_cache_valid(strategy_id):
                return self.performance_cache[strategy_id]

            # Get historical performance data
            performance_data = await self._get_strategy_performance_data(strategy_id)

            if not performance_data:
                # Return neutral scores if no data available
                default_scores = {
                    "recent_performance": 0.5,
                    "risk_adjusted_return": 0.5,
                    "consistency_score": 0.5,
                    "drawdown_score": 0.5,
                    "win_rate_score": 0.5,
                    "overall_score": 0.5,
                }
                self._cache_results(strategy_id, default_scores)
                return default_scores

            # Calculate individual metric scores
            scores = {}

            # 1. Recent Performance Score
            scores["recent_performance"] = self._calculate_recent_performance_score(
                performance_data
            )

            # 2. Risk-Adjusted Return Score
            scores["risk_adjusted_return"] = self._calculate_risk_adjusted_score(
                performance_data
            )

            # 3. Consistency Score
            scores["consistency_score"] = self._calculate_consistency_score(
                performance_data
            )

            # 4. Drawdown Score
            scores["drawdown_score"] = self._calculate_drawdown_score(performance_data)

            # 5. Win Rate Score
            scores["win_rate_score"] = self._calculate_win_rate_score(performance_data)

            # 6. Market Adaptability Score
            scores["adaptability_score"] = self._calculate_adaptability_score(
                performance_data, price_data
            )

            # Calculate overall weighted score
            scores["overall_score"] = self._calculate_overall_score(scores)

            # Cache results
            self._cache_results(strategy_id, scores)

            return scores

        except Exception as e:
            self.logger.error(f"Error calculating scores for {strategy_id}: {e}")
            return {
                "recent_performance": 0.3,
                "risk_adjusted_return": 0.3,
                "consistency_score": 0.3,
                "drawdown_score": 0.3,
                "win_rate_score": 0.3,
                "overall_score": 0.3,
            }

    async def _get_strategy_performance_data(
        self, strategy_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get historical performance data for a strategy."""
        try:
            # Get recent trades for this strategy
            trades = self.database.get_recent_trades(limit=100, strategy_id=strategy_id)

            if not trades:
                return None

            # Get recent signals
            signals = self.database.get_recent_signals(
                strategy_id=strategy_id, limit=50
            )

            # Process trade data
            trade_returns = []
            trade_durations = []
            profitable_trades = 0
            total_pnl = 0

            for trade in trades:
                pnl = trade.get("pnl", 0)
                trade_returns.append(pnl / 1000)  # Normalize to percentage
                total_pnl += pnl

                if pnl > 0:
                    profitable_trades += 1

                # Calculate duration if available
                entry_time = trade.get("entry_time")
                exit_time = trade.get("exit_time")
                if entry_time and exit_time:
                    duration = (exit_time - entry_time).total_seconds() / 3600  # hours
                    trade_durations.append(duration)

            # Calculate metrics
            total_trades = len(trades)
            win_rate = profitable_trades / total_trades if total_trades > 0 else 0
            avg_return = mean(trade_returns) if trade_returns else 0
            return_std = stdev(trade_returns) if len(trade_returns) > 1 else 0

            # Calculate Sharpe ratio (simplified)
            sharpe_ratio = avg_return / return_std if return_std > 0 else 0

            # Calculate maximum drawdown
            cumulative_returns = np.cumsum(trade_returns)
            if len(cumulative_returns) > 0:
                peak = np.maximum.accumulate(cumulative_returns)
                drawdowns = (peak - cumulative_returns) / np.maximum(peak, 1e-10)
                max_drawdown = np.max(drawdowns) if len(drawdowns) > 0 else 0
            else:
                max_drawdown = 0

            return {
                "total_trades": total_trades,
                "profitable_trades": profitable_trades,
                "win_rate": win_rate,
                "total_return": sum(trade_returns),
                "avg_return": avg_return,
                "return_std": return_std,
                "sharpe_ratio": sharpe_ratio,
                "max_drawdown": max_drawdown,
                "trade_returns": trade_returns,
                "trade_durations": trade_durations,
                "recent_signals": len(signals),
                "total_pnl": total_pnl,
            }

        except Exception as e:
            self.logger.error(f"Error getting performance data for {strategy_id}: {e}")
            return None

    def _calculate_recent_performance_score(
        self, performance_data: Dict[str, Any]
    ) -> float:
        """Calculate score based on recent performance."""
        try:
            total_return = performance_data.get("total_return", 0)

            # Score based on return thresholds
            if total_return >= self.thresholds["excellent_return"]:
                return 0.9
            elif total_return >= self.thresholds["good_return"]:
                return 0.7
            elif total_return >= 0:
                return 0.6
            elif total_return >= -0.02:  # Small loss acceptable
                return 0.4
            else:
                return 0.2

        except Exception as e:
            self.logger.error(f"Error calculating recent performance score: {e}")
            return 0.5

    def _calculate_risk_adjusted_score(self, performance_data: Dict[str, Any]) -> float:
        """Calculate risk-adjusted performance score."""
        try:
            sharpe_ratio = performance_data.get("sharpe_ratio", 0)

            # Score based on Sharpe ratio
            if sharpe_ratio >= self.thresholds["excellent_sharpe"]:
                return 0.9
            elif sharpe_ratio >= self.thresholds["good_sharpe"]:
                return 0.7
            elif sharpe_ratio >= 0.5:
                return 0.6
            elif sharpe_ratio >= 0:
                return 0.4
            else:
                return 0.2

        except Exception as e:
            self.logger.error(f"Error calculating risk-adjusted score: {e}")
            return 0.5

    def _calculate_consistency_score(self, performance_data: Dict[str, Any]) -> float:
        """Calculate consistency score based on return volatility."""
        try:
            trade_returns = performance_data.get("trade_returns", [])

            if len(trade_returns) < 3:
                return 0.5  # Insufficient data

            # Calculate coefficient of variation
            avg_return = mean(trade_returns)
            return_std = stdev(trade_returns)

            if avg_return == 0:
                return 0.3  # No average return

            cv = abs(return_std / avg_return)

            # Lower coefficient of variation = higher consistency
            if cv <= 0.5:
                return 0.9
            elif cv <= 1.0:
                return 0.7
            elif cv <= 2.0:
                return 0.5
            else:
                return 0.3

        except Exception as e:
            self.logger.error(f"Error calculating consistency score: {e}")
            return 0.5

    def _calculate_drawdown_score(self, performance_data: Dict[str, Any]) -> float:
        """Calculate score based on maximum drawdown."""
        try:
            max_drawdown = performance_data.get("max_drawdown", 0)

            # Score based on drawdown thresholds
            if max_drawdown <= 0.05:  # <= 5% drawdown
                return 0.9
            elif max_drawdown <= 0.10:  # <= 10% drawdown
                return 0.7
            elif max_drawdown <= self.thresholds["max_acceptable_drawdown"]:
                return 0.5
            elif max_drawdown <= 0.25:  # <= 25% drawdown
                return 0.3
            else:
                return 0.1

        except Exception as e:
            self.logger.error(f"Error calculating drawdown score: {e}")
            return 0.5

    def _calculate_win_rate_score(self, performance_data: Dict[str, Any]) -> float:
        """Calculate score based on win rate."""
        try:
            win_rate = performance_data.get("win_rate", 0)

            # Score based on win rate thresholds
            if win_rate >= 0.65:  # >= 65% win rate
                return 0.9
            elif win_rate >= 0.55:  # >= 55% win rate
                return 0.7
            elif win_rate >= self.thresholds["min_win_rate"]:
                return 0.6
            elif win_rate >= 0.35:  # >= 35% win rate
                return 0.4
            else:
                return 0.2

        except Exception as e:
            self.logger.error(f"Error calculating win rate score: {e}")
            return 0.5

    def _calculate_adaptability_score(
        self, performance_data: Dict[str, Any], price_data: List[PriceData]
    ) -> float:
        """Calculate market adaptability score."""
        try:
            # Look at recent performance trend
            trade_returns = performance_data.get("trade_returns", [])

            if len(trade_returns) < 5:
                return 0.5

            # Analyze recent vs older performance
            recent_returns = trade_returns[-10:]  # Last 10 trades
            older_returns = trade_returns[-20:-10] if len(trade_returns) >= 20 else []

            recent_avg = mean(recent_returns) if recent_returns else 0
            older_avg = mean(older_returns) if older_returns else recent_avg

            # Check if strategy is adapting (improving or maintaining performance)
            if recent_avg > older_avg + 0.01:  # Improving
                return 0.8
            elif recent_avg >= older_avg - 0.005:  # Maintaining
                return 0.6
            elif recent_avg >= older_avg - 0.02:  # Slight decline
                return 0.4
            else:  # Significant decline
                return 0.2

        except Exception as e:
            self.logger.error(f"Error calculating adaptability score: {e}")
            return 0.5

    def _calculate_overall_score(self, scores: Dict[str, float]) -> float:
        """Calculate weighted overall performance score."""
        try:
            # Use the main scoring weights
            overall = (
                scores.get("recent_performance", 0.5) * self.metric_weights["returns"]
                + scores.get("consistency_score", 0.5)
                * self.metric_weights["consistency"]
                + scores.get("risk_adjusted_return", 0.5)
                * self.metric_weights["risk_adjusted"]
                + scores.get("drawdown_score", 0.5) * self.metric_weights["drawdown"]
                + scores.get("win_rate_score", 0.5) * self.metric_weights["win_rate"]
            )

            # Apply adaptability as a multiplier
            adaptability = scores.get("adaptability_score", 0.5)
            overall = overall * (
                0.8 + 0.4 * adaptability
            )  # Scale between 0.8x and 1.2x

            return max(0.0, min(1.0, overall))

        except Exception as e:
            self.logger.error(f"Error calculating overall score: {e}")
            return 0.5

    def _is_cache_valid(self, strategy_id: str) -> bool:
        """Check if cached results are still valid."""
        if strategy_id not in self.performance_cache:
            return False

        if strategy_id not in self.cache_expiry:
            return False

        return datetime.now(timezone.utc) < self.cache_expiry[strategy_id]

    def _cache_results(self, strategy_id: str, scores: Dict[str, float]):
        """Cache performance scores."""
        self.performance_cache[strategy_id] = scores
        self.cache_expiry[strategy_id] = (
            datetime.now(timezone.utc) + self.cache_duration
        )

    async def compare_strategies(
        self, strategy_ids: List[str], price_data: List[PriceData]
    ) -> Dict[str, Any]:
        """Compare multiple strategies and rank them."""
        try:
            strategy_comparisons = []

            for strategy_id in strategy_ids:
                scores = await self.calculate_strategy_scores(strategy_id, price_data)

                strategy_comparisons.append(
                    {
                        "strategy_id": strategy_id,
                        "overall_score": scores.get("overall_score", 0.0),
                        "scores": scores,
                    }
                )

            # Sort by overall score
            strategy_comparisons.sort(key=lambda x: x["overall_score"], reverse=True)

            # Add rankings
            for i, strategy in enumerate(strategy_comparisons):
                strategy["rank"] = i + 1

            return {
                "rankings": strategy_comparisons,
                "best_strategy": (
                    strategy_comparisons[0] if strategy_comparisons else None
                ),
                "worst_strategy": (
                    strategy_comparisons[-1] if strategy_comparisons else None
                ),
                "average_score": (
                    mean([s["overall_score"] for s in strategy_comparisons])
                    if strategy_comparisons
                    else 0
                ),
            }

        except Exception as e:
            self.logger.error(f"Error comparing strategies: {e}")
            return {"rankings": [], "best_strategy": None, "worst_strategy": None}

    async def get_performance_insights(self, strategy_id: str) -> List[str]:
        """Generate performance insights for a strategy."""
        try:
            performance_data = await self._get_strategy_performance_data(strategy_id)

            if not performance_data:
                return ["Insufficient data for analysis"]

            insights = []

            # Win rate insights
            win_rate = performance_data.get("win_rate", 0)
            if win_rate > 0.6:
                insights.append(f"Excellent win rate of {win_rate:.1%}")
            elif win_rate < 0.4:
                insights.append(
                    f"Low win rate of {win_rate:.1%} - consider optimization"
                )

            # Return insights
            total_return = performance_data.get("total_return", 0)
            if total_return > 0.05:
                insights.append("Strong positive returns generated")
            elif total_return < -0.02:
                insights.append("Recent losses detected - strategy may need adjustment")

            # Risk insights
            sharpe_ratio = performance_data.get("sharpe_ratio", 0)
            if sharpe_ratio > 1.5:
                insights.append("Excellent risk-adjusted returns")
            elif sharpe_ratio < 0.5:
                insights.append("Poor risk-adjusted performance")

            # Consistency insights
            trade_returns = performance_data.get("trade_returns", [])
            if len(trade_returns) > 5:
                cv = (
                    stdev(trade_returns) / abs(mean(trade_returns))
                    if mean(trade_returns) != 0
                    else float("inf")
                )
                if cv < 1.0:
                    insights.append("Consistent performance across trades")
                elif cv > 3.0:
                    insights.append("High volatility in trade outcomes")

            # Drawdown insights
            max_drawdown = performance_data.get("max_drawdown", 0)
            if max_drawdown > 0.15:
                insights.append(f"High maximum drawdown of {max_drawdown:.1%}")
            elif max_drawdown < 0.05:
                insights.append("Low drawdown - good risk management")

            return (
                insights if insights else ["Strategy performance within normal ranges"]
            )

        except Exception as e:
            self.logger.error(f"Error generating insights for {strategy_id}: {e}")
            return ["Error generating performance insights"]

    def update_scoring_weights(self, new_weights: Dict[str, float]):
        """Update the metric weights for scoring."""
        try:
            # Normalize weights to sum to 1.0
            total_weight = sum(new_weights.values())
            if total_weight > 0:
                normalized_weights = {
                    k: v / total_weight for k, v in new_weights.items()
                }
                self.metric_weights.update(normalized_weights)
                self.logger.info(f"Updated scoring weights: {self.metric_weights}")

                # Clear cache to force recalculation
                self.performance_cache.clear()
                self.cache_expiry.clear()

        except Exception as e:
            self.logger.error(f"Error updating scoring weights: {e}")

    def update_thresholds(self, new_thresholds: Dict[str, float]):
        """Update performance thresholds."""
        try:
            self.thresholds.update(new_thresholds)
            self.logger.info(f"Updated performance thresholds: {self.thresholds}")

            # Clear cache to force recalculation
            self.performance_cache.clear()
            self.cache_expiry.clear()

        except Exception as e:
            self.logger.error(f"Error updating thresholds: {e}")

    async def analyze_strategy_trends(
        self, strategy_id: str, days: int = 7
    ) -> Dict[str, Any]:
        """Analyze performance trends for a strategy over time."""
        try:
            # Get extended trade history
            trades = self.database.get_recent_trades(limit=200, strategy_id=strategy_id)

            if not trades:
                return {"trend": "insufficient_data", "analysis": "No trades available"}

            # Group trades by day
            daily_performance = {}
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)

            for trade in trades:
                trade_date = trade.get("exit_time", datetime.now(timezone.utc))
                if trade_date >= cutoff_date:
                    day_key = trade_date.date()
                    if day_key not in daily_performance:
                        daily_performance[day_key] = []
                    daily_performance[day_key].append(trade.get("pnl", 0))

            if not daily_performance:
                return {
                    "trend": "no_recent_data",
                    "analysis": "No recent trades in specified period",
                }

            # Calculate daily returns
            daily_returns = []
            for day, pnls in daily_performance.items():
                daily_return = sum(pnls) / 1000  # Normalize
                daily_returns.append(daily_return)

            # Analyze trend
            if len(daily_returns) >= 3:
                # Simple linear regression to detect trend
                x = list(range(len(daily_returns)))
                slope = np.polyfit(x, daily_returns, 1)[0]

                if slope > 0.001:
                    trend = "improving"
                elif slope < -0.001:
                    trend = "declining"
                else:
                    trend = "stable"
            else:
                trend = "insufficient_data"

            # Performance statistics
            avg_daily = mean(daily_returns) if daily_returns else 0
            volatility = stdev(daily_returns) if len(daily_returns) > 1 else 0

            return {
                "trend": trend,
                "days_analyzed": len(daily_performance),
                "average_daily_return": round(avg_daily, 4),
                "daily_volatility": round(volatility, 4),
                "total_return": round(sum(daily_returns), 4),
                "best_day": round(max(daily_returns), 4) if daily_returns else 0,
                "worst_day": round(min(daily_returns), 4) if daily_returns else 0,
                "analysis": self._generate_trend_analysis(trend, avg_daily, volatility),
            }

        except Exception as e:
            self.logger.error(f"Error analyzing trends for {strategy_id}: {e}")
            return {"trend": "error", "analysis": f"Error: {str(e)}"}

    def _generate_trend_analysis(
        self, trend: str, avg_return: float, volatility: float
    ) -> str:
        """Generate human-readable trend analysis."""
        analysis_parts = []

        # Trend analysis
        if trend == "improving":
            analysis_parts.append("Strategy showing improving performance trend")
        elif trend == "declining":
            analysis_parts.append("Strategy performance is declining")
        elif trend == "stable":
            analysis_parts.append("Strategy performance is stable")

        # Return analysis
        if avg_return > 0.01:
            analysis_parts.append("with strong positive daily returns")
        elif avg_return > 0:
            analysis_parts.append("with modest positive returns")
        elif avg_return < -0.01:
            analysis_parts.append("with concerning negative returns")

        # Volatility analysis
        if volatility > 0.02:
            analysis_parts.append("but showing high volatility")
        elif volatility < 0.005:
            analysis_parts.append("with low volatility")

        return " ".join(analysis_parts)

    async def health_check(self) -> bool:
        """Check if the strategy scorer is functioning properly."""
        try:
            # Test with dummy data
            dummy_performance = {
                "total_trades": 10,
                "win_rate": 0.6,
                "total_return": 0.03,
                "sharpe_ratio": 1.2,
                "max_drawdown": 0.08,
                "trade_returns": [0.01, -0.005, 0.02, 0.015, -0.01],
            }

            # Test all scoring methods
            recent_score = self._calculate_recent_performance_score(dummy_performance)
            risk_score = self._calculate_risk_adjusted_score(dummy_performance)
            consistency_score = self._calculate_consistency_score(dummy_performance)

            # Check if scores are reasonable
            return (
                0 <= recent_score <= 1
                and 0 <= risk_score <= 1
                and 0 <= consistency_score <= 1
            )

        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return False

    def get_scoring_configuration(self) -> Dict[str, Any]:
        """Get current scoring configuration."""
        return {
            "metric_weights": self.metric_weights,
            "performance_thresholds": self.thresholds,
            "cache_duration_minutes": self.cache_duration.total_seconds() / 60,
            "cached_strategies": list(self.performance_cache.keys()),
        }

    def clear_cache(self):
        """Clear all cached performance data."""
        self.performance_cache.clear()
        self.cache_expiry.clear()
        self.logger.info("Performance cache cleared")
