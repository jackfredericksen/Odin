"""
Enhanced Strategy Manager with AI-Driven Strategy Orchestration

Implements intelligent strategy selection using ML-based market regime detection
and real-time strategy performance scoring for optimal trading decisions.

File: odin/core/strategy_manager.py
"""

import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Tuple
import pandas as pd
import numpy as np
from statistics import mean, stdev

from .database import Database
from .models import StrategySignal, PriceData
from .exceptions import StrategyException, StrategyConfigurationException
from ..ai.strategy_selection.ai_strategy_selector import AIStrategySelector
from ..ai.regime_detection.regime_detector import RegimeDetector
from ..ai.strategy_selection.strategy_scorer import StrategyScorer

# Import all available strategies
from ..strategies import (
    MovingAverageStrategy, 
    RSIStrategy, 
    BollingerBandsStrategy, 
    MACDStrategy,
    SwingTradingStrategy
)

logger = logging.getLogger(__name__)


class EnhancedStrategyManager:
    """
    AI-Driven Strategy Orchestration System
    
    Manages a pool of trading strategies and uses ML to dynamically select
    the optimal strategy based on real-time market conditions and performance.
    """
    
    def __init__(self, database: Database):
        """
        Initialize enhanced strategy manager with AI components.
        
        Args:
            database: Database instance for data persistence
        """
        self.database = database
        
        # Strategy pool - all available strategies
        self.strategy_pool: Dict[str, Any] = {}
        self.strategy_classes = {
            "moving_average": MovingAverageStrategy,
            "rsi": RSIStrategy,
            "bollinger_bands": BollingerBandsStrategy,
            "macd": MACDStrategy,
            "swing_trading": SwingTradingStrategy
        }
        
        # AI Components
        self.regime_detector = RegimeDetector()
        self.strategy_scorer = StrategyScorer(database)
        self.ai_selector = AIStrategySelector(
            regime_detector=self.regime_detector,
            strategy_scorer=self.strategy_scorer
        )
        
        # Current active strategy
        self.active_strategy_id: Optional[str] = None
        self.active_strategy_confidence: float = 0.0
        self.last_evaluation: datetime = datetime.now(timezone.utc)
        self.evaluation_interval: int = 300  # 5 minutes
        
        # Performance tracking
        self.strategy_scores: Dict[str, float] = {}
        self.strategy_performance: Dict[str, Dict[str, Any]] = {}
        self.market_regime: Dict[str, Any] = {}
        
        # AI Configuration
        self.config = {
            "min_confidence_threshold": 0.65,
            "strategy_switch_threshold": 0.15,  # Switch if new strategy scores 15% higher
            "evaluation_frequency": 300,  # seconds
            "performance_lookback": 24,  # hours
            "regime_confidence_threshold": 0.7
        }
        
        # Initialize system
        asyncio.create_task(self._initialize_system())
        
        logger.info("Enhanced Strategy Manager with AI orchestration initialized")
    
    async def _initialize_system(self):
        """Initialize the entire AI strategy system."""
        try:
            # Initialize all strategies in the pool
            await self._initialize_strategy_pool()
            
            # Load AI models
            await self._initialize_ai_components()
            
            # Select initial strategy
            await self._perform_initial_strategy_selection()
            
            # Start continuous evaluation loop
            asyncio.create_task(self._continuous_evaluation_loop())
            
            logger.info(f"System initialized with {len(self.strategy_pool)} strategies")
            
        except Exception as e:
            logger.error(f"Error initializing AI strategy system: {e}")
    
    async def _initialize_strategy_pool(self):
        """Initialize all available strategies in the pool."""
        try:
            # Create instances of all strategies with default parameters
            strategy_configs = {
                "moving_average": {
                    "name": "Moving Average Crossover",
                    "params": {"fast_period": 21, "slow_period": 50}
                },
                "rsi": {
                    "name": "RSI Momentum",
                    "params": {"rsi_period": 14, "oversold": 30, "overbought": 70}
                },
                "bollinger_bands": {
                    "name": "Bollinger Bands",
                    "params": {"period": 20, "std_dev": 2.0}
                },
                "macd": {
                    "name": "MACD Convergence",
                    "params": {"fast": 12, "slow": 26, "signal": 9}
                },
                "swing_trading": {
                    "name": "Advanced Swing Trading",
                    "params": {
                        "primary_timeframe": "4H",
                        "rsi_period": 14,
                        "rsi_oversold": 35,
                        "rsi_overbought": 65,
                        "ma_fast": 21,
                        "ma_slow": 50,
                        "min_risk_reward": 2.0
                    }
                }
            }
            
            for strategy_type, config in strategy_configs.items():
                try:
                    strategy_class = self.strategy_classes[strategy_type]
                    strategy_instance = strategy_class(**config["params"])
                    
                    strategy_id = f"{strategy_type}_{int(datetime.now().timestamp())}"
                    
                    self.strategy_pool[strategy_id] = {
                        "instance": strategy_instance,
                        "type": strategy_type,
                        "name": config["name"],
                        "parameters": config["params"],
                        "created_at": datetime.now(timezone.utc),
                        "last_used": None,
                        "total_signals": 0,
                        "successful_signals": 0
                    }
                    
                    # Initialize performance tracking
                    self.strategy_performance[strategy_id] = {
                        "total_return": 0.0,
                        "win_rate": 0.0,
                        "sharpe_ratio": 0.0,
                        "max_drawdown": 0.0,
                        "recent_performance": []
                    }
                    
                    logger.debug(f"Initialized strategy: {strategy_id}")
                    
                except Exception as e:
                    logger.error(f"Error initializing {strategy_type}: {e}")
                    continue
            
        except Exception as e:
            logger.error(f"Error initializing strategy pool: {e}")
    
    async def _initialize_ai_components(self):
        """Initialize AI components for strategy selection."""
        try:
            # Initialize regime detector with historical data
            historical_data = self.database.get_recent_prices(limit=1000)
            if historical_data:
                await self.regime_detector.initialize(historical_data)
            
            # Initialize strategy scorer
            await self.strategy_scorer.initialize()
            
            logger.info("AI components initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing AI components: {e}")
    
    async def _perform_initial_strategy_selection(self):
        """Perform initial strategy selection."""
        try:
            # Get recent market data
            recent_data = self.database.get_recent_prices(limit=100)
            if not recent_data:
                # Default to swing trading if no data
                self.active_strategy_id = list(self.strategy_pool.keys())[0]
                self.active_strategy_confidence = 0.5
                return
            
            # Convert to required format
            price_data = self._convert_to_price_data(recent_data)
            
            # Use AI to select best strategy
            selection_result = await self.ai_selector.select_optimal_strategy(
                price_data, list(self.strategy_pool.keys())
            )
            
            self.active_strategy_id = selection_result["strategy_id"]
            self.active_strategy_confidence = selection_result["confidence"]
            self.market_regime = selection_result["market_regime"]
            
            # Update strategy usage
            if self.active_strategy_id:
                self.strategy_pool[self.active_strategy_id]["last_used"] = datetime.now(timezone.utc)
            
            logger.info(f"Initial strategy selected: {self.active_strategy_id} "
                       f"(confidence: {self.active_strategy_confidence:.3f})")
            
        except Exception as e:
            logger.error(f"Error in initial strategy selection: {e}")
            # Fallback to first available strategy
            if self.strategy_pool:
                self.active_strategy_id = list(self.strategy_pool.keys())[0]
                self.active_strategy_confidence = 0.5
    
    async def _continuous_evaluation_loop(self):
        """Continuous strategy evaluation and selection loop."""
        while True:
            try:
                await asyncio.sleep(self.config["evaluation_frequency"])
                
                # Perform strategy evaluation
                await self._evaluate_and_potentially_switch_strategy()
                
                # Update performance metrics
                await self._update_strategy_performance()
                
                # Update market regime
                await self._update_market_regime()
                
                self.last_evaluation = datetime.now(timezone.utc)
                
            except Exception as e:
                logger.error(f"Error in continuous evaluation loop: {e}")
                await asyncio.sleep(60)  # Wait a minute before retrying
    
    async def _evaluate_and_potentially_switch_strategy(self):
        """Evaluate all strategies and switch if a better one is found."""
        try:
            # Get recent market data
            recent_data = self.database.get_recent_prices(limit=100)
            if not recent_data:
                return
            
            price_data = self._convert_to_price_data(recent_data)
            
            # Get AI recommendation
            selection_result = await self.ai_selector.select_optimal_strategy(
                price_data, list(self.strategy_pool.keys())
            )
            
            recommended_strategy = selection_result["strategy_id"]
            recommended_confidence = selection_result["confidence"]
            
            # Check if we should switch strategies
            should_switch = self._should_switch_strategy(
                recommended_strategy, recommended_confidence
            )
            
            if should_switch:
                await self._switch_strategy(recommended_strategy, recommended_confidence)
                
                logger.info(f"Strategy switched to: {recommended_strategy} "
                           f"(confidence: {recommended_confidence:.3f})")
            
            # Update current scores regardless
            self.strategy_scores = selection_result["all_scores"]
            
        except Exception as e:
            logger.error(f"Error evaluating strategies: {e}")
    
    def _should_switch_strategy(self, recommended_strategy: str, recommended_confidence: float) -> bool:
        """Determine if we should switch to a different strategy."""
        # Don't switch if confidence is too low
        if recommended_confidence < self.config["min_confidence_threshold"]:
            return False
        
        # Don't switch if it's the same strategy
        if recommended_strategy == self.active_strategy_id:
            return False
        
        # Switch if new strategy has significantly higher confidence
        confidence_improvement = recommended_confidence - self.active_strategy_confidence
        return confidence_improvement >= self.config["strategy_switch_threshold"]
    
    async def _switch_strategy(self, new_strategy_id: str, confidence: float):
        """Switch to a new active strategy."""
        old_strategy = self.active_strategy_id
        
        self.active_strategy_id = new_strategy_id
        self.active_strategy_confidence = confidence
        
        # Update usage tracking
        self.strategy_pool[new_strategy_id]["last_used"] = datetime.now(timezone.utc)
        
        # Log the switch
        logger.info(f"Strategy switched: {old_strategy} -> {new_strategy_id}")
    
    async def generate_trading_signal(self, price_data: List[PriceData]) -> Optional[StrategySignal]:
        """
        Generate trading signal using the currently active strategy.
        
        Args:
            price_data: Recent price data for signal generation
            
        Returns:
            Trading signal from active strategy or None
        """
        if not self.active_strategy_id or not price_data:
            return None
        
        try:
            # Get active strategy instance
            active_strategy = self.strategy_pool[self.active_strategy_id]["instance"]
            
            # Convert price data to DataFrame
            df = self._price_data_to_dataframe(price_data)
            
            # Generate signal
            signal = active_strategy.generate_signal(df)
            
            if signal:
                # Update strategy usage stats
                self.strategy_pool[self.active_strategy_id]["total_signals"] += 1
                
                # Add metadata about AI selection
                if hasattr(signal, 'indicators'):
                    signal.indicators.update({
                        'ai_selected_strategy': self.active_strategy_id,
                        'strategy_confidence': self.active_strategy_confidence,
                        'market_regime': self.market_regime.get('current_regime', 'unknown'),
                        'regime_confidence': self.market_regime.get('confidence', 0.0)
                    })
                
                logger.info(f"Signal generated by {self.active_strategy_id}: {signal.signal.value}")
            
            return signal
            
        except Exception as e:
            logger.error(f"Error generating signal with active strategy: {e}")
            return None
    
    async def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status for display."""
        try:
            # Update recent performance
            await self._update_strategy_performance()
            
            # Prepare strategy pool status
            strategy_status = []
            for strategy_id, strategy_info in self.strategy_pool.items():
                performance = self.strategy_performance.get(strategy_id, {})
                score = self.strategy_scores.get(strategy_id, 0.0)
                
                strategy_status.append({
                    "id": strategy_id,
                    "name": strategy_info["name"],
                    "type": strategy_info["type"],
                    "score": round(score, 3),
                    "is_active": strategy_id == self.active_strategy_id,
                    "last_used": strategy_info["last_used"],
                    "performance": {
                        "return_24h": round(performance.get("total_return", 0.0), 2),
                        "win_rate": round(performance.get("win_rate", 0.0), 1),
                        "sharpe_ratio": round(performance.get("sharpe_ratio", 0.0), 2)
                    },
                    "total_signals": strategy_info["total_signals"],
                    "successful_signals": strategy_info["successful_signals"]
                })
            
            # Sort by score (highest first)
            strategy_status.sort(key=lambda x: x["score"], reverse=True)
            
            return {
                "active_strategy": {
                    "id": self.active_strategy_id,
                    "name": self.strategy_pool[self.active_strategy_id]["name"] if self.active_strategy_id else "None",
                    "confidence": round(self.active_strategy_confidence, 3),
                    "type": self.strategy_pool[self.active_strategy_id]["type"] if self.active_strategy_id else "None"
                },
                "market_regime": {
                    "current": self.market_regime.get("current_regime", "unknown"),
                    "confidence": round(self.market_regime.get("confidence", 0.0), 3),
                    "trend": self.market_regime.get("trend", "neutral"),
                    "volatility": self.market_regime.get("volatility", "medium")
                },
                "strategy_pool": strategy_status,
                "system_stats": {
                    "total_strategies": len(self.strategy_pool),
                    "last_evaluation": self.last_evaluation,
                    "next_evaluation": self.last_evaluation + timedelta(seconds=self.config["evaluation_frequency"]),
                    "evaluation_interval": self.config["evaluation_frequency"],
                    "ai_enabled": True
                },
                "configuration": self.config
            }
            
        except Exception as e:
            logger.error(f"Error getting system status: {e}")
            return {
                "error": str(e),
                "active_strategy": {"id": None, "name": "Error", "confidence": 0.0},
                "strategy_pool": [],
                "system_stats": {"total_strategies": 0, "ai_enabled": False}
            }
    
    async def get_ai_insights(self) -> Dict[str, Any]:
        """Get AI insights and reasoning for current selections."""
        try:
            insights = []
            
            # Market regime insights
            regime = self.market_regime.get("current_regime", "unknown")
            regime_confidence = self.market_regime.get("confidence", 0.0)
            
            if regime_confidence > 0.7:
                insights.append(f"High confidence {regime} market detected - strategy selection optimized")
            elif regime_confidence > 0.5:
                insights.append(f"Moderate confidence {regime} market - monitoring for changes")
            else:
                insights.append("Uncertain market conditions - using conservative strategy selection")
            
            # Strategy performance insights
            if self.strategy_scores:
                best_strategy = max(self.strategy_scores.items(), key=lambda x: x[1])
                worst_strategy = min(self.strategy_scores.items(), key=lambda x: x[1])
                
                if best_strategy[1] > 0.8:
                    insights.append(f"Strong strategy signals detected - {best_strategy[0]} highly favored")
                
                score_spread = best_strategy[1] - worst_strategy[1]
                if score_spread < 0.2:
                    insights.append("Strategy scores are close - market conditions may be transitioning")
            
            # Active strategy insights
            if self.active_strategy_confidence > 0.8:
                insights.append("High confidence in current strategy selection")
            elif self.active_strategy_confidence < 0.6:
                insights.append("Lower confidence - system may switch strategies soon")
            
            # Performance insights
            active_strategy_id = self.active_strategy_id
            if active_strategy_id and active_strategy_id in self.strategy_performance:
                perf = self.strategy_performance[active_strategy_id]
                if perf.get("total_return", 0) > 0:
                    insights.append("Current strategy showing positive returns")
                elif perf.get("total_return", 0) < -2:
                    insights.append("Current strategy underperforming - evaluation increased")
            
            return {
                "insights": insights,
                "reasoning": {
                    "regime_analysis": self.market_regime,
                    "strategy_scores": self.strategy_scores,
                    "selection_confidence": self.active_strategy_confidence
                },
                "recommendations": await self._generate_recommendations()
            }
            
        except Exception as e:
            logger.error(f"Error generating AI insights: {e}")
            return {"insights": ["Error generating insights"], "reasoning": {}, "recommendations": []}
    
    async def _generate_recommendations(self) -> List[str]:
        """Generate actionable recommendations based on current state."""
        recommendations = []
        
        try:
            # Check if strategy switching is frequent
            recent_switches = await self._count_recent_strategy_switches()
            if recent_switches > 3:
                recommendations.append("Consider increasing switch threshold - frequent strategy changes detected")
            
            # Check overall performance
            avg_performance = np.mean([
                perf.get("total_return", 0) 
                for perf in self.strategy_performance.values()
            ])
            
            if avg_performance < -1:
                recommendations.append("Overall strategy performance declining - consider parameter optimization")
            elif avg_performance > 2:
                recommendations.append("Strong performance across strategies - current market conditions favorable")
            
            # Market regime recommendations
            regime_conf = self.market_regime.get("confidence", 0)
            if regime_conf < 0.5:
                recommendations.append("Low regime confidence - consider more conservative position sizing")
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
        
        return recommendations
    
    async def _count_recent_strategy_switches(self, hours: int = 24) -> int:
        """Count strategy switches in recent hours."""
        # This would be implemented by tracking switches in database
        # For now, return a placeholder
        return 0
    
    def _convert_to_price_data(self, db_records: List[Dict]) -> List[PriceData]:
        """Convert database records to PriceData objects."""
        price_data = []
        for record in reversed(db_records):  # Ensure chronological order
            price_data.append(PriceData(
                timestamp=datetime.fromisoformat(record["timestamp"]),
                price=float(record["price"]),
                volume=float(record.get("volume", 1000))
            ))
        return price_data
    
    def _price_data_to_dataframe(self, price_data: List[PriceData]) -> pd.DataFrame:
        """Convert price data to DataFrame for strategy analysis."""
        data = []
        for price_point in price_data:
            data.append({
                'timestamp': price_point.timestamp,
                'open': price_point.price,
                'high': price_point.price,
                'low': price_point.price,
                'close': price_point.price,
                'volume': price_point.volume or 1000.0
            })
        
        df = pd.DataFrame(data)
        if not df.empty:
            df.set_index('timestamp', inplace=True)
        return df
    
    async def _update_strategy_performance(self):
        """Update performance metrics for all strategies."""
        try:
            for strategy_id in self.strategy_pool:
                performance = await self._calculate_strategy_performance(strategy_id)
                self.strategy_performance[strategy_id] = performance
                
        except Exception as e:
            logger.error(f"Error updating strategy performance: {e}")
    
    async def _calculate_strategy_performance(self, strategy_id: str) -> Dict[str, Any]:
        """Calculate performance metrics for a specific strategy."""
        try:
            # Get recent trades for this strategy
            trades = self.database.get_recent_trades(limit=100, strategy_id=strategy_id)
            
            if not trades:
                return {
                    "total_return": 0.0,
                    "win_rate": 0.0,
                    "sharpe_ratio": 0.0,
                    "max_drawdown": 0.0,
                    "recent_performance": []
                }
            
            # Calculate basic metrics
            total_trades = len(trades)
            winning_trades = sum(1 for trade in trades if trade.get("pnl", 0) > 0)
            win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
            
            # Calculate returns
            total_pnl = sum(trade.get("pnl", 0) for trade in trades)
            trade_returns = [trade.get("pnl", 0) / 1000 for trade in trades]  # Normalize
            
            total_return = (total_pnl / (total_trades * 1000) * 100) if total_trades > 0 else 0
            
            # Calculate Sharpe ratio
            if len(trade_returns) > 1:
                avg_return = mean(trade_returns)
                return_std = stdev(trade_returns)
                sharpe_ratio = (avg_return / return_std) if return_std > 0 else 0
            else:
                sharpe_ratio = 0
            
            # Calculate max drawdown
            cumulative_returns = np.cumsum(trade_returns)
            if len(cumulative_returns) > 0:
                peak = np.maximum.accumulate(cumulative_returns)
                drawdown = (peak - cumulative_returns) / peak
                max_drawdown = np.max(drawdown) * 100 if len(drawdown) > 0 else 0
            else:
                max_drawdown = 0
            
            return {
                "total_return": round(total_return, 2),
                "win_rate": round(win_rate, 1),
                "sharpe_ratio": round(sharpe_ratio, 2),
                "max_drawdown": round(max_drawdown, 2),
                "recent_performance": trade_returns[-10:]  # Last 10 trades
            }
            
        except Exception as e:
            logger.error(f"Error calculating performance for {strategy_id}: {e}")
            return {
                "total_return": 0.0,
                "win_rate": 0.0,
                "sharpe_ratio": 0.0,
                "max_drawdown": 0.0,
                "recent_performance": []
            }
    
    async def _update_market_regime(self):
        """Update current market regime analysis."""
        try:
            # Get recent price data
            recent_data = self.database.get_recent_prices(limit=200)
            if recent_data:
                price_data = self._convert_to_price_data(recent_data)
                regime_result = await self.regime_detector.detect_regime(price_data)
                self.market_regime = regime_result
                
        except Exception as e:
            logger.error(f"Error updating market regime: {e}")
    
    async def force_strategy_switch(self, strategy_id: str) -> bool:
        """Manually force a strategy switch (for testing/override)."""
        try:
            if strategy_id in self.strategy_pool:
                await self._switch_strategy(strategy_id, 0.9)  # High confidence for manual
                logger.info(f"Manually switched to strategy: {strategy_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error forcing strategy switch: {e}")
            return False
    
    async def update_ai_configuration(self, config_updates: Dict[str, Any]) -> bool:
        """Update AI system configuration."""
        try:
            for key, value in config_updates.items():
                if key in self.config:
                    self.config[key] = value
                    logger.info(f"Updated AI config: {key} = {value}")
            return True
        except Exception as e:
            logger.error(f"Error updating AI configuration: {e}")
            return False
    
    async def health_check(self) -> Dict[str, Any]:
        """Comprehensive system health check."""
        try:
            health_status = {
                "status": "healthy",
                "timestamp": datetime.now(timezone.utc),
                "components": {
                    "strategy_pool": len(self.strategy_pool) > 0,
                    "active_strategy": self.active_strategy_id is not None,
                    "regime_detector": await self.regime_detector.health_check(),
                    "strategy_scorer": await self.strategy_scorer.health_check(),
                    "ai_selector": True
                },
                "metrics": {
                    "total_strategies": len(self.strategy_pool),
                    "active_strategy_confidence": self.active_strategy_confidence,
                    "last_evaluation": self.last_evaluation,
                    "evaluation_interval": self.config["evaluation_frequency"]
                }
            }
            
            # Check for any unhealthy components
            unhealthy_components = [
                comp for comp, status in health_status["components"].items() 
                if not status
            ]
            
            if unhealthy_components:
                health_status["status"] = "warning"
                health_status["issues"] = unhealthy_components
            
            return health_status
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc)
            }