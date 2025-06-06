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
    'TradeExecution',
    
    # Strategy Models
    'StrategySignal',
    
    # Portfolio Models
    'PortfolioSnapshot',
    
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