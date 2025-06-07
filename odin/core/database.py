"""
Odin Bitcoin Trading Bot - Simple SQLite Database (No SQLAlchemy ORM)
"""

import sqlite3
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Simple SQLite database manager for Odin Bitcoin Trading Bot."""
    
    def __init__(self, db_path: str = "data/bitcoin_data.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()
    
    def _init_database(self):
        """Initialize database tables."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("PRAGMA foreign_keys = ON")
                cursor = conn.cursor()
                
                # Bitcoin prices table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS bitcoin_prices (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp DATETIME NOT NULL,
                        price REAL NOT NULL CHECK(price > 0),
                        volume REAL CHECK(volume >= 0),
                        market_cap REAL CHECK(market_cap >= 0),
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(timestamp)
                    )
                """)
                
                # Strategies table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS strategies (
                        id TEXT PRIMARY KEY,
                        name TEXT NOT NULL,
                        type TEXT NOT NULL,
                        description TEXT,
                        parameters TEXT,
                        active BOOLEAN DEFAULT FALSE,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Trades table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS trades (
                        id TEXT PRIMARY KEY,
                        timestamp DATETIME NOT NULL,
                        strategy_id TEXT,
                        symbol TEXT DEFAULT 'BTC-USD',
                        side TEXT NOT NULL CHECK(side IN ('buy', 'sell')),
                        order_type TEXT NOT NULL CHECK(order_type IN ('market', 'limit', 'stop_loss', 'take_profit')),
                        amount REAL NOT NULL CHECK(amount > 0),
                        price REAL NOT NULL CHECK(price > 0),
                        status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'filled', 'cancelled', 'rejected', 'expired')),
                        executed_amount REAL CHECK(executed_amount >= 0),
                        executed_price REAL CHECK(executed_price > 0),
                        fees REAL CHECK(fees >= 0),
                        pnl REAL,
                        pnl_percentage REAL,
                        notes TEXT,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (strategy_id) REFERENCES strategies (id)
                    )
                """)
                
                # Portfolio snapshots table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS portfolio_snapshots (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp DATETIME NOT NULL,
                        total_value REAL NOT NULL CHECK(total_value >= 0),
                        cash_balance REAL NOT NULL CHECK(cash_balance >= 0),
                        btc_balance REAL NOT NULL CHECK(btc_balance >= 0),
                        daily_pnl REAL,
                        daily_pnl_percentage REAL,
                        allocation TEXT,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(timestamp)
                    )
                """)
                
                # Strategy signals table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS strategy_signals (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        strategy_id TEXT NOT NULL,
                        timestamp DATETIME NOT NULL,
                        signal_type TEXT NOT NULL CHECK(signal_type IN ('buy', 'sell', 'hold')),
                        confidence REAL NOT NULL CHECK(confidence >= 0 AND confidence <= 1),
                        price REAL NOT NULL CHECK(price > 0),
                        indicators TEXT,
                        reasoning TEXT,
                        executed BOOLEAN DEFAULT FALSE,
                        execution_id TEXT,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (strategy_id) REFERENCES strategies (id),
                        FOREIGN KEY (execution_id) REFERENCES trades (id)
                    )
                """)
                
                # Create indexes for better performance
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_prices_timestamp ON bitcoin_prices(timestamp DESC)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_trades_timestamp ON trades(timestamp DESC)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_trades_strategy ON trades(strategy_id)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_signals_timestamp ON strategy_signals(timestamp DESC)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_signals_strategy ON strategy_signals(strategy_id)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_portfolio_timestamp ON portfolio_snapshots(timestamp DESC)")
                
                conn.commit()
                logger.info("Database initialized successfully")
                
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            raise
    
    # Price Data Methods
    def add_price_data(self, timestamp: datetime, price: float, 
                      volume: Optional[float] = None, market_cap: Optional[float] = None) -> bool:
        """Add Bitcoin price data."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO bitcoin_prices (timestamp, price, volume, market_cap)
                    VALUES (?, ?, ?, ?)
                """, (timestamp, price, volume, market_cap))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error adding price data: {e}")
            return False
    
    def get_recent_prices(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent Bitcoin prices."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT timestamp, price, volume, market_cap
                    FROM bitcoin_prices
                    ORDER BY timestamp DESC
                    LIMIT ?
                """, (limit,))
                
                return [dict(row) for row in reversed(cursor.fetchall())]
        except Exception as e:
            logger.error(f"Error getting recent prices: {e}")
            return []
    
    def get_current_price(self) -> Optional[Dict[str, Any]]:
        """Get the most recent Bitcoin price."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT timestamp, price, volume, market_cap
                    FROM bitcoin_prices
                    ORDER BY timestamp DESC
                    LIMIT 1
                """)
                
                row = cursor.fetchone()
                return dict(row) if row else None
        except Exception as e:
            logger.error(f"Error getting current price: {e}")
            return None
    
    # Strategy Methods
    def add_strategy(self, strategy_id: str, name: str, strategy_type: str, 
                    description: str = None, parameters: Dict[str, Any] = None, 
                    active: bool = False) -> bool:
        """Add or update strategy."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                params_json = json.dumps(parameters) if parameters else None
                
                cursor.execute("""
                    INSERT OR REPLACE INTO strategies 
                    (id, name, type, description, parameters, active, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (strategy_id, name, strategy_type, description, params_json, active, datetime.now()))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error adding strategy: {e}")
            return False
    
    def get_strategies(self, active_only: bool = False) -> List[Dict[str, Any]]:
        """Get all strategies."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                query = """
                    SELECT id, name, type, description, parameters, active, created_at, updated_at
                    FROM strategies
                """
                
                if active_only:
                    query += " WHERE active = 1"
                
                query += " ORDER BY created_at DESC"
                
                cursor.execute(query)
                
                strategies = []
                for row in cursor.fetchall():
                    strategy = dict(row)
                    if strategy['parameters']:
                        strategy['parameters'] = json.loads(strategy['parameters'])
                    strategies.append(strategy)
                
                return strategies
        except Exception as e:
            logger.error(f"Error getting strategies: {e}")
            return []
    
    def update_strategy_status(self, strategy_id: str, active: bool) -> bool:
        """Update strategy active status."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE strategies 
                    SET active = ?, updated_at = ?
                    WHERE id = ?
                """, (active, datetime.now(), strategy_id))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Error updating strategy status: {e}")
            return False
    
    # Trade Methods
    def add_trade(self, trade_id: str, timestamp: datetime, strategy_id: str,
                 symbol: str, side: str, order_type: str, amount: float, 
                 price: float, status: str = "pending", **kwargs) -> bool:
        """Add trade execution."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO trades 
                    (id, timestamp, strategy_id, symbol, side, order_type, amount, price, status,
                     executed_amount, executed_price, fees, pnl, pnl_percentage, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    trade_id, timestamp, strategy_id, symbol, side, order_type, 
                    amount, price, status,
                    kwargs.get('executed_amount'),
                    kwargs.get('executed_price'),
                    kwargs.get('fees'),
                    kwargs.get('pnl'),
                    kwargs.get('pnl_percentage'),
                    kwargs.get('notes')
                ))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error adding trade: {e}")
            return False
    
    def get_recent_trades(self, limit: int = 10, strategy_id: str = None) -> List[Dict[str, Any]]:
        """Get recent trades."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                query = """
                    SELECT id, timestamp, strategy_id, symbol, side, order_type, 
                           amount, price, status, executed_amount, executed_price, 
                           fees, pnl, pnl_percentage, notes
                    FROM trades
                """
                
                params = []
                if strategy_id:
                    query += " WHERE strategy_id = ?"
                    params.append(strategy_id)
                
                query += " ORDER BY timestamp DESC LIMIT ?"
                params.append(limit)
                
                cursor.execute(query, params)
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error getting recent trades: {e}")
            return []
    
    # Portfolio Methods
    def add_portfolio_snapshot(self, timestamp: datetime, total_value: float,
                              cash_balance: float, btc_balance: float, **kwargs) -> bool:
        """Add portfolio snapshot."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                allocation_json = json.dumps(kwargs.get('allocation')) if kwargs.get('allocation') else None
                
                cursor.execute("""
                    INSERT OR REPLACE INTO portfolio_snapshots
                    (timestamp, total_value, cash_balance, btc_balance, 
                     daily_pnl, daily_pnl_percentage, allocation)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    timestamp, total_value, cash_balance, btc_balance,
                    kwargs.get('daily_pnl'),
                    kwargs.get('daily_pnl_percentage'),
                    allocation_json
                ))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error adding portfolio snapshot: {e}")
            return False
    
    def get_latest_portfolio(self) -> Optional[Dict[str, Any]]:
        """Get latest portfolio snapshot."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT timestamp, total_value, cash_balance, btc_balance,
                           daily_pnl, daily_pnl_percentage, allocation
                    FROM portfolio_snapshots
                    ORDER BY timestamp DESC
                    LIMIT 1
                """)
                
                row = cursor.fetchone()
                if row:
                    portfolio = dict(row)
                    if portfolio['allocation']:
                        portfolio['allocation'] = json.loads(portfolio['allocation'])
                    return portfolio
                return None
        except Exception as e:
            logger.error(f"Error getting latest portfolio: {e}")
            return None
    
    # Signal Methods
    def add_signal(self, strategy_id: str, timestamp: datetime, signal_type: str,
                  confidence: float, price: float, **kwargs) -> bool:
        """Add strategy signal."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                indicators_json = json.dumps(kwargs.get('indicators')) if kwargs.get('indicators') else None
                
                cursor.execute("""
                    INSERT INTO strategy_signals
                    (strategy_id, timestamp, signal_type, confidence, price,
                     indicators, reasoning, executed, execution_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    strategy_id, timestamp, signal_type, confidence, price,
                    indicators_json,
                    kwargs.get('reasoning'),
                    kwargs.get('executed', False),
                    kwargs.get('execution_id')
                ))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error adding signal: {e}")
            return False
    
    def get_recent_signals(self, strategy_id: str = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent strategy signals."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                query = """
                    SELECT strategy_id, timestamp, signal_type, confidence, price,
                           indicators, reasoning, executed, execution_id
                    FROM strategy_signals
                """
                
                params = []
                if strategy_id:
                    query += " WHERE strategy_id = ?"
                    params.append(strategy_id)
                
                query += " ORDER BY timestamp DESC LIMIT ?"
                params.append(limit)
                
                cursor.execute(query, params)
                
                results = []
                for row in cursor.fetchall():
                    signal = dict(row)
                    if signal['indicators']:
                        signal['indicators'] = json.loads(signal['indicators'])
                    results.append(signal)
                
                return results
        except Exception as e:
            logger.error(f"Error getting recent signals: {e}")
            return []
    
    # Statistics Methods
    def get_database_stats(self) -> Dict[str, Any]:
        """Get comprehensive database statistics."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                stats = {}
                
                # Count records in each table
                tables = ['bitcoin_prices', 'strategies', 'trades', 'portfolio_snapshots', 'strategy_signals']
                
                for table in tables:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    stats[f"{table}_count"] = cursor.fetchone()[0]
                
                # Get data ranges
                cursor.execute("SELECT MIN(timestamp), MAX(timestamp) FROM bitcoin_prices")
                price_range = cursor.fetchone()
                if price_range[0]:
                    stats['price_data_range'] = {
                        'start': price_range[0],
                        'end': price_range[1]
                    }
                
                # Get active strategies count
                cursor.execute("SELECT COUNT(*) FROM strategies WHERE active = 1")
                stats['active_strategies'] = cursor.fetchone()[0]
                
                # Get today's trade count
                today = datetime.now().date()
                cursor.execute("SELECT COUNT(*) FROM trades WHERE DATE(timestamp) = ?", (today,))
                stats['trades_today'] = cursor.fetchone()[0]
                
                # Get latest portfolio value
                cursor.execute("SELECT total_value FROM portfolio_snapshots ORDER BY timestamp DESC LIMIT 1")
                latest_value = cursor.fetchone()
                if latest_value:
                    stats['latest_portfolio_value'] = latest_value[0]
                
                # Database file size
                stats['database_size_mb'] = round(self.db_path.stat().st_size / (1024 * 1024), 2)
                
                return stats
        except Exception as e:
            logger.error(f"Error getting database stats: {e}")
            return {}
    
    def close(self):
        """Close database connection (no-op for SQLite with context managers)."""
        pass

# Convenience functions
def get_database(db_path: str = "data/bitcoin_data.db") -> DatabaseManager:
    """Get database manager instance."""
    return DatabaseManager(db_path)

def init_sample_data(db: DatabaseManager) -> bool:
    """Initialize database with sample data for testing."""
    try:
        import random
        
        # Add sample strategies
        strategies = [
            ("ma_cross", "Moving Average Crossover", "moving_average", 
             "Simple moving average crossover strategy", {"short_period": 5, "long_period": 20}),
            ("rsi_momentum", "RSI Momentum", "rsi", 
             "RSI-based momentum strategy", {"period": 14, "overbought": 70, "oversold": 30}),
            ("bollinger_bands", "Bollinger Bands", "bollinger_bands", 
             "Bollinger Bands mean reversion strategy", {"period": 20, "std_dev": 2}),
            ("macd_trend", "MACD Trend", "macd", 
             "MACD trend following strategy", {"fast_period": 12, "slow_period": 26, "signal_period": 9})
        ]
        
        for strategy_id, name, strategy_type, description, params in strategies:
            db.add_strategy(strategy_id, name, strategy_type, description, params, 
                          active=random.choice([True, False]))
        
        # Add sample price data
        base_price = 45000
        current_time = datetime.now()
        
        for i in range(168):  # 1 week of hourly data
            timestamp = current_time - timedelta(hours=i)
            price = base_price + random.uniform(-2000, 2000)
            volume = random.uniform(1000, 5000)
            market_cap = price * 19700000  # Approximate BTC supply
            
            db.add_price_data(timestamp, price, volume, market_cap)
        
        # Add sample portfolio snapshot
        db.add_portfolio_snapshot(
            current_time, 10000, 5000, 0.25,
            daily_pnl=random.uniform(-200, 200),
            daily_pnl_percentage=random.uniform(-2, 2),
            allocation={"Bitcoin": 50, "USD": 50}
        )
        
        logger.info("Sample data initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Error initializing sample data: {e}")
        return False