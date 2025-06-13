"""
Odin Core Risk Manager - Risk Management & Controls

Comprehensive risk management system for the Odin trading bot providing
position sizing, drawdown protection, exposure limits, and risk monitoring
with real-time alerts and automated risk controls.

File: odin/core/risk_manager.py
Author: Odin Development Team
License: MIT
"""

import asyncio
import logging
import math
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from statistics import mean, stdev
from typing import Any, Callable, Dict, List, Optional, Tuple

from .database import Database
from .exceptions import (
    DrawdownLimitException,
    PositionSizeException,
    RiskLimitExceededException,
    RiskManagerException,
)
from .models import (
    DrawdownAlert,
    OrderSide,
    PortfolioSummary,
    Position,
    PositionType,
    RiskLimits,
    RiskMetrics,
    TradeOrder,
)

logger = logging.getLogger(__name__)


@dataclass
class RiskCalculation:
    """Risk calculation result."""

    is_allowed: bool
    risk_score: float  # 0-1 scale
    max_position_size: float
    stop_loss_price: Optional[float]
    take_profit_price: Optional[float]
    reason: Optional[str] = None
    warnings: List[str] = None

    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []


@dataclass
class VaRCalculation:
    """Value at Risk calculation result."""

    var_1d_95: float
    var_1d_99: float
    expected_shortfall: float
    confidence_level: float
    holding_period_days: int
    method: str  # "historical", "parametric", "monte_carlo"


class RiskMonitor:
    """Real-time risk monitoring."""

    def __init__(self, risk_manager: "RiskManager"):
        self.risk_manager = risk_manager
        self.alert_callbacks: List[Callable] = []
        self.monitoring_task: Optional[asyncio.Task] = None
        self.is_monitoring = False

        # Alert thresholds
        self.alert_thresholds = {
            "drawdown_warning": 0.05,  # 5%
            "drawdown_critical": 0.10,  # 10%
            "exposure_warning": 0.80,  # 80%
            "exposure_critical": 0.95,  # 95%
            "var_breach": 0.02,  # 2%
        }

    def add_alert_callback(self, callback: Callable[[Dict[str, Any]], None]):
        """Add alert callback."""
        self.alert_callbacks.append(callback)

    async def start_monitoring(self, interval: int = 60):
        """Start risk monitoring."""
        if self.is_monitoring:
            return

        self.is_monitoring = True
        self.monitoring_task = asyncio.create_task(self._monitoring_loop(interval))
        logger.info("Risk monitoring started")

    async def stop_monitoring(self):
        """Stop risk monitoring."""
        if not self.is_monitoring:
            return

        self.is_monitoring = False
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass

        logger.info("Risk monitoring stopped")

    async def _monitoring_loop(self, interval: int):
        """Risk monitoring loop."""
        while self.is_monitoring:
            try:
                await self._check_risk_metrics()
                await asyncio.sleep(interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Risk monitoring error: {e}")
                await asyncio.sleep(5)

    async def _check_risk_metrics(self):
        """Check all risk metrics and trigger alerts."""
        try:
            # Get current risk metrics
            risk_metrics = await self.risk_manager.get_current_risk_metrics()

            # Check drawdown
            await self._check_drawdown(risk_metrics)

            # Check exposure
            await self._check_exposure(risk_metrics)

            # Check VaR breaches
            await self._check_var_breaches(risk_metrics)

            # Check position concentrations
            await self._check_concentrations(risk_metrics)

        except Exception as e:
            logger.error(f"Risk metrics check error: {e}")

    async def _check_drawdown(self, risk_metrics: RiskMetrics):
        """Check drawdown limits."""
        current_dd = abs(risk_metrics.current_drawdown)

        if current_dd >= self.alert_thresholds["drawdown_critical"]:
            alert = DrawdownAlert(
                current_drawdown=current_dd,
                threshold=self.alert_thresholds["drawdown_critical"],
                severity="CRITICAL",
                peak_value=risk_metrics.peak_value,
                current_value=risk_metrics.peak_value * (1 - current_dd),
                days_in_drawdown=self._calculate_days_in_drawdown(risk_metrics),
                recommended_actions=[
                    "Reduce position sizes",
                    "Pause new trades",
                    "Review strategy performance",
                    "Consider emergency stop",
                ],
            )
            await self._trigger_alert("drawdown_critical", alert.dict())

        elif current_dd >= self.alert_thresholds["drawdown_warning"]:
            alert = DrawdownAlert(
                current_drawdown=current_dd,
                threshold=self.alert_thresholds["drawdown_warning"],
                severity="WARNING",
                peak_value=risk_metrics.peak_value,
                current_value=risk_metrics.peak_value * (1 - current_dd),
                days_in_drawdown=self._calculate_days_in_drawdown(risk_metrics),
                recommended_actions=[
                    "Monitor closely",
                    "Review recent trades",
                    "Consider reducing exposure",
                ],
            )
            await self._trigger_alert("drawdown_warning", alert.dict())

    async def _check_exposure(self, risk_metrics: RiskMetrics):
        """Check exposure limits."""
        exposure = risk_metrics.current_exposure

        if exposure >= self.alert_thresholds["exposure_critical"]:
            await self._trigger_alert(
                "exposure_critical",
                {
                    "current_exposure": exposure,
                    "threshold": self.alert_thresholds["exposure_critical"],
                    "message": "Critical exposure level reached",
                    "recommended_actions": ["Reduce positions immediately"],
                },
            )
        elif exposure >= self.alert_thresholds["exposure_warning"]:
            await self._trigger_alert(
                "exposure_warning",
                {
                    "current_exposure": exposure,
                    "threshold": self.alert_thresholds["exposure_warning"],
                    "message": "High exposure level",
                    "recommended_actions": ["Consider reducing positions"],
                },
            )

    async def _check_var_breaches(self, risk_metrics: RiskMetrics):
        """Check VaR breaches."""
        if risk_metrics.var_1d_95:
            # Get actual daily P&L
            actual_pnl = await self._get_daily_pnl()

            # Check if actual loss exceeds VaR
            if actual_pnl < 0 and abs(actual_pnl) > abs(risk_metrics.var_1d_95):
                await self._trigger_alert(
                    "var_breach",
                    {
                        "actual_pnl": actual_pnl,
                        "var_95": risk_metrics.var_1d_95,
                        "breach_amount": abs(actual_pnl) - abs(risk_metrics.var_1d_95),
                        "message": "VaR limit breached",
                        "recommended_actions": [
                            "Review risk models",
                            "Assess portfolio",
                        ],
                    },
                )

    async def _check_concentrations(self, risk_metrics: RiskMetrics):
        """Check concentration risks."""
        max_concentration = (
            max(risk_metrics.strategy_concentrations.values())
            if risk_metrics.strategy_concentrations
            else 0
        )

        if max_concentration > 0.7:  # 70% in single strategy
            strategy_name = max(
                risk_metrics.strategy_concentrations.items(), key=lambda x: x[1]
            )[0]
            await self._trigger_alert(
                "concentration_risk",
                {
                    "strategy_name": strategy_name,
                    "concentration": max_concentration,
                    "message": f"High concentration in {strategy_name}",
                    "recommended_actions": [
                        "Rebalance portfolio",
                        "Reduce strategy allocation",
                    ],
                },
            )

    def _calculate_days_in_drawdown(self, risk_metrics: RiskMetrics) -> int:
        """Calculate days in current drawdown."""
        if risk_metrics.peak_date:
            days = (datetime.now(timezone.utc) - risk_metrics.peak_date).days
            return max(0, days)
        return 0

    async def _get_daily_pnl(self) -> float:
        """Get today's P&L."""
        # This would be implemented to get actual daily P&L
        # For now, return 0 as placeholder
        return 0.0

    async def _trigger_alert(self, alert_type: str, alert_data: Dict[str, Any]):
        """Trigger risk alert."""
        alert = {
            "type": alert_type,
            "timestamp": datetime.now(timezone.utc),
            "data": alert_data,
        }

        logger.warning(f"Risk alert triggered: {alert_type}")

        # Notify callbacks
        for callback in self.alert_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(alert)
                else:
                    callback(alert)
            except Exception as e:
                logger.error(f"Risk alert callback error: {e}")


class RiskManager:
    """Main risk management system."""

    def __init__(self, database: Database, initial_capital: float = 100000.0):
        """
        Initialize risk manager.

        Args:
            database: Database instance
            initial_capital: Initial portfolio capital
        """
        self.database = database
        self.initial_capital = initial_capital

        # Risk limits (configurable)
        self.risk_limits = RiskLimits(
            max_position_size=0.95,  # 95% max position
            max_drawdown=0.15,  # 15% max drawdown
            max_daily_loss=0.05,  # 5% max daily loss
            max_correlation=0.7,  # 70% max strategy correlation
            max_trade_size=0.1,  # 10% max single trade
            min_liquidity=1000000,  # $1M min liquidity
            max_strategy_allocation=0.5,  # 50% max per strategy
            max_sector_exposure=1.0,  # 100% sector exposure (crypto only)
        )

        # Risk monitoring
        self.monitor = RiskMonitor(self)

        # Emergency stop flag
        self.emergency_stop = False

        # Risk calculation cache
        self._risk_cache: Dict[str, Any] = {}
        self._cache_expiry = datetime.now(timezone.utc)

        logger.info("Risk manager initialized")

    def update_risk_limits(self, new_limits: RiskLimits):
        """Update risk limits."""
        self.risk_limits = new_limits
        logger.info("Risk limits updated")

    def set_emergency_stop(self, enabled: bool):
        """Set emergency stop flag."""
        self.emergency_stop = enabled
        if enabled:
            logger.critical("EMERGENCY STOP ACTIVATED")
        else:
            logger.info("Emergency stop deactivated")

    async def validate_trade(
        self, order: TradeOrder, current_price: float
    ) -> RiskCalculation:
        """
        Validate a trade order against risk limits.

        Args:
            order: Trade order to validate
            current_price: Current market price

        Returns:
            RiskCalculation with validation result
        """
        try:
            # Check emergency stop
            if self.emergency_stop:
                return RiskCalculation(
                    is_allowed=False,
                    risk_score=1.0,
                    max_position_size=0,
                    stop_loss_price=None,
                    take_profit_price=None,
                    reason="Emergency stop activated",
                )

            # Get current portfolio state
            portfolio_value = await self._get_portfolio_value()
            current_positions = await self._get_current_positions()
            current_exposure = await self._calculate_current_exposure(
                current_positions, current_price
            )

            # Calculate position value
            position_value = order.quantity * current_price
            position_size_pct = position_value / portfolio_value

            warnings = []

            # Check position size limit
            if position_size_pct > self.risk_limits.max_trade_size:
                return RiskCalculation(
                    is_allowed=False,
                    risk_score=1.0,
                    max_position_size=self.risk_limits.max_trade_size
                    * portfolio_value
                    / current_price,
                    stop_loss_price=None,
                    take_profit_price=None,
                    reason=f"Trade size {position_size_pct:.1%} exceeds limit {self.risk_limits.max_trade_size:.1%}",
                )

            # Check total exposure after trade
            new_exposure = current_exposure
            if order.side == OrderSide.BUY:
                new_exposure += position_size_pct
            else:
                new_exposure -= position_size_pct

            if new_exposure > self.risk_limits.max_position_size:
                return RiskCalculation(
                    is_allowed=False,
                    risk_score=1.0,
                    max_position_size=(
                        self.risk_limits.max_position_size - current_exposure
                    )
                    * portfolio_value
                    / current_price,
                    stop_loss_price=None,
                    take_profit_price=None,
                    reason=f"Total exposure {new_exposure:.1%} would exceed limit {self.risk_limits.max_position_size:.1%}",
                )

            # Check drawdown limits
            current_drawdown = await self._calculate_current_drawdown()
            if abs(current_drawdown) > self.risk_limits.max_drawdown:
                return RiskCalculation(
                    is_allowed=False,
                    risk_score=1.0,
                    max_position_size=0,
                    stop_loss_price=None,
                    take_profit_price=None,
                    reason=f"Current drawdown {current_drawdown:.1%} exceeds limit {self.risk_limits.max_drawdown:.1%}",
                )

            # Check daily loss limit
            daily_pnl_pct = await self._calculate_daily_pnl_percentage()
            if daily_pnl_pct < -self.risk_limits.max_daily_loss:
                return RiskCalculation(
                    is_allowed=False,
                    risk_score=1.0,
                    max_position_size=0,
                    stop_loss_price=None,
                    take_profit_price=None,
                    reason=f"Daily loss {abs(daily_pnl_pct):.1%} exceeds limit {self.risk_limits.max_daily_loss:.1%}",
                )

            # Check strategy allocation limit
            strategy_allocation = await self._get_strategy_allocation(
                order.strategy_name
            )
            strategy_position_value = 0
            if order.side == OrderSide.BUY:
                strategy_position_value = position_value

            new_strategy_allocation = (
                strategy_allocation + strategy_position_value
            ) / portfolio_value
            if new_strategy_allocation > self.risk_limits.max_strategy_allocation:
                max_additional = (
                    self.risk_limits.max_strategy_allocation * portfolio_value
                ) - strategy_allocation
                return RiskCalculation(
                    is_allowed=False,
                    risk_score=0.9,
                    max_position_size=max(0, max_additional / current_price),
                    stop_loss_price=None,
                    take_profit_price=None,
                    reason=f"Strategy allocation {new_strategy_allocation:.1%} would exceed limit {self.risk_limits.max_strategy_allocation:.1%}",
                )

            # Add warnings for high risk levels
            if position_size_pct > self.risk_limits.max_trade_size * 0.8:
                warnings.append(f"Large trade size: {position_size_pct:.1%}")

            if new_exposure > self.risk_limits.max_position_size * 0.8:
                warnings.append(f"High total exposure: {new_exposure:.1%}")

            # Calculate risk score (0 = low risk, 1 = high risk)
            risk_score = self._calculate_risk_score(
                position_size_pct, new_exposure, current_drawdown, daily_pnl_pct
            )

            # Calculate stop loss and take profit
            stop_loss_price = self._calculate_stop_loss(order, current_price)
            take_profit_price = self._calculate_take_profit(order, current_price)

            return RiskCalculation(
                is_allowed=True,
                risk_score=risk_score,
                max_position_size=order.quantity,
                stop_loss_price=stop_loss_price,
                take_profit_price=take_profit_price,
                warnings=warnings,
            )

        except Exception as e:
            logger.error(f"Trade validation error: {e}")
            raise RiskManagerException(
                message=f"Failed to validate trade: {str(e)}",
                context={"order_id": str(order.id)},
                original_exception=e,
            )

    def _calculate_risk_score(
        self,
        position_size_pct: float,
        exposure: float,
        drawdown: float,
        daily_pnl_pct: float,
    ) -> float:
        """Calculate overall risk score (0-1)."""
        # Normalize each risk factor to 0-1 scale
        size_risk = min(1.0, position_size_pct / self.risk_limits.max_trade_size)
        exposure_risk = min(1.0, exposure / self.risk_limits.max_position_size)
        drawdown_risk = min(1.0, abs(drawdown) / self.risk_limits.max_drawdown)
        daily_loss_risk = min(
            1.0, abs(min(0, daily_pnl_pct)) / self.risk_limits.max_daily_loss
        )

        # Weighted average of risk factors
        weights = [0.3, 0.3, 0.25, 0.15]  # size, exposure, drawdown, daily_loss
        risk_factors = [size_risk, exposure_risk, drawdown_risk, daily_loss_risk]

        return sum(w * f for w, f in zip(weights, risk_factors))

    def _calculate_stop_loss(
        self, order: TradeOrder, current_price: float
    ) -> Optional[float]:
        """Calculate stop loss price."""
        if order.stop_loss:
            return order.stop_loss

        # Default stop loss based on risk per trade
        risk_per_trade = 0.02  # 2% default risk

        if order.side == OrderSide.BUY:
            return current_price * (1 - risk_per_trade)
        else:
            return current_price * (1 + risk_per_trade)

    def _calculate_take_profit(
        self, order: TradeOrder, current_price: float
    ) -> Optional[float]:
        """Calculate take profit price."""
        if order.take_profit:
            return order.take_profit

        # Default 2:1 risk-reward ratio
        risk_per_trade = 0.02
        reward_ratio = 2.0

        if order.side == OrderSide.BUY:
            return current_price * (1 + risk_per_trade * reward_ratio)
        else:
            return current_price * (1 - risk_per_trade * reward_ratio)

    async def calculate_position_size(
        self,
        strategy_name: str,
        signal_confidence: float,
        current_price: float,
        risk_per_trade: float = 0.02,
    ) -> float:
        """
        Calculate optimal position size based on Kelly criterion and risk management.

        Args:
            strategy_name: Strategy requesting position
            signal_confidence: Signal confidence (0-1)
            current_price: Current market price
            risk_per_trade: Risk per trade (default 2%)

        Returns:
            Optimal position size in BTC
        """
        try:
            # Get portfolio value and strategy performance
            portfolio_value = await self._get_portfolio_value()
            strategy_stats = await self._get_strategy_statistics(strategy_name)

            # Calculate Kelly fraction
            win_rate = strategy_stats.get("win_rate", 0.5)
            avg_win = strategy_stats.get("avg_win", 0.02)
            avg_loss = strategy_stats.get("avg_loss", 0.02)

            if avg_loss > 0:
                kelly_fraction = (win_rate / avg_loss) - ((1 - win_rate) / avg_win)
                kelly_fraction = max(0, min(0.25, kelly_fraction))  # Cap at 25%
            else:
                kelly_fraction = 0.1  # Default to 10%

            # Adjust for signal confidence
            confidence_adjusted_fraction = kelly_fraction * signal_confidence

            # Apply risk per trade limit
            max_risk_fraction = risk_per_trade / avg_loss if avg_loss > 0 else 0.1
            final_fraction = min(confidence_adjusted_fraction, max_risk_fraction)

            # Apply position size limits
            max_position_value = portfolio_value * self.risk_limits.max_trade_size
            kelly_position_value = portfolio_value * final_fraction

            position_value = min(max_position_value, kelly_position_value)
            position_size = position_value / current_price

            logger.debug(
                f"Position sizing for {strategy_name}: "
                f"Kelly={kelly_fraction:.3f}, "
                f"Confidence={signal_confidence:.3f}, "
                f"Final={final_fraction:.3f}, "
                f"Size={position_size:.6f} BTC"
            )

            return position_size

        except Exception as e:
            logger.error(f"Position sizing error: {e}")
            # Fallback to conservative sizing
            portfolio_value = await self._get_portfolio_value()
            fallback_size = (portfolio_value * 0.01) / current_price  # 1% fallback
            return fallback_size

    async def calculate_var(
        self,
        confidence_level: float = 0.95,
        holding_period: int = 1,
        method: str = "historical",
    ) -> VaRCalculation:
        """
        Calculate Value at Risk.

        Args:
            confidence_level: Confidence level (0.95 for 95% VaR)
            holding_period: Holding period in days
            method: Calculation method ("historical", "parametric")

        Returns:
            VaR calculation result
        """
        try:
            # Get historical returns
            returns = await self._get_historical_returns(days=252)  # 1 year

            if len(returns) < 30:
                logger.warning("Insufficient historical data for VaR calculation")
                return VaRCalculation(
                    var_1d_95=0.0,
                    var_1d_99=0.0,
                    expected_shortfall=0.0,
                    confidence_level=confidence_level,
                    holding_period_days=holding_period,
                    method=method,
                )

            if method == "historical":
                return await self._calculate_historical_var(
                    returns, confidence_level, holding_period
                )
            elif method == "parametric":
                return await self._calculate_parametric_var(
                    returns, confidence_level, holding_period
                )
            else:
                raise ValueError(f"Unknown VaR method: {method}")

        except Exception as e:
            logger.error(f"VaR calculation error: {e}")
            raise RiskManagerException(
                message=f"Failed to calculate VaR: {str(e)}", original_exception=e
            )

    async def _calculate_historical_var(
        self, returns: List[float], confidence_level: float, holding_period: int
    ) -> VaRCalculation:
        """Calculate historical VaR."""
        # Sort returns (losses are negative)
        sorted_returns = sorted(returns)

        # Calculate percentiles
        var_95_idx = int((1 - 0.95) * len(sorted_returns))
        var_99_idx = int((1 - 0.99) * len(sorted_returns))

        var_95 = (
            sorted_returns[var_95_idx]
            if var_95_idx < len(sorted_returns)
            else sorted_returns[0]
        )
        var_99 = (
            sorted_returns[var_99_idx]
            if var_99_idx < len(sorted_returns)
            else sorted_returns[0]
        )

        # Scale for holding period
        scaling_factor = math.sqrt(holding_period)
        var_95 *= scaling_factor
        var_99 *= scaling_factor

        # Calculate Expected Shortfall (average of losses beyond VaR)
        tail_losses = [r for r in sorted_returns if r <= var_95]
        expected_shortfall = (
            mean(tail_losses) * scaling_factor if tail_losses else var_95
        )

        return VaRCalculation(
            var_1d_95=var_95,
            var_1d_99=var_99,
            expected_shortfall=expected_shortfall,
            confidence_level=confidence_level,
            holding_period_days=holding_period,
            method="historical",
        )

    async def _calculate_parametric_var(
        self, returns: List[float], confidence_level: float, holding_period: int
    ) -> VaRCalculation:
        """Calculate parametric VaR assuming normal distribution."""
        # Calculate return statistics
        mean_return = mean(returns)
        return_vol = stdev(returns)

        # Z-scores for confidence levels
        z_95 = 1.645  # 95% confidence
        z_99 = 2.326  # 99% confidence

        # Scale for holding period
        scaling_factor = math.sqrt(holding_period)

        # Calculate VaR (assuming normal distribution)
        var_95 = (mean_return - z_95 * return_vol) * scaling_factor
        var_99 = (mean_return - z_99 * return_vol) * scaling_factor

        # Expected Shortfall for normal distribution
        # ES = μ - σ * φ(Φ^(-1)(α)) / α, where α = 1 - confidence_level
        alpha = 1 - confidence_level
        expected_shortfall = (mean_return - return_vol * 0.4 / alpha) * scaling_factor

        return VaRCalculation(
            var_1d_95=var_95,
            var_1d_99=var_99,
            expected_shortfall=expected_shortfall,
            confidence_level=confidence_level,
            holding_period_days=holding_period,
            method="parametric",
        )

    async def get_current_risk_metrics(self) -> RiskMetrics:
        """Get current risk metrics."""
        try:
            # Check cache
            now = datetime.now(timezone.utc)
            if now < self._cache_expiry and "risk_metrics" in self._risk_cache:
                return self._risk_cache["risk_metrics"]

            # Calculate fresh metrics
            portfolio_value = await self._get_portfolio_value()
            current_positions = await self._get_current_positions()
            current_price = await self._get_current_btc_price()

            # Calculate exposure
            current_exposure = await self._calculate_current_exposure(
                current_positions, current_price
            )

            # Calculate leverage
            total_position_value = sum(
                abs(pos.quantity * current_price) for pos in current_positions
            )
            leverage = (
                total_position_value / portfolio_value if portfolio_value > 0 else 0
            )

            # Calculate drawdown
            peak_value, peak_date = await self._get_portfolio_peak()
            current_drawdown = (
                (portfolio_value - peak_value) / peak_value if peak_value > 0 else 0
            )

            # Calculate VaR
            var_calc = await self.calculate_var(confidence_level=0.95)

            # Calculate strategy concentrations
            strategy_concentrations = await self._calculate_strategy_concentrations()

            # Calculate market correlation (simplified)
            beta, correlation = await self._calculate_market_correlation()

            risk_metrics = RiskMetrics(
                current_exposure=current_exposure,
                leverage=leverage,
                current_drawdown=current_drawdown,
                peak_value=peak_value,
                peak_date=peak_date,
                var_1d_95=var_calc.var_1d_95 * portfolio_value,
                var_1d_99=var_calc.var_1d_99 * portfolio_value,
                expected_shortfall=var_calc.expected_shortfall * portfolio_value,
                strategy_concentrations=strategy_concentrations,
                beta=beta,
                correlation_to_market=correlation,
            )

            # Cache for 60 seconds
            self._risk_cache["risk_metrics"] = risk_metrics
            self._cache_expiry = now + timedelta(seconds=60)

            return risk_metrics

        except Exception as e:
            logger.error(f"Risk metrics calculation error: {e}")
            raise RiskManagerException(
                message=f"Failed to calculate risk metrics: {str(e)}",
                original_exception=e,
            )

    # Helper methods for data retrieval and calculations
    async def _get_portfolio_value(self) -> float:
        """Get current portfolio value."""
        # This would get actual portfolio value from database
        # For now, return initial capital as placeholder
        return self.initial_capital

    async def _get_current_positions(self) -> List[Position]:
        """Get current open positions."""
        # This would query database for open positions
        return []

    async def _get_current_btc_price(self) -> float:
        """Get current BTC price."""
        latest_price = await self.database.get_latest_price()
        return float(latest_price.price) if latest_price else 50000.0

    async def _calculate_current_exposure(
        self, positions: List[Position], current_price: float
    ) -> float:
        """Calculate current market exposure."""
        if not positions:
            return 0.0

        total_exposure = sum(abs(pos.quantity * current_price) for pos in positions)
        portfolio_value = await self._get_portfolio_value()

        return total_exposure / portfolio_value if portfolio_value > 0 else 0.0

    async def _calculate_current_drawdown(self) -> float:
        """Calculate current drawdown from peak."""
        portfolio_value = await self._get_portfolio_value()
        peak_value, _ = await self._get_portfolio_peak()

        if peak_value > 0:
            return (portfolio_value - peak_value) / peak_value
        return 0.0

    async def _calculate_daily_pnl_percentage(self) -> float:
        """Calculate today's P&L as percentage."""
        # This would calculate actual daily P&L
        # For now, return 0 as placeholder
        return 0.0

    async def _get_strategy_allocation(self, strategy_name: str) -> float:
        """Get current allocation for strategy."""
        # This would query database for strategy positions
        return 0.0

    async def _get_strategy_statistics(self, strategy_name: str) -> Dict[str, float]:
        """Get strategy performance statistics."""
        # This would query database for strategy performance
        return {
            "win_rate": 0.55,
            "avg_win": 0.025,
            "avg_loss": 0.015,
            "total_trades": 100,
        }

    async def _get_historical_returns(self, days: int = 252) -> List[float]:
        """Get historical daily returns."""
        # This would calculate returns from price history
        # For now, return simulated returns
        import random

        return [random.gauss(0.001, 0.03) for _ in range(days)]

    async def _get_portfolio_peak(self) -> Tuple[float, datetime]:
        """Get portfolio peak value and date."""
        # This would query database for historical peak
        return self.initial_capital, datetime.now(timezone.utc) - timedelta(days=30)

    async def _calculate_strategy_concentrations(self) -> Dict[str, float]:
        """Calculate strategy concentration percentages."""
        # This would calculate actual strategy allocations
        return {"moving_average": 0.3, "rsi": 0.2, "macd": 0.25, "bollinger": 0.25}

    async def _calculate_market_correlation(
        self,
    ) -> Tuple[Optional[float], Optional[float]]:
        """Calculate portfolio beta and correlation to market."""
        # This would calculate actual correlation with market indices
        return 1.2, 0.85  # Example values

    async def health_check(self) -> Dict[str, Any]:
        """Risk manager health check."""
        try:
            risk_metrics = await self.get_current_risk_metrics()

            return {
                "emergency_stop": self.emergency_stop,
                "monitoring_active": self.monitor.is_monitoring,
                "current_drawdown": risk_metrics.current_drawdown,
                "current_exposure": risk_metrics.current_exposure,
                "risk_limits": self.risk_limits.dict(),
                "cache_expiry": self._cache_expiry.isoformat(),
                "alert_thresholds": self.monitor.alert_thresholds,
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "emergency_stop": self.emergency_stop,
            }
