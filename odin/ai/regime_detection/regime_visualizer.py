"""
Regime Detection Visualization for Dashboard Integration
"""

import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd


class RegimeVisualizer:
    """Creates visualizations and data for regime detection dashboard"""

    def __init__(self, regime_detector):
        self.regime_detector = regime_detector

    def get_regime_timeline_data(self, days: int = 30) -> Dict[str, Any]:
        """Get timeline data for regime visualization"""
        try:
            regime_history = self.regime_detector.get_regime_history(days=days)

            if not regime_history:
                return {"timeline": [], "summary": "No data"}

            # Prepare timeline data for frontend charting
            timeline_data = []
            for entry in regime_history:
                timeline_data.append(
                    {
                        "timestamp": entry["timestamp"].isoformat(),
                        "regime": entry["regime"],
                        "confidence": round(entry["confidence"], 3),
                        "color": self._get_regime_color(entry["regime"]),
                    }
                )

            # Calculate regime distribution
            regime_counts = {}
            total_time = timedelta(0)

            for i in range(len(regime_history) - 1):
                current = regime_history[i]
                next_entry = regime_history[i + 1]

                regime = current["regime"]
                duration = next_entry["timestamp"] - current["timestamp"]

                if regime not in regime_counts:
                    regime_counts[regime] = timedelta(0)
                regime_counts[regime] += duration
                total_time += duration

            # Convert to percentages
            regime_distribution = {}
            if total_time.total_seconds() > 0:
                for regime, duration in regime_counts.items():
                    percentage = (
                        duration.total_seconds() / total_time.total_seconds()
                    ) * 100
                    regime_distribution[regime] = round(percentage, 1)

            return {
                "timeline": timeline_data,
                "distribution": regime_distribution,
                "total_periods": len(regime_history),
                "date_range": {
                    "start": regime_history[0]["timestamp"].isoformat(),
                    "end": regime_history[-1]["timestamp"].isoformat(),
                },
            }

        except Exception as e:
            return {"error": str(e)}

    def get_regime_transition_matrix(self, days: int = 90) -> Dict[str, Any]:
        """Get regime transition probabilities for visualization"""
        try:
            regime_history = self.regime_detector.get_regime_history(days=days)

            if len(regime_history) < 2:
                return {"matrix": {}, "summary": "Insufficient data"}

            # Count transitions
            transitions = {}

            for i in range(len(regime_history) - 1):
                from_regime = regime_history[i]["regime"]
                to_regime = regime_history[i + 1]["regime"]

                if from_regime not in transitions:
                    transitions[from_regime] = {}

                if to_regime not in transitions[from_regime]:
                    transitions[from_regime][to_regime] = 0

                transitions[from_regime][to_regime] += 1

            # Convert to probabilities
            transition_matrix = {}
            for from_regime, to_regimes in transitions.items():
                total_transitions = sum(to_regimes.values())
                transition_matrix[from_regime] = {}

                for to_regime, count in to_regimes.items():
                    probability = count / total_transitions
                    transition_matrix[from_regime][to_regime] = round(probability, 3)

            return {
                "matrix": transition_matrix,
                "total_transitions": sum(
                    sum(to_regimes.values()) for to_regimes in transitions.values()
                ),
                "analysis_period": f"{days} days",
            }

        except Exception as e:
            return {"error": str(e)}

    def get_confidence_analytics(self) -> Dict[str, Any]:
        """Get confidence score analytics"""
        try:
            regime_history = self.regime_detector.get_regime_history(days=30)

            if not regime_history:
                return {"analytics": {}, "summary": "No data"}

            # Calculate confidence statistics by regime
            regime_confidence = {}

            for entry in regime_history:
                regime = entry["regime"]
                confidence = entry["confidence"]

                if regime not in regime_confidence:
                    regime_confidence[regime] = []

                regime_confidence[regime].append(confidence)

            # Calculate statistics
            confidence_stats = {}
            for regime, confidences in regime_confidence.items():
                confidence_stats[regime] = {
                    "avg_confidence": round(np.mean(confidences), 3),
                    "min_confidence": round(np.min(confidences), 3),
                    "max_confidence": round(np.max(confidences), 3),
                    "std_confidence": round(np.std(confidences), 3),
                    "sample_count": len(confidences),
                }

            # Overall confidence trend
            recent_confidences = [entry["confidence"] for entry in regime_history[-10:]]
            confidence_trend = "stable"

            if len(recent_confidences) >= 3:
                if all(
                    recent_confidences[i] < recent_confidences[i + 1]
                    for i in range(len(recent_confidences) - 1)
                ):
                    confidence_trend = "increasing"
                elif all(
                    recent_confidences[i] > recent_confidences[i + 1]
                    for i in range(len(recent_confidences) - 1)
                ):
                    confidence_trend = "decreasing"

            return {
                "regime_confidence": confidence_stats,
                "overall_trend": confidence_trend,
                "recent_avg": (
                    round(np.mean(recent_confidences), 3) if recent_confidences else 0
                ),
                "analysis_summary": f"Analyzed {len(regime_history)} regime detections",
            }

        except Exception as e:
            return {"error": str(e)}

    def _get_regime_color(self, regime: str) -> str:
        """Get color code for regime visualization"""
        color_map = {
            "bull_trending": "#22c55e",  # Green
            "bear_trending": "#ef4444",  # Red
            "sideways": "#6366f1",  # Blue
            "high_volatility": "#f59e0b",  # Orange
            "crisis": "#dc2626",  # Dark Red
            "unknown": "#6b7280",  # Gray
        }
        return color_map.get(regime, "#6b7280")
