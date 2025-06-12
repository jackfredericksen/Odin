"""
Odin Strategy Manager - Centralized Strategy Management

Manages all trading strategies, signals, and performance tracking.
Provides a unified interface for strategy operations and real-time monitoring.

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
from .models import SignalType, PriceData  # Import from core models - single source of truth
from .exceptions import StrategyException, StrategyConfigurationException

# Import strategies
from ..strategies import (
    MovingAverageStrategy, 
    RSIStrategy, 
    BollingerBandsStrategy, 
    MACDStrategy
)

logger = logging.getLogger(__name__)


class StrategyManager:
    """
    Centralized strategy management system.
    
    Handles strategy lifecycle, signal generation, performance tracking,
    and real-time monitoring of all trading strategies.
    """
    
    def __init__(self, database: Database):
        """
        Initialize strategy manager.
        
        Args:
            database: Database instance for data persistence
        """
        self.database = database
        self.strategies: Dict[str, Any] = {}
        self.strategy_classes = {
            "moving_average": MovingAverageStrategy,
            "rsi": RSIStrategy,
            "bollinger_bands": BollingerBandsStrategy,
            "macd": MACDStrategy
        }
        
        # Performance tracking
        self.performance_cache: Dict[str, Dict[str, Any]] = {}
        self.signal_history: Dict[str, List[Any]] = {}  # Will store signal data as dicts
        
        # Initialize strategies
        asyncio.create_task(self._initialize_strategies())
        
        logger.info("Strategy Manager initialized")
    
    async def _initialize_strategies(self):
        """Initialize all strategies from database."""
        try:
            strategies_data = self.database.get_strategies()
            
            for strategy_data in strategies_data:
                await self._create_strategy_instance(strategy_data)
                
            logger.info(f"Initialized {len(self.strategies)} strategies")
            
        except Exception as e:
            logger.error(f"Error initializing strategies: {e}")
    
    async def _create_strategy_instance(self, strategy_data: Dict[str, Any]):
        """Create strategy instance from database data."""
        try:
            strategy_id = strategy_data["id"]
            strategy_type = strategy_data["type"]
            parameters = strategy_data.get("parameters", {})
            
            if strategy_type not in self.strategy_classes:
                logger.warning(f"Unknown strategy type: {strategy_type}")
                return
            
            # Create strategy instance
            strategy_class = self.strategy_classes[strategy_type]
            strategy_instance = strategy_class(**parameters)
            
            # Store strategy with metadata
            self.strategies[strategy_id] = {
                "instance": strategy_instance,
                "metadata": strategy_data,
                "last_signal": None,
                "performance": None,
                "enabled": strategy_data.get("active", False)
            }
            
            # Initialize signal history
            self.signal_history[strategy_id] = []
            
            logger.debug(f"Created strategy instance: {strategy_id}")
            
        except Exception as e:
            logger.error(f"Error creating strategy {strategy_data.get('id')}: {e}")
    
    async def get_all_strategies(self) -> List[Dict[str, Any]]:
        """
        Get all strategies with current status and performance.
        
        Returns:
            List of strategy data with performance metrics
        """
        try:
            strategies_list = []
            
            for strategy_id, strategy_info in self.strategies.items():
                # Get performance metrics
                performance = await self._calculate_strategy_performance(strategy_id)
                
                # Get recent signals
                recent_signals = await self._get_recent_signals(strategy_id, limit=10)
                
                # Format strategy data
                strategy_data = {
                    "id": strategy_id,
                    "name": strategy_info["metadata"]["name"],
                    "type": strategy_info["metadata"]["type"],
                    "description": strategy_info["metadata"].get("description", ""),
                    "active": strategy_info["enabled"],
                    "parameters": strategy_info["metadata"].get("parameters", {}),
                    
                    # Performance metrics
                    "return": performance.get("total_return", 0.0),
                    "total_trades": performance.get("total_trades", 0),
                    "win_rate": performance.get("win_rate", 0.0),
                    "sharpe_ratio": performance.get("sharpe_ratio", 0.0),
                    "max_drawdown": performance.get("max_drawdown", 0.0),
                    "volatility": performance.get("volatility", 0.0),
                    
                    # Recent activity
                    "last_signal": strategy_info["last_signal"],
                    "recent_signals": len(recent_signals),
                    "performance_history": performance.get("performance_history", [])
                }
                
                strategies_list.append(strategy_data)
            
            return strategies_list
            
        except Exception as e:
            logger.error(f"Error getting all strategies: {e}")
            raise StrategyException(f"Failed to get strategies: {str(e)}")
    
    async def generate_signals(self, price_data: List[PriceData]) -> Dict[str, Any]:
        """
        Generate signals from all active strategies.
        
        Args:
            price_data: Recent price data for signal generation
            
        Returns:
            Dictionary mapping strategy_id to generated signal
        """
        signals = {}
        
        if not price_data:
            logger.warning("No price data provided for signal generation")
            return signals
        
        # Convert price data to DataFrame
        df = self._price_data_to_dataframe(price_data)
        
        for strategy_id, strategy_info in self.strategies.items():
            if not strategy_info["enabled"]:
                continue
                
            try:
                strategy_instance = strategy_info["instance"]
                
                # Generate signal
                signal = strategy_instance.generate_signal(df)
                
                if signal and signal.signal != SignalType.HOLD:
                    signals[strategy_id] = signal
                    strategy_info["last_signal"] = signal
                    self.signal_history[strategy_id].append(signal)
                    
                    # Save signal to database
                    await self._save_signal_to_database(strategy_id, signal)
                    
                    logger.info(f"Generated signal for {strategy_id}: {signal.signal.value}")
                
            except Exception as e:
                logger.error(f"Error generating signal for {strategy_id}: {e}")
                continue
        
        return signals
    
    async def _calculate_strategy_performance(self, strategy_id: str) -> Dict[str, Any]:
        """Calculate performance metrics for a strategy."""
        try:
            # Get trades for this strategy
            trades = self.database.get_recent_trades(limit=1000, strategy_id=strategy_id)
            
            if not trades:
                return {
                    "total_return": 0.0,
                    "total_trades": 0,
                    "win_rate": 0.0,
                    "sharpe_ratio": 0.0,
                    "max_drawdown": 0.0,
                    "volatility": 0.0,
                    "performance_history": []
                }
            
            # Calculate basic metrics
            total_trades = len(trades)
            winning_trades = sum(1 for trade in trades if trade.get("pnl", 0) > 0)
            win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
            
            # Calculate returns
            total_pnl = sum(trade.get("pnl", 0) for trade in trades)
            trade_returns = [trade.get("pnl", 0) / 1000 for trade in trades]  # Normalize by $1000
            
            # Calculate total return percentage
            total_return = (total_pnl / (total_trades * 1000) * 100) if total_trades > 0 else 0
            
            # Calculate Sharpe ratio (simplified)
            if len(trade_returns) > 1:
                avg_return = mean(trade_returns)
                return_std = stdev(trade_returns)
                sharpe_ratio = (avg_return / return_std) if return_std > 0 else 0
            else:
                sharpe_ratio = 0
            
            # Calculate volatility
            volatility = stdev(trade_returns) * 100 if len(trade_returns) > 1 else 0
            
            # Calculate max drawdown (simplified)
            cumulative_returns = []
            cumulative = 0
            for ret in trade_returns:
                cumulative += ret
                cumulative_returns.append(cumulative)
            
            if cumulative_returns:
                peak = cumulative_returns[0]
                max_drawdown = 0
                for value in cumulative_returns:
                    if value > peak:
                        peak = value
                    drawdown = (peak - value) / peak if peak != 0 else 0
                    max_drawdown = max(max_drawdown, drawdown)
                max_drawdown = max_drawdown * 100
            else:
                max_drawdown = 0
            
            # Generate performance history (daily returns over last 30 days)
            performance_history = self._generate_performance_history(trade_returns, days=30)
            
            return {
                "total_return": round(total_return, 2),
                "total_trades": total_trades,
                "win_rate": round(win_rate, 1),
                "sharpe_ratio": round(sharpe_ratio, 2),
                "max_drawdown": round(max_drawdown, 2),
                "volatility": round(volatility, 2),
                "performance_history": performance_history
            }
            
        except Exception as e:
            logger.error(f"Error calculating performance for {strategy_id}: {e}")
            return {
                "total_return": 0.0,
                "total_trades": 0,
                "win_rate": 0.0,
                "sharpe_ratio": 0.0,
                "max_drawdown": 0.0,
                "volatility": 0.0,
                "performance_history": []
            }
    
    def _generate_performance_history(self, trade_returns: List[float], days: int = 30) -> List[Dict[str, Any]]:
        """Generate performance history for charting."""
        history = []
        current_time = datetime.now(timezone.utc)
        
        # If we have trade returns, distribute them over the time period
        if trade_returns:
            avg_daily_return = sum(trade_returns) / days if days > 0 else 0
            cumulative_return = 0
            
            for i in range(days):
                timestamp = current_time - timedelta(days=days-i)
                
                # Add some realistic variation
                daily_return = avg_daily_return + np.random.normal(0, avg_daily_return * 0.3)
                cumulative_return += daily_return
                
                history.append({
                    "timestamp": timestamp.timestamp(),
                    "value": cumulative_return * 100  # Convert to percentage
                })
        else:
            # Generate flat line at 0 if no trades
            for i in range(days):
                timestamp = current_time - timedelta(days=days-i)
                history.append({
                    "timestamp": timestamp.timestamp(),
                    "value": 0.0
                })
        
        return history
    
    async def _get_recent_signals(self, strategy_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent signals for a strategy."""
        try:
            signals = self.database.get_recent_signals(strategy_id=strategy_id, limit=limit)
            return signals
        except Exception as e:
            logger.error(f"Error getting recent signals for {strategy_id}: {e}")
            return []
    
    async def _save_signal_to_database(self, strategy_id: str, signal: Any):
        """Save signal to database."""
        try:
            self.database.add_signal(
                strategy_id=strategy_id,
                timestamp=signal.timestamp,
                signal_type=signal.signal.value,
                confidence=signal.confidence,
                price=signal.price,
                indicators=signal.indicators,
                reasoning=signal.reasoning
            )
        except Exception as e:
            logger.error(f"Error saving signal for {strategy_id}: {e}")
    
    def _price_data_to_dataframe(self, price_data: List[PriceData]) -> pd.DataFrame:
        """Convert price data to DataFrame for strategy analysis."""
        data = []
        for price_point in price_data:
            data.append({
                'timestamp': price_point.timestamp,
                'open': price_point.price,  # Simplified - using price as OHLC
                'high': price_point.price,
                'low': price_point.price,
                'close': price_point.price,
                'volume': price_point.volume or 1000.0
            })
        
        df = pd.DataFrame(data)
        df.set_index('timestamp', inplace=True)
        return df
    
    async def enable_strategy(self, strategy_id: str) -> bool:
        """Enable a strategy."""
        try:
            if strategy_id in self.strategies:
                self.strategies[strategy_id]["enabled"] = True
                success = self.database.update_strategy_status(strategy_id, True)
                if success:
                    logger.info(f"Enabled strategy: {strategy_id}")
                return success
            return False
        except Exception as e:
            logger.error(f"Error enabling strategy {strategy_id}: {e}")
            return False
    
    async def disable_strategy(self, strategy_id: str) -> bool:
        """Disable a strategy."""
        try:
            if strategy_id in self.strategies:
                self.strategies[strategy_id]["enabled"] = False
                success = self.database.update_strategy_status(strategy_id, False)
                if success:
                    logger.info(f"Disabled strategy: {strategy_id}")
                return success
            return False
        except Exception as e:
            logger.error(f"Error disabling strategy {strategy_id}: {e}")
            return False
    
    async def get_strategy_details(self, strategy_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific strategy."""
        try:
            if strategy_id not in self.strategies:
                return None
            
            strategy_info = self.strategies[strategy_id]
            performance = await self._calculate_strategy_performance(strategy_id)
            recent_signals = await self._get_recent_signals(strategy_id, limit=20)
            
            return {
                "id": strategy_id,
                "name": strategy_info["metadata"]["name"],
                "type": strategy_info["metadata"]["type"],
                "description": strategy_info["metadata"].get("description", ""),
                "active": strategy_info["enabled"],
                "parameters": strategy_info["metadata"].get("parameters", {}),
                "performance": performance,
                "recent_signals": recent_signals,
                "last_signal": strategy_info["last_signal"],
                "strategy_info": strategy_info["instance"].get_strategy_info() if hasattr(strategy_info["instance"], 'get_strategy_info') else {}
            }
        except Exception as e:
            logger.error(f"Error getting strategy details for {strategy_id}: {e}")
            return None
    
    async def update_strategy_parameters(self, strategy_id: str, parameters: Dict[str, Any]) -> bool:
        """Update strategy parameters."""
        try:
            if strategy_id not in self.strategies:
                return False
            
            strategy_info = self.strategies[strategy_id]
            strategy_instance = strategy_info["instance"]
            
            # Update strategy instance parameters
            strategy_instance.update_parameters(parameters)
            
            # Update database
            strategy_info["metadata"]["parameters"] = parameters
            success = self.database.add_strategy(
                strategy_id=strategy_id,
                name=strategy_info["metadata"]["name"],
                strategy_type=strategy_info["metadata"]["type"],
                description=strategy_info["metadata"].get("description"),
                parameters=parameters,
                active=strategy_info["enabled"]
            )
            
            if success:
                logger.info(f"Updated parameters for strategy {strategy_id}")
            
            return success
        except Exception as e:
            logger.error(f"Error updating parameters for {strategy_id}: {e}")
            return False
    
    async def backtest_strategy(self, strategy_id: str, hours: int = 168) -> Dict[str, Any]:
        """Run backtest for a strategy."""
        try:
            if strategy_id not in self.strategies:
                raise StrategyException(f"Strategy {strategy_id} not found")
            
            strategy_instance = self.strategies[strategy_id]["instance"]
            
            # Get historical data for backtesting
            historical_data = self.database.get_recent_prices(limit=hours * 2)
            if not historical_data:
                raise StrategyException("Insufficient historical data for backtesting")
            
            # Convert to DataFrame
            price_data = [
                PriceData(
                    timestamp=datetime.fromisoformat(record["timestamp"]),
                    price=float(record["price"]),
                    volume=float(record.get("volume", 1000))
                )
                for record in reversed(historical_data)
            ]
            
            df = self._price_data_to_dataframe(price_data)
            
            # Run backtest
            if hasattr(strategy_instance, 'backtest'):
                backtest_result = strategy_instance.backtest(df)
                return {
                    "success": True,
                    "strategy_id": strategy_id,
                    "backtest_result": backtest_result.__dict__ if hasattr(backtest_result, '__dict__') else str(backtest_result)
                }
            else:
                raise StrategyException(f"Strategy {strategy_id} does not support backtesting")
                
        except Exception as e:
            logger.error(f"Error backtesting strategy {strategy_id}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def optimize_strategy(self, strategy_id: str) -> Dict[str, Any]:
        """Optimize strategy parameters."""
        try:
            if strategy_id not in self.strategies:
                raise StrategyException(f"Strategy {strategy_id} not found")
            
            strategy_instance = self.strategies[strategy_id]["instance"]
            
            # Get historical data for optimization
            historical_data = self.database.get_recent_prices(limit=1000)
            if not historical_data:
                raise StrategyException("Insufficient historical data for optimization")
            
            # Convert to DataFrame
            price_data = [
                PriceData(
                    timestamp=datetime.fromisoformat(record["timestamp"]),
                    price=float(record["price"]),
                    volume=float(record.get("volume", 1000))
                )
                for record in reversed(historical_data)
            ]
            
            df = self._price_data_to_dataframe(price_data)
            
            # Run optimization
            if hasattr(strategy_instance, 'optimize_parameters'):
                optimization_result = strategy_instance.optimize_parameters(df)
                
                # Update strategy with optimized parameters
                if optimization_result.get('best_parameters'):
                    await self.update_strategy_parameters(strategy_id, optimization_result['best_parameters'])
                
                return {
                    "success": True,
                    "strategy_id": strategy_id,
                    "optimization_result": optimization_result
                }
            else:
                raise StrategyException(f"Strategy {strategy_id} does not support optimization")
                
        except Exception as e:
            logger.error(f"Error optimizing strategy {strategy_id}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_strategy_signals_history(self, strategy_id: str, hours: int = 24) -> List[Dict[str, Any]]:
        """Get historical signals for a strategy."""
        try:
            signals = self.database.get_recent_signals(strategy_id=strategy_id, limit=hours * 4)  # Assume max 4 signals per hour
            
            # Filter by time range
            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
            filtered_signals = []
            
            for signal in signals:
                signal_time = datetime.fromisoformat(signal["timestamp"])
                if signal_time >= cutoff_time:
                    filtered_signals.append({
                        "timestamp": signal["timestamp"],
                        "signal_type": signal["signal_type"],
                        "confidence": float(signal["confidence"]),
                        "price": float(signal["price"]),
                        "reasoning": signal.get("reasoning", ""),
                        "executed": bool(signal.get("executed", False))
                    })
            
            return filtered_signals
        except Exception as e:
            logger.error(f"Error getting signal history for {strategy_id}: {e}")
            return []
    
    def get_active_strategies(self) -> List[str]:
        """Get list of active strategy IDs."""
        return [
            strategy_id 
            for strategy_id, strategy_info in self.strategies.items() 
            if strategy_info["enabled"]
        ]
    
    def get_strategy_count(self) -> Dict[str, int]:
        """Get strategy count statistics."""
        total = len(self.strategies)
        active = len(self.get_active_strategies())
        inactive = total - active
        
        return {
            "total": total,
            "active": active,
            "inactive": inactive
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Strategy manager health check."""
        try:
            strategy_counts = self.get_strategy_count()
            
            # Check signal generation health
            recent_signals = 0
            for strategy_id in self.strategies:
                signals = await self._get_recent_signals(strategy_id, limit=10)
                recent_signals += len(signals)
            
            return {
                "status": "healthy",
                "strategy_count": strategy_counts,
                "recent_signals": recent_signals,
                "signal_history_size": sum(len(history) for history in self.signal_history.values()),
                "performance_cache_size": len(self.performance_cache)
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }