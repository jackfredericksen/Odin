"""
Odin Core Models - Pydantic Data Models for Validation and Serialization

Comprehensive data models for the Odin trading system providing type safety,
validation, and serialization for all core data structures.

File: odin/core/models.py
Author: Odin Development Team
License: MIT
"""

from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Optional, List, Dict, Any, Union
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, validator, root_validator
from pydantic.types import PositiveFloat, NonNegativeFloat


# Enums for type safety
class OrderType(str, Enum):
    """Order types for trading."""
    MARKET = "market"
    LIMIT = "limit"
    STOP_LOSS = "stop_loss"
    TAKE_PROFIT = "take_profit"
    STOP_LIMIT = "stop_limit"


class OrderSide(str, Enum):
    """Order sides for trading."""
    BUY = "buy"
    SELL = "sell"


class OrderStatus(str, Enum):
    """Order execution status."""
    PENDING = "pending"
    PARTIAL = "partial"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"
    EXPIRED = "expired"


class PositionType(str, Enum):
    """Position types."""
    LONG = "long"
    SHORT = "short"


class SignalType(str, Enum):
    """Trading signal types."""
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"


class StrategyStatus(str, Enum):
    """Strategy execution status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    PAUSED = "paused"
    ERROR = "error"


class MarketRegime(str, Enum):
    """Market regime classifications."""
    BULL = "bull"
    BEAR = "bear"
    SIDEWAYS = "sideways"
    VOLATILE = "volatile"


# Base Models
class OdinBaseModel(BaseModel):
    """Base model with common configuration."""
    
    class Config:
        use_enum_values = True
        arbitrary_types_allowed = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            Decimal: lambda v: float(v),
            UUID: lambda v: str(v),
        }
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary with proper serialization."""
        return self.dict(by_alias=True, exclude_none=True)


class TimestampMixin(BaseModel):
    """Mixin for timestamp fields."""
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = None
    
    @validator('updated_at', pre=True, always=True)
    def set_updated_at(cls, v):
        return v or datetime.now(timezone.utc)


# Market Data Models
class PriceData(OdinBaseModel):
    """Bitcoin price data point."""
    symbol: str = Field(default="BTC-USD", description="Trading symbol")
    price: PositiveFloat = Field(description="Current price in USD")
    volume: NonNegativeFloat = Field(description="24h trading volume")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    source: str = Field(description="Data source (e.g., 'coinbase', 'binance')")
    
    # Additional market data
    bid: Optional[PositiveFloat] = Field(None, description="Best bid price")
    ask: Optional[PositiveFloat] = Field(None, description="Best ask price")
    spread: Optional[NonNegativeFloat] = Field(None, description="Bid-ask spread")
    
    @validator('spread', pre=True, always=True)
    def calculate_spread(cls, v, values):
        if v is None and 'bid' in values and 'ask' in values:
            bid, ask = values.get('bid'), values.get('ask')
            if bid and ask:
                return float(ask - bid)
        return v


class OHLCData(OdinBaseModel):
    """OHLC candlestick data."""
    symbol: str = Field(default="BTC-USD")
    timeframe: str = Field(description="Timeframe (e.g., '1m', '5m', '1h', '1d')")
    timestamp: datetime = Field(description="Candle start time")
    
    open: PositiveFloat = Field(description="Opening price")
    high: PositiveFloat = Field(description="Highest price")
    low: PositiveFloat = Field(description="Lowest price")
    close: PositiveFloat = Field(description="Closing price")
    volume: NonNegativeFloat = Field(description="Trading volume")
    
    # Technical indicators (optional)
    sma_20: Optional[float] = Field(None, description="20-period Simple Moving Average")
    ema_12: Optional[float] = Field(None, description="12-period Exponential Moving Average")
    rsi: Optional[float] = Field(None, ge=0, le=100, description="RSI indicator")
    macd: Optional[float] = Field(None, description="MACD line")
    macd_signal: Optional[float] = Field(None, description="MACD signal line")
    bb_upper: Optional[float] = Field(None, description="Bollinger Bands upper")
    bb_lower: Optional[float] = Field(None, description="Bollinger Bands lower")
    
    @root_validator
    def validate_ohlc(cls, values):
        """Validate OHLC relationships."""
        open_price, high, low, close = values.get('open'), values.get('high'), values.get('low'), values.get('close')
        
        if all(x is not None for x in [open_price, high, low, close]):
            if not (low <= min(open_price, close) and max(open_price, close) <= high):
                raise ValueError("Invalid OHLC relationships: high/low must contain open/close")
        
        return values


class MarketDepth(OdinBaseModel):
    """Order book market depth data."""
    symbol: str = Field(default="BTC-USD")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    bids: List[List[float]] = Field(description="Bid orders [price, size]")
    asks: List[List[float]] = Field(description="Ask orders [price, size]")
    
    # Calculated metrics
    spread: Optional[float] = Field(None, description="Best bid-ask spread")
    mid_price: Optional[float] = Field(None, description="Mid-market price")
    liquidity_score: Optional[float] = Field(None, ge=0, le=1, description="Liquidity score")
    
    @validator('spread', pre=True, always=True)
    def calculate_spread(cls, v, values):
        if v is None:
            bids, asks = values.get('bids', []), values.get('asks', [])
            if bids and asks:
                best_bid = max(bids, key=lambda x: x[0])[0]
                best_ask = min(asks, key=lambda x: x[0])[0]
                return best_ask - best_bid
        return v
    
    @validator('mid_price', pre=True, always=True)
    def calculate_mid_price(cls, v, values):
        if v is None and values.get('spread'):
            bids, asks = values.get('bids', []), values.get('asks', [])
            if bids and asks:
                best_bid = max(bids, key=lambda x: x[0])[0]
                best_ask = min(asks, key=lambda x: x[0])[0]
                return (best_bid + best_ask) / 2
        return v


# Trading Models
class TradeSignal(OdinBaseModel):
    """Trading signal from strategy."""
    id: UUID = Field(default_factory=uuid4)
    strategy_name: str = Field(description="Strategy that generated signal")
    symbol: str = Field(default="BTC-USD")
    signal_type: SignalType = Field(description="Buy, sell, or hold signal")
    confidence: float = Field(ge=0, le=1, description="Signal confidence score")
    price: PositiveFloat = Field(description="Price when signal generated")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Strategy-specific data
    indicators: Dict[str, float] = Field(default_factory=dict, description="Technical indicators")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional signal data")
    
    # Execution tracking
    executed: bool = Field(default=False, description="Whether signal was executed")
    execution_price: Optional[float] = Field(None, description="Actual execution price")
    execution_time: Optional[datetime] = Field(None, description="Execution timestamp")


class TradeOrder(OdinBaseModel, TimestampMixin):
    """Trade order specification."""
    id: UUID = Field(default_factory=uuid4)
    strategy_name: str = Field(description="Strategy placing the order")
    symbol: str = Field(default="BTC-USD")
    
    # Order details
    order_type: OrderType = Field(description="Order type")
    side: OrderSide = Field(description="Buy or sell")
    quantity: PositiveFloat = Field(description="Order quantity")
    
    # Price specifications
    price: Optional[PositiveFloat] = Field(None, description="Limit price (for limit orders)")
    stop_price: Optional[PositiveFloat] = Field(None, description="Stop price (for stop orders)")
    
    # Risk management
    stop_loss: Optional[PositiveFloat] = Field(None, description="Stop loss price")
    take_profit: Optional[PositiveFloat] = Field(None, description="Take profit price")
    
    # Execution parameters
    time_in_force: str = Field(default="GTC", description="Time in force (GTC, IOC, FOK)")
    reduce_only: bool = Field(default=False, description="Reduce only flag")
    
    # Status tracking
    status: OrderStatus = Field(default=OrderStatus.PENDING)
    filled_quantity: NonNegativeFloat = Field(default=0)
    remaining_quantity: Optional[float] = Field(None)
    
    # External references
    exchange_order_id: Optional[str] = Field(None, description="Exchange order ID")
    client_order_id: Optional[str] = Field(None, description="Client order ID")
    
    @validator('remaining_quantity', pre=True, always=True)
    def calculate_remaining(cls, v, values):
        if v is None:
            quantity = values.get('quantity', 0)
            filled = values.get('filled_quantity', 0)
            return max(0, quantity - filled)
        return v


class TradeExecution(OdinBaseModel, TimestampMixin):
    """Trade execution result."""
    id: UUID = Field(default_factory=uuid4)
    order_id: UUID = Field(description="Related order ID")
    strategy_name: str = Field(description="Executing strategy")
    symbol: str = Field(default="BTC-USD")
    
    # Execution details
    side: OrderSide = Field(description="Buy or sell")
    quantity: PositiveFloat = Field(description="Executed quantity")
    price: PositiveFloat = Field(description="Execution price")
    
    # Costs and fees
    fee: NonNegativeFloat = Field(default=0, description="Trading fee")
    fee_currency: str = Field(default="USD", description="Fee currency")
    total_cost: Optional[float] = Field(None, description="Total cost including fees")
    
    # Performance tracking
    slippage: Optional[float] = Field(None, description="Price slippage")
    market_impact: Optional[float] = Field(None, description="Market impact estimate")
    
    # External references
    trade_id: Optional[str] = Field(None, description="Exchange trade ID")
    
    @validator('total_cost', pre=True, always=True)
    def calculate_total_cost(cls, v, values):
        if v is None:
            quantity = values.get('quantity', 0)
            price = values.get('price', 0)
            fee = values.get('fee', 0)
            side = values.get('side')
            
            base_cost = quantity * price
            if side == OrderSide.BUY:
                return base_cost + fee
            else:
                return base_cost - fee
        return v


class Position(OdinBaseModel, TimestampMixin):
    """Trading position."""
    id: UUID = Field(default_factory=uuid4)
    symbol: str = Field(default="BTC-USD")
    strategy_name: str = Field(description="Strategy holding position")
    
    # Position details
    type: PositionType = Field(description="Long or short position")
    quantity: float = Field(description="Position size (can be negative for short)")
    entry_price: PositiveFloat = Field(description="Average entry price")
    current_price: PositiveFloat = Field(description="Current market price")
    
    # P&L calculations
    unrealized_pnl: Optional[float] = Field(None, description="Unrealized P&L")
    realized_pnl: float = Field(default=0, description="Realized P&L")
    total_fees: NonNegativeFloat = Field(default=0, description="Total fees paid")
    
    # Risk management
    stop_loss: Optional[PositiveFloat] = Field(None, description="Stop loss price")
    take_profit: Optional[PositiveFloat] = Field(None, description="Take profit price")
    
    # Position tracking
    open_orders: List[UUID] = Field(default_factory=list, description="Related open orders")
    trades: List[UUID] = Field(default_factory=list, description="Related trade executions")
    
    @validator('unrealized_pnl', pre=True, always=True)
    def calculate_unrealized_pnl(cls, v, values):
        if v is None:
            quantity = values.get('quantity', 0)
            entry_price = values.get('entry_price', 0)
            current_price = values.get('current_price', 0)
            
            if quantity and entry_price and current_price:
                return quantity * (current_price - entry_price)
        return v


# Portfolio Models
class Allocation(OdinBaseModel):
    """Portfolio allocation breakdown."""
    cash: NonNegativeFloat = Field(description="Cash holdings in USD")
    btc: NonNegativeFloat = Field(description="Bitcoin holdings")
    
    # Strategy allocations
    strategy_allocations: Dict[str, float] = Field(
        default_factory=dict,
        description="Allocation by strategy"
    )
    
    # Calculated metrics
    total_value: Optional[float] = Field(None, description="Total portfolio value")
    btc_percentage: Optional[float] = Field(None, ge=0, le=1, description="BTC allocation %")
    cash_percentage: Optional[float] = Field(None, ge=0, le=1, description="Cash allocation %")
    
    @validator('total_value', pre=True, always=True)
    def calculate_total_value(cls, v, values):
        if v is None:
            cash = values.get('cash', 0)
            btc = values.get('btc', 0)
            # Note: In real implementation, multiply BTC by current price
            return cash + btc  # Simplified for model
        return v


class PerformanceMetrics(OdinBaseModel):
    """Portfolio performance metrics."""
    period_start: datetime = Field(description="Performance period start")
    period_end: datetime = Field(description="Performance period end")
    
    # Returns
    total_return: float = Field(description="Total return %")
    annualized_return: float = Field(description="Annualized return %")
    benchmark_return: Optional[float] = Field(None, description="Benchmark return %")
    excess_return: Optional[float] = Field(None, description="Excess return vs benchmark")
    
    # Risk metrics
    volatility: NonNegativeFloat = Field(description="Annualized volatility %")
    sharpe_ratio: Optional[float] = Field(None, description="Sharpe ratio")
    sortino_ratio: Optional[float] = Field(None, description="Sortino ratio")
    max_drawdown: Optional[float] = Field(None, description="Maximum drawdown %")
    
    # Trading metrics
    total_trades: int = Field(ge=0, description="Total number of trades")
    win_rate: Optional[float] = Field(None, ge=0, le=1, description="Win rate %")
    profit_factor: Optional[float] = Field(None, description="Profit factor")
    avg_trade_return: Optional[float] = Field(None, description="Average trade return %")


class Portfolio(OdinBaseModel, TimestampMixin):
    """Complete portfolio state."""
    id: UUID = Field(default_factory=uuid4)
    name: str = Field(description="Portfolio name")
    
    # Current state
    allocation: Allocation = Field(description="Current allocation")
    positions: List[Position] = Field(default_factory=list, description="Open positions")
    
    # Performance
    performance: PerformanceMetrics = Field(description="Performance metrics")
    
    # Risk metrics
    current_drawdown: float = Field(default=0, description="Current drawdown %")
    var_95: Optional[float] = Field(None, description="95% Value at Risk")
    expected_shortfall: Optional[float] = Field(None, description="Expected shortfall")
    
    # Trading activity
    active_strategies: List[str] = Field(default_factory=list, description="Active strategies")
    pending_orders: List[TradeOrder] = Field(default_factory=list, description="Pending orders")


class PortfolioSummary(OdinBaseModel):
    """Portfolio summary for dashboard."""
    total_value: PositiveFloat = Field(description="Total portfolio value")
    daily_pnl: float = Field(description="Daily P&L")
    daily_pnl_percent: float = Field(description="Daily P&L %")
    
    # Quick metrics
    positions_count: int = Field(ge=0, description="Number of open positions")
    active_orders_count: int = Field(ge=0, description="Number of active orders")
    active_strategies_count: int = Field(ge=0, description="Number of active strategies")
    
    # Risk overview
    current_exposure: float = Field(ge=0, le=1, description="Current market exposure %")
    risk_level: str = Field(description="Risk level (Low/Medium/High)")
    
    last_updated: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# Risk Models
class RiskLimits(OdinBaseModel):
    """Risk management limits."""
    max_position_size: float = Field(default=0.95, ge=0, le=1, description="Max position size %")
    max_drawdown: float = Field(default=0.15, ge=0, le=1, description="Max drawdown %")
    max_daily_loss: float = Field(default=0.05, ge=0, le=1, description="Max daily loss %")
    max_correlation: float = Field(default=0.7, ge=0, le=1, description="Max strategy correlation")
    
    # Per-trade limits
    max_trade_size: float = Field(default=0.1, ge=0, le=1, description="Max trade size %")
    min_liquidity: float = Field(default=1000000, ge=0, description="Min liquidity requirement")
    
    # Concentration limits
    max_strategy_allocation: float = Field(default=0.5, ge=0, le=1, description="Max per strategy %")
    max_sector_exposure: float = Field(default=1.0, ge=0, le=1, description="Max sector exposure %")


class RiskMetrics(OdinBaseModel, TimestampMixin):
    """Current risk metrics."""
    # Portfolio risk
    current_exposure: float = Field(ge=0, le=1, description="Current market exposure")
    leverage: float = Field(ge=0, description="Portfolio leverage")
    
    # Drawdown tracking
    current_drawdown: float = Field(description="Current drawdown from peak")
    peak_value: PositiveFloat = Field(description="Portfolio peak value")
    peak_date: datetime = Field(description="Date of peak value")
    
    # Risk measures
    var_1d_95: Optional[float] = Field(None, description="1-day 95% VaR")
    var_1d_99: Optional[float] = Field(None, description="1-day 99% VaR")
    expected_shortfall: Optional[float] = Field(None, description="Expected shortfall")
    
    # Concentration risk
    strategy_concentrations: Dict[str, float] = Field(
        default_factory=dict,
        description="Strategy concentration percentages"
    )
    
    # Market risk
    beta: Optional[float] = Field(None, description="Portfolio beta")
    correlation_to_market: Optional[float] = Field(None, description="Market correlation")


class DrawdownAlert(OdinBaseModel):
    """Drawdown alert notification."""
    id: UUID = Field(default_factory=uuid4)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    current_drawdown: float = Field(description="Current drawdown %")
    threshold: float = Field(description="Drawdown threshold %")
    severity: str = Field(description="Alert severity (Warning/Critical)")
    
    # Context
    peak_value: PositiveFloat = Field(description="Peak portfolio value")
    current_value: PositiveFloat = Field(description="Current portfolio value")
    days_in_drawdown: int = Field(ge=0, description="Days in drawdown")
    
    # Recommended actions
    recommended_actions: List[str] = Field(
        default_factory=list,
        description="Recommended risk management actions"
    )


# Strategy Models
class StrategyConfig(OdinBaseModel):
    """Strategy configuration."""
    name: str = Field(description="Strategy name")
    enabled: bool = Field(default=True, description="Strategy enabled status")
    
    # Allocation
    target_allocation: float = Field(ge=0, le=1, description="Target allocation %")
    max_allocation: float = Field(ge=0, le=1, description="Maximum allocation %")
    
    # Parameters
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Strategy parameters")
    
    # Risk management
    stop_loss_pct: Optional[float] = Field(None, ge=0, le=1, description="Stop loss %")
    take_profit_pct: Optional[float] = Field(None, ge=0, description="Take profit %")
    max_trade_size: float = Field(default=0.1, ge=0, le=1, description="Max trade size %")
    
    # Execution settings
    signal_threshold: float = Field(default=0.6, ge=0, le=1, description="Signal confidence threshold")
    cooldown_period: int = Field(default=3600, ge=0, description="Cooldown between trades (seconds)")


class StrategyResult(OdinBaseModel):
    """Strategy analysis result."""
    strategy_name: str = Field(description="Strategy name")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Current signal
    current_signal: TradeSignal = Field(description="Current trading signal")
    
    # Technical indicators
    indicators: Dict[str, float] = Field(description="Current indicator values")
    
    # Performance
    daily_return: float = Field(description="Daily return %")
    total_return: float = Field(description="Total return %")
    sharpe_ratio: Optional[float] = Field(None, description="Sharpe ratio")
    win_rate: Optional[float] = Field(None, description="Win rate %")
    
    # Status
    status: StrategyStatus = Field(description="Strategy status")
    last_trade: Optional[datetime] = Field(None, description="Last trade timestamp")


class BacktestResult(OdinBaseModel):
    """Strategy backtest results."""
    strategy_name: str = Field(description="Strategy name")
    start_date: datetime = Field(description="Backtest start date")
    end_date: datetime = Field(description="Backtest end date")
    
    # Performance metrics
    total_return: float = Field(description="Total return %")
    annualized_return: float = Field(description="Annualized return %")
    volatility: NonNegativeFloat = Field(description="Volatility %")
    sharpe_ratio: Optional[float] = Field(None, description="Sharpe ratio")
    max_drawdown: float = Field(description="Maximum drawdown %")
    
    # Trading statistics
    total_trades: int = Field(ge=0, description="Total trades")
    win_rate: float = Field(ge=0, le=1, description="Win rate")
    profit_factor: Optional[float] = Field(None, description="Profit factor")
    avg_trade_return: float = Field(description="Average trade return %")
    
    # Time series data
    equity_curve: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Daily equity curve data"
    )
    trades: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Individual trade details"
    )


class OptimizationResult(OdinBaseModel):
    """Strategy parameter optimization result."""
    strategy_name: str = Field(description="Strategy name")
    optimization_id: UUID = Field(default_factory=uuid4)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Optimization parameters
    parameter_space: Dict[str, Any] = Field(description="Parameter search space")
    optimization_metric: str = Field(description="Optimization target metric")
    
    # Results
    best_parameters: Dict[str, Any] = Field(description="Best parameter combination")
    best_score: float = Field(description="Best optimization score")
    
    # Performance comparison
    baseline_performance: Dict[str, float] = Field(description="Performance with original parameters")
    optimized_performance: Dict[str, float] = Field(description="Performance with optimized parameters")
    improvement: float = Field(description="Performance improvement %")
    
    # Detailed results
    all_results: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="All parameter combinations tested"
    )
    convergence_data: List[float] = Field(
        default_factory=list,
        description="Optimization convergence data"
    )