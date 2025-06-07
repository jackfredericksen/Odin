# odin/strategies/ai_adaptive.py
"""
AI Adaptive Strategy for Odin Trading Bot
Integrates regime detection with adaptive strategy selection
"""

import pandas as pd
import numpy as np
from typing import Optional, Dict, Any
from datetime import datetime
import sys
import os

# Add parent directories to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '../'))

from strategies.base import BaseStrategy
from core.models import Signal, SignalType
from ai.regime_detection.regime_detector import MarketRegimeDetector
from ai.strategy_selection.adaptive_manager import AdaptiveStrategyManager

class AIAdaptiveStrategy(BaseStrategy):
    """
    AI-powered adaptive strategy that combines regime detection 
    with dynamic strategy selection
    """
    
    def __init__(self, 
                 regime_update_frequency: int = 20,
                 min_regime_confidence: float = 0.6,
                 strategy_rebalance_frequency: int = 100):
        """
        Initialize AI Adaptive Strategy
        
        Args:
            regime_update_frequency: How often to update regime detection (in data points)
            min_regime_confidence: Minimum confidence required for regime-based decisions
            strategy_rebalance_frequency: How often to rebalance strategy weights
        """
        super().__init__(name="AI_Adaptive")
        
        # AI Components
        self.regime_detector = MarketRegimeDetector()
        self.strategy_manager = AdaptiveStrategyManager()
        
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
            if self.regime_detector.load_models():
                self.logger.info("Loaded existing regime detection models")
                self.initialization_complete = True
            else:
                self.logger.info("No existing models found - will train on first data batch")
                self.initialization_complete = False
                
        except Exception as e:
            self.logger.error(f"Model initialization failed: {e}")
            self.initialization_complete = False
    
    def generate_signal(self, data: pd.DataFrame) -> Optional[Signal]:
        """
        Generate trading signal using AI adaptive approach
        
        Args:
            data: Market data DataFrame with OHLCV and technical indicators
            
        Returns:
            Signal object or None
        """
        try:
            self.data_point_count += 1
            
            # Ensure we have enough data
            if len(data) < 50:
                return self._create_hold_signal("Insufficient data for AI analysis")
            
            # Initialize models if not done yet
            if not self.initialization_complete:
                success = self._train_initial_models(data)
                if not success:
                    return self._create_hold_signal("Model training in progress")
                self.initialization_complete = True
            
            # Update regime detection periodically
            if (self.data_point_count - self.last_regime_update) >= self.regime_update_frequency:
                self._update_regime_detection(data)
                self.last_regime_update = self.data_point_count
            
            # Rebalance strategy weights periodically
            if (self.data_point_count - self.last_strategy_rebalance) >= self.strategy_rebalance_frequency:
                self._rebalance_strategies()
                self.last_strategy_rebalance = self.data_point_count
            
            # Generate signal using adaptive strategy selection
            combined_signal = self.strategy_manager.get_combined_signal(data)
            
            if not combined_signal:
                return self._create_hold_signal("No signal from adaptive strategies")
            
            # Create final signal with AI enhancements
            final_signal = self._create_ai_enhanced_signal(combined_signal, data)
            
            # Track performance
            self._track_signal_performance(final_signal, data)
            
            return final_signal
            
        except Exception as e:
            self.logger.error(f"AI adaptive signal generation failed: {e}")
            return self._create_hold_signal("AI processing error")
    
    def _train_initial_models(self, data: pd.DataFrame) -> bool:
        """Train initial regime detection models"""
        try:
            self.logger.info("Training initial AI models...")
            
            # Prepare features for regime detection
            features = self.regime_detector.prepare_features(data)
            
            if features.empty or len(features) < 100:
                self.logger.warning("Insufficient data for model training")
                return False
            
            # Train regime detection models
            success = self.regime_detector.train_models(features)
            
            if success:
                self.logger.info("Initial model training completed successfully")
                return True
            else:
                self.logger.error("Initial model training failed")
                return False
                
        except Exception as e:
            self.logger.error(f"Initial model training error: {e}")
            return False
    
    def _update_regime_detection(self, data: pd.DataFrame):
        """Update regime detection and adapt strategies"""
        try:
            # Detect current market regime
            regime, confidence = self.regime_detector.detect_regime(data)
            
            self.logger.info(f"Detected regime: {regime} (confidence: {confidence:.3f})")
            
            # Update strategy manager with new regime
            if confidence >= self.min_regime_confidence:
                self.strategy_manager.update_regime(regime, confidence)
            else:
                self.logger.warning(f"Low regime confidence ({confidence:.3f}) - maintaining current strategies")
            
            # Track regime accuracy for model evaluation
            self._track_regime_accuracy(regime, confidence)
            
        except Exception as e:
            self.logger.error(f"Regime update failed: {e}")
    
    def _rebalance_strategies(self):
        """Rebalance strategy weights based on recent performance"""
        try:
            self.logger.info("Rebalancing strategy weights...")
            self.strategy_manager.optimize_strategy_weights(lookback_days=30)
            
        except Exception as e:
            self.logger.error(f"Strategy rebalancing failed: {e}")
    
    def _create_ai_enhanced_signal(self, combined_signal: Dict, data: pd.DataFrame) -> Signal:
        """Create final signal with AI enhancements"""
        try:
            # Extract signal components
            signal_type = combined_signal['signal_type']
            base_strength = combined_signal['strength']
            base_confidence = combined_signal['confidence']
            position_size = combined_signal['position_size']
            
            # Apply AI enhancements
            enhanced_strength, enhanced_confidence = self._apply_ai_enhancements(
                base_strength, base_confidence, data
            )
            
            # Create signal metadata
            metadata = {
                'ai_strategy': True,
                'regime': combined_signal.get('regime', 'unknown'),
                'regime_confidence': combined_signal.get('regime_confidence', 0),
                'contributing_strategies': combined_signal.get('contributing_strategies', []),
                'active_strategy_count': combined_signal.get('active_strategy_count', 0),
                'position_size': position_size,
                'base_strength': base_strength,
                'enhanced_strength': enhanced_strength,
                'enhancement_factor': enhanced_strength / max(base_strength, 0.001)
            }
            
            # Create enhanced signal
            signal = Signal(
                signal_type=signal_type,
                strength=enhanced_strength,
                confidence=enhanced_confidence,
                timestamp=datetime.now(),
                strategy_name=self.name,
                metadata=metadata
            )
            
            return signal
            
        except Exception as e:
            self.logger.error(f"AI signal enhancement failed: {e}")
            # Return basic signal if enhancement fails
            return Signal(
                signal_type=combined_signal['signal_type'],
                strength=combined_signal['strength'],
                confidence=combined_signal['confidence'],
                timestamp=datetime.now(),
                strategy_name=self.name
            )
    
    def _apply_ai_enhancements(self, strength: float, confidence: float, 
                             data: pd.DataFrame) -> tuple:
        """Apply AI-based enhancements to signal strength and confidence"""
        try:
            enhanced_strength = strength
            enhanced_confidence = confidence
            
            # Enhancement 1: Market momentum analysis
            momentum_factor = self._calculate_momentum_factor(data)
            enhanced_strength *= momentum_factor
            
            # Enhancement 2: Volatility adjustment
            volatility_factor = self._calculate_volatility_factor(data)
            enhanced_confidence *= volatility_factor
            
            # Enhancement 3: Regime consistency check
            regime_consistency = self._check_regime_consistency()
            enhanced_confidence *= regime_consistency
            
            # Enhancement 4: Multi-timeframe confirmation
            timeframe_confirmation = self._get_timeframe_confirmation(data)
            enhanced_strength *= timeframe_confirmation
            
            # Ensure values stay within valid ranges
            enhanced_strength = max(0.1, min(1.0, enhanced_strength))
            enhanced_confidence = max(0.1, min(1.0, enhanced_confidence))
            
            return enhanced_strength, enhanced_confidence
            
        except Exception as e:
            self.logger.error(f"AI enhancement calculation failed: {e}")
            return strength, confidence
    
    def _calculate_momentum_factor(self, data: pd.DataFrame) -> float:
        """Calculate momentum factor for signal enhancement"""
        try:
            if len(data) < 10:
                return 1.0
            
            recent_data = data.tail(10)
            
            # Price momentum
            price_change = (recent_data['close'].iloc[-1] / recent_data['close'].iloc[0]) - 1
            
            # Volume momentum  
            if 'volume' in recent_data.columns:
                avg_volume = recent_data['volume'].mean()
                recent_volume = recent_data['volume'].iloc[-1]
                volume_factor = min(2.0, recent_volume / max(avg_volume, 1))
            else:
                volume_factor = 1.0
            
            # Combine factors
            momentum_factor = 1.0 + (price_change * 0.5) + ((volume_factor - 1) * 0.3)
            
            return max(0.5, min(1.5, momentum_factor))
            
        except Exception as e:
            self.logger.error(f"Momentum factor calculation failed: {e}")
            return 1.0
    
    def _calculate_volatility_factor(self, data: pd.DataFrame) -> float:
        """Calculate volatility factor for confidence adjustment"""
        try:
            if len(data) < 20:
                return 1.0
            
            recent_data = data.tail(20)
            returns = recent_data['close'].pct_change().dropna()
            
            if len(returns) < 10:
                return 1.0
            
            current_volatility = returns.std()
            historical_volatility = data['close'].pct_change().tail(100).std()
            
            # Lower confidence in high volatility environments
            volatility_ratio = current_volatility / max(historical_volatility, 0.001)
            
            # Reduce confidence when volatility is significantly higher than normal
            if volatility_ratio > 1.5:
                volatility_factor = 0.7
            elif volatility_ratio > 1.2:
                volatility_factor = 0.85
            elif volatility_ratio < 0.8:
                volatility_factor = 1.1  # Slightly boost confidence in low volatility
            else:
                volatility_factor = 1.0
            
            return max(0.5, min(1.2, volatility_factor))
            
        except Exception as e:
            self.logger.error(f"Volatility factor calculation failed: {e}")
            return 1.0
    
    def _check_regime_consistency(self) -> float:
        """Check consistency of recent regime detections"""
        try:
            regime_history = self.regime_detector.get_regime_history(days=7)
            
            if len(regime_history) < 5:
                return 1.0
            
            # Check how stable the regime has been
            recent_regimes = [entry['regime'] for entry in regime_history[-10:]]
            unique_regimes = set(recent_regimes)
            
            # More consistent regimes get higher confidence
            if len(unique_regimes) == 1:
                consistency_factor = 1.2  # Very stable
            elif len(unique_regimes) == 2:
                consistency_factor = 1.0  # Moderately stable
            else:
                consistency_factor = 0.8  # Unstable/transitioning
            
            return max(0.7, min(1.3, consistency_factor))
            
        except Exception as e:
            self.logger.error(f"Regime consistency check failed: {e}")
            return 1.0
    
    def _get_timeframe_confirmation(self, data: pd.DataFrame) -> float:
        """Get confirmation from multiple timeframes"""
        try:
            if len(data) < 50:
                return 1.0
            
            # Short-term trend (5 periods)
            short_trend = (data['close'].iloc[-1] / data['close'].iloc[-5]) - 1
            
            # Medium-term trend (20 periods)
            medium_trend = (data['close'].iloc[-1] / data['close'].iloc[-20]) - 1
            
            # Long-term trend (50 periods) if available
            if len(data) >= 50:
                long_trend = (data['close'].iloc[-1] / data['close'].iloc[-50]) - 1
            else:
                long_trend = medium_trend
            
            # Check alignment of trends
            trends = [short_trend, medium_trend, long_trend]
            positive_trends = sum(1 for t in trends if t > 0)
            negative_trends = sum(1 for t in trends if t < 0)
            
            # Higher confirmation when trends align
            if positive_trends == 3 or negative_trends == 3:
                confirmation_factor = 1.2  # All trends aligned
            elif positive_trends >= 2 or negative_trends >= 2:
                confirmation_factor = 1.1  # Majority aligned
            else:
                confirmation_factor = 0.9  # Mixed signals
            
            return max(0.8, min(1.3, confirmation_factor))
            
        except Exception as e:
            self.logger.error(f"Timeframe confirmation failed: {e}")
            return 1.0
    
    def _track_signal_performance(self, signal: Signal, data: pd.DataFrame):
        """Track signal performance for model improvement"""
        try:
            performance_entry = {
                'timestamp': datetime.now(),
                'signal_type': signal.signal_type.value,
                'strength': signal.strength,
                'confidence': signal.confidence,
                'current_price': data['close'].iloc[-1] if not data.empty else 0,
                'regime': signal.metadata.get('regime', 'unknown'),
                'contributing_strategies': signal.metadata.get('contributing_strategies', [])
            }
            
            self.performance_history.append(performance_entry)
            
            # Keep only recent history
            if len(self.performance_history) > 1000:
                self.performance_history = self.performance_history[-1000:]
                
        except Exception as e:
            self.logger.error(f"Performance tracking failed: {e}")
    
    def _track_regime_accuracy(self, regime: str, confidence: float):
        """Track regime detection accuracy"""
        try:
            accuracy_entry = {
                'timestamp': datetime.now(),
                'regime': regime,
                'confidence': confidence
            }
            
            self.regime_accuracy.append(accuracy_entry)
            
            # Keep only recent accuracy data
            if len(self.regime_accuracy) > 500:
                self.regime_accuracy = self.regime_accuracy[-500:]
                
        except Exception as e:
            self.logger.error(f"Regime accuracy tracking failed: {e}")
    
    def _create_hold_signal(self, reason: str) -> Signal:
        """Create a HOLD signal with reason"""
        return Signal(
            signal_type=SignalType.HOLD,
            strength=0.0,
            confidence=1.0,
            timestamp=datetime.now(),
            strategy_name=self.name,
            metadata={'reason': reason, 'ai_strategy': True}
        )
    
    def get_ai_analytics(self) -> Dict[str, Any]:
        """Get comprehensive AI analytics and performance metrics"""
        try:
            # Regime detection analytics
            regime_stats = self.regime_detector.get_regime_statistics()
            
            # Strategy manager analytics
            regime_info = self.strategy_manager.get_regime_info()
            active_strategies = self.strategy_manager.get_active_strategies_info()
            
            # Performance analytics
            recent_performance = self._calculate_recent_performance()
            
            # Model health metrics
            model_health = self._assess_model_health()
            
            analytics = {
                'regime_detection': {
                    'current_regime': regime_stats.get('current_regime', 'unknown'),
                    'confidence': regime_stats.get('current_confidence', 0),
                    'regime_distribution': regime_stats.get('regime_distribution_30d', {}),
                    'detection_count': regime_stats.get('total_detections', 0)
                },
                'strategy_management': {
                    'active_strategies': active_strategies,
                    'regime_info': regime_info,
                    'strategy_count': len(active_strategies)
                },
                'performance': recent_performance,
                'model_health': model_health,
                'system_status': {
                    'initialization_complete': self.initialization_complete,
                    'data_points_processed': self.data_point_count,
                    'last_regime_update': self.last_regime_update,
                    'last_strategy_rebalance': self.last_strategy_rebalance
                }
            }
            
            return analytics
            
        except Exception as e:
            self.logger.error(f"AI analytics generation failed: {e}")
            return {'error': str(e)}
    
    def _calculate_recent_performance(self) -> Dict[str, Any]:
        """Calculate recent performance metrics"""
        try:
            if len(self.performance_history) < 10:
                return {'status': 'insufficient_data'}
            
            recent_signals = self.performance_history[-50:]  # Last 50 signals
            
            # Signal distribution
            signal_types = [entry['signal_type'] for entry in recent_signals]
            signal_distribution = {
                'buy_signals': signal_types.count('BUY'),
                'sell_signals': signal_types.count('SELL'),
                'hold_signals': signal_types.count('HOLD')
            }
            
            # Average confidence and strength
            confidences = [entry['confidence'] for entry in recent_signals]
            strengths = [entry['strength'] for entry in recent_signals if entry['strength'] > 0]
            
            performance_metrics = {
                'signal_distribution': signal_distribution,
                'avg_confidence': sum(confidences) / len(confidences) if confidences else 0,
                'avg_strength': sum(strengths) / len(strengths) if strengths else 0,
                'total_signals': len(recent_signals),
                'active_signal_ratio': (len(strengths) / len(recent_signals)) if recent_signals else 0
            }
            
            return performance_metrics
            
        except Exception as e:
            self.logger.error(f"Performance calculation failed: {e}")
            return {'error': str(e)}
    
    def _assess_model_health(self) -> Dict[str, Any]:
        """Assess the health of AI models"""
        try:
            health_metrics = {
                'regime_model_loaded': self.regime_detector.hmm_model is not None,
                'strategy_manager_active': len(self.strategy_manager.active_strategies) > 0,
                'recent_regime_accuracy': self._calculate_regime_accuracy(),
                'model_freshness': self._check_model_freshness(),
                'data_quality': self._assess_data_quality()
            }
            
            # Overall health score
            health_score = sum([
                1 if health_metrics['regime_model_loaded'] else 0,
                1 if health_metrics['strategy_manager_active'] else 0,
                health_metrics['recent_regime_accuracy'],
                health_metrics['model_freshness'],
                health_metrics['data_quality']
            ]) / 5.0
            
            health_metrics['overall_health_score'] = health_score
            health_metrics['health_status'] = self._get_health_status(health_score)
            
            return health_metrics
            
        except Exception as e:
            self.logger.error(f"Model health assessment failed: {e}")
            return {'error': str(e)}
    
    def _calculate_regime_accuracy(self) -> float:
        """Calculate recent regime detection accuracy"""
        try:
            if len(self.regime_accuracy) < 10:
                return 0.5  # Default score for insufficient data
            
            recent_accuracy = self.regime_accuracy[-20:]  # Last 20 detections
            avg_confidence = sum(entry['confidence'] for entry in recent_accuracy) / len(recent_accuracy)
            
            # Use confidence as a proxy for accuracy (higher confidence = better accuracy)
            return min(1.0, avg_confidence)
            
        except Exception as e:
            self.logger.error(f"Regime accuracy calculation failed: {e}")
            return 0.5
    
    def _check_model_freshness(self) -> float:
        """Check how recently models were updated"""
        try:
            updates_ago = self.data_point_count - self.last_regime_update
            
            # Model is fresh if updated within last 50 data points
            if updates_ago <= 20:
                return 1.0
            elif updates_ago <= 50:
                return 0.8
            elif updates_ago <= 100:
                return 0.6
            else:
                return 0.4
                
        except Exception as e:
            self.logger.error(f"Model freshness check failed: {e}")
            return 0.5
    
    def _assess_data_quality(self) -> float:
        """Assess the quality of recent data"""
        try:
            # For now, return a default value
            # In a full implementation, this would check for:
            # - Data completeness
            # - Data freshness
            # - Technical indicator availability
            # - Price data consistency
            return 0.9
            
        except Exception as e:
            self.logger.error(f"Data quality assessment failed: {e}")
            return 0.5
    
    def _get_health_status(self, health_score: float) -> str:
        """Get health status description"""
        if health_score >= 0.9:
            return "excellent"
        elif health_score >= 0.8:
            return "good"
        elif health_score >= 0.7:
            return "fair"
        elif health_score >= 0.6:
            return "poor"
        else:
            return "critical"
    
    def retrain_models(self, historical_data: pd.DataFrame) -> bool:
        """Retrain AI models with new historical data"""
        try:
            self.logger.info("Retraining AI models...")
            
            # Retrain regime detection models
            features = self.regime_detector.prepare_features(historical_data)
            
            if features.empty or len(features) < 200:
                self.logger.warning("Insufficient data for retraining")
                return False
            
            success = self.regime_detector.train_models(features)
            
            if success:
                self.logger.info("Model retraining completed successfully")
                self.initialization_complete = True
                
                # Reset counters
                self.last_regime_update = self.data_point_count
                self.last_strategy_rebalance = self.data_point_count
                
                return True
            else:
                self.logger.error("Model retraining failed")
                return False
                
        except Exception as e:
            self.logger.error(f"Model retraining error: {e}")
            return False
    
    def get_strategy_recommendations(self) -> Dict[str, Any]:
        """Get AI-powered strategy recommendations"""
        try:
            current_regime = self.strategy_manager.current_regime
            
            if not current_regime:
                return {'status': 'no_regime_detected'}
            
            # Get regime-specific performance
            regime_performance = self.strategy_manager.get_strategy_performance_by_regime(
                current_regime, days=30
            )
            
            # Generate recommendations
            recommendations = {
                'current_regime': current_regime.value,
                'regime_confidence': self.strategy_manager.current_confidence,
                'recommended_strategies': [],
                'risk_recommendations': self._get_risk_recommendations(),
                'position_sizing': self._get_position_sizing_recommendations()
            }
            
            # Add strategy-specific recommendations
            for strategy_name, performance in regime_performance.items():
                if performance['sample_count'] >= 5:  # Enough data for recommendation
                    avg_metrics = performance['avg_metrics']
                    
                    recommendation = {
                        'strategy': strategy_name,
                        'performance_score': avg_metrics.get('total_return', 0),
                        'win_rate': avg_metrics.get('win_rate', 0.5),
                        'sharpe_ratio': avg_metrics.get('sharpe_ratio', 0),
                        'recommendation': self._get_strategy_recommendation(avg_metrics)
                    }
                    
                    recommendations['recommended_strategies'].append(recommendation)
            
            return recommendations
            
        except Exception as e:
            self.logger.error(f"Strategy recommendations failed: {e}")
            return {'error': str(e)}
    
    def _get_risk_recommendations(self) -> Dict[str, Any]:
        """Get risk management recommendations"""
        try:
            current_regime = self.strategy_manager.current_regime
            
            if not current_regime:
                return {'status': 'unknown_regime'}
            
            regime_mapping = self.strategy_manager.regime_strategy_map.get(current_regime)
            
            if not regime_mapping:
                return {'status': 'no_mapping'}
            
            risk_recommendations = {
                'risk_multiplier': regime_mapping.risk_multiplier,
                'max_exposure': regime_mapping.max_exposure,
                'position_size_limit': regime_mapping.max_exposure * 0.8,  # Conservative
                'stop_loss_recommendation': self._get_stop_loss_recommendation(current_regime),
                'diversification_advice': self._get_diversification_advice(current_regime)
            }
            
            return risk_recommendations
            
        except Exception as e:
            self.logger.error(f"Risk recommendations failed: {e}")
            return {'error': str(e)}
    
    def _get_position_sizing_recommendations(self) -> Dict[str, Any]:
        """Get position sizing recommendations"""
        try:
            current_regime = self.strategy_manager.current_regime
            regime_confidence = self.strategy_manager.current_confidence
            
            # Base position size on regime and confidence
            if current_regime and regime_confidence > 0.8:
                regime_mapping = self.strategy_manager.regime_strategy_map.get(current_regime)
                base_size = regime_mapping.max_exposure if regime_mapping else 0.5
            else:
                base_size = 0.3  # Conservative default
            
            # Adjust based on volatility and momentum
            volatility_adj = 1.0  # Would calculate from recent data
            momentum_adj = 1.0    # Would calculate from recent data
            
            recommended_size = base_size * volatility_adj * momentum_adj
            recommended_size = max(0.1, min(0.9, recommended_size))
            
            sizing_recommendations = {
                'recommended_position_size': recommended_size,
                'base_regime_size': base_size,
                'volatility_adjustment': volatility_adj,
                'momentum_adjustment': momentum_adj,
                'confidence_factor': regime_confidence,
                'size_rationale': self._get_sizing_rationale(current_regime, regime_confidence)
            }
            
            return sizing_recommendations
            
        except Exception as e:
            self.logger.error(f"Position sizing recommendations failed: {e}")
            return {'error': str(e)}
    
    def _get_strategy_recommendation(self, metrics: Dict[str, float]) -> str:
        """Get recommendation for a specific strategy"""
        total_return = metrics.get('total_return', 0)
        win_rate = metrics.get('win_rate', 0.5)
        sharpe_ratio = metrics.get('sharpe_ratio', 0)
        
        if total_return > 0.1 and win_rate > 0.6 and sharpe_ratio > 1.0:
            return "highly_recommended"
        elif total_return > 0.05 and win_rate > 0.55:
            return "recommended"
        elif total_return > 0 and win_rate > 0.5:
            return "neutral"
        elif total_return < -0.05 or win_rate < 0.4:
            return "not_recommended"
        else:
            return "insufficient_data"
    
    def _get_stop_loss_recommendation(self, regime) -> Dict[str, float]:
        """Get stop loss recommendations based on regime"""
        if regime.value == "crisis":
            return {"tight_stop": 0.02, "normal_stop": 0.03, "wide_stop": 0.05}
        elif regime.value == "high_volatility":
            return {"tight_stop": 0.03, "normal_stop": 0.05, "wide_stop": 0.08}
        elif regime.value in ["bull_trending", "bear_trending"]:
            return {"tight_stop": 0.02, "normal_stop": 0.04, "wide_stop": 0.06}
        else:  # sideways
            return {"tight_stop": 0.015, "normal_stop": 0.03, "wide_stop": 0.05}
    
    def _get_diversification_advice(self, regime) -> str:
        """Get diversification advice based on regime"""
        if regime.value == "crisis":
            return "Minimize exposure, consider cash position"
        elif regime.value == "high_volatility":
            return "Use smaller position sizes, increase diversification"
        elif regime.value == "bull_trending":
            return "Can increase concentration in strong performers"
        elif regime.value == "bear_trending":
            return "Maintain defensive positioning, avoid concentration"
        else:  # sideways
            return "Balanced approach, moderate diversification"
    
    def _get_sizing_rationale(self, regime, confidence: float) -> str:
        """Get rationale for position sizing"""
        if not regime:
            return "Conservative sizing due to uncertain regime"
        elif confidence < 0.6:
            return f"Reduced sizing due to low regime confidence ({confidence:.2f})"
        elif regime.value == "crisis":
            return "Minimal sizing due to crisis conditions"
        elif regime.value == "bull_trending" and confidence > 0.8:
            return "Increased sizing due to strong bull trend confidence"
        else:
            return f"Standard sizing for {regime.value} regime"

# Example usage and testing
if __name__ == "__main__":
    # Test the AI Adaptive Strategy
    ai_strategy = AIAdaptiveStrategy(
        regime_update_frequency=10,
        min_regime_confidence=0.6,
        strategy_rebalance_frequency=50
    )
    
    print("Testing AI Adaptive Strategy...")
    
    # Create sample market data
    dates = pd.date_range(start='2024-01-01', end='2024-06-06', freq='D')
    sample_data = pd.DataFrame({
        'close': np.random.randn(len(dates)).cumsum() + 50000,
        'high': np.random.randn(len(dates)).cumsum() + 51000,
        'low': np.random.randn(len(dates)).cumsum() + 49000,
        'volume': np.random.randint(1000, 10000, len(dates)),
        'rsi_14': np.random.uniform(20, 80, len(dates)),
        'ma_20': np.random.randn(len(dates)).cumsum() + 49500,
        'ma_50': np.random.randn(len(dates)).cumsum() + 49000,
        'bollinger_upper': np.random.randn(len(dates)).cumsum() + 52000,
        'bollinger_lower': np.random.randn(len(dates)).cumsum() + 48000,
        'macd': np.random.randn(len(dates)) * 100,
        'macd_signal': np.random.randn(len(dates)) * 100,
    }, index=dates)
    
    # Test signal generation
    signal = ai_strategy.generate_signal(sample_data)
    if signal:
        print(f"Generated signal: {signal.signal_type.value}")
        print(f"Strength: {signal.strength:.3f}")
        print(f"Confidence: {signal.confidence:.3f}")
        print(f"Metadata: {signal.metadata}")
    
    # Test AI analytics
    analytics = ai_strategy.get_ai_analytics()
    print(f"\nAI Analytics: {analytics}")
    
    # Test strategy recommendations
    recommendations = ai_strategy.get_strategy_recommendations()
    print(f"\nStrategy Recommendations: {recommendations}")