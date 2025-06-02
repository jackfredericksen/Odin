"""
Odin Core Package - Professional Bitcoin Trading Bot Core Business Logic

This package contains the core business logic for the Odin trading system:
- Trading Engine: Live trade execution and order management
- Portfolio Manager: Portfolio tracking, P&L calculation, and allocation
- Risk Manager: Risk controls, position sizing, and drawdown protection
- Data Collector: Real-time Bitcoin data collection and processing
- Database: SQLAlchemy models and database operations
- Models: Pydantic data models for validation and serialization
- Exceptions: Custom exception classes for error handling

Author: Odin Development Team
License: MIT
"""

from .trading_engine import TradingEngine
from .portfolio_manager import PortfolioManager
from .risk_manager import RiskManager
from .data_collector import DataCollector
from .database import Database, BitcoinPrice, Trade, Position, StrategyPerformance
from .models import (
    # Market Data Models
    PriceData,
    OHLCData,
    MarketDepth,
    
    # Trading Models
    TradeSignal,
    TradeOrder,
    TradeExecution,
    Position as PositionModel,
    
    # Portfolio Models
    Portfolio,
    PortfolioSummary,
    PerformanceMetrics,
    Allocation,
    
    # Risk Models
    RiskMetrics,
    RiskLimits,
    DrawdownAlert,
    
    # Strategy Models
    StrategyConfig,
    StrategyResult,
    BacktestResult,
    OptimizationResult,
)
from .exceptions import (
    OdinCoreException,
    TradingEngineException,
    PortfolioManagerException,
    RiskManagerException,
    DataCollectorException,
    DatabaseException,
    InsufficientFundsException,
    RiskLimitExceededException,
    InvalidOrderException,
    MarketDataException,
)

__version__ = "1.0.0"
__author__ = "Odin Development Team"

# Core component initialization order for dependency injection
CORE_COMPONENTS = [
    "Database",
    "DataCollector", 
    "RiskManager",
    "PortfolioManager",
    "TradingEngine",
]

__all__ = [
    # Core Components
    "TradingEngine",
    "PortfolioManager", 
    "RiskManager",
    "DataCollector",
    "Database",
    
    # Database Models
    "BitcoinPrice",
    "Trade", 
    "Position",
    "StrategyPerformance",
    
    # Pydantic Models
    "PriceData",
    "OHLCData", 
    "MarketDepth",
    "TradeSignal",
    "TradeOrder",
    "TradeExecution",
    "PositionModel",
    "Portfolio",
    "PortfolioSummary",
    "PerformanceMetrics",
    "Allocation",
    "RiskMetrics",
    "RiskLimits", 
    "DrawdownAlert",
    "StrategyConfig",
    "StrategyResult",
    "BacktestResult",
    "OptimizationResult",
    
    # Exceptions
    "OdinCoreException",
    "TradingEngineException",
    "PortfolioManagerException", 
    "RiskManagerException",
    "DataCollectorException",
    "DatabaseException",
    "InsufficientFundsException",
    "RiskLimitExceededException",
    "InvalidOrderException", 
    "MarketDataException",
    
    # Metadata
    "__version__",
    "__author__",
    "CORE_COMPONENTS",
]