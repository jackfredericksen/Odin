"""
Odin Core Portfolio Manager - Portfolio Operations & Tracking

Comprehensive portfolio management system for the Odin trading bot providing
real-time portfolio tracking, P&L calculation, performance analysis, allocation
management, and rebalancing with detailed attribution and reporting.

File: odin/core/portfolio_manager.py
Author: Odin Development Team
License: MIT
"""

import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Tuple
from decimal import Decimal
from statistics import mean, stdev
from dataclasses import dataclass
import math

from .database import Database
from .models import (
    Portfolio, PortfolioSummary, Allocation, PerformanceMetrics,
    Position, TradeExecution, PriceData, OrderSide, PositionType
)
from .exceptions import (
    PortfolioManagerException, PortfolioValidationException, 
    AllocationException
)

logger = logging.getLogger(__name__)


@dataclass
class PortfolioSnapshot:
    """Portfolio state snapshot."""
    timestamp: datetime
    total_value: float
    cash_balance: float
    btc_balance: float
    btc_value: float
    positions: List[Position]
    daily_pnl: float
    total_pnl: float
    allocation: Allocation


@dataclass
class PerformanceAttribution:
    """Performance attribution by strategy."""
    strategy_name: str
    allocation: float
    return_contribution: float
    risk_contribution: float
    sharpe_ratio: float
    trades_count: int
    win_rate: float
    avg_trade_return: float


@dataclass
class RebalanceRecommendation:
    """Portfolio rebalancing recommendation."""
    strategy_name: str
    current_allocation: float
    target_allocation: float
    recommended_action: str  # "BUY", "SELL", "HOLD"
    amount_btc: float
    amount_usd: float
    priority: int  # 1=high, 2=medium, 3=low
    reason: str


class PortfolioTracker:
    """Real-time portfolio tracking."""
    
    def __init__(self, portfolio_manager: 'PortfolioManager'):
        self.portfolio_manager = portfolio_manager
        self.snapshots: List[PortfolioSnapshot] = []
        self.tracking_task: Optional[asyncio.Task] = None
        self.is_tracking = False
        
        # Performance tracking
        self.daily_snapshots: Dict[str, PortfolioSnapshot] = {}  # date -> snapshot
        self.peak_value = 0.0
        self.peak_date = datetime.now(timezone.utc)
    
    async def start_tracking(self, interval: int = 300):  # 5 minutes
        """Start portfolio tracking."""
        if self.is_tracking:
            return
        
        self.is_tracking = True
        self.tracking_task = asyncio.create_task(self._tracking_loop(interval))
        logger.info("Portfolio tracking started")
    
    async def stop_tracking(self):
        """Stop portfolio tracking."""
        if not self.is_tracking:
            return
        
        self.is_tracking = False
        if self.tracking_task:
            self.tracking_task.cancel()
            try:
                await self.tracking_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Portfolio tracking stopped")
    
    async def _tracking_loop(self, interval: int):
        """Portfolio tracking loop."""
        while self.is_tracking:
            try:
                await self._take_snapshot()
                await asyncio.sleep(interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Portfolio tracking error: {e}")
                await asyncio.sleep(30)  # Brief pause before retry
    
    async def _take_snapshot(self):
        """Take portfolio snapshot."""
        try:
            snapshot = await self.portfolio_manager._create_portfolio_snapshot()
            
            # Add to snapshots list (keep last 288 = 24 hours at 5-min intervals)
            self.snapshots.append(snapshot)
            if len(self.snapshots) > 288:
                self.snapshots.pop(0)
            
            # Track daily snapshots (keep end-of-day snapshot)
            date_key = snapshot.timestamp.date().isoformat()
            self.daily_snapshots[date_key] = snapshot
            
            # Update peak tracking
            if snapshot.total_value > self.peak_value:
                self.peak_value = snapshot.total_value
                self.peak_date = snapshot.timestamp
            
            logger.debug(f"Portfolio snapshot: ${snapshot.total_value:.2f}")
            
        except Exception as e:
            logger.error(f"Failed to take portfolio snapshot: {e}")
    
    def get_snapshots(self, hours: int = 24) -> List[PortfolioSnapshot]:
        """Get snapshots from last N hours."""
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        return [s for s in self.snapshots if s.timestamp >= cutoff]
    
    def get_daily_snapshots(self, days: int = 30) -> List[PortfolioSnapshot]:
        """Get daily end-of-day snapshots."""
        cutoff_date = (datetime.now(timezone.utc) - timedelta(days=days)).date()
        
        snapshots = []
        for date_key, snapshot in self.daily_snapshots.items():
            if datetime.fromisoformat(date_key).date() >= cutoff_date:
                snapshots.append(snapshot)
        
        return sorted(snapshots, key=lambda x: x.timestamp)


class PortfolioManager:
    """Main portfolio management system."""
    
    def __init__(self, database: Database, initial_capital: float = 100000.0):
        """
        Initialize portfolio manager.
        
        Args:
            database: Database instance
            initial_capital: Initial portfolio capital in USD
        """
        self.database = database
        self.initial_capital = initial_capital
        
        # Portfolio state
        self.cash_balance = initial_capital
        self.btc_balance = 0.0
        self.start_date = datetime.now(timezone.utc)
        
        # Portfolio tracking
        self.tracker = PortfolioTracker(self)
        
        # Target allocations by strategy
        self.target_allocations: Dict[str, float] = {
            "moving_average": 0.25,
            "rsi": 0.25,
            "bollinger_bands": 0.25,
            "macd": 0.25
        }
        
        # Rebalancing settings
        self.rebalance_threshold = 0.05  # 5% deviation triggers rebalance
        self.rebalance_frequency_hours = 24  # Daily rebalancing check
        self.last_rebalance = datetime.now(timezone.utc)
        
        logger.info(f"Portfolio manager initialized with ${initial_capital:,.2f}")
    
    async def update_allocation(self, allocations: Dict[str, float]):
        """Update target allocations."""
        # Validate allocations sum to 1.0
        total_allocation = sum(allocations.values())
        if abs(total_allocation - 1.0) > 0.01:
            raise AllocationException(
                f"Allocations sum to {total_allocation:.3f}, must sum to 1.0",
                target_allocation=allocations
            )
        
        self.target_allocations = allocations.copy()
        logger.info(f"Updated target allocations: {allocations}")
    
    async def execute_trade(self, trade: TradeExecution, current_price: float):
        """
        Execute trade and update portfolio.
        
        Args:
            trade: Trade execution details
            current_price: Current market price
        """
        try:
            # Calculate trade impact
            trade_value = trade.quantity * trade.price
            total_cost = trade.total_cost or trade_value
            
            if trade.side == OrderSide.BUY:
                # Buy BTC with USD
                if self.cash_balance < total_cost:
                    raise PortfolioValidationException(
                        f"Insufficient cash: ${self.cash_balance:.2f} < ${total_cost:.2f}",
                        validation_errors=["insufficient_cash"]
                    )
                
                self.cash_balance -= total_cost
                self.btc_balance += trade.quantity
                
                logger.info(f"BUY executed: {trade.quantity:.6f} BTC at ${trade.price:.2f}")
                
            else:  # SELL
                # Sell BTC for USD
                if self.btc_balance < trade.quantity:
                    raise PortfolioValidationException(
                        f"Insufficient BTC: {self.btc_balance:.6f} < {trade.quantity:.6f}",
                        validation_errors=["insufficient_btc"]
                    )
                
                self.btc_balance -= trade.quantity
                self.cash_balance += (trade_value - trade.fee)
                
                logger.info(f"SELL executed: {trade.quantity:.6f} BTC at ${trade.price:.2f}")
            
            # Save trade to database
            await self.database.save_trade(trade)
            
            # Log portfolio state
            total_value = await self.get_total_value(current_price)
            logger.info(
                f"Portfolio update: "
                f"Cash=${self.cash_balance:.2f}, "
                f"BTC={self.btc_balance:.6f}, "
                f"Total=${total_value:.2f}"
            )
            
        except Exception as e:
            logger.error(f"Trade execution error: {e}")
            raise PortfolioManagerException(
                message=f"Failed to execute trade: {str(e)}",
                context={"trade_id": str(trade.id)},
                original_exception=e
            )
    
    async def get_total_value(self, current_price: float) -> float:
        """Get total portfolio value."""
        btc_value = self.btc_balance * current_price
        return self.cash_balance + btc_value
    
    async def get_portfolio_summary(self, current_price: float) -> PortfolioSummary:
        """Get portfolio summary for dashboard."""
        try:
            total_value = await self.get_total_value(current_price)
            daily_pnl = await self._calculate_daily_pnl(current_price)
            daily_pnl_percent = daily_pnl / self.initial_capital if self.initial_capital > 0 else 0
            
            # Get position and order counts
            positions = await self._get_current_positions()
            pending_orders = await self._get_pending_orders()
            
            # Calculate exposure
            btc_value = self.btc_balance * current_price
            exposure = btc_value / total_value if total_value > 0 else 0
            
            # Determine risk level
            risk_level = "Low"
            if exposure > 0.8:
                risk_level = "High"
            elif exposure > 0.5:
                risk_level = "Medium"
            
            return PortfolioSummary(
                total_value=total_value,
                daily_pnl=daily_pnl,
                daily_pnl_percent=daily_pnl_percent,
                positions_count=len(positions),
                active_orders_count=len(pending_orders),
                active_strategies_count=len(self.target_allocations),
                current_exposure=exposure,
                risk_level=risk_level
            )
            
        except Exception as e:
            logger.error(f"Portfolio summary error: {e}")
            raise PortfolioManagerException(
                message=f"Failed to get portfolio summary: {str(e)}",
                original_exception=e
            )
    
    async def get_allocation(self, current_price: float) -> Allocation:
        """Get current portfolio allocation."""
        try:
            btc_value = self.btc_balance * current_price
            total_value = self.cash_balance + btc_value
            
            # Get strategy allocations
            strategy_allocations = await self._calculate_strategy_allocations(current_price)
            
            return Allocation(
                cash=self.cash_balance,
                btc=self.btc_balance,
                strategy_allocations=strategy_allocations,
                total_value=total_value,
                btc_percentage=btc_value / total_value if total_value > 0 else 0,
                cash_percentage=self.cash_balance / total_value if total_value > 0 else 1
            )
            
        except Exception as e:
            logger.error(f"Allocation calculation error: {e}")
            raise PortfolioManagerException(
                message=f"Failed to calculate allocation: {str(e)}",
                original_exception=e
            )
    
    async def get_performance_metrics(self, hours: int = 24) -> PerformanceMetrics:
        """Calculate performance metrics."""
        try:
            # Get time range
            end_time = datetime.now(timezone.utc)
            start_time = end_time - timedelta(hours=hours)
            
            # Get price history and snapshots
            daily_snapshots = self.tracker.get_daily_snapshots(days=hours // 24 + 1)
            
            if len(daily_snapshots) < 2:
                # Not enough data, return basic metrics
                return PerformanceMetrics(
                    period_start=start_time,
                    period_end=end_time,
                    total_return=0.0,
                    annualized_return=0.0,
                    volatility=0.0,
                    total_trades=0
                )
            
            # Calculate returns
            start_value = daily_snapshots[0].total_value
            end_value = daily_snapshots[-1].total_value
            total_return = (end_value - start_value) / start_value
            
            # Calculate daily returns
            daily_returns = []
            for i in range(1, len(daily_snapshots)):
                prev_value = daily_snapshots[i-1].total_value
                curr_value = daily_snapshots[i].total_value
                daily_return = (curr_value - prev_value) / prev_value
                daily_returns.append(daily_return)
            
            # Calculate annualized metrics
            days_elapsed = len(daily_returns)
            annualized_return = ((1 + total_return) ** (365 / days_elapsed) - 1) if days_elapsed > 0 else 0
            volatility = stdev(daily_returns) * math.sqrt(365) if len(daily_returns) > 1 else 0
            
            # Calculate Sharpe ratio (assuming 2% risk-free rate)
            risk_free_rate = 0.02
            sharpe_ratio = (annualized_return - risk_free_rate) / volatility if volatility > 0 else 0
            
            # Calculate Sortino ratio (downside deviation)
            downside_returns = [r for r in daily_returns if r < 0]
            downside_deviation = stdev(downside_returns) * math.sqrt(365) if len(downside_returns) > 1 else volatility
            sortino_ratio = (annualized_return - risk_free_rate) / downside_deviation if downside_deviation > 0 else 0
            
            # Calculate max drawdown
            max_drawdown = await self._calculate_max_drawdown(daily_snapshots)
            
            # Get trading statistics
            trades = await self._get_recent_trades(hours)
            total_trades = len(trades)
            win_rate = await self._calculate_win_rate(trades) if trades else 0
            profit_factor = await self._calculate_profit_factor(trades) if trades else 0
            avg_trade_return = mean([t.total_cost / (t.quantity * t.price) - 1 for t in trades]) if trades else 0
            
            return PerformanceMetrics(
                period_start=start_time,
                period_end=end_time,
                total_return=total_return * 100,  # Convert to percentage
                annualized_return=annualized_return * 100,
                volatility=volatility * 100,
                sharpe_ratio=sharpe_ratio,
                sortino_ratio=sortino_ratio,
                max_drawdown=max_drawdown * 100,
                total_trades=total_trades,
                win_rate=win_rate,
                profit_factor=profit_factor,
                avg_trade_return=avg_trade_return * 100
            )
            
        except Exception as e:
            logger.error(f"Performance metrics error: {e}")
            raise PortfolioManagerException(
                message=f"Failed to calculate performance metrics: {str(e)}",
                original_exception=e
            )
    
    async def get_performance_attribution(self, hours: int = 24) -> List[PerformanceAttribution]:
        """Calculate performance attribution by strategy."""
        try:
            attributions = []
            
            for strategy_name in self.target_allocations.keys():
                # Get strategy-specific data
                strategy_trades = await self.database.get_strategy_trades(strategy_name, hours)
                allocation = await self._get_strategy_allocation_percentage(strategy_name)
                
                if not strategy_trades:
                    attributions.append(PerformanceAttribution(
                        strategy_name=strategy_name,
                        allocation=allocation,
                        return_contribution=0.0,
                        risk_contribution=0.0,
                        sharpe_ratio=0.0,
                        trades_count=0,
                        win_rate=0.0,
                        avg_trade_return=0.0
                    ))
                    continue
                
                # Calculate strategy returns
                strategy_returns = []
                total_pnl = 0
                
                for trade in strategy_trades:
                    # Calculate trade P&L
                    if trade.side == "BUY":
                        # For buys, P&L is unrealized until sold
                        current_price = await self._get_current_price()
                        pnl = (current_price - trade.price) * trade.quantity - trade.fee
                    else:
                        # For sells, P&L is realized
                        # This is simplified - in reality we'd match with corresponding buys
                        pnl = trade.total_cost - trade.fee
                    
                    total_pnl += pnl
                    trade_return = pnl / (trade.quantity * trade.price)
                    strategy_returns.append(trade_return)
                
                # Calculate metrics
                avg_return = mean(strategy_returns) if strategy_returns else 0
                return_volatility = stdev(strategy_returns) if len(strategy_returns) > 1 else 0
                sharpe_ratio = avg_return / return_volatility if return_volatility > 0 else 0
                
                # Calculate contribution to portfolio
                portfolio_value = await self.get_total_value(await self._get_current_price())
                return_contribution = (total_pnl / portfolio_value) * 100 if portfolio_value > 0 else 0
                risk_contribution = allocation * return_volatility * 100
                
                # Trading statistics
                winning_trades = sum(1 for r in strategy_returns if r > 0)
                win_rate = winning_trades / len(strategy_returns) if strategy_returns else 0
                
                attributions.append(PerformanceAttribution(
                    strategy_name=strategy_name,
                    allocation=allocation,
                    return_contribution=return_contribution,
                    risk_contribution=risk_contribution,
                    sharpe_ratio=sharpe_ratio,
                    trades_count=len(strategy_trades),
                    win_rate=win_rate,
                    avg_trade_return=avg_return * 100
                ))
            
            return attributions
            
        except Exception as e:
            logger.error(f"Performance attribution error: {e}")
            raise PortfolioManagerException(
                message=f"Failed to calculate performance attribution: {str(e)}",
                original_exception=e
            )
    
    async def get_rebalance_recommendations(self, current_price: float) -> List[RebalanceRecommendation]:
        """Get portfolio rebalancing recommendations."""
        try:
            recommendations = []
            current_allocations = await self._calculate_strategy_allocations(current_price)
            total_value = await self.get_total_value(current_price)
            
            for strategy_name, target_allocation in self.target_allocations.items():
                current_allocation = current_allocations.get(strategy_name, 0.0)
                allocation_diff = target_allocation - current_allocation
                
                # Check if rebalancing is needed
                if abs(allocation_diff) > self.rebalance_threshold:
                    # Calculate amounts
                    target_value = target_allocation * total_value
                    current_value = current_allocation * total_value
                    amount_usd = target_value - current_value
                    amount_btc = amount_usd / current_price
                    
                    # Determine action
                    if allocation_diff > 0:
                        action = "BUY"
                        priority = 1 if allocation_diff > 0.1 else 2
                        reason = f"Underallocated by {allocation_diff:.1%}"
                    else:
                        action = "SELL"
                        priority = 1 if allocation_diff < -0.1 else 2
                        reason = f"Overallocated by {abs(allocation_diff):.1%}"
                    
                    recommendations.append(RebalanceRecommendation(
                        strategy_name=strategy_name,
                        current_allocation=current_allocation,
                        target_allocation=target_allocation,
                        recommended_action=action,
                        amount_btc=abs(amount_btc),
                        amount_usd=abs(amount_usd),
                        priority=priority,
                        reason=reason
                    ))
            
            # Sort by priority
            recommendations.sort(key=lambda x: x.priority)
            return recommendations
            
        except Exception as e:
            logger.error(f"Rebalance recommendations error: {e}")
            raise PortfolioManagerException(
                message=f"Failed to get rebalance recommendations: {str(e)}",
                original_exception=e
            )
    
    async def execute_rebalance(self, current_price: float) -> Dict[str, Any]:
        """Execute portfolio rebalancing."""
        try:
            recommendations = await self.get_rebalance_recommendations(current_price)
            
            if not recommendations:
                return {
                    "rebalanced": False,
                    "reason": "Portfolio already balanced",
                    "recommendations": []
                }
            
            # Execute high-priority rebalancing
            executed_actions = []
            
            for rec in recommendations:
                if rec.priority == 1:  # Only execute high-priority rebalances
                    # This would integrate with trading engine to execute trades
                    # For now, we'll log the intended action
                    logger.info(
                        f"Rebalancing {rec.strategy_name}: "
                        f"{rec.recommended_action} {rec.amount_btc:.6f} BTC "
                        f"(${rec.amount_usd:.2f})"
                    )
                    executed_actions.append(rec)
            
            self.last_rebalance = datetime.now(timezone.utc)
            
            return {
                "rebalanced": len(executed_actions) > 0,
                "executed_actions": len(executed_actions),
                "recommendations": [r.__dict__ for r in recommendations],
                "timestamp": self.last_rebalance.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Rebalancing error: {e}")
            raise PortfolioManagerException(
                message=f"Failed to execute rebalancing: {str(e)}",
                original_exception=e
            )
    
    async def _create_portfolio_snapshot(self) -> PortfolioSnapshot:
        """Create current portfolio snapshot."""
        current_price = await self._get_current_price()
        total_value = await self.get_total_value(current_price)
        btc_value = self.btc_balance * current_price
        
        # Calculate P&L
        daily_pnl = await self._calculate_daily_pnl(current_price)
        total_pnl = total_value - self.initial_capital
        
        # Get positions and allocation
        positions = await self._get_current_positions()
        allocation = await self.get_allocation(current_price)
        
        return PortfolioSnapshot(
            timestamp=datetime.now(timezone.utc),
            total_value=total_value,
            cash_balance=self.cash_balance,
            btc_balance=self.btc_balance,
            btc_value=btc_value,
            positions=positions,
            daily_pnl=daily_pnl,
            total_pnl=total_pnl,
            allocation=allocation
        )
    
    # Helper methods
    async def _get_current_price(self) -> float:
        """Get current BTC price."""
        latest_price = await self.database.get_latest_price()
        return float(latest_price.price) if latest_price else 50000.0
    
    async def _calculate_daily_pnl(self, current_price: float) -> float:
        """Calculate today's P&L."""
        today = datetime.now(timezone.utc).date()
        
        # Get yesterday's closing value
        yesterday_snapshots = self.tracker.get_daily_snapshots(days=2)
        if len(yesterday_snapshots) >= 2:
            yesterday_value = yesterday_snapshots[-2].total_value
        else:
            yesterday_value = self.initial_capital
        
        current_value = await self.get_total_value(current_price)
        return current_value - yesterday_value
    
    async def _calculate_strategy_allocations(self, current_price: float) -> Dict[str, float]:
        """Calculate current strategy allocations."""
        # This would calculate actual allocations based on positions
        # For now, return target allocations as placeholder
        total_value = await self.get_total_value(current_price)
        
        if total_value == 0:
            return {}
        
        # Get actual strategy positions/values
        strategy_values = {}
        for strategy_name in self.target_allocations.keys():
            # This would query database for strategy-specific positions
            strategy_value = total_value * self.target_allocations[strategy_name]  # Placeholder
            strategy_values[strategy_name] = strategy_value / total_value
        
        return strategy_values
    
    async def _get_strategy_allocation_percentage(self, strategy_name: str) -> float:
        """Get allocation percentage for strategy."""
        current_price = await self._get_current_price()
        allocations = await self._calculate_strategy_allocations(current_price)
        return allocations.get(strategy_name, 0.0)
    
    async def _get_current_positions(self) -> List[Position]:
        """Get current open positions."""
        # This would query database for open positions
        return []
    
    async def _get_pending_orders(self) -> List:
        """Get pending orders."""
        # This would query database for pending orders
        return []
    
    async def _get_recent_trades(self, hours: int) -> List:
        """Get recent trades."""
        # This would query database for recent trades
        return []
    
    async def _calculate_win_rate(self, trades: List) -> float:
        """Calculate win rate from trades."""
        if not trades:
            return 0.0
        
        # This would calculate actual win rate
        return 0.55  # Placeholder
    
    async def _calculate_profit_factor(self, trades: List) -> float:
        """Calculate profit factor from trades."""
        if not trades:
            return 0.0
        
        # This would calculate actual profit factor
        return 1.25  # Placeholder
    
    async def _calculate_max_drawdown(self, snapshots: List[PortfolioSnapshot]) -> float:
        """Calculate maximum drawdown from snapshots."""
        if len(snapshots) < 2:
            return 0.0
        
        peak = 0
        max_drawdown = 0
        
        for snapshot in snapshots:
            if snapshot.total_value > peak:
                peak = snapshot.total_value
            
            drawdown = (peak - snapshot.total_value) / peak if peak > 0 else 0
            max_drawdown = max(max_drawdown, drawdown)
        
        return max_drawdown
    
    async def health_check(self) -> Dict[str, Any]:
        """Portfolio manager health check."""
        try:
            current_price = await self._get_current_price()
            total_value = await self.get_total_value(current_price)
            
            return {
                "total_value": total_value,
                "cash_balance": self.cash_balance,
                "btc_balance": self.btc_balance,
                "tracking_active": self.tracker.is_tracking,
                "snapshots_count": len(self.tracker.snapshots),
                "target_allocations": self.target_allocations,
                "last_rebalance": self.last_rebalance.isoformat(),
                "rebalance_threshold": self.rebalance_threshold
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "cash_balance": self.cash_balance,
                "btc_balance": self.btc_balance
            }