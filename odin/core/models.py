"""
Odin Bitcoin Trading Bot - Data Models (SAFE Pydantic v2 with Dashboard Compatibility)
Ensures proper serialization for both API responses and dashboard integration
"""

from datetime import datetime
from typing import Optional, Dict, Any, List, Union
from enum import Enum

# Use Pydantic v2 but with compatibility layer for dashboard
try:
    from pydantic import BaseModel, Field, field_validator, ConfigDict
    from pydantic_settings import BaseSettings
    PYDANTIC_V2 = True
except ImportError:
    # Fallback for environments that might have v1
    from pydantic import BaseModel, Field, validator
    try:
        from pydantic_settings import BaseSettings
    except ImportError:
        from pydantic import BaseSettings
    PYDANTIC_V2 = False

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
    """Unified signal type enum - single source of truth"""
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"

class StrategyStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    PAUSED = "paused"
    ERROR = "error"

# Base Model Class with Dashboard Compatibility
class OdinBaseModel(BaseModel):
    """Base model for all Odin data structures with dashboard compatibility."""
    
    if PYDANTIC_V2:
        model_config = ConfigDict(
            arbitrary_types_allowed=True,
            str_strip_whitespace=True,
            validate_assignment=True,
            use_enum_values=True,
            # IMPORTANT: This ensures proper JSON serialization for dashboard
            json_encoders={
                datetime: lambda v: v.isoformat() if v else None,
            }
        )
    else:
        class Config:
            arbitrary_types_allowed = True
            str_strip_whitespace = True
            validate_assignment = True
            use_enum_values = True
            json_encoders = {
                datetime: lambda v: v.isoformat() if v else None,
            }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary with proper serialization for dashboard."""
        if PYDANTIC_V2:
            return self.model_dump(mode='json')
        else:
            return self.dict()
    
    def to_json(self) -> str:
        """Convert to JSON string for dashboard compatibility."""
        if PYDANTIC_V2:
            return self.model_dump_json()
        else:
            return self.json()

# Price Data Models
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
    
    if PYDANTIC_V2:
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

# Trading Models
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

# Strategy Models
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

# Portfolio Models
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

# API Response Models with Dashboard Compatibility
class APIResponse(OdinBaseModel):
    """Standard API response format optimized for dashboard consumption."""
    success: bool = Field(..., description="Whether the request was successful")
    message: Optional[str] = Field(None, description="Response message")
    data: Optional[Any] = Field(None, description="Response data")
    timestamp: datetime = Field(default_factory=datetime.now, description="Response timestamp")
    
    def to_dashboard_json(self) -> str:
        """Convert to JSON optimized for dashboard consumption."""
        if PYDANTIC_V2:
            return self.model_dump_json(exclude_none=False)
        else:
            return self.json(exclude_none=False)
    
class ErrorResponse(APIResponse):
    """Error response format."""
    success: bool = Field(default=False)
    error_code: Optional[str] = Field(None, description="Error code")
    error_details: Optional[Dict[str, Any]] = Field(None, description="Detailed error information")

# Data Collection Models
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

# Configuration Models
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
    
    if PYDANTIC_V2:
        model_config = ConfigDict(
            env_prefix="ODIN_",
            case_sensitive=False,
            env_file=".env",
        )
    else:
        class Config:
            env_prefix = "ODIN_"
            case_sensitive = False
            env_file = ".env"

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

def create_api_response(success: bool, data: Any = None, message: str = None) -> APIResponse:
    """Create an APIResponse instance optimized for dashboard."""
    return APIResponse(success=success, data=data, message=message)

def serialize_for_dashboard(obj: Any) -> Dict[str, Any]:
    """Serialize any object for dashboard consumption."""
    if isinstance(obj, OdinBaseModel):
        return obj.to_dict()
    elif isinstance(obj, list):
        return [serialize_for_dashboard(item) for item in obj]
    elif isinstance(obj, dict):
        return {k: serialize_for_dashboard(v) for k, v in obj.items()}
    elif isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, Enum):
        return obj.value
    else:
        return obj

# Export all models
__all__ = [
    # Enums
    'OrderType', 'OrderSide', 'OrderStatus', 'PositionType', 'SignalType', 'StrategyStatus',
    
    # Base
    'OdinBaseModel',
    
    # Price Models
    'PriceData', 'HistoricalData', 'OHLCData', 'MarketDepth', 'DataStats',
    
    # Trading Models
    'TradeExecution', 'TradeOrder', 'TradeSignal',
    
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
    'create_price_data', 'create_api_response', 'serialize_for_dashboard'
]