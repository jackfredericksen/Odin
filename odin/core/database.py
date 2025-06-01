"""Database operations for Odin trading bot."""

import asyncio
import sqlite3
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from pathlib import Path
from typing import AsyncGenerator, List, Optional, Tuple

import pandas as pd
import structlog
from sqlalchemy import (
    Column, DateTime, Float, Integer, String, Text, create_engine, MetaData
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from odin.config import get_settings
from odin.core.exceptions import DatabaseError
from odin.core.models import PriceData

logger = structlog.get_logger(__name__)

Base = declarative_base()
metadata = MetaData()


class BitcoinPrice(Base):
    """Bitcoin price data table."""
    
    __tablename__ = "btc_prices"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    price = Column(Float, nullable=False)
    volume = Column(Float)
    high = Column(Float)
    low = Column(Float)
    change_24h = Column(Float)
    source = Column(String(50), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def to_price_data(self) -> PriceData:
        """Convert to PriceData model."""
        return PriceData(
            timestamp=self.timestamp,
            price=self.price,
            volume=self.volume,
            high=self.high,
            low=self.low,
            change_24h=self.change_24h,
            source=self.source,
        )


class Database:
    """Database manager for Odin trading bot."""
    
    def __init__(self) -> None:
        """Initialize database."""
        self.settings = get_settings()
        self.engine = None
        self.SessionLocal = None
        
    async def init(self) -> None:
        """Initialize database connection and tables."""
        try:
            # Create database directory if needed
            if self.settings.database_url.startswith('sqlite:///'):
                db_path = Path(self.settings.database_url.replace('sqlite:///', ''))
                db_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Create engine with appropriate settings
            if self.settings.database_url.startswith('sqlite'):
                self.engine = create_engine(
                    self.settings.database_url,
                    poolclass=StaticPool,
                    connect_args={
                        "check_same_thread": False,
                        "timeout": 30,
                    },
                    echo=False,
                )
            else:
                self.engine = create_engine(
                    self.settings.database_url,
                    pool_pre_ping=True,
                    pool_recycle=300,
                    echo=False,
                )
            
            # Create session factory
            self.SessionLocal = sessionmaker(
                autocommit=False, autoflush=False, bind=self.engine
            )
            
            # Create tables
            Base.metadata.create_all(bind=self.engine)
            
            logger.info("Database initialized", url=self.settings.database_url)
            
        except Exception as e:
            logger.error("Failed to initialize database", error=str(e))
            raise DatabaseError(f"Database initialization failed: {e}")
    
    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator:
        """Get database session with automatic cleanup."""
        if not self.SessionLocal:
            raise DatabaseError("Database not initialized")
        
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error("Database session error", error=str(e))
            raise DatabaseError(f"Database operation failed: {e}")
        finally:
            session.close()
    
    async def save_price_data(self, price_data: PriceData) -> bool:
        """Save price data to database."""
        try:
            async with self.get_session() as session:
                price_record = BitcoinPrice(
                    timestamp=price_data.timestamp,
                    price=price_data.price,
                    volume=price_data.volume,
                    high=price_data.high,
                    low=price_data.low,
                    change_24h=price_data.change_24h,
                    source=price_data.source,
                )
                session.add(price_record)
                
            logger.debug("Price data saved", price=price_data.price, source=price_data.source)
            return True
            
        except Exception as e:
            logger.error("Failed to save price data", error=str(e))
            return False
    
    async def get_recent_prices(self, limit: int = 100) -> List[PriceData]:
        """Get recent price data."""
        try:
            async with self.get_session() as session:
                records = (
                    session.query(BitcoinPrice)
                    .order_by(BitcoinPrice.timestamp.desc())
                    .limit(limit)
                    .all()
                )
                
                return [record.to_price_data() for record in records]
                
        except Exception as e:
            logger.error("Failed to get recent prices", error=str(e))
            raise DatabaseError(f"Failed to retrieve recent prices: {e}")
    
    async def get_price_history(
        self, 
        hours: int = 24,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> pd.DataFrame:
        """Get price history as DataFrame."""
        try:
            async with self.get_session() as session:
                query = session.query(BitcoinPrice)
                
                if start_time and end_time:
                    query = query.filter(
                        BitcoinPrice.timestamp >= start_time,
                        BitcoinPrice.timestamp <= end_time
                    )
                elif hours:
                    cutoff_time = datetime.utcnow() - timedelta(hours=hours)
                    query = query.filter(BitcoinPrice.timestamp >= cutoff_time)
                
                records = query.order_by(BitcoinPrice.timestamp.asc()).all()
                
                if not records:
                    return pd.DataFrame()
                
                # Convert to DataFrame
                data = {
                    'timestamp': [r.timestamp for r in records],
                    'price': [r.price for r in records],
                    'volume': [r.volume for r in records],
                    'high': [r.high for r in records],
                    'low': [r.low for r in records],
                    'change_24h': [r.change_24h for r in records],
                    'source': [r.source for r in records],
                }
                
                df = pd.DataFrame(data)
                df.set_index('timestamp', inplace=True)
                
                return df
                
        except Exception as e:
            logger.error("Failed to get price history", error=str(e))
            raise DatabaseError(f"Failed to retrieve price history: {e}")
    
    async def get_data_stats(self) -> dict:
        """Get database statistics."""
        try:
            async with self.get_session() as session:
                total_records = session.query(BitcoinPrice).count()
                
                if total_records == 0:
                    return {
                        'total_records': 0,
                        'oldest_record': None,
                        'newest_record': None,
                        'sources': [],
                    }
                
                oldest = (
                    session.query(BitcoinPrice.timestamp)
                    .order_by(BitcoinPrice.timestamp.asc())
                    .first()[0]
                )
                
                newest = (
                    session.query(BitcoinPrice.timestamp)
                    .order_by(BitcoinPrice.timestamp.desc())
                    .first()[0]
                )
                
                sources = (
                    session.query(BitcoinPrice.source)
                    .distinct()
                    .all()
                )
                
                return {
                    'total_records': total_records,
                    'oldest_record': oldest.isoformat() if oldest else None,
                    'newest_record': newest.isoformat() if newest else None,
                    'sources': [s[0] for s in sources],
                }
                
        except Exception as e:
            logger.error("Failed to get data stats", error=str(e))
            raise DatabaseError(f"Failed to retrieve data stats: {e}")
    
    async def cleanup_old_data(self, days_to_keep: int = 30) -> int:
        """Clean up old data beyond retention period."""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
            
            async with self.get_session() as session:
                deleted_count = (
                    session.query(BitcoinPrice)
                    .filter(BitcoinPrice.timestamp < cutoff_date)
                    .delete()
                )
                
            logger.info("Cleaned up old data", 
                       deleted_count=deleted_count, 
                       cutoff_date=cutoff_date)
            
            return deleted_count
            
        except Exception as e:
            logger.error("Failed to cleanup old data", error=str(e))
            raise DatabaseError(f"Failed to cleanup old data: {e}")


# Global database instance
_db: Optional[Database] = None


async def get_database() -> Database:
    """Get database instance."""
    global _db
    if _db is None:
        _db = Database()
        await _db.init()
    return _db


async def init_database() -> Database:
    """Initialize database."""
    return await get_database()