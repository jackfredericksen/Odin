"""
Updated Core Models for Odin Trading Bot

Enhanced model definitions to support AI-driven strategy orchestration
and comprehensive trading functionality.

File: odin/core/models.py
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Union
from enum import Enum
import json


class SignalType(Enum):
    """Trading signal types."""
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"
    STRONG_BUY = "strong_buy"
    STRONG_SELL = "strong_sell"


class StrategyType(Enum):
    """Strategy classification types."""
    TREND_FOLLOWING = "trend_following"
    MEAN_REVERSION = "mean_reversion"
    VOLATILITY = "volatility"
    MOMENTUM = "momentum"
    ARBITRAGE = "arbitrage"
    SWING_TRADING = "swing_trading"
    SCALPING = "scalping"
    AI_ENHANCED = "ai_enhanced"


class MarketRegime(Enum):
    """Market regime classifications."""
    TRENDING_BULLISH = "trending_bullish"
    TRENDING_BEARISH = "trending_bearish"
    RANGING = "ranging"
    VOLATILE = "volatile"
    BREAKOUT = "breakout"
    UNKNOWN = "unknown"


class TradingMode(Enum):
    """Trading operation modes."""
    LIVE = "live"
    PAPER = "paper"
    BACKTEST = "backtest"
    SIMULATION = "simulation"


@dataclass
class PriceData:
    """Price data point with OHLCV information."""
    timestamp: datetime
    price: float
    volume: Optional[float] = None
    open: Optional[float] = None
    high: Optional[float] = None
    low: Optional[float] = None
    close: Optional[float] = None
    
    def __post_init__(self):
        """Set OHLC values to price if not provided."""
        if self.open is None:
            self.open = self.price
        if self.high is None:
            self.high = self.price
        if self.low is None:
            self.low = self.price
        if self.close is None:
            self.close = self.price
        if self.volume is None:
            self.volume = 1000.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "price": self.price,
            "open": self.open,
            "high": self.high,
            "low": self.low,
            "close": self.close,
            "volume": self.volume
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PriceData':
        """Create from dictionary."""
        return cls(
            timestamp=datetime.fromisoformat(data["timestamp"]),
            price=data["price"],
            open=data.get("open"),
            high=data.get("high"),
            low=data.get("low"),
            close=data.get("close"),
            volume=data.get("volume")
        )


@dataclass
class StrategySignal:
    """Enhanced trading signal with AI metadata."""
    signal: SignalType
    confidence: float  # 0-1 confidence score
    timestamp: datetime
    price: float
    reasoning: str
    indicators: Dict[str, Any]  # Technical indicator values
    risk_score: float  # 0-1 risk assessment
    
    # AI-specific fields
    strategy_id: Optional[str] = None
    market_regime: Optional[MarketRegime] = None
    regime_confidence: Optional[float] = None
    expected_duration: Optional[int] = None  # Expected holding period in hours
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    position_size_recommendation: Optional[float] = None
    
    # Metadata
    signal_id: Optional[str] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    executed: bool = False
    execution_price: Optional[float] = None
    execution_time: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "signal": self.signal.value,
            "confidence": self.confidence,
            "timestamp": self.timestamp.isoformat(),
            "price": self.price,
            "reasoning": self.reasoning,
            "indicators": self.indicators,
            "risk_score": self.risk_score,
            "strategy_id": self.strategy_id,
            "market_regime": self.market_regime.value if self.market_regime else None,
            "regime_confidence": self.regime_confidence,
            "expected_duration": self.expected_duration,
            "stop_loss": self.stop_loss,
            "take_profit": self.take_profit,
            "position_size_recommendation": self.position_size_recommendation,
            "signal_id": self.signal_id,
            "created_at": self.created_at.isoformat(),
            "executed": self.executed,
            "execution_price": self.execution_price,
            "execution_time": self.execution_time.isoformat() if self.execution_time else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StrategySignal':
        """Create from dictionary."""
        return cls(
            signal=SignalType(data["signal"]),
            confidence=data["confidence"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            price=data["price"],
            reasoning=data["reasoning"],
            indicators=data["indicators"],
            risk_score=data["risk_score"],
            strategy_id=data.get("strategy_id"),
            market_regime=MarketRegime(data["market_regime"]) if data.get("market_regime") else None,
            regime_confidence=data.get("regime_confidence"),
            expected_duration=data.get("expected_duration"),
            stop_loss=data.get("stop_loss"),
            take_profit=data.get("take_profit"),
            position_size_recommendation=data.get("position_size_recommendation"),
            signal_id=data.get("signal_id"),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else datetime.now(timezone.utc),
            executed=data.get("executed", False),
            execution_price=data.get("execution_price"),
            execution_time=datetime.fromisoformat(data["execution_time"]) if data.get("execution_time") else None
        )


@dataclass
class Trade:
    """Enhanced trade record with AI tracking."""
    trade_id: str
    strategy_id: str
    signal_id: Optional[str]
    
    # Trade details
    side: str  # "buy" or "sell"
    amount: float
    price: float
    timestamp: datetime
    
    # Position tracking
    entry_price: Optional[float] = None
    exit_price: Optional[float] = None
    entry_time: Optional[datetime] = None
    exit_time: Optional[datetime] = None
    
    # Risk management
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    actual_stop_loss: Optional[float] = None
    actual_take_profit: Optional[float] = None
    
    # Performance
    pnl: Optional[float] = None
    pnl_percentage: Optional[float] = None
    fees: float = 0.0
    slippage: float = 0.0
    
    # AI metadata
    ai_confidence: Optional[float] = None
    market_regime_at_entry: Optional[MarketRegime] = None
    expected_duration: Optional[int] = None
    actual_duration: Optional[int] = None
    
    # Status
    status: str = "pending"  # pending, filled, cancelled, expired
    notes: Optional[str] = None
    
    def calculate_pnl(self):
        """Calculate P&L if both entry and exit prices are available."""
        if self.entry_price and self.exit_price:
            if self.side == "buy":
                self.pnl = (self.exit_price - self.entry_price) * self.amount - self.fees
            else:  # sell
                self.pnl = (self.entry_price - self.exit_price) * self.amount - self.fees
            
            if self.entry_price > 0:
                self.pnl_percentage = (self.pnl / (self.entry_price * self.amount)) * 100
        
        # Calculate actual duration
        if self.entry_time and self.exit_time:
            duration = self.exit_time - self.entry_time
            self.actual_duration = int(duration.total_seconds() / 3600)  # hours
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "trade_id": self.trade_id,
            "strategy_id": self.strategy_id,
            "signal_id": self.signal_id,
            "side": self.side,
            "amount": self.amount,
            "price": self.price,
            "timestamp": self.timestamp.isoformat(),
            "entry_price": self.entry_price,
            "exit_price": self.exit_price,
            "entry_time": self.entry_time.isoformat() if self.entry_time else None,
            "exit_time": self.exit_time.isoformat() if self.exit_time else None,
            "stop_loss": self.stop_loss,
            "take_profit": self.take_profit,
            "actual_stop_loss": self.actual_stop_loss,
            "actual_take_profit": self.actual_take_profit,
            "pnl": self.pnl,
            "pnl_percentage": self.pnl_percentage,
            "fees": self.fees,
            "slippage": self.slippage,
            "ai_confidence": self.ai_confidence,
            "market_regime_at_entry": self.market_regime_at_entry.value if self.market_regime_at_entry else None,
            "expected_duration": self.expected_duration,
            "actual_duration": self.actual_duration,
            "status": self.status,
            "notes": self.notes
        }


@dataclass
class Portfolio:
    """Enhanced portfolio with AI analytics."""
    portfolio_id: str
    total_value: float
    cash_balance: float
    btc_balance: float
    btc_value: float
    timestamp: datetime
    
    # Performance metrics
    total_return: float = 0.0
    total_return_percentage: float = 0.0
    daily_pnl: float = 0.0
    daily_pnl_percentage: float = 0.0
    
    # Risk metrics
    volatility: float = 0.0
    max_drawdown: float = 0.0
    sharpe_ratio: float = 0.0
    win_rate: float = 0.0
    
    # AI insights
    active_strategies: List[str] = field(default_factory=list)
    current_allocation: Dict[str, float] = field(default_factory=dict)
    recommended_allocation: Dict[str, float] = field(default_factory=dict)
    risk_score: float = 0.0
    
    def calculate_allocation(self):
        """Calculate current allocation percentages."""
        if self.total_value > 0:
            self.current_allocation = {
                "cash": (self.cash_balance / self.total_value) * 100,
                "btc": (self.btc_value / self.total_value) * 100
            }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "portfolio_id": self.portfolio_id,
            "total_value": self.total_value,
            "cash_balance": self.cash_balance,
            "btc_balance": self.btc_balance,
            "btc_value": self.btc_value,
            "timestamp": self.timestamp.isoformat(),
            "total_return": self.total_return,
            "total_return_percentage": self.total_return_percentage,
            "daily_pnl": self.daily_pnl,
            "daily_pnl_percentage": self.daily_pnl_percentage,
            "volatility": self.volatility,
            "max_drawdown": self.max_drawdown,
            "sharpe_ratio": self.sharpe_ratio,
            "win_rate": self.win_rate,
            "active_strategies": self.active_strategies,
            "current_allocation": self.current_allocation,
            "recommended_allocation": self.recommended_allocation,
            "risk_score": self.risk_score
        }


@dataclass
class MarketRegimeData:
    """Market regime detection result."""
    regime: MarketRegime
    confidence: float
    timestamp: datetime
    
    # Regime characteristics
    trend_direction: str = "neutral"  # bullish, bearish, neutral
    volatility_level: str = "medium"  # low, medium, high
    market_strength: str = "neutral"  # strong, weak, neutral
    
    # Supporting indicators
    indicators: Dict[str, float] = field(default_factory=dict)
    regime_probabilities: Dict[str, float] = field(default_factory=dict)
    
    # Metadata
    detection_method: str = "hybrid"  # rule_based, ml, hybrid
    model_version: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "regime": self.regime.value,
            "confidence": self.confidence,
            "timestamp": self.timestamp.isoformat(),
            "trend_direction": self.trend_direction,
            "volatility_level": self.volatility_level,
            "market_strength": self.market_strength,
            "indicators": self.indicators,
            "regime_probabilities": self.regime_probabilities,
            "detection_method": self.detection_method,
            "model_version": self.model_version
        }


@dataclass
class StrategyPerformance:
    """Enhanced strategy performance metrics."""
    strategy_id: str
    strategy_name: str
    timestamp: datetime
    
    # Basic performance
    total_return: float
    total_return_percentage: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    
    # Risk metrics
    sharpe_ratio: float
    sortino_ratio: float
    max_drawdown: float
    volatility: float
    calmar_ratio: float
    
    # Trade statistics
    avg_trade_return: float
    avg_winning_trade: float
    avg_losing_trade: float
    largest_win: float
    largest_loss: float
    avg_trade_duration: float  # in hours
    
    # AI-specific metrics
    ai_confidence_avg: float = 0.0
    regime_accuracy: float = 0.0  # How often regime predictions were correct
    signal_accuracy: float = 0.0  # Signal prediction accuracy
    
    # Recent performance (last 30 days)
    recent_return: float = 0.0
    recent_win_rate: float = 0.0
    recent_sharpe: float = 0.0
    
    def calculate_derived_metrics(self):
        """Calculate derived performance metrics."""
        if self.total_trades > 0:
            self.win_rate = (self.winning_trades / self.total_trades) * 100
        
        if self.total_return != 0 and self.volatility > 0:
            self.sharpe_ratio = self.total_return / self.volatility
        
        if self.max_drawdown > 0:
            self.calmar_ratio = self.total_return / self.max_drawdown
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "strategy_id": self.strategy_id,
            "strategy_name": self.strategy_name,
            "timestamp": self.timestamp.isoformat(),
            "total_return": self.total_return,
            "total_return_percentage": self.total_return_percentage,
            "total_trades": self.total_trades,
            "winning_trades": self.winning_trades,
            "losing_trades": self.losing_trades,
            "win_rate": self.win_rate,
            "sharpe_ratio": self.sharpe_ratio,
            "sortino_ratio": self.sortino_ratio,
            "max_drawdown": self.max_drawdown,
            "volatility": self.volatility,
            "calmar_ratio": self.calmar_ratio,
            "avg_trade_return": self.avg_trade_return,
            "avg_winning_trade": self.avg_winning_trade,
            "avg_losing_trade": self.avg_losing_trade,
            "largest_win": self.largest_win,
            "largest_loss": self.largest_loss,
            "avg_trade_duration": self.avg_trade_duration,
            "ai_confidence_avg": self.ai_confidence_avg,
            "regime_accuracy": self.regime_accuracy,
            "signal_accuracy": self.signal_accuracy,
            "recent_return": self.recent_return,
            "recent_win_rate": self.recent_win_rate,
            "recent_sharpe": self.recent_sharpe
        }


@dataclass
class AISystemStatus:
    """AI system status and health metrics."""
    timestamp: datetime
    system_enabled: bool
    active_strategy_id: Optional[str]
    active_strategy_name: Optional[str]
    strategy_confidence: float
    
    # Market analysis
    current_regime: MarketRegime
    regime_confidence: float
    market_trend: str
    volatility_level: str
    
    # System performance
    total_strategies: int
    active_strategies: int
    signals_today: int
    trades_today: int
    system_uptime: float  # hours
    
    # AI metrics
    model_accuracy: float = 0.0
    prediction_success_rate: float = 0.0
    last_model_update: Optional[datetime] = None
    
    # Health indicators
    data_quality_score: float = 1.0
    system_load: float = 0.0
    error_rate: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "system_enabled": self.system_enabled,
            "active_strategy_id": self.active_strategy_id,
            "active_strategy_name": self.active_strategy_name,
            "strategy_confidence": self.strategy_confidence,
            "current_regime": self.current_regime.value,
            "regime_confidence": self.regime_confidence,
            "market_trend": self.market_trend,
            "volatility_level": self.volatility_level,
            "total_strategies": self.total_strategies,
            "active_strategies": self.active_strategies,
            "signals_today": self.signals_today,
            "trades_today": self.trades_today,
            "system_uptime": self.system_uptime,
            "model_accuracy": self.model_accuracy,
            "prediction_success_rate": self.prediction_success_rate,
            "last_model_update": self.last_model_update.isoformat() if self.last_model_update else None,
            "data_quality_score": self.data_quality_score,
            "system_load": self.system_load,
            "error_rate": self.error_rate
        }


@dataclass
class StrategyConfig:
    """Strategy configuration and parameters."""
    strategy_id: str
    strategy_name: str
    strategy_type: StrategyType
    enabled: bool
    
    # Core parameters
    parameters: Dict[str, Any]
    risk_limits: Dict[str, float]
    
    # AI configuration
    ai_enabled: bool = True
    confidence_threshold: float = 0.6
    max_position_size: float = 0.25
    
    # Performance targets
    target_return: Optional[float] = None
    max_drawdown_limit: float = 0.15
    stop_loss_default: float = 0.05
    take_profit_default: float = 0.10
    
    # Metadata
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    version: str = "1.0"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "strategy_id": self.strategy_id,
            "strategy_name": self.strategy_name,
            "strategy_type": self.strategy_type.value,
            "enabled": self.enabled,
            "parameters": self.parameters,
            "risk_limits": self.risk_limits,
            "ai_enabled": self.ai_enabled,
            "confidence_threshold": self.confidence_threshold,
            "max_position_size": self.max_position_size,
            "target_return": self.target_return,
            "max_drawdown_limit": self.max_drawdown_limit,
            "stop_loss_default": self.stop_loss_default,
            "take_profit_default": self.take_profit_default,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "version": self.version
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StrategyConfig':
        """Create from dictionary."""
        return cls(
            strategy_id=data["strategy_id"],
            strategy_name=data["strategy_name"],
            strategy_type=StrategyType(data["strategy_type"]),
            enabled=data["enabled"],
            parameters=data["parameters"],
            risk_limits=data["risk_limits"],
            ai_enabled=data.get("ai_enabled", True),
            confidence_threshold=data.get("confidence_threshold", 0.6),
            max_position_size=data.get("max_position_size", 0.25),
            target_return=data.get("target_return"),
            max_drawdown_limit=data.get("max_drawdown_limit", 0.15),
            stop_loss_default=data.get("stop_loss_default", 0.05),
            take_profit_default=data.get("take_profit_default", 0.10),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else datetime.now(timezone.utc),
            updated_at=datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else datetime.now(timezone.utc),
            version=data.get("version", "1.0")
        )


@dataclass
class BacktestResult:
    """Enhanced backtesting results."""
    backtest_id: str
    strategy_id: str
    start_date: datetime
    end_date: datetime
    initial_capital: float
    final_capital: float
    
    # Performance summary
    total_return: float
    total_return_percentage: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    
    # Trade statistics
    total_trades: int
    avg_trade_duration: float
    best_trade: float
    worst_trade: float
    
    # Detailed results
    trades: List[Dict[str, Any]] = field(default_factory=list)
    equity_curve: List[Dict[str, Any]] = field(default_factory=list)
    signals: List[Dict[str, Any]] = field(default_factory=list)
    
    # AI analysis
    regime_accuracy: float = 0.0
    signal_accuracy: float = 0.0
    confidence_correlation: float = 0.0  # Correlation between confidence and success
    
    # Metadata
    parameters_used: Dict[str, Any] = field(default_factory=dict)
    market_conditions: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "backtest_id": self.backtest_id,
            "strategy_id": self.strategy_id,
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat(),
            "initial_capital": self.initial_capital,
            "final_capital": self.final_capital,
            "total_return": self.total_return,
            "total_return_percentage": self.total_return_percentage,
            "sharpe_ratio": self.sharpe_ratio,
            "max_drawdown": self.max_drawdown,
            "win_rate": self.win_rate,
            "total_trades": self.total_trades,
            "avg_trade_duration": self.avg_trade_duration,
            "best_trade": self.best_trade,
            "worst_trade": self.worst_trade,
            "trades": self.trades,
            "equity_curve": self.equity_curve,
            "signals": self.signals,
            "regime_accuracy": self.regime_accuracy,
            "signal_accuracy": self.signal_accuracy,
            "confidence_correlation": self.confidence_correlation,
            "parameters_used": self.parameters_used,
            "market_conditions": self.market_conditions,
            "created_at": self.created_at.isoformat()
        }


# Utility functions for model conversions
def create_price_data_from_ohlcv(timestamp: datetime, open_price: float, high: float, 
                                low: float, close: float, volume: float) -> PriceData:
    """Create PriceData from OHLCV values."""
    return PriceData(
        timestamp=timestamp,
        price=close,  # Use close as primary price
        open=open_price,
        high=high,
        low=low,
        close=close,
        volume=volume
    )


def create_signal_from_strategy(signal_type: SignalType, price: float, confidence: float,
                               reasoning: str, strategy_id: str, 
                               indicators: Dict[str, Any] = None) -> StrategySignal:
    """Create a StrategySignal with common defaults."""
    return StrategySignal(
        signal=signal_type,
        confidence=confidence,
        timestamp=datetime.now(timezone.utc),
        price=price,
        reasoning=reasoning,
        indicators=indicators or {},
        risk_score=1.0 - confidence,  # Simple risk calculation
        strategy_id=strategy_id
    )


def calculate_portfolio_metrics(trades: List[Trade], initial_capital: float) -> Dict[str, float]:
    """Calculate portfolio performance metrics from trades."""
    if not trades:
        return {
            "total_return": 0.0,
            "win_rate": 0.0,
            "sharpe_ratio": 0.0,
            "max_drawdown": 0.0,
            "total_trades": 0
        }
    
    # Calculate basic metrics
    total_pnl = sum(trade.pnl for trade in trades if trade.pnl is not None)
    winning_trades = sum(1 for trade in trades if trade.pnl and trade.pnl > 0)
    total_trades = len(trades)
    
    total_return = (total_pnl / initial_capital) * 100 if initial_capital > 0 else 0
    win_rate = (winning_trades / total_trades) * 100 if total_trades > 0 else 0
    
    # Calculate returns series for advanced metrics
    returns = [trade.pnl / initial_capital for trade in trades if trade.pnl is not None]
    
    # Sharpe ratio (simplified)
    if len(returns) > 1:
        import statistics
        avg_return = statistics.mean(returns)
        std_return = statistics.stdev(returns)
        sharpe_ratio = avg_return / std_return if std_return > 0 else 0
    else:
        sharpe_ratio = 0
    
    # Max drawdown (simplified)
    cumulative_returns = []
    cumulative = 0
    for ret in returns:
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
    
    return {
        "total_return": total_return,
        "win_rate": win_rate,
        "sharpe_ratio": sharpe_ratio,
        "max_drawdown": max_drawdown,
        "total_trades": total_trades,
        "total_pnl": total_pnl
    }


# Legacy compatibility aliases
Signal = StrategySignal  # For backward compatibility with existing code


# Model validation functions
def validate_signal(signal: StrategySignal) -> bool:
    """Validate signal data integrity."""
    if not isinstance(signal.confidence, (int, float)) or not 0 <= signal.confidence <= 1:
        return False
    
    if not isinstance(signal.risk_score, (int, float)) or not 0 <= signal.risk_score <= 1:
        return False
    
    if not isinstance(signal.price, (int, float)) or signal.price <= 0:
        return False
    
    return True


def validate_trade(trade: Trade) -> bool:
    """Validate trade data integrity."""
    if trade.amount <= 0:
        return False
    
    if trade.price <= 0:
        return False
    
    if trade.side not in ["buy", "sell"]:
        return False
    
    return True


# Export all models for easy importing
__all__ = [
    'SignalType', 'StrategyType', 'MarketRegime', 'TradingMode',
    'PriceData', 'StrategySignal', 'Trade', 'Portfolio',
    'MarketRegimeData', 'StrategyPerformance', 'AISystemStatus',
    'StrategyConfig', 'BacktestResult', 'Signal',
    'create_price_data_from_ohlcv', 'create_signal_from_strategy',
    'calculate_portfolio_metrics', 'validate_signal', 'validate_trade'
]