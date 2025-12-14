"""
Odin Database Repository - Clean and Complete Implementation
Focused, working repository system without bloat.
"""

import sqlite3
import asyncio
import json
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
from pathlib import Path
from contextlib import asynccontextmanager
from dataclasses import dataclass

from ..utils.logging import get_logger
from .exceptions import OdinException, ErrorCode, ErrorSeverity

logger = get_logger(__name__)


@dataclass
class QueryResult:
    """Simple query result wrapper."""
    success: bool
    data: Any = None
    error: Optional[str] = None
    rows_affected: int = 0


class DatabaseManager:
    """Simple database connection manager."""
    
    def __init__(self, database_path: str = "data/odin.db"):
        self.database_path = database_path
        self.connection_pool = asyncio.Queue(maxsize=5)
        self._initialized = False
    
    async def initialize(self):
        """Initialize database and connection pool."""
        if self._initialized:
            return
        
        Path(self.database_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Create connection pool
        for _ in range(3):
            conn = sqlite3.connect(self.database_path, check_same_thread=False)
            conn.row_factory = sqlite3.Row
            await self.connection_pool.put(conn)
        
        # Create tables
        await self._create_tables()
        self._initialized = True
        logger.info("Database initialized")
    
    @asynccontextmanager
    async def get_connection(self):
        """Get database connection."""
        if not self._initialized:
            await self.initialize()
        
        try:
            conn = await asyncio.wait_for(self.connection_pool.get(), timeout=5.0)
            yield conn
        finally:
            try:
                self.connection_pool.put_nowait(conn)
            except asyncio.QueueFull:
                conn.close()
    
    async def execute_query(self, query: str, params: Tuple = None, fetch_one: bool = False) -> QueryResult:
        """Execute database query."""
        try:
            async with self.get_connection() as conn:
                cursor = conn.cursor()
                
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                
                if query.strip().upper().startswith('SELECT'):
                    if fetch_one:
                        data = cursor.fetchone()
                        data = dict(data) if data else None
                    else:
                        rows = cursor.fetchall()
                        data = [dict(row) for row in rows]
                    rows_affected = 0
                else:
                    data = None
                    rows_affected = cursor.rowcount
                    conn.commit()
                
                return QueryResult(success=True, data=data, rows_affected=rows_affected)
                
        except Exception as e:
            logger.error(f"Query failed: {e}")
            return QueryResult(success=False, error=str(e))
    
    async def _create_tables(self):
        """Create database tables."""
        tables = [
            """CREATE TABLE IF NOT EXISTS bitcoin_prices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL UNIQUE,
                price REAL NOT NULL,
                volume REAL,
                source TEXT DEFAULT 'unknown',
                rsi REAL,
                macd REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""",
            
            """CREATE TABLE IF NOT EXISTS trades (
                id TEXT PRIMARY KEY,
                timestamp TEXT NOT NULL,
                strategy_id TEXT NOT NULL,
                symbol TEXT NOT NULL DEFAULT 'BTC-USD',
                side TEXT NOT NULL,
                amount REAL NOT NULL,
                price REAL NOT NULL,
                status TEXT NOT NULL DEFAULT 'completed',
                fees REAL DEFAULT 0,
                pnl REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""",
            
            """CREATE TABLE IF NOT EXISTS strategy_signals (
                id TEXT PRIMARY KEY,
                strategy_id TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                signal_type TEXT NOT NULL,
                confidence REAL NOT NULL,
                price REAL NOT NULL,
                executed INTEGER DEFAULT 0,
                execution_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""",
            
            """CREATE TABLE IF NOT EXISTS portfolio_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                total_value REAL NOT NULL,
                cash_balance REAL NOT NULL,
                btc_balance REAL NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""",
            
            # Indexes
            "CREATE INDEX IF NOT EXISTS idx_prices_timestamp ON bitcoin_prices(timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_trades_strategy ON trades(strategy_id, timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_signals_strategy ON strategy_signals(strategy_id, timestamp)"
        ]
        
        for table_sql in tables:
            result = await self.execute_query(table_sql)
            if not result.success:
                raise OdinException(f"Table creation failed: {result.error}", ErrorCode.DATABASE_MIGRATION_FAILED)


class PriceRepository:
    """Price data repository."""
    
    def __init__(self, db: DatabaseManager):
        self.db = db
    
    async def save_price(self, price_data: Dict[str, Any]) -> bool:
        """Save price data."""
        query = """INSERT OR REPLACE INTO bitcoin_prices 
                   (timestamp, price, volume, source, rsi, macd) 
                   VALUES (?, ?, ?, ?, ?, ?)"""
        
        timestamp = price_data['timestamp']
        if isinstance(timestamp, datetime):
            timestamp = timestamp.isoformat()
        
        params = (
            timestamp,
            price_data['price'],
            price_data.get('volume'),
            price_data.get('source', 'unknown'),
            price_data.get('rsi'),
            price_data.get('macd')
        )
        
        result = await self.db.execute_query(query, params)
        return result.success
    
    async def get_latest_price(self) -> Optional[Dict[str, Any]]:
        """Get latest price."""
        query = "SELECT * FROM bitcoin_prices ORDER BY timestamp DESC LIMIT 1"
        result = await self.db.execute_query(query, fetch_one=True)
        
        if result.success and result.data:
            data = result.data
            data['timestamp'] = datetime.fromisoformat(data['timestamp'])
            return data
        return None
    
    async def get_price_history(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get price history."""
        cutoff = (datetime.now() - timedelta(hours=hours)).isoformat()
        query = "SELECT * FROM bitcoin_prices WHERE timestamp >= ? ORDER BY timestamp ASC"
        result = await self.db.execute_query(query, (cutoff,))
        
        if result.success and result.data:
            for item in result.data:
                item['timestamp'] = datetime.fromisoformat(item['timestamp'])
            return result.data
        return []


class TradeRepository:
    """Trade execution repository."""
    
    def __init__(self, db: DatabaseManager):
        self.db = db
    
    async def save_trade(self, trade_data: Dict[str, Any]) -> bool:
        """Save trade execution."""
        query = """INSERT INTO trades 
                   (id, timestamp, strategy_id, symbol, side, amount, price, status, fees, pnl) 
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""
        
        timestamp = trade_data['timestamp']
        if isinstance(timestamp, datetime):
            timestamp = timestamp.isoformat()
        
        params = (
            trade_data['id'],
            timestamp,
            trade_data['strategy_id'],
            trade_data.get('symbol', 'BTC-USD'),
            trade_data['side'],
            trade_data['amount'],
            trade_data['price'],
            trade_data.get('status', 'completed'),
            trade_data.get('fees', 0),
            trade_data.get('pnl')
        )
        
        result = await self.db.execute_query(query, params)
        return result.success
    
    async def get_strategy_trades(self, strategy_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get trades for strategy."""
        query = "SELECT * FROM trades WHERE strategy_id = ? ORDER BY timestamp DESC LIMIT ?"
        result = await self.db.execute_query(query, (strategy_id, limit))
        
        if result.success and result.data:
            for trade in result.data:
                trade['timestamp'] = datetime.fromisoformat(trade['timestamp'])
            return result.data
        return []
    
    async def get_trade_stats(self, strategy_id: Optional[str] = None) -> Dict[str, Any]:
        """Get trade statistics."""
        if strategy_id:
            query = """SELECT COUNT(*) as total_trades, 
                             SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) as winning_trades,
                             SUM(pnl) as total_pnl, AVG(pnl) as avg_pnl
                      FROM trades WHERE strategy_id = ?"""
            params = (strategy_id,)
        else:
            query = """SELECT COUNT(*) as total_trades,
                             SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) as winning_trades,
                             SUM(pnl) as total_pnl, AVG(pnl) as avg_pnl
                      FROM trades"""
            params = None
        
        result = await self.db.execute_query(query, params, fetch_one=True)
        return result.data if result.success and result.data else {}


class StrategyRepository:
    """Strategy signals repository."""
    
    def __init__(self, db: DatabaseManager):
        self.db = db
    
    async def save_signal(self, signal_data: Dict[str, Any]) -> bool:
        """Save strategy signal."""
        query = """INSERT INTO strategy_signals 
                   (id, strategy_id, timestamp, signal_type, confidence, price, executed, execution_id) 
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)"""
        
        timestamp = signal_data['timestamp']
        if isinstance(timestamp, datetime):
            timestamp = timestamp.isoformat()
        
        params = (
            signal_data['id'],
            signal_data['strategy_id'],
            timestamp,
            signal_data['signal_type'],
            signal_data['confidence'],
            signal_data['price'],
            signal_data.get('executed', False),
            signal_data.get('execution_id')
        )
        
        result = await self.db.execute_query(query, params)
        return result.success
    
    async def get_strategy_signals(self, strategy_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get signals for strategy."""
        query = "SELECT * FROM strategy_signals WHERE strategy_id = ? ORDER BY timestamp DESC LIMIT ?"
        result = await self.db.execute_query(query, (strategy_id, limit))
        
        if result.success and result.data:
            for signal in result.data:
                signal['timestamp'] = datetime.fromisoformat(signal['timestamp'])
                signal['executed'] = bool(signal['executed'])
            return result.data
        return []
    
    async def update_signal_execution(self, signal_id: str, execution_id: str) -> bool:
        """Mark signal as executed."""
        query = "UPDATE strategy_signals SET executed = 1, execution_id = ? WHERE id = ?"
        result = await self.db.execute_query(query, (execution_id, signal_id))
        return result.success


class PortfolioRepository:
    """Portfolio snapshots repository."""
    
    def __init__(self, db: DatabaseManager):
        self.db = db
    
    async def save_snapshot(self, snapshot_data: Dict[str, Any]) -> bool:
        """Save portfolio snapshot."""
        query = """INSERT INTO portfolio_snapshots 
                   (timestamp, total_value, cash_balance, btc_balance) 
                   VALUES (?, ?, ?, ?)"""
        
        timestamp = snapshot_data['timestamp']
        if isinstance(timestamp, datetime):
            timestamp = timestamp.isoformat()
        
        params = (
            timestamp,
            snapshot_data['total_value'],
            snapshot_data['cash_balance'],
            snapshot_data['btc_balance']
        )
        
        result = await self.db.execute_query(query, params)
        return result.success
    
    async def get_latest_snapshot(self) -> Optional[Dict[str, Any]]:
        """Get latest portfolio snapshot."""
        query = "SELECT * FROM portfolio_snapshots ORDER BY timestamp DESC LIMIT 1"
        result = await self.db.execute_query(query, fetch_one=True)
        
        if result.success and result.data:
            data = result.data
            data['timestamp'] = datetime.fromisoformat(data['timestamp'])
            return data
        return None
    
    async def get_snapshot_history(self, days: int = 30) -> List[Dict[str, Any]]:
        """Get portfolio snapshot history."""
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        query = "SELECT * FROM portfolio_snapshots WHERE timestamp >= ? ORDER BY timestamp ASC"
        result = await self.db.execute_query(query, (cutoff,))
        
        if result.success and result.data:
            for snapshot in result.data:
                snapshot['timestamp'] = datetime.fromisoformat(snapshot['timestamp'])
            return result.data
        return []


class RepositoryManager:
    """Main repository manager."""
    
    def __init__(self, database_path: str = "data/odin.db"):
        self.db = DatabaseManager(database_path)
        self.price_repo = PriceRepository(self.db)
        self.trade_repo = TradeRepository(self.db)
        self.strategy_repo = StrategyRepository(self.db)
        self.portfolio_repo = PortfolioRepository(self.db)
    
    async def initialize(self):
        """Initialize repository manager."""
        await self.db.initialize()
    
    async def close(self):
        """Close database connections."""
        while not self.db.connection_pool.empty():
            try:
                conn = self.db.connection_pool.get_nowait()
                conn.close()
            except asyncio.QueueEmpty:
                break
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get database statistics."""
        stats = {}
        
        # Price data count
        result = await self.db.execute_query("SELECT COUNT(*) as count FROM bitcoin_prices", fetch_one=True)
        stats['price_records'] = result.data['count'] if result.success and result.data else 0
        
        # Trade count
        result = await self.db.execute_query("SELECT COUNT(*) as count FROM trades", fetch_one=True)
        stats['trade_records'] = result.data['count'] if result.success and result.data else 0
        
        # Signal count
        result = await self.db.execute_query("SELECT COUNT(*) as count FROM strategy_signals", fetch_one=True)
        stats['signal_records'] = result.data['count'] if result.success and result.data else 0
        
        return stats


# Global instance
_repo_manager: Optional[RepositoryManager] = None


async def get_repository_manager() -> RepositoryManager:
    """Get global repository manager."""
    global _repo_manager
    if _repo_manager is None:
        _repo_manager = RepositoryManager()
        await _repo_manager.initialize()
    return _repo_manager


# Convenience functions
async def save_price_data(price_data: Dict[str, Any]) -> bool:
    """Save price data."""
    repo = await get_repository_manager()
    return await repo.price_repo.save_price(price_data)


async def get_latest_price() -> Optional[Dict[str, Any]]:
    """Get latest price."""
    repo = await get_repository_manager()
    return await repo.price_repo.get_latest_price()


async def save_trade(trade_data: Dict[str, Any]) -> bool:
    """Save trade."""
    repo = await get_repository_manager()
    return await repo.trade_repo.save_trade(trade_data)


async def save_signal(signal_data: Dict[str, Any]) -> bool:
    """Save strategy signal."""
    repo = await get_repository_manager()
    return await repo.strategy_repo.save_signal(signal_data)


async def save_portfolio_snapshot(snapshot_data: Dict[str, Any]) -> bool:
    """Save portfolio snapshot."""
    repo = await get_repository_manager()
    return await repo.portfolio_repo.save_snapshot(snapshot_data)


async def get_database_stats() -> Dict[str, Any]:
    """Get database statistics."""
    repo = await get_repository_manager()
    return await repo.get_stats()