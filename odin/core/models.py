"""
Odin Bitcoin Trading Bot - Data Models (Complete Fixed Version)
Compatible with both Pydantic v1 and v2, with dataclass fallback
"""

from datetime import datetime
from typing import Optional, Dict, Any, List, Union
from enum import Enum

# Try Pydantic v2 first, then v1, then fallback to dataclasses
try:
    from pydantic import BaseModel, Field, field_validator, model_validator
    from pydantic_settings import BaseSettings
    PYDANTIC_VERSION = 2
    print("Using Pydantic v2")
except ImportError:
    try:
        from pydantic import BaseModel, Field, validator, root_validator
        from pydantic import BaseSettings
        PYDANTIC_VERSION = 1
        print("Using Pydantic v1")
    except ImportError:
        # Fallback to dataclasses
        from dataclasses import dataclass, field
        BaseModel = object
        BaseSettings = object
        PYDANTIC_VERSION = 0
        print("Using dataclass fallback")

# Enums
class OrderType(str, Enum):
    MARKET = "market"
    LIMIT = "limit"
    STOP_LOSS = "stop_loss"
    TAKE_PROFIT = "take_profit"

class OrderSide(str, Enum):
    BUY = "buy"
    SELL = "sell"

class OrderStatus(str, Enum):
    PENDING = "pending"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"
    EXPIRED = "expired"

class PositionType(str, Enum):
    LONG = "long"
    SHORT = "short"

class SignalType(str, Enum):
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"

class StrategyStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    PAUSED = "paused"
    ERROR = "error"

# Base Model Classes
if PYDANTIC_VERSION > 0:
    class OdinBaseModel(BaseModel):
        """Base model for all Odin data structures."""
        
        class Config:
            arbitrary_types_allowed = True
            str_strip_whitespace = True
            validate_assignment = True
            use_enum_values = True
            
        def to_dict(self) -> Dict[str, Any]:
            """Convert to dictionary."""
            if PYDANTIC_VERSION == 2:
                return self.model_dump()
            else:
                return self.dict()
else:
    @dataclass
    class OdinBaseModel:
        """Base model using dataclasses."""
        
        def to_dict(self) -> Dict[str, Any]:
            """Convert to dictionary."""
            result = {}
            for key, value in self.__dict__.items():
                if isinstance(value, datetime):
                    result[key] = value.isoformat()
                elif isinstance(value, Enum):
                    result[key] = value.value
                else:
                    result[key] = value
            return result

# Price Data Models
if PYDANTIC_VERSION > 0:
    class PriceData(OdinBaseModel):
        """Bitcoin price data structure."""
        symbol: str = Field(default="BTC-USD", description="Trading symbol")
        timestamp: datetime
        price: float = Field(..., gt=0, description="Bitcoin price in USD")
        volume: Optional[float] = Field(None, ge=0, description="Trading volume")
        bid: Optional[float] = Field(None, gt=0, description="Highest bid price")
        ask: Optional[float] = Field(None, gt=0, description="Lowest ask price")
        source: str = Field(default="unknown", description="Data source")
        
        # Technical indicators (optional)
        sma_5: Optional[float] = Field(None, description="5-period SMA")
        sma_20: Optional[float] = Field(None, description="20-period SMA")
        ema_12: Optional[float] = Field(None, description="12-period EMA")
        ema_26: Optional[float] = Field(None, description="26-period EMA")
        rsi: Optional[float] = Field(None, ge=0, le=100, description="RSI value")
        macd: Optional[float] = Field(None, description="MACD line")
        macd_signal: Optional[float] = Field(None, description="MACD signal line")
        bb_upper: Optional[float] = Field(None, description="Bollinger Band upper")
        bb_lower: Optional[float] = Field(None, description="Bollinger Band lower")
        
        if PYDANTIC_VERSION == 2:
            @field_validator('price', 'bid', 'ask')
            @classmethod
            def validate_positive_prices(cls, v):
                if v is not None and v <= 0:
                    raise ValueError('Prices must be positive')
                return v
        else:
            @validator('price', 'bid', 'ask')
            def validate_positive_prices(cls, v):
                if v is not None and v <= 0:
                    raise ValueError('Prices must be positive')
                return v

    class HistoricalData(OdinBaseModel):
        """Historical price data structure."""
        timestamp: datetime
        price: float = Field(..., gt=0, description="Price at timestamp")
        volume: Optional[float] = Field(None, ge=0, description="Trading volume")
        high: Optional[float] = Field(None, gt=0, description="High price")
        low: Optional[float] = Field(None, gt=0, description="Low price")
        source: str = Field(default="unknown", description="Data source")

    class OHLCData(OdinBaseModel):
        """OHLC candlestick data."""
        symbol: str = Field(default="BTC-USD", description="Trading symbol")
        timeframe: str = Field(..., description="Timeframe (1m, 5m, 1h, etc.)")
        timestamp: datetime
        open: float = Field(..., gt=0, description="Open price")
        high: float = Field(..., gt=0, description="High price")
        low: float = Field(..., gt=0, description="Low price")
        close: float = Field(..., gt=0, description="Close price")
        volume: Optional[float] = Field(None, ge=0, description="Trading volume")
        
        # Technical indicators (optional)
        sma_20: Optional[float] = Field(None, description="20-period SMA")
        ema_12: Optional[float] = Field(None, description="12-period EMA")
        ema_26: Optional[float] = Field(None, description="26-period EMA")
        rsi: Optional[float] = Field(None, ge=0, le=100, description="RSI value")
        macd: Optional[float] = Field(None, description="MACD line")
        macd_signal: Optional[float] = Field(None, description="MACD signal line")
        bb_upper: Optional[float] = Field(None, description="Bollinger Band upper")
        bb_lower: Optional[float] = Field(None, description="Bollinger Band lower")

    class MarketDepth(OdinBaseModel):
        """Market depth/order book data."""
        symbol: str = Field(default="BTC-USD", description="Trading symbol")
        bids: List[List[float]] = Field(..., description="Bid orders [[price, size], ...]")
        asks: List[List[float]] = Field(..., description="Ask orders [[price, size], ...]")
        timestamp: datetime
        source: str = Field(default="unknown", description="Data source")

    class DataStats(OdinBaseModel):
        """Data statistics."""
        total_records: int = Field(..., ge=0, description="Total number of records")
        average_price: float = Field(..., gt=0, description="Average price")
        median_price: float = Field(..., gt=0, description="Median price")
        max_price: float = Field(..., gt=0, description="Maximum price")
        min_price: float = Field(..., gt=0, description="Minimum price")
        price_range: float = Field(..., ge=0, description="Price range (max - min)")
        price_std_dev: float = Field(..., ge=0, description="Price standard deviation")
        volatility_percent: float = Field(..., ge=0, description="Volatility percentage")
        average_volume: Optional[float] = Field(None, ge=0, description="Average volume")
        total_volume: Optional[float] = Field(None, ge=0, description="Total volume")
        oldest_record: Optional[datetime] = Field(None, description="Oldest record timestamp")
        newest_record: Optional[datetime] = Field(None, description="Newest record timestamp")
        data_sources: List[str] = Field(default_factory=list, description="Data sources used")

else:
    @dataclass
    class PriceData(OdinBaseModel):
        symbol: str
        timestamp: datetime
        price: float
        volume: Optional[float] = None
        bid: Optional[float] = None
        ask: Optional[float] = None
        source: str = "unknown"
        sma_5: Optional[float] = None
        sma_20: Optional[float] = None
        ema_12: Optional[float] = None
        ema_26: Optional[float] = None
        rsi: Optional[float] = None
        macd: Optional[float] = None
        macd_signal: Optional[float] = None
        bb_upper: Optional[float] = None
        bb_lower: Optional[float] = None
        
        def __post_init__(self):
            if self.price <= 0:
                raise ValueError('Price must be positive')

    @dataclass
    class HistoricalData(OdinBaseModel):
        timestamp: datetime
        price: float
        volume: Optional[float] = None
        high: Optional[float] = None
        low: Optional[float] = None
        source: str = "unknown"

    @dataclass
    class OHLCData(OdinBaseModel):
        symbol: str
        timeframe: str
        timestamp: datetime
        open: float
        high: float
        low: float
        close: float
        volume: Optional[float] = None
        sma_20: Optional[float] = None
        ema_12: Optional[float] = None
        ema_26: Optional[float] = None
        rsi: Optional[float] = None
        macd: Optional[float] = None
        macd_signal: Optional[float] = None
        bb_upper: Optional[float] = None
        bb_lower: Optional[float] = None

    @dataclass
    class MarketDepth(OdinBaseModel):
        symbol: str
        bids: List[List[float]]
        asks: List[List[float]]
        timestamp: datetime
        source: str = "unknown"

    @dataclass
    class DataStats(OdinBaseModel):
        total_records: int
        average_price: float
        median_price: float
        max_price: float
        min_price: float
        price_range: float
        price_std_dev: float
        volatility_percent: float
        average_volume: Optional[float] = None
        total_volume: Optional[float] = None
        oldest_record: Optional[datetime] = None
        newest_record: Optional[datetime] = None
        data_sources: List[str] = field(default_factory=list)

# Trading Models
if PYDANTIC_VERSION > 0:
    class TradeExecution(OdinBaseModel):
        """Trade execution details."""
        id: str
        timestamp: datetime
        strategy_id: str
        symbol: str = Field(default="BTC-USD")
        side: OrderSide
        order_type: OrderType
        amount: float = Field(..., gt=0)
        price: float = Field(..., gt=0)
        status: OrderStatus = Field(default=OrderStatus.PENDING)
        
        # Execution details
        executed_amount: Optional[float] = Field(None, ge=0)
        executed_price: Optional[float] = Field(None, gt=0)
        fees: Optional[float] = Field(None, ge=0)
        
        # P&L
        pnl: Optional[float] = Field(None, description="Profit and Loss")
        pnl_percentage: Optional[float] = Field(None, description="P&L as percentage")

    class TradeOrder(OdinBaseModel):
        """Trade order model for order management."""
        id: str = Field(..., description="Order unique identifier")
        portfolio_id: str = Field(..., description="Associated portfolio ID")
        strategy_id: Optional[str] = Field(None, description="Strategy that generated this order")
        
        # Order details
        symbol: str = Field(default="BTC-USD", description="Trading symbol")
        side: OrderSide = Field(..., description="Buy or sell")
        order_type: OrderType = Field(..., description="Order type (market, limit, etc.)")
        status: OrderStatus = Field(default=OrderStatus.PENDING, description="Order status")
        
        # Amounts and pricing
        quantity: float = Field(..., gt=0, description="Order quantity")
        price: Optional[float] = Field(None, gt=0, description="Order price (for limit orders)")
        filled_quantity: float = Field(default=0, ge=0, description="Filled quantity")
        average_fill_price: Optional[float] = Field(None, gt=0, description="Average fill price")
        
        # Fees and costs
        fees: float = Field(default=0, ge=0, description="Trading fees")
        commission: float = Field(default=0, ge=0, description="Commission paid")
        
        # Risk management
        stop_loss: Optional[float] = Field(None, gt=0, description="Stop loss price")
        take_profit: Optional[float] = Field(None, gt=0, description="Take profit price")
        
        # Timestamps
        created_at: datetime = Field(default_factory=datetime.now, description="Order creation time")
        updated_at: datetime = Field(default_factory=datetime.now, description="Last update time")
        filled_at: Optional[datetime] = Field(None, description="Order fill time")
        
        # Execution details
        exchange_order_id: Optional[str] = Field(None, description="Exchange order ID")
        error_message: Optional[str] = Field(None, description="Error message if failed")
        
        # Performance tracking
        pnl: Optional[float] = Field(None, description="Realized P&L for this order")
        pnl_percentage: Optional[float] = Field(None, description="P&L as percentage")

    class TradeSignal(OdinBaseModel):
        """Trade signal model for strategy signals."""
        id: str = Field(..., description="Signal unique identifier")
        strategy_id: str = Field(..., description="Strategy that generated the signal")
        
        # Signal details
        symbol: str = Field(default="BTC-USD", description="Trading symbol")
        signal_type: SignalType = Field(..., description="Signal type (buy/sell/hold)")
        confidence: float = Field(..., ge=0, le=1, description="Signal confidence (0-1)")
        strength: float = Field(default=0.5, ge=0, le=1, description="Signal strength")
        
        # Price information
        price: float = Field(..., gt=0, description="Price when signal generated")
        target_price: Optional[float] = Field(None, gt=0, description="Target price")
        stop_loss_price: Optional[float] = Field(None, gt=0, description="Stop loss price")
        
        # Technical indicators
        indicators: Optional[Dict[str, float]] = Field(None, description="Technical indicators")
        reasoning: Optional[str] = Field(None, description="Signal reasoning")
        
        # Risk metrics
        risk_score: float = Field(default=0.5, ge=0, le=1, description="Risk score")
        expected_return: Optional[float] = Field(None, description="Expected return percentage")
        
        # Execution tracking
        executed: bool = Field(default=False, description="Whether signal was executed")
        execution_id: Optional[str] = Field(None, description="Related execution ID")
        execution_price: Optional[float] = Field(None, gt=0, description="Actual execution price")
        
        # Timestamps
        created_at: datetime = Field(default_factory=datetime.now, description="Signal creation time")
        expires_at: Optional[datetime] = Field(None, description="Signal expiration time")
        executed_at: Optional[datetime] = Field(None, description="Signal execution time")

else:
    @dataclass
    class TradeExecution(OdinBaseModel):
        id: str
        timestamp: datetime
        strategy_id: str
        symbol: str
        side: OrderSide
        order_type: OrderType
        amount: float
        price: float
        status: OrderStatus = OrderStatus.PENDING
        executed_amount: Optional[float] = None
        executed_price: Optional[float] = None
        fees: Optional[float] = None
        pnl: Optional[float] = None
        pnl_percentage: Optional[float] = None
        
        def __post_init__(self):
            if self.amount <= 0:
                raise ValueError('Amount must be positive')
            if self.price <= 0:
                raise ValueError('Price must be positive')

    @dataclass
    class TradeOrder(OdinBaseModel):
        id: str
        portfolio_id: str
        strategy_id: Optional[str] = None
        symbol: str = "BTC-USD"
        side: OrderSide = OrderSide.BUY
        order_type: OrderType = OrderType.MARKET
        status: OrderStatus = OrderStatus.PENDING
        quantity: float = 0.0
        price: Optional[float] = None
        filled_quantity: float = 0.0
        average_fill_price: Optional[float] = None
        fees: float = 0.0
        commission: float = 0.0
        stop_loss: Optional[float] = None
        take_profit: Optional[float] = None
        created_at: datetime = field(default_factory=datetime.now)
        updated_at: datetime = field(default_factory=datetime.now)
        filled_at: Optional[datetime] = None
        exchange_order_id: Optional[str] = None
        error_message: Optional[str] = None
        pnl: Optional[float] = None
        pnl_percentage: Optional[float] = None
        
        def __post_init__(self):
            if self.quantity <= 0:
                raise ValueError('Quantity must be positive')
            if self.price is not None and self.price <= 0:
                raise ValueError('Price must be positive')

    @dataclass
    class TradeSignal(OdinBaseModel):
        id: str
        strategy_id: str
        symbol: str = "BTC-USD"
        signal_type: SignalType = SignalType.HOLD
        confidence: float = 0.5
        strength: float = 0.5
        price: float = 0.0
        target_price: Optional[float] = None
        stop_loss_price: Optional[float] = None
        indicators: Optional[Dict[str, float]] = None
        reasoning: Optional[str] = None
        risk_score: float = 0.5
        expected_return: Optional[float] = None
        executed: bool = False
        execution_id: Optional[str] = None
        execution_price: Optional[float] = None
        created_at: datetime = field(default_factory=datetime.now)
        expires_at: Optional[datetime] = None
        executed_at: Optional[datetime] = None
        
        def __post_init__(self):
            if not 0 <= self.confidence <= 1:
                raise ValueError('Confidence must be between 0 and 1')
            if self.price <= 0:
                raise ValueError('Price must be positive')

# Strategy Models
if PYDANTIC_VERSION > 0:
    class StrategySignal(OdinBaseModel):
        """Trading signal from a strategy."""
        strategy_id: str
        timestamp: datetime
        signal_type: SignalType
        confidence: float = Field(..., ge=0, le=1, description="Signal confidence (0-1)")
        price: float = Field(..., gt=0, description="Price at signal generation")
        
        # Additional signal data
        indicators: Optional[Dict[str, float]] = Field(None, description="Technical indicators")
        reasoning: Optional[str] = Field(None, description="Signal reasoning")
        
        # Execution tracking
        executed: bool = Field(default=False)
        execution_id: Optional[str] = Field(None)

else:
    @dataclass
    class StrategySignal(OdinBaseModel):
        strategy_id: str
        timestamp: datetime
        signal_type: SignalType
        confidence: float
        price: float
        indicators: Optional[Dict[str, float]] = None
        reasoning: Optional[str] = None
        executed: bool = False
        execution_id: Optional[str] = None
        
        def __post_init__(self):
            if not 0 <= self.confidence <= 1:
                raise ValueError('Confidence must be between 0 and 1')
            if self.price <= 0:
                raise ValueError('Price must be positive')

# Portfolio Models
if PYDANTIC_VERSION > 0:
    class PortfolioSnapshot(OdinBaseModel):
        """Portfolio snapshot at a point in time."""
        timestamp: datetime
        
        # Balances
        total_value: float = Field(..., ge=0, description="Total portfolio value in USD")
        cash_balance: float = Field(..., ge=0, description="Cash balance in USD")
        btc_balance: float = Field(..., ge=0, description="Bitcoin balance")
        
        # Performance
        daily_pnl: Optional[float] = Field(None, description="24h P&L in USD")
        daily_pnl_percentage: Optional[float] = Field(None, description="24h P&L percentage")
        
        # Allocation
        allocation: Optional[Dict[str, float]] = Field(None, description="Asset allocation percentages")

    class Portfolio(OdinBaseModel):
        """Portfolio management model."""
        id: str = Field(..., description="Portfolio unique identifier")
        name: str = Field(..., description="Portfolio name")
        description: Optional[str] = Field(None, description="Portfolio description")
        
        # Core values
        total_value: float = Field(..., gt=0, description="Total portfolio value in USD")
        cash_balance: float = Field(..., ge=0, description="Available cash balance")
        invested_amount: float = Field(..., ge=0, description="Total invested amount")
        
        # Performance metrics
        unrealized_pnl: Optional[float] = Field(None, description="Unrealized P&L")
        realized_pnl: Optional[float] = Field(None, description="Realized P&L")
        daily_pnl: Optional[float] = Field(None, description="24h P&L")
        daily_pnl_percentage: Optional[float] = Field(None, description="24h P&L percentage")
        
        # Risk metrics
        max_drawdown: Optional[float] = Field(None, description="Maximum drawdown")
        sharpe_ratio: Optional[float] = Field(None, description="Sharpe ratio")
        volatility: Optional[float] = Field(None, ge=0, description="Portfolio volatility")
        
        # Allocation
        allocation: Optional[Dict[str, float]] = Field(None, description="Asset allocation percentages")
        target_allocation: Optional[Dict[str, float]] = Field(None, description="Target allocation percentages")
        
        # Timestamps
        created_at: datetime = Field(default_factory=datetime.now, description="Portfolio creation time")
        updated_at: datetime = Field(default_factory=datetime.now, description="Last update time")
        
        # Status
        status: str = Field(default="active", description="Portfolio status")

    class PortfolioSummary(OdinBaseModel):
        """Portfolio summary metrics model."""
        portfolio_id: str = Field(..., description="Portfolio ID")
        
        # Core metrics
        total_value: float = Field(..., gt=0, description="Total portfolio value")
        available_cash: float = Field(..., ge=0, description="Available cash")
        invested_amount: float = Field(..., ge=0, description="Total invested")
        
        # P&L metrics
        unrealized_pnl: float = Field(default=0, description="Unrealized P&L")
        realized_pnl: float = Field(default=0, description="Realized P&L")
        total_fees_paid: float = Field(default=0, ge=0, description="Total fees paid")
        
        # Performance metrics
        number_of_trades: int = Field(default=0, ge=0, description="Total number of trades")
        win_rate: float = Field(default=0, ge=0, le=100, description="Win rate percentage")
        avg_trade_size: float = Field(default=0, ge=0, description="Average trade size")
        largest_win: float = Field(default=0, description="Largest winning trade")
        largest_loss: float = Field(default=0, description="Largest losing trade")
        
        # Time tracking
        created_at: datetime = Field(default_factory=datetime.now, description="Summary creation time")
        updated_at: datetime = Field(default_factory=datetime.now, description="Last update time")

    class Allocation(OdinBaseModel):
        """Portfolio allocation model."""
        portfolio_id: str = Field(..., description="Portfolio ID")
        
        # Current allocation
        current_allocation: Dict[str, float] = Field(..., description="Current asset allocation percentages")
        target_allocation: Dict[str, float] = Field(..., description="Target asset allocation percentages")
        
        # Allocation drift
        allocation_drift: Dict[str, float] = Field(..., description="Difference between current and target")
        drift_percentage: float = Field(..., description="Total drift as percentage")
        
        # Rebalancing
        rebalance_needed: bool = Field(default=False, description="Whether rebalancing is needed")
        rebalance_threshold: float = Field(default=5.0, description="Rebalance threshold percentage")
        last_rebalance: Optional[datetime] = Field(None, description="Last rebalance timestamp")
        
        # Metadata
        created_at: datetime = Field(default_factory=datetime.now, description="Creation time")
        updated_at: datetime = Field(default_factory=datetime.now, description="Last update time")

    class PerformanceMetrics(OdinBaseModel):
        """Performance metrics model."""
        portfolio_id: str = Field(..., description="Portfolio ID")
        timeframe: str = Field(..., description="Timeframe (1d, 7d, 30d, etc.)")
        
        # Return metrics
        total_return: float = Field(..., description="Total return percentage")
        annualized_return: float = Field(..., description="Annualized return percentage")
        daily_return: float = Field(default=0, description="Daily return percentage")
        
        # Risk-adjusted metrics
        sharpe_ratio: float = Field(..., description="Sharpe ratio")
        sortino_ratio: Optional[float] = Field(None, description="Sortino ratio")
        calmar_ratio: Optional[float] = Field(None, description="Calmar ratio")
        
        # Volatility metrics
        volatility: float = Field(..., ge=0, description="Volatility percentage")
        downside_volatility: Optional[float] = Field(None, ge=0, description="Downside volatility")
        
        # Drawdown metrics
        max_drawdown: float = Field(..., description="Maximum drawdown percentage")
        current_drawdown: float = Field(default=0, description="Current drawdown percentage")
        drawdown_duration: int = Field(default=0, ge=0, description="Current drawdown duration in days")
        
        # Win/Loss metrics
        win_rate: float = Field(..., ge=0, le=100, description="Win rate percentage")
        profit_factor: Optional[float] = Field(None, description="Profit factor")
        average_win: float = Field(default=0, description="Average winning trade")
        average_loss: float = Field(default=0, description="Average losing trade")
        
        # Trade metrics
        total_trades: int = Field(default=0, ge=0, description="Total number of trades")
        winning_trades: int = Field(default=0, ge=0, description="Number of winning trades")
        losing_trades: int = Field(default=0, ge=0, description="Number of losing trades")
        
        # Portfolio metrics
        starting_value: float = Field(..., gt=0, description="Starting portfolio value")
        ending_value: float = Field(..., gt=0, description="Ending portfolio value")
        peak_value: float = Field(..., gt=0, description="Peak portfolio value")
        
        # Benchmarking
        benchmark_return: Optional[float] = Field(None, description="Benchmark return percentage")
        alpha: Optional[float] = Field(None, description="Alpha vs benchmark")
        beta: Optional[float] = Field(None, description="Beta vs benchmark")
        
        # Timestamps
        period_start: datetime = Field(..., description="Performance period start")
        period_end: datetime = Field(..., description="Performance period end")
        calculated_at: datetime = Field(default_factory=datetime.now, description="Calculation timestamp")

    class RiskMetrics(OdinBaseModel):
        """Risk metrics model."""
        portfolio_id: str = Field(..., description="Portfolio ID")
        
        # Value at Risk
        var_95: float = Field(..., description="Value at Risk at 95% confidence")
        var_99: float = Field(..., description="Value at Risk at 99% confidence")
        cvar_95: float = Field(..., description="Conditional VaR at 95% confidence")
        
        # Risk ratios
        risk_score: float = Field(..., ge=0, le=10, description="Overall risk score (0-10)")
        concentration_risk: float = Field(..., ge=0, le=1, description="Concentration risk (0-1)")
        liquidity_risk: float = Field(..., ge=0, le=1, description="Liquidity risk (0-1)")
        
        # Exposure metrics
        current_exposure: float = Field(..., ge=0, le=1, description="Current market exposure")
        max_exposure_allowed: float = Field(..., ge=0, le=1, description="Maximum allowed exposure")
        leverage: float = Field(default=1.0, ge=1, description="Current leverage ratio")
        
        # Position sizing
        largest_position_pct: float = Field(..., ge=0, le=100, description="Largest position as percentage")
        avg_position_size: float = Field(..., ge=0, description="Average position size")
        
        # Drawdown risk
        max_historical_drawdown: float = Field(..., description="Maximum historical drawdown")
        time_to_recovery: Optional[int] = Field(None, ge=0, description="Average recovery time in days")
        
        # Correlation metrics
        correlation_to_btc: float = Field(..., ge=-1, le=1, description="Correlation to Bitcoin")
        diversification_ratio: Optional[float] = Field(None, description="Portfolio diversification ratio")
        
        # Stress testing
        stress_test_results: Optional[Dict[str, float]] = Field(None, description="Stress test scenario results")
        
        # Risk limits compliance
        within_risk_limits: bool = Field(..., description="Whether portfolio is within risk limits")
        limit_breaches: List[str] = Field(default_factory=list, description="Current limit breaches")
        
        # Timestamps
        calculated_at: datetime = Field(default_factory=datetime.now, description="Calculation timestamp")
        next_calculation: Optional[datetime] = Field(None, description="Next scheduled calculation")

    class Position(OdinBaseModel):
        """Trading position model."""
        id: str = Field(..., description="Position unique identifier")
        portfolio_id: str = Field(..., description="Associated portfolio ID")
        strategy_id: Optional[str] = Field(None, description="Strategy that opened this position")
        
        # Position details
        symbol: str = Field(default="BTC-USD", description="Trading symbol")
        side: PositionType = Field(..., description="Long or short position")
        status: str = Field(default="open", description="Position status (open, closed, partial)")
        
        # Size and pricing
        size: float = Field(..., gt=0, description="Position size")
        entry_price: float = Field(..., gt=0, description="Average entry price")
        current_price: Optional[float] = Field(None, gt=0, description="Current market price")
        
        # Cost basis
        cost_basis: float = Field(..., gt=0, description="Total cost basis")
        market_value: Optional[float] = Field(None, description="Current market value")
        
        # P&L tracking
        unrealized_pnl: float = Field(default=0, description="Unrealized P&L")
        realized_pnl: float = Field(default=0, description="Realized P&L")
        unrealized_pnl_percent: float = Field(default=0, description="Unrealized P&L percentage")
        
        # Risk management
        stop_loss: Optional[float] = Field(None, gt=0, description="Stop loss price")
        take_profit: Optional[float] = Field(None, gt=0, description="Take profit price")
        trailing_stop: Optional[float] = Field(None, description="Trailing stop distance")
        
        # Fees and costs
        total_fees: float = Field(default=0, ge=0, description="Total fees paid")
        commission: float = Field(default=0, ge=0, description="Commission paid")
        
        # Timestamps
        opened_at: datetime = Field(default_factory=datetime.now, description="Position open time")
        closed_at: Optional[datetime] = Field(None, description="Position close time")
        updated_at: datetime = Field(default_factory=datetime.now, description="Last update time")
        
        # Duration tracking
        duration_minutes: Optional[int] = Field(None, ge=0, description="Position duration in minutes")
        
        # Execution details
        opening_orders: List[str] = Field(default_factory=list, description="Order IDs that opened this position")
        closing_orders: List[str] = Field(default_factory=list, description="Order IDs that closed this position")

    class DrawdownAlert(OdinBaseModel):
        """Drawdown alert model."""
        id: str = Field(..., description="Alert unique identifier")
        portfolio_id: str = Field(..., description="Associated portfolio ID")
        
        # Alert details
        alert_type: str = Field(..., description="Type of drawdown alert")
        severity: str = Field(..., description="Alert severity (warning, critical, emergency)")
        
        # Drawdown information
        current_drawdown: float = Field(..., description="Current drawdown percentage")
        max_allowed_drawdown: float = Field(..., description="Maximum allowed drawdown")
        peak_value: float = Field(..., gt=0, description="Portfolio peak value")
        current_value: float = Field(..., gt=0, description="Current portfolio value")
        
        # Duration tracking
        drawdown_duration: int = Field(..., ge=0, description="Drawdown duration in hours")
        max_duration_allowed: Optional[int] = Field(None, description="Maximum allowed duration")
        
        # Risk metrics
        recovery_estimate: Optional[int] = Field(None, description="Estimated recovery time in days")
        risk_score: float = Field(..., ge=0, le=10, description="Current risk score")
        
        # Actions taken
        actions_taken: List[str] = Field(default_factory=list, description="Automated actions taken")
        manual_review_required: bool = Field(default=False, description="Whether manual review is required")
        
        # Status
        status: str = Field(default="active", description="Alert status (active, resolved, dismissed)")
        acknowledged: bool = Field(default=False, description="Whether alert has been acknowledged")
        acknowledged_by: Optional[str] = Field(None, description="User who acknowledged the alert")
        
        # Timestamps
        triggered_at: datetime = Field(default_factory=datetime.now, description="Alert trigger time")
        resolved_at: Optional[datetime] = Field(None, description="Alert resolution time")
        acknowledged_at: Optional[datetime] = Field(None, description="Alert acknowledgment time")
        
        # Additional context
        market_conditions: Optional[Dict[str, Any]] = Field(None, description="Market conditions when triggered")
        recommended_actions: List[str] = Field(default_factory=list, description="Recommended actions")
        
        # Escalation
        escalation_level: int = Field(default=1, ge=1, le=5, description="Escalation level (1-5)")
        escalated_to: Optional[str] = Field(None, description="Who the alert was escalated to")

    class RiskLimits(OdinBaseModel):
        """Risk management limits model."""
        portfolio_id: str = Field(..., description="Portfolio ID")
        
        # Position limits
        max_position_size: float = Field(default=0.95, ge=0, le=1, description="Maximum position size (0-1)")
        max_leverage: float = Field(default=1.0, ge=1, description="Maximum leverage allowed")
        
        # Risk per trade
        risk_per_trade: float = Field(default=0.02, ge=0, le=0.1, description="Risk per trade (0-0.1)")
        max_daily_loss: float = Field(default=0.05, ge=0, le=0.2, description="Maximum daily loss (0-0.2)")
        max_drawdown: float = Field(default=0.15, ge=0, le=0.5, description="Maximum drawdown (0-0.5)")
        
        # Exposure limits
        max_exposure: float = Field(default=0.8, ge=0, le=1, description="Maximum portfolio exposure")
        concentration_limit: float = Field(default=0.3, ge=0, le=1, description="Single asset concentration limit")
        
        # Stop loss settings
        global_stop_loss: Optional[float] = Field(None, description="Global stop loss percentage")
        trailing_stop: bool = Field(default=False, description="Enable trailing stop loss")
        
        # Time-based limits
        max_trades_per_day: int = Field(default=50, ge=0, description="Maximum trades per day")
        cooldown_period: int = Field(default=0, ge=0, description="Cooldown period in minutes")
        
        # Metadata
        created_at: datetime = Field(default_factory=datetime.now, description="Creation time")
        updated_at: datetime = Field(default_factory=datetime.now, description="Last update time")

else:
    @dataclass
    class PortfolioSnapshot(OdinBaseModel):
        timestamp: datetime
        total_value: float
        cash_balance: float
        btc_balance: float
        daily_pnl: Optional[float] = None
        daily_pnl_percentage: Optional[float] = None
        allocation: Optional[Dict[str, float]] = None
        
        def __post_init__(self):
            if self.total_value < 0:
                raise ValueError('Total value cannot be negative')

    @dataclass
    class Portfolio(OdinBaseModel):
        id: str
        name: str
        description: Optional[str] = None
        total_value: float = 0.0
        cash_balance: float = 0.0
        invested_amount: float = 0.0
        unrealized_pnl: Optional[float] = None
        realized_pnl: Optional[float] = None
        daily_pnl: Optional[float] = None
        daily_pnl_percentage: Optional[float] = None
        max_drawdown: Optional[float] = None
        sharpe_ratio: Optional[float] = None
        volatility: Optional[float] = None
        allocation: Optional[Dict[str, float]] = None
        target_allocation: Optional[Dict[str, float]] = None
        created_at: datetime = field(default_factory=datetime.now)
        updated_at: datetime = field(default_factory=datetime.now)
        status: str = "active"
        
        def __post_init__(self):
            if self.total_value < 0:
                raise ValueError('Total value cannot be negative')
            if self.cash_balance < 0:
                raise ValueError('Cash balance cannot be negative')

    @dataclass
    class PortfolioSummary(OdinBaseModel):
        portfolio_id: str
        total_value: float = 0.0
        available_cash: float = 0.0
        invested_amount: float = 0.0
        unrealized_pnl: float = 0.0
        realized_pnl: float = 0.0
        total_fees_paid: float = 0.0
        number_of_trades: int = 0
        win_rate: float = 0.0
        avg_trade_size: float = 0.0
        largest_win: float = 0.0
        largest_loss: float = 0.0
        created_at: datetime = field(default_factory=datetime.now)
        updated_at: datetime = field(default_factory=datetime.now)
        
        def __post_init__(self):
            if self.total_value < 0:
                raise ValueError('Total value cannot be negative')
            if not 0 <= self.win_rate <= 100:
                raise ValueError('Win rate must be between 0 and 100')

    @dataclass
    class Allocation(OdinBaseModel):
        portfolio_id: str
        current_allocation: Dict[str, float] = field(default_factory=dict)
        target_allocation: Dict[str, float] = field(default_factory=dict)
        allocation_drift: Dict[str, float] = field(default_factory=dict)
        drift_percentage: float = 0.0
        rebalance_needed: bool = False
        rebalance_threshold: float = 5.0
        last_rebalance: Optional[datetime] = None
        created_at: datetime = field(default_factory=datetime.now)
        updated_at: datetime = field(default_factory=datetime.now)

    @dataclass
    class RiskLimits(OdinBaseModel):
        portfolio_id: str
        max_position_size: float = 0.95
        max_leverage: float = 1.0
        risk_per_trade: float = 0.02
        max_daily_loss: float = 0.05
        max_drawdown: float = 0.15
        max_exposure: float = 0.8
        concentration_limit: float = 0.3
        global_stop_loss: Optional[float] = None
        trailing_stop: bool = False
        max_trades_per_day: int = 50
        cooldown_period: int = 0
        created_at: datetime = field(default_factory=datetime.now)
        updated_at: datetime = field(default_factory=datetime.now)
        
        def __post_init__(self):
            if not 0 <= self.max_position_size <= 1:
                raise ValueError('Max position size must be between 0 and 1')
            if not 0 <= self.risk_per_trade <= 0.1:
                raise ValueError('Risk per trade must be between 0 and 0.1')

    @dataclass
    class PerformanceMetrics(OdinBaseModel):
        portfolio_id: str
        timeframe: str
        total_return: float = 0.0
        annualized_return: float = 0.0
        daily_return: float = 0.0
        sharpe_ratio: float = 0.0
        sortino_ratio: Optional[float] = None
        calmar_ratio: Optional[float] = None
        volatility: float = 0.0
        downside_volatility: Optional[float] = None
        max_drawdown: float = 0.0
        current_drawdown: float = 0.0
        drawdown_duration: int = 0
        win_rate: float = 0.0
        profit_factor: Optional[float] = None
        average_win: float = 0.0
        average_loss: float = 0.0
        total_trades: int = 0
        winning_trades: int = 0
        losing_trades: int = 0
        starting_value: float = 10000.0
        ending_value: float = 10000.0
        peak_value: float = 10000.0
        benchmark_return: Optional[float] = None
        alpha: Optional[float] = None
        beta: Optional[float] = None
        period_start: datetime = field(default_factory=datetime.now)
        period_end: datetime = field(default_factory=datetime.now)
        calculated_at: datetime = field(default_factory=datetime.now)
        
        def __post_init__(self):
            if not 0 <= self.win_rate <= 100:
                raise ValueError('Win rate must be between 0 and 100')

    @dataclass
    class RiskMetrics(OdinBaseModel):
        portfolio_id: str
        var_95: float = 0.0
        var_99: float = 0.0
        cvar_95: float = 0.0
        risk_score: float = 5.0
        concentration_risk: float = 0.0
        liquidity_risk: float = 0.0
        current_exposure: float = 0.0
        max_exposure_allowed: float = 0.8
        leverage: float = 1.0
        largest_position_pct: float = 0.0
        avg_position_size: float = 0.0
        max_historical_drawdown: float = 0.0
        time_to_recovery: Optional[int] = None
        correlation_to_btc: float = 1.0
        diversification_ratio: Optional[float] = None
        stress_test_results: Optional[Dict[str, float]] = None
        within_risk_limits: bool = True
        limit_breaches: List[str] = field(default_factory=list)
        calculated_at: datetime = field(default_factory=datetime.now)
        next_calculation: Optional[datetime] = None
        
        def __post_init__(self):
            if not 0 <= self.risk_score <= 10:
                raise ValueError('Risk score must be between 0 and 10')
            if not -1 <= self.correlation_to_btc <= 1:
                raise ValueError('Correlation must be between -1 and 1')

    @dataclass
    class Position(OdinBaseModel):
        id: str
        portfolio_id: str
        strategy_id: Optional[str] = None
        symbol: str = "BTC-USD"
        side: PositionType = PositionType.LONG
        status: str = "open"
        size: float = 0.0
        entry_price: float = 0.0
        current_price: Optional[float] = None
        cost_basis: float = 0.0
        market_value: Optional[float] = None
        unrealized_pnl: float = 0.0
        realized_pnl: float = 0.0
        unrealized_pnl_percent: float = 0.0
        stop_loss: Optional[float] = None
        take_profit: Optional[float] = None
        trailing_stop: Optional[float] = None
        total_fees: float = 0.0
        commission: float = 0.0
        opened_at: datetime = field(default_factory=datetime.now)
        closed_at: Optional[datetime] = None
        updated_at: datetime = field(default_factory=datetime.now)
        duration_minutes: Optional[int] = None
        opening_orders: List[str] = field(default_factory=list)
        closing_orders: List[str] = field(default_factory=list)
        
        def __post_init__(self):
            if self.size <= 0:
                raise ValueError('Position size must be positive')
            if self.entry_price <= 0:
                raise ValueError('Entry price must be positive')

    @dataclass
    class DrawdownAlert(OdinBaseModel):
        id: str
        portfolio_id: str
        alert_type: str = "drawdown_warning"
        severity: str = "warning"
        current_drawdown: float = 0.0
        max_allowed_drawdown: float = 15.0
        peak_value: float = 10000.0
        current_value: float = 10000.0
        drawdown_duration: int = 0
        max_duration_allowed: Optional[int] = None
        recovery_estimate: Optional[int] = None
        risk_score: float = 5.0
        actions_taken: List[str] = field(default_factory=list)
        manual_review_required: bool = False
        status: str = "active"
        acknowledged: bool = False
        acknowledged_by: Optional[str] = None
        triggered_at: datetime = field(default_factory=datetime.now)
        resolved_at: Optional[datetime] = None
        acknowledged_at: Optional[datetime] = None
        market_conditions: Optional[Dict[str, Any]] = None
        recommended_actions: List[str] = field(default_factory=list)
        escalation_level: int = 1
        escalated_to: Optional[str] = None
        
        def __post_init__(self):
            if not 1 <= self.escalation_level <= 5:
                raise ValueError('Escalation level must be between 1 and 5')
            if self.peak_value <= 0:
                raise ValueError('Peak value must be positive')
            if self.current_value <= 0:
                raise ValueError('Current value must be positive')

# API Response Models
if PYDANTIC_VERSION > 0:
    class APIResponse(OdinBaseModel):
        """Standard API response format."""
        success: bool = Field(..., description="Whether the request was successful")
        message: Optional[str] = Field(None, description="Response message")
        data: Optional[Any] = Field(None, description="Response data")
        timestamp: datetime = Field(default_factory=datetime.now, description="Response timestamp")
        
    class ErrorResponse(APIResponse):
        """Error response format."""
        success: bool = Field(default=False)
        error_code: Optional[str] = Field(None, description="Error code")
        error_details: Optional[Dict[str, Any]] = Field(None, description="Detailed error information")

else:
    @dataclass
    class APIResponse(OdinBaseModel):
        success: bool
        message: Optional[str] = None
        data: Optional[Any] = None
        timestamp: datetime = field(default_factory=datetime.now)
    
    @dataclass
    class ErrorResponse(APIResponse):
        success: bool = False
        error_code: Optional[str] = None
        error_details: Optional[Dict[str, Any]] = None

# Data Collection Models
if PYDANTIC_VERSION > 0:
    class DataSourceStatus(OdinBaseModel):
        """Data source status information."""
        name: str = Field(..., description="Data source name")
        enabled: bool = Field(default=True, description="Whether source is enabled")
        healthy: bool = Field(default=True, description="Whether source is healthy")
        priority: int = Field(default=1, description="Source priority (lower = higher priority)")
        error_count: int = Field(default=0, ge=0, description="Current error count")
        last_update: Optional[datetime] = Field(None, description="Last successful update")
        response_time_ms: Optional[float] = Field(None, ge=0, description="Average response time")

    class DataCollectionResult(OdinBaseModel):
        """Result of a data collection operation."""
        success: bool = Field(..., description="Whether collection was successful")
        price: Optional[float] = Field(None, gt=0, description="Collected price")
        source: Optional[str] = Field(None, description="Data source used")
        timestamp: Optional[datetime] = Field(None, description="Collection timestamp")
        error: Optional[str] = Field(None, description="Error message if failed")

else:
    @dataclass
    class DataSourceStatus(OdinBaseModel):
        name: str
        enabled: bool = True
        healthy: bool = True
        priority: int = 1
        error_count: int = 0
        last_update: Optional[datetime] = None
        response_time_ms: Optional[float] = None

    @dataclass
    class DataCollectionResult(OdinBaseModel):
        success: bool
        price: Optional[float] = None
        source: Optional[str] = None
        timestamp: Optional[datetime] = None
        error: Optional[str] = None

# Configuration Models
if PYDANTIC_VERSION > 0 and BaseSettings != object:
    class TradingConfig(BaseSettings):
        """Trading configuration settings."""
        
        # Risk management
        max_position_size: float = Field(0.95, ge=0, le=1, description="Maximum position size (0-1)")
        risk_per_trade: float = Field(0.02, ge=0, le=0.1, description="Risk per trade (0-0.1)")
        max_daily_loss: float = Field(0.05, ge=0, le=0.2, description="Maximum daily loss (0-0.2)")
        max_drawdown: float = Field(0.15, ge=0, le=0.5, description="Maximum drawdown (0-0.5)")
        
        # Trading settings
        enable_live_trading: bool = Field(False, description="Enable live trading")
        auto_rebalance: bool = Field(True, description="Enable automatic rebalancing")
        
        # Exchange settings
        exchange_name: str = Field("binance", description="Exchange name")
        exchange_sandbox: bool = Field(True, description="Use exchange sandbox")
        
        class Config:
            env_prefix = "ODIN_"
            case_sensitive = False
            env_file = ".env"
            
else:
    # Fallback simple config
    @dataclass
    class TradingConfig:
        """Simple trading configuration."""
        max_position_size: float = 0.95
        risk_per_trade: float = 0.02
        max_daily_loss: float = 0.05
        max_drawdown: float = 0.15
        enable_live_trading: bool = False
        auto_rebalance: bool = True
        exchange_name: str = "binance"
        exchange_sandbox: bool = True
        
        def __post_init__(self):
            if not 0 <= self.max_position_size <= 1:
                raise ValueError('Max position size must be between 0 and 1')
            if not 0 <= self.risk_per_trade <= 0.1:
                raise ValueError('Risk per trade must be between 0 and 0.1')

# Utility Functions
def create_price_data(timestamp: datetime, price: float, volume: float = None, 
                      market_cap: float = None, source: str = "unknown") -> PriceData:
    """Create a PriceData instance."""
    return PriceData(
        symbol="BTC-USD",
        timestamp=timestamp, 
        price=price, 
        volume=volume, 
        source=source
    )

def create_ohlc_data(symbol: str, timeframe: str, timestamp: datetime,
                     open_price: float, high: float, low: float, close: float,
                     volume: float = None) -> OHLCData:
    """Create an OHLCData instance."""
    return OHLCData(
        symbol=symbol,
        timeframe=timeframe,
        timestamp=timestamp,
        open=open_price,
        high=high,
        low=low,
        close=close,
        volume=volume
    )

def create_trade_execution(trade_id: str, strategy_id: str, side: str, 
                          amount: float, price: float) -> TradeExecution:
    """Create a TradeExecution instance."""
    return TradeExecution(
        id=trade_id,
        timestamp=datetime.now(),
        strategy_id=strategy_id,
        symbol="BTC-USD",
        side=OrderSide(side),
        order_type=OrderType.MARKET,
        amount=amount,
        price=price
    )

def create_api_response(success: bool, data: Any = None, message: str = None) -> APIResponse:
    """Create an APIResponse instance."""
    return APIResponse(success=success, data=data, message=message)

def create_market_depth(symbol: str, bids: List[List[float]], asks: List[List[float]],
                        timestamp: datetime = None, source: str = "unknown") -> MarketDepth:
    """Create a MarketDepth instance."""
    return MarketDepth(
        symbol=symbol,
        bids=bids,
        asks=asks,
        timestamp=timestamp or datetime.now(),
        source=source
    )

# Export all models
__all__ = [
    # Enums
    'OrderType', 'OrderSide', 'OrderStatus', 'PositionType', 'SignalType', 'StrategyStatus',
    
    # Base
    'OdinBaseModel',
    
    # Price Models
    'PriceData', 'HistoricalData', 'OHLCData', 'MarketDepth', 'DataStats',
    
    # Trading Models
    'TradeExecution', 'TradeOrder', 'TradeSignal', 'Position',
    
    # Strategy Models
    'StrategySignal',
    
    # Portfolio Models
    'PortfolioSnapshot', 'Portfolio', 'PortfolioSummary', 'Allocation', 'RiskLimits',
    'PerformanceMetrics', 'RiskMetrics', 'DrawdownAlert',
    
    # API Models
    'APIResponse', 'ErrorResponse',
    
    # Data Collection Models
    'DataSourceStatus', 'DataCollectionResult',
    
    # Configuration
    'TradingConfig',
    
    # Utility Functions
    'create_price_data', 'create_ohlc_data', 'create_trade_execution', 
    'create_api_response', 'create_market_depth'
]