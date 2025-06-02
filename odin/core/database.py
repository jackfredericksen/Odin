"""
Odin Core Database - SQLAlchemy Models and Database Operations

Comprehensive database layer for the Odin trading system providing
models, operations, and connection management with SQLAlchemy.

File: odin/core/database.py
Author: Odin Development Team
License: MIT
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional, Dict, Any, AsyncGenerator
from uuid import UUID, uuid4

import asyncpg
from sqlalchemy import (
    Column, String, Float, Integer, DateTime, Boolean, Text, JSON,
    ForeignKey, Index, UniqueConstraint, CheckConstraint, Numeric,
    create_engine, event
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.pool import QueuePool
from sqlalchemy.sql import func

from .exceptions import DatabaseException, DatabaseConnectionException, DatabaseOperationException
from .models import OrderType, OrderSide, OrderStatus, PositionType, PriceData, SignalType, StrategyStatus, TradeExecution

logger = logging.getLogger(__name__)

# SQLAlchemy base
Base = declarative_base()


# Database Models
class BitcoinPrice(Base):
    """Bitcoin price data storage."""
    __tablename__ = "bitcoin_prices"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(20), nullable=False, default="BTC-USD")
    price = Column(Numeric(precision=15, scale=8), nullable=False)
    volume = Column(Numeric(precision=20, scale=8), nullable=False, default=0)
    timestamp = Column(DateTime(timezone=True), nullable=False, default=func.now())
    source = Column(String(50), nullable=False)
    
    # Additional market data
    bid = Column(Numeric(precision=15, scale=8), nullable=True)
    ask = Column(Numeric(precision=15, scale=8), nullable=True)
    spread = Column(Numeric(precision=15, scale=8), nullable=True)
    
    # Technical indicators (computed and stored for performance)
    sma_5 = Column(Numeric(precision=15, scale=8), nullable=True)
    sma_20 = Column(Numeric(precision=15, scale=8), nullable=True)
    ema_12 = Column(Numeric(precision=15, scale=8), nullable=True)
    ema_26 = Column(Numeric(precision=15, scale=8), nullable=True)
    rsi = Column(Numeric(precision=5, scale=2), nullable=True)
    macd = Column(Numeric(precision=15, scale=8), nullable=True)
    macd_signal = Column(Numeric(precision=15, scale=8), nullable=True)
    bb_upper = Column(Numeric(precision=15, scale=8), nullable=True)
    bb_lower = Column(Numeric(precision=15, scale=8), nullable=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_bitcoin_prices_timestamp', 'timestamp'),
        Index('idx_bitcoin_prices_symbol_timestamp', 'symbol', 'timestamp'),
        Index('idx_bitcoin_prices_source', 'source'),
        UniqueConstraint('symbol', 'timestamp', 'source', name='uq_price_record'),
    )
    
    def __repr__(self):
        return f"<BitcoinPrice(symbol={self.symbol}, price={self.price}, timestamp={self.timestamp})>"


class Trade(Base):
    """Trade execution records."""
    __tablename__ = "trades"
    
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    order_id = Column(PG_UUID(as_uuid=True), nullable=True)  # Reference to order
    strategy_name = Column(String(100), nullable=False)
    symbol = Column(String(20), nullable=False, default="BTC-USD")
    
    # Trade details
    side = Column(String(10), nullable=False)  # BUY/SELL
    quantity = Column(Numeric(precision=20, scale=8), nullable=False)
    price = Column(Numeric(precision=15, scale=8), nullable=False)
    
    # Costs and fees
    fee = Column(Numeric(precision=15, scale=8), nullable=False, default=0)
    fee_currency = Column(String(10), nullable=False, default="USD")
    total_cost = Column(Numeric(precision=15, scale=8), nullable=True)
    
    # Performance tracking
    slippage = Column(Numeric(precision=10, scale=6), nullable=True)
    market_impact = Column(Numeric(precision=10, scale=6), nullable=True)
    
    # External references
    trade_id = Column(String(100), nullable=True)  # Exchange trade ID
    exchange = Column(String(50), nullable=True)
    
    # Timestamps
    timestamp = Column(DateTime(timezone=True), nullable=False, default=func.now())
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    
    # Relationships
    position_trades = relationship("PositionTrade", back_populates="trade")
    
    # Constraints
    __table_args__ = (
        Index('idx_trades_strategy', 'strategy_name'),
        Index('idx_trades_timestamp', 'timestamp'),
        Index('idx_trades_symbol', 'symbol'),
        CheckConstraint('side IN (\'BUY\', \'SELL\')', name='check_trade_side'),
        CheckConstraint('quantity > 0', name='check_trade_quantity'),
        CheckConstraint('price > 0', name='check_trade_price'),
    )
    
    def __repr__(self):
        return f"<Trade(id={self.id}, strategy={self.strategy_name}, side={self.side}, quantity={self.quantity})>"


class Position(Base):
    """Trading positions."""
    __tablename__ = "positions"
    
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    symbol = Column(String(20), nullable=False, default="BTC-USD")
    strategy_name = Column(String(100), nullable=False)
    
    # Position details
    type = Column(String(10), nullable=False)  # LONG/SHORT
    quantity = Column(Numeric(precision=20, scale=8), nullable=False)
    entry_price = Column(Numeric(precision=15, scale=8), nullable=False)
    current_price = Column(Numeric(precision=15, scale=8), nullable=False)
    
    # P&L calculations
    unrealized_pnl = Column(Numeric(precision=15, scale=8), nullable=True)
    realized_pnl = Column(Numeric(precision=15, scale=8), nullable=False, default=0)
    total_fees = Column(Numeric(precision=15, scale=8), nullable=False, default=0)
    
    # Risk management
    stop_loss = Column(Numeric(precision=15, scale=8), nullable=True)
    take_profit = Column(Numeric(precision=15, scale=8), nullable=True)
    
    # Status
    is_open = Column(Boolean, nullable=False, default=True)
    
    # Timestamps
    opened_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    closed_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=func.now(), onupdate=func.now())
    
    # Relationships
    position_trades = relationship("PositionTrade", back_populates="position")
    
    # Constraints
    __table_args__ = (
        Index('idx_positions_strategy', 'strategy_name'),
        Index('idx_positions_symbol', 'symbol'),
        Index('idx_positions_status', 'is_open'),
        CheckConstraint('type IN (\'LONG\', \'SHORT\')', name='check_position_type'),
        CheckConstraint('entry_price > 0', name='check_entry_price'),
        CheckConstraint('current_price > 0', name='check_current_price'),
    )
    
    def __repr__(self):
        return f"<Position(id={self.id}, strategy={self.strategy_name}, type={self.type}, quantity={self.quantity})>"


class PositionTrade(Base):
    """Many-to-many relationship between positions and trades."""
    __tablename__ = "position_trades"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    position_id = Column(PG_UUID(as_uuid=True), ForeignKey('positions.id'), nullable=False)
    trade_id = Column(PG_UUID(as_uuid=True), ForeignKey('trades.id'), nullable=False)
    
    # Relationship metadata
    trade_type = Column(String(20), nullable=False)  # ENTRY, EXIT, PARTIAL_EXIT
    quantity_impact = Column(Numeric(precision=20, scale=8), nullable=False)
    
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    
    # Relationships
    position = relationship("Position", back_populates="position_trades")
    trade = relationship("Trade", back_populates="position_trades")
    
    __table_args__ = (
        UniqueConstraint('position_id', 'trade_id', name='uq_position_trade'),
        Index('idx_position_trades_position', 'position_id'),
        Index('idx_position_trades_trade', 'trade_id'),
    )


class TradeOrder(Base):
    """Trade orders."""
    __tablename__ = "trade_orders"
    
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    strategy_name = Column(String(100), nullable=False)
    symbol = Column(String(20), nullable=False, default="BTC-USD")
    
    # Order details
    order_type = Column(String(20), nullable=False)
    side = Column(String(10), nullable=False)
    quantity = Column(Numeric(precision=20, scale=8), nullable=False)
    
    # Price specifications
    price = Column(Numeric(precision=15, scale=8), nullable=True)
    stop_price = Column(Numeric(precision=15, scale=8), nullable=True)
    
    # Risk management
    stop_loss = Column(Numeric(precision=15, scale=8), nullable=True)
    take_profit = Column(Numeric(precision=15, scale=8), nullable=True)
    
    # Execution parameters
    time_in_force = Column(String(10), nullable=False, default="GTC")
    reduce_only = Column(Boolean, nullable=False, default=False)
    
    # Status tracking
    status = Column(String(20), nullable=False, default="PENDING")
    filled_quantity = Column(Numeric(precision=20, scale=8), nullable=False, default=0)
    remaining_quantity = Column(Numeric(precision=20, scale=8), nullable=True)
    
    # External references
    exchange_order_id = Column(String(100), nullable=True)
    client_order_id = Column(String(100), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, default=func.now(), onupdate=func.now())
    
    __table_args__ = (
        Index('idx_orders_strategy', 'strategy_name'),
        Index('idx_orders_status', 'status'),
        Index('idx_orders_symbol', 'symbol'),
        CheckConstraint('side IN (\'BUY\', \'SELL\')', name='check_order_side'),
        CheckConstraint('quantity > 0', name='check_order_quantity'),
        CheckConstraint('filled_quantity >= 0', name='check_filled_quantity'),
        CheckConstraint('filled_quantity <= quantity', name='check_filled_vs_quantity'),
    )


class StrategyPerformance(Base):
    """Strategy performance tracking."""
    __tablename__ = "strategy_performance"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    strategy_name = Column(String(100), nullable=False)
    date = Column(DateTime(timezone=True), nullable=False)
    
    # Performance metrics
    daily_return = Column(Numeric(precision=10, scale=6), nullable=False, default=0)
    cumulative_return = Column(Numeric(precision=10, scale=6), nullable=False, default=0)
    sharpe_ratio = Column(Numeric(precision=8, scale=4), nullable=True)
    max_drawdown = Column(Numeric(precision=10, scale=6), nullable=True)
    
    # Trading statistics
    trades_count = Column(Integer, nullable=False, default=0)
    win_rate = Column(Numeric(precision=5, scale=4), nullable=True)
    profit_factor = Column(Numeric(precision=8, scale=4), nullable=True)
    
    # Portfolio allocation
    portfolio_value = Column(Numeric(precision=15, scale=2), nullable=False, default=0)
    strategy_allocation = Column(Numeric(precision=5, scale=4), nullable=False, default=0)
    
    # Status
    status = Column(String(20), nullable=False, default="ACTIVE")
    
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    
    __table_args__ = (
        Index('idx_strategy_performance_name_date', 'strategy_name', 'date'),
        Index('idx_strategy_performance_date', 'date'),
        UniqueConstraint('strategy_name', 'date', name='uq_strategy_daily_performance'),
    )


class TradingSignal(Base):
    """Trading signals from strategies."""
    __tablename__ = "trading_signals"
    
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    strategy_name = Column(String(100), nullable=False)
    symbol = Column(String(20), nullable=False, default="BTC-USD")
    
    # Signal details
    signal_type = Column(String(10), nullable=False)  # BUY/SELL/HOLD
    confidence = Column(Numeric(precision=3, scale=2), nullable=False)
    price = Column(Numeric(precision=15, scale=8), nullable=False)
    
    # Strategy-specific data
    indicators = Column(JSON, nullable=True)
    metadata = Column(JSON, nullable=True)
    
    # Execution tracking
    executed = Column(Boolean, nullable=False, default=False)
    execution_price = Column(Numeric(precision=15, scale=8), nullable=True)
    execution_time = Column(DateTime(timezone=True), nullable=True)
    
    timestamp = Column(DateTime(timezone=True), nullable=False, default=func.now())
    
    __table_args__ = (
        Index('idx_signals_strategy_timestamp', 'strategy_name', 'timestamp'),
        Index('idx_signals_executed', 'executed'),
        CheckConstraint('signal_type IN (\'BUY\', \'SELL\', \'HOLD\')', name='check_signal_type'),
        CheckConstraint('confidence >= 0 AND confidence <= 1', name='check_confidence_range'),
    )


class Portfolio(Base):
    """Portfolio snapshots."""
    __tablename__ = "portfolios"
    
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(100), nullable=False)
    
    # Portfolio values
    total_value = Column(Numeric(precision=15, scale=2), nullable=False)
    cash_balance = Column(Numeric(precision=15, scale=2), nullable=False)
    btc_balance = Column(Numeric(precision=20, scale=8), nullable=False)
    
    # Performance
    daily_pnl = Column(Numeric(precision=15, scale=2), nullable=False, default=0)
    total_pnl = Column(Numeric(precision=15, scale=2), nullable=False, default=0)
    max_drawdown = Column(Numeric(precision=10, scale=6), nullable=True)
    
    # Risk metrics
    current_exposure = Column(Numeric(precision=5, scale=4), nullable=False, default=0)
    var_95 = Column(Numeric(precision=15, scale=2), nullable=True)
    
    # Metadata
    active_strategies = Column(JSON, nullable=True)
    
    timestamp = Column(DateTime(timezone=True), nullable=False, default=func.now())
    
    __table_args__ = (
        Index('idx_portfolios_timestamp', 'timestamp'),
        Index('idx_portfolios_name', 'name'),
    )


# Database Operations Class
class Database:
    """Database operations manager."""
    
    def __init__(self, connection_string: str, echo: bool = False):
        """
        Initialize database manager.
        
        Args:
            connection_string: Database connection string
            echo: Whether to echo SQL statements
        """
        self.connection_string = connection_string
        self.echo = echo
        
        # Sync engine for migrations and simple operations
        self.sync_engine = create_engine(
            connection_string.replace('postgresql+asyncpg://', 'postgresql://'),
            echo=echo,
            poolclass=QueuePool,
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True,
            pool_recycle=3600,
        )
        
        # Async engine for main operations
        self.async_engine = create_async_engine(
            connection_string,
            echo=echo,
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True,
            pool_recycle=3600,
        )
        
        # Session makers
        self.sync_session = sessionmaker(bind=self.sync_engine)
        self.async_session = async_sessionmaker(
            bind=self.async_engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
        
        logger.info("Database manager initialized")
    
    def create_tables(self):
        """Create all database tables."""
        try:
            Base.metadata.create_all(self.sync_engine)
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Failed to create database tables: {e}")
            raise DatabaseException(
                message="Failed to create database tables",
                error_code="TABLE_CREATION_FAILED",
                context={"error": str(e)},
                original_exception=e
            )
    
    def drop_tables(self):
        """Drop all database tables."""
        try:
            Base.metadata.drop_all(self.sync_engine)
            logger.info("Database tables dropped successfully")
        except Exception as e:
            logger.error(f"Failed to drop database tables: {e}")
            raise DatabaseException(
                message="Failed to drop database tables",
                error_code="TABLE_DROP_FAILED",
                context={"error": str(e)},
                original_exception=e
            )
    
    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get async database session with automatic cleanup."""
        async with self.async_session() as session:
            try:
                yield session
                await session.commit()
            except Exception as e:
                await session.rollback()
                logger.error(f"Database session error: {e}")
                raise DatabaseOperationException(
                    operation="session_management",
                    error_details=str(e),
                    original_exception=e
                )
            finally:
                await session.close()
    
    async def health_check(self) -> bool:
        """Check database connectivity."""
        try:
            async with self.get_session() as session:
                await session.execute("SELECT 1")
                return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False
    
    # Price data operations
    async def save_price_data(self, price_data: 'PriceData') -> BitcoinPrice:
        """Save price data to database."""
        try:
            async with self.get_session() as session:
                db_price = BitcoinPrice(
                    symbol=price_data.symbol,
                    price=price_data.price,
                    volume=price_data.volume,
                    timestamp=price_data.timestamp,
                    source=price_data.source,
                    bid=price_data.bid,
                    ask=price_data.ask,
                    spread=price_data.spread,
                )
                
                session.add(db_price)
                await session.flush()
                await session.refresh(db_price)
                
                logger.debug(f"Saved price data: {db_price}")
                return db_price
                
        except Exception as e:
            logger.error(f"Failed to save price data: {e}")
            raise DatabaseOperationException(
                operation="save_price_data",
                table="bitcoin_prices",
                error_details=str(e),
                original_exception=e
            )
    
    async def get_latest_price(self, symbol: str = "BTC-USD") -> Optional[BitcoinPrice]:
        """Get latest price for symbol."""
        try:
            async with self.get_session() as session:
                result = await session.execute(
                    """
                    SELECT * FROM bitcoin_prices 
                    WHERE symbol = :symbol 
                    ORDER BY timestamp DESC 
                    LIMIT 1
                    """,
                    {"symbol": symbol}
                )
                row = result.fetchone()
                
                if row:
                    return BitcoinPrice(**dict(row))
                return None
                
        except Exception as e:
            logger.error(f"Failed to get latest price: {e}")
            raise DatabaseOperationException(
                operation="get_latest_price",
                table="bitcoin_prices",
                error_details=str(e),
                original_exception=e
            )
    
    async def get_price_history(
        self, 
        symbol: str = "BTC-USD",
        hours: int = 24,
        limit: Optional[int] = None
    ) -> List[BitcoinPrice]:
        """Get price history."""
        try:
            async with self.get_session() as session:
                query = """
                    SELECT * FROM bitcoin_prices 
                    WHERE symbol = :symbol 
                    AND timestamp >= NOW() - INTERVAL ':hours hours'
                    ORDER BY timestamp DESC
                """
                
                if limit:
                    query += f" LIMIT {limit}"
                
                result = await session.execute(
                    query,
                    {"symbol": symbol, "hours": hours}
                )
                
                return [BitcoinPrice(**dict(row)) for row in result.fetchall()]
                
        except Exception as e:
            logger.error(f"Failed to get price history: {e}")
            raise DatabaseOperationException(
                operation="get_price_history",
                table="bitcoin_prices",
                error_details=str(e),
                original_exception=e
            )
    
    # Trade operations
    async def save_trade(self, trade_data: 'TradeExecution') -> Trade:
        """Save trade execution to database."""
        try:
            async with self.get_session() as session:
                db_trade = Trade(
                    id=trade_data.id,
                    order_id=trade_data.order_id,
                    strategy_name=trade_data.strategy_name,
                    symbol=trade_data.symbol,
                    side=trade_data.side.value,
                    quantity=trade_data.quantity,
                    price=trade_data.price,
                    fee=trade_data.fee,
                    fee_currency=trade_data.fee_currency,
                    total_cost=trade_data.total_cost,
                    slippage=trade_data.slippage,
                    market_impact=trade_data.market_impact,
                    trade_id=trade_data.trade_id,
                    timestamp=trade_data.created_at,
                )
                
                session.add(db_trade)
                await session.flush()
                await session.refresh(db_trade)
                
                logger.info(f"Saved trade: {db_trade}")
                return db_trade
                
        except Exception as e:
            logger.error(f"Failed to save trade: {e}")
            raise DatabaseOperationException(
                operation="save_trade",
                table="trades",
                error_details=str(e),
                original_exception=e
            )
    
    async def get_strategy_trades(
        self, 
        strategy_name: str,
        hours: Optional[int] = None
    ) -> List[Trade]:
        """Get trades for a strategy."""
        try:
            async with self.get_session() as session:
                query = "SELECT * FROM trades WHERE strategy_name = :strategy_name"
                params = {"strategy_name": strategy_name}
                
                if hours:
                    query += " AND timestamp >= NOW() - INTERVAL ':hours hours'"
                    params["hours"] = hours
                
                query += " ORDER BY timestamp DESC"
                
                result = await session.execute(query, params)
                return [Trade(**dict(row)) for row in result.fetchall()]
                
        except Exception as e:
            logger.error(f"Failed to get strategy trades: {e}")
            raise DatabaseOperationException(
                operation="get_strategy_trades",
                table="trades",
                error_details=str(e),
                original_exception=e
            )
    
    async def close(self):
        """Close database connections."""
        try:
            await self.async_engine.dispose()
            self.sync_engine.dispose()
            logger.info("Database connections closed")
        except Exception as e:
            logger.error(f"Error closing database connections: {e}")


# Database event listeners for automatic calculations
@event.listens_for(BitcoinPrice, 'before_insert')
def calculate_spread(mapper, connection, target):
    """Calculate spread if bid/ask are available."""
    if target.bid and target.ask and not target.spread:
        target.spread = target.ask - target.bid


@event.listens_for(Trade, 'before_insert')
def calculate_total_cost(mapper, connection, target):
    """Calculate total cost including fees."""
    if target.total_cost is None:
        base_cost = target.quantity * target.price
        if target.side == 'BUY':
            target.total_cost = base_cost + target.fee
        else:
            target.total_cost = base_cost - target.fee


@event.listens_for(Position, 'before_update')
def calculate_unrealized_pnl(mapper, connection, target):
    """Calculate unrealized P&L on position updates."""
    if target.quantity and target.entry_price and target.current_price:
        target.unrealized_pnl = target.quantity * (target.current_price - target.entry_price)