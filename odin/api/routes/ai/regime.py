"""
COMPLETE API endpoints for AI regime detection and analytics
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, Dict, Any, List
import pandas as pd
from datetime import datetime, timedelta
import logging

# Import Odin components
from odin.api.dependencies import get_data_collector, get_database
from odin.core.models import APIResponse
from odin.ai.regime_detection.regime_detector import MarketRegimeDetector
from odin.ai.regime_detection.regime_visualizer import RegimeVisualizer
from odin.ai.regime_detection.market_states import get_all_regime_info, get_regime_characteristics, MarketRegime
from odin.ai.strategy_selection.adaptive_manager import AdaptiveStrategyManager
from odin.strategies.ai_adaptive import AIAdaptiveStrategy

router = APIRouter(prefix="/ai", tags=["AI Regime Detection"])
logger = logging.getLogger(__name__)

# Global AI instances (would be managed by dependency injection in production)
regime_detector = MarketRegimeDetector()
strategy_manager = AdaptiveStrategyManager()
ai_strategy = AIAdaptiveStrategy()
regime_visualizer = RegimeVisualizer(regime_detector)

@router.get("/regime/current")
async def get_current_regime(
    db = Depends(get_database)
) -> APIResponse:
    """
    Get current market regime detection
    
    Returns:
        Current regime, confidence score, and regime statistics
    """
    try:
        # Get recent market data
        data_collector = get_data_collector()
        recent_data = await data_collector.get_recent_data(hours=24)
        
        if recent_data.empty:
            raise HTTPException(status_code=404, detail="No recent market data available")
        
        # Detect current regime
        regime, confidence = regime_detector.detect_regime(recent_data)
        
        # Get regime statistics
        regime_stats = regime_detector.get_regime_statistics()
        
        # Get regime characteristics
        regime_info = get_regime_characteristics(MarketRegime(regime)) if regime != "unknown" else None
        
        response_data = {
            "current_regime": regime,
            "confidence": round(confidence, 4),
            "regime_characteristics": {
                "description": regime_info.description if regime_info else "Unknown regime",
                "risk_level": regime_info.risk_level if regime_info else "Unknown",
                "trading_approach": regime_info.trading_approach if regime_info else "Cautious",
                "typical_indicators": regime_info.typical_indicators if regime_info else []
            },
            "regime_statistics": regime_stats,
            "market_context": {
                "last_updated": datetime.now().isoformat(),
                "data_points_analyzed": len(recent_data),
                "analysis_timeframe": "24 hours"
            }
        }
        
        return APIResponse(
            success=True,
            data=response_data,
            message=f"Current regime: {regime} (confidence: {confidence:.2%})"
        )
        
    except Exception as e:
        logger.error(f"Current regime detection failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/regime/history")
async def get_regime_history(
    days: int = Query(30, ge=1, le=365, description="Number of days of history"),
    include_transitions: bool = Query(True, description="Include transition analysis"),
    db = Depends(get_database)
) -> APIResponse:
    """
    Get historical regime detection data with transition analysis
    """
    try:
        # Get regime history
        regime_history = regime_detector.get_regime_history(days=days)
        
        if not regime_history:
            return APIResponse(
                success=True,
                data={"regime_history": [], "summary": "No regime history available"},
                message="No regime detection history found"
            )
        
        # Calculate regime transition statistics
        transitions = []
        for i in range(1, len(regime_history)):
            prev_regime = regime_history[i-1]['regime']
            curr_regime = regime_history[i]['regime']
            
            if prev_regime != curr_regime:
                transitions.append({
                    "timestamp": regime_history[i]['timestamp'].isoformat(),
                    "from_regime": prev_regime,
                    "to_regime": curr_regime,
                    "confidence": regime_history[i]['confidence'],
                    "duration_since_last": (regime_history[i]['timestamp'] - regime_history[i-1]['timestamp']).total_seconds() / 3600  # hours
                })
        
        # Calculate regime distribution
        regime_counts = {}
        total_duration = timedelta(0)
        
        for i in range(len(regime_history) - 1):
            regime = regime_history[i]['regime']
            duration = regime_history[i+1]['timestamp'] - regime_history[i]['timestamp']
            
            if regime not in regime_counts:
                regime_counts[regime] = timedelta(0)
            regime_counts[regime] += duration
            total_duration += duration
        
        # Convert to percentages
        regime_distribution = {}
        if total_duration.total_seconds() > 0:
            for regime, duration in regime_counts.items():
                percentage = (duration.total_seconds() / total_duration.total_seconds()) * 100
                regime_distribution[regime] = round(percentage, 2)
        
        # Transition matrix if requested
        transition_data = {}
        if include_transitions:
            transition_data = regime_visualizer.get_regime_transition_matrix(days=days)
        
        response_data = {
            "regime_history": [
                {
                    "timestamp": entry['timestamp'].isoformat(),
                    "regime": entry['regime'],
                    "confidence": round(entry['confidence'], 4)
                }
                for entry in regime_history
            ],
            "regime_transitions": transitions,
            "regime_distribution": regime_distribution,
            "transition_analysis": transition_data,
            "summary": {
                "total_detections": len(regime_history),
                "unique_regimes": len(regime_counts),
                "transition_count": len(transitions),
                "most_common_regime": max(regime_counts.items(), key=lambda x: x[1].total_seconds())[0] if regime_counts else None,
                "analysis_period": f"{days} days",
                "avg_regime_duration": round(total_duration.total_seconds() / len(regime_counts) / 3600, 1) if regime_counts else 0  # hours
            }
        }
        
        return APIResponse(
            success=True,
            data=response_data,
            message=f"Retrieved {len(regime_history)} regime detections with {len(transitions)} transitions"
        )
        
    except Exception as e:
        logger.error(f"Regime history retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/regime/info")
async def get_regime_definitions() -> APIResponse:
    """
    Get comprehensive information about all market regimes
    
    Returns:
        Detailed definitions and characteristics of all regime types
    """
    try:
        regime_info = get_all_regime_info()
        
        # Add additional context
        enhanced_info = {}
        for regime_name, info in regime_info.items():
            enhanced_info[regime_name] = {
                **info,
                "color_code": regime_visualizer._get_regime_color(regime_name),
                "recommended_strategies": _get_recommended_strategies(regime_name),
                "risk_guidelines": _get_risk_guidelines(regime_name)
            }
        
        return APIResponse(
            success=True,
            data={
                "regime_definitions": enhanced_info,
                "total_regimes": len(enhanced_info),
                "classification_method": "AI-powered using HMM and GMM models"
            },
            message="Retrieved definitions for all market regimes"
        )
        
    except Exception as e:
        logger.error(f"Regime definitions retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/regime/visualization")
async def get_regime_visualization_data(
    days: int = Query(30, ge=7, le=90, description="Days of data for visualization"),
    db = Depends(get_database)
) -> APIResponse:
    """
    Get data formatted for regime visualization charts
    
    Returns:
        Chart-ready data for regime timeline and distribution visualization
    """
    try:
        # Get timeline data
        timeline_data = regime_visualizer.get_regime_timeline_data(days=days)
        
        # Get confidence analytics
        confidence_data = regime_visualizer.get_confidence_analytics()
        
        # Get transition matrix
        transition_data = regime_visualizer.get_regime_transition_matrix(days=days)
        
        response_data = {
            "timeline_chart": timeline_data,
            "confidence_analytics": confidence_data,
            "transition_matrix": transition_data,
            "chart_config": {
                "regime_colors": {
                    regime: regime_visualizer._get_regime_color(regime)
                    for regime in ["bull_trending", "bear_trending", "sideways", "high_volatility", "crisis"]
                },
                "recommended_chart_types": ["timeline", "pie_chart", "heatmap"],
                "update_frequency": "real-time"
            }
        }
        
        return APIResponse(
            success=True,
            data=response_data,
            message=f"Visualization data prepared for {days} days"
        )
        
    except Exception as e:
        logger.error(f"Visualization data preparation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def _get_recommended_strategies(regime: str) -> List[str]:
    """Get recommended strategies for a regime"""
    strategy_map = {
        "bull_trending": ["Moving Average", "MACD", "Momentum"],
        "bear_trending": ["RSI Oversold", "Short MA", "Defensive"],
        "sideways": ["RSI Mean Reversion", "Bollinger Bands", "Range Trading"],
        "high_volatility": ["Volatility Breakout", "Reduced Position Size"],
        "crisis": ["Cash Position", "Risk Off", "Capital Preservation"]
    }
    return strategy_map.get(regime, ["Conservative Approach"])

def _get_risk_guidelines(regime: str) -> Dict[str, str]:
    """Get risk management guidelines for a regime"""
    risk_map = {
        "bull_trending": {
            "position_size": "Up to 90% exposure",
            "stop_loss": "2-4% below entry",
            "approach": "Aggressive growth"
        },
        "bear_trending": {
            "position_size": "Maximum 50% exposure", 
            "stop_loss": "Tight stops, 1-3%",
            "approach": "Defensive positioning"
        },
        "sideways": {
            "position_size": "Up to 70% exposure",
            "stop_loss": "3-5% range boundaries", 
            "approach": "Balanced risk"
        },
        "high_volatility": {
            "position_size": "Maximum 40% exposure",
            "stop_loss": "Wide stops, 5-8%",
            "approach": "Risk management priority"
        },
        "crisis": {
            "position_size": "Minimal exposure <10%",
            "stop_loss": "Immediate exit on losses",
            "approach": "Capital preservation"
        }
    }
    return risk_map.get(regime, {
        "position_size": "Conservative sizing",
        "stop_loss": "Standard risk management", 
        "approach": "Cautious"
    })
