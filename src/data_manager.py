# src/data_manager.py (Enhanced with CSV Auto-Detection)
"""
Enhanced Data Manager - Automatically detects and integrates CSV historical data
Seamlessly combines your 17+ years of historical data with live feeds
"""

import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import threading
import time
import logging
from typing import Dict, List, Optional, Tuple, Union
import requests
from dataclasses import dataclass
import os
import glob

logger = logging.getLogger(__name__)

@dataclass
class PriceData:
    """Standardized price data structure"""
    timestamp: datetime
    price: float
    volume: float
    high: float
    low: float
    source: str
    
    def to_dict(self) -> dict:
        return {
            'timestamp': self.timestamp.isoformat(),
            'price': self.price,
            'volume': self.volume,
            'high': self.high,
            'low': self.low,
            'source': self.source
        }

class EnhancedDataManager:
    """
    Enhanced data manager with automatic CSV detection and integration
    Combines your historical CSV data with live price feeds
    """
    
    def __init__(self, 
                 historical_db_path: str = None,
                 live_update_interval: int = 30,
                 data_retention_days: int = 365):
        
        # Setup paths
        current_file = os.path.abspath(__file__)
        self.src_dir = os.path.dirname(current_file)
        self.project_root = os.path.dirname(self.src_dir)
        
        # Database setup
        if historical_db_path is None:
            data_dir = os.path.join(self.project_root, 'data')
            os.makedirs(data_dir, exist_ok=True)
            historical_db_path = os.path.join(data_dir, 'bitcoin_data.db')
        
        self.historical_db_path = historical_db_path
        self.live_update_interval = live_update_interval
        self.data_retention_days = data_retention_days
        
        # In-memory cache for recent data
        self.live_cache = []
        self.cache_lock = threading.Lock()
        
        # Track data status
        self.historical_data_loaded = False
        self.csv_file_path = None
        
        # Data sources configuration
        self.data_sources = {
            'coindesk': {
                'url': 'https://api.coindesk.com/v1/bpi/currentprice.json',
                'parser': self._parse_coindesk
            },
            'blockchain_info': {
                'url': 'https://api.blockchain.info/ticker',
                'parser': self._parse_blockchain_info
            },
            'coingecko': {
                'url': 'https://api.coingecko.com/api/v3/simple/price',
                'params': {'ids': 'bitcoin', 'vs_currencies': 'usd', 'include_24hr_change': 'true'},
                'parser': self._parse_coingecko
            }
        }
        
        # Initialize system
        self.database_ready = self._setup_database()
        self._detect_and_load_historical_data()
        self._start_live_collection()
    
    def _setup_database(self):
        """Setup database with enhanced schema"""
        try:
            # Handle path and permission issues
            try:
                test_path = os.path.dirname(self.historical_db_path)
                if test_path and not os.path.exists(test_path):
                    os.makedirs(test_path, exist_ok=True)
                
                conn = sqlite3.connect(self.historical_db_path)
                cursor = conn.cursor()
                
                # Test write permissions
                cursor.execute("CREATE TABLE IF NOT EXISTS test_table (id INTEGER)")
                cursor.execute("DROP TABLE test_table")
                
            except (PermissionError, OSError) as e:
                logger.warning(f"File system database failed: {e}")
                logger.info("🔄 Switching to in-memory database")
                self.historical_db_path = ":memory:"
                conn = sqlite3.connect(":memory:")
                cursor = conn.cursor()
                self._memory_conn = conn  # Keep connection open for memory DB
            
            # Create enhanced table schema
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS btc_prices (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT UNIQUE,
                    price REAL NOT NULL,
                    volume REAL,
                    high REAL,
                    low REAL,
                    open_price REAL,
                    close_price REAL,
                    source TEXT,
                    data_type TEXT DEFAULT 'live'
                )
            ''')
            
            # Create indexes for performance
            cursor.execute('''CREATE INDEX IF NOT EXISTS idx_timestamp ON btc_prices(timestamp)''')
            cursor.execute('''CREATE INDEX IF NOT EXISTS idx_data_type ON btc_prices(data_type)''')
            cursor.execute('''CREATE INDEX IF NOT EXISTS idx_source ON btc_prices(source)''')
            
            if self.historical_db_path != ":memory:":
                conn.commit()
                conn.close()
            
            logger.info(f"✅ Database setup completed: {self.historical_db_path}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Database setup error: {e}")
            return False
    
    def _detect_and_load_historical_data(self):
        """Automatically detect and load historical CSV data"""
        try:
            logger.info("🔍 Scanning for historical Bitcoin CSV data...")
            
            # Search locations for CSV files
            search_locations = [
                self.project_root,  # Project root
                os.path.join(self.project_root, 'scripts'),  # Scripts folder
                os.path.join(self.project_root, 'data'),     # Data folder
                self.src_dir,  # Source directory
                os.getcwd()    # Current working directory
            ]
            
            # Patterns to look for
            csv_patterns = [
                'bitcoin_*.csv',
                'btc_*.csv', 
                '*bitcoin*.csv',
                '*historical*.csv',
                '*price*.csv'
            ]
            
            found_files = []
            
            for location in search_locations:
                if not os.path.exists(location):
                    continue
                    
                for pattern in csv_patterns:
                    search_pattern = os.path.join(location, pattern)
                    matches = glob.glob(search_pattern)
                    for match in matches:
                        if os.path.isfile(match):
                            file_size = os.path.getsize(match) / (1024 * 1024)  # MB
                            found_files.append({
                                'path': match,
                                'size_mb': file_size,
                                'name': os.path.basename(match)
                            })
            
            if not found_files:
                logger.info("📭 No historical CSV files found")
                return
            
            # Sort by size (largest first) and log findings
            found_files.sort(key=lambda x: x['size_mb'], reverse=True)
            
            logger.info(f"📊 Found {len(found_files)} potential CSV file(s):")
            for file_info in found_files:
                logger.info(f"   📄 {file_info['name']} ({file_info['size_mb']:.1f} MB)")
            
            # Try to load the largest file first (most likely to be comprehensive)
            for file_info in found_files:
                if self._load_csv_data(file_info['path']):
                    self.csv_file_path = file_info['path']
                    self.historical_data_loaded = True
                    logger.info(f"✅ Successfully loaded historical data from {file_info['name']}")
                    break
                else:
                    logger.warning(f"⚠️ Failed to load {file_info['name']}")
            
            if not self.historical_data_loaded:
                logger.info("📭 No compatible CSV files found")
                
        except Exception as e:
            logger.error(f"❌ Error detecting historical data: {e}")
    
    def _load_csv_data(self, csv_path: str) -> bool:
        """Load historical data from CSV file"""
        try:
            logger.info(f"📖 Loading CSV data from {os.path.basename(csv_path)}...")
            
            # Read CSV with flexible parsing
            try:
                df = pd.read_csv(csv_path)
            except Exception as e:
                logger.error(f"Failed to read CSV: {e}")
                return False
            
            logger.info(f"📊 CSV loaded: {len(df)} rows, columns: {list(df.columns)}")
            
            # Detect column mapping (flexible column names)
            column_mapping = self._detect_column_mapping(df.columns)
            
            if not column_mapping:
                logger.warning("⚠️ Could not map required columns in CSV")
                return False
            
            logger.info(f"🗂️ Column mapping: {column_mapping}")
            
            # Process and load data
            processed_count = 0
            batch_size = 1000
            
            # Get database connection
            if self.historical_db_path == ":memory:":
                conn = self._memory_conn
            else:
                conn = sqlite3.connect(self.historical_db_path)
            
            cursor = conn.cursor()
            
            # Process data in batches
            for start_idx in range(0, len(df), batch_size):
                batch = df.iloc[start_idx:start_idx + batch_size]
                batch_data = []
                
                for _, row in batch.iterrows():
                    try:
                        # Extract data using column mapping
                        timestamp_str = str(row[column_mapping['date']])
                        price = float(row[column_mapping['price']])
                        
                        # Parse timestamp (handle different formats)
                        timestamp = self._parse_timestamp(timestamp_str)
                        if not timestamp:
                            continue
                        
                        # Extract optional fields
                        volume = self._safe_float(row.get(column_mapping.get('volume'), 0))
                        high = self._safe_float(row.get(column_mapping.get('high'), price))
                        low = self._safe_float(row.get(column_mapping.get('low'), price))
                        open_price = self._safe_float(row.get(column_mapping.get('open'), price))
                        close_price = self._safe_float(row.get(column_mapping.get('close'), price))
                        
                        batch_data.append((
                            timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                            price,
                            volume,
                            high,
                            low,
                            open_price,
                            close_price,
                            'csv_historical',
                            'historical'
                        ))
                        
                    except Exception as e:
                        logger.debug(f"Skipping row due to error: {e}")
                        continue
                
                # Insert batch
                if batch_data:
                    cursor.executemany('''
                        INSERT OR REPLACE INTO btc_prices 
                        (timestamp, price, volume, high, low, open_price, close_price, source, data_type)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', batch_data)
                    
                    processed_count += len(batch_data)
                    
                    if start_idx % (batch_size * 10) == 0:  # Progress every 10 batches
                        logger.info(f"   Processed {processed_count:,} records...")
            
            # Commit changes
            if self.historical_db_path != ":memory:":
                conn.commit()
                conn.close()
            
            if processed_count > 0:
                logger.info(f"✅ Successfully loaded {processed_count:,} historical records")
                
                # Log date range
                cursor = self._get_cursor()
                cursor.execute("SELECT MIN(timestamp), MAX(timestamp) FROM btc_prices WHERE data_type='historical'")
                min_date, max_date = cursor.fetchone()
                if min_date and max_date:
                    logger.info(f"📅 Historical data range: {min_date} to {max_date}")
                
                return True
            else:
                logger.warning("⚠️ No data could be processed from CSV")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error loading CSV data: {e}")
            return False
    
    def _detect_column_mapping(self, columns) -> Dict[str, str]:
        """Detect column mapping for different CSV formats"""
        columns_lower = [col.lower() for col in columns]
        mapping = {}
        
        # Date/timestamp column
        date_patterns = ['date', 'timestamp', 'time', 'start', 'end']
        for pattern in date_patterns:
            for i, col in enumerate(columns_lower):
                if pattern in col:
                    mapping['date'] = columns[i]
                    break
            if 'date' in mapping:
                break
        
        # Price columns
        price_patterns = ['close', 'price', 'last', 'value']
        for pattern in price_patterns:
            for i, col in enumerate(columns_lower):
                if pattern in col and 'date' not in col:
                    mapping['price'] = columns[i]
                    break
            if 'price' in mapping:
                break
        
        # Optional columns
        optional_mappings = {
            'volume': ['volume', 'vol'],
            'high': ['high', 'max'],
            'low': ['low', 'min'],
            'open': ['open', 'opening'],
            'close': ['close', 'closing']
        }
        
        for key, patterns in optional_mappings.items():
            for pattern in patterns:
                for i, col in enumerate(columns_lower):
                    if pattern in col:
                        mapping[key] = columns[i]
                        break
                if key in mapping:
                    break
        
        # Require at least date and price
        if 'date' in mapping and 'price' in mapping:
            return mapping
        else:
            return {}
    
    def _parse_timestamp(self, timestamp_str: str) -> Optional[datetime]:
        """Parse timestamp from various formats"""
        if pd.isna(timestamp_str) or not timestamp_str:
            return None
        
        # Common timestamp formats
        formats = [
            '%Y-%m-%d',
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%d %H:%M',
            '%m/%d/%Y',
            '%d/%m/%Y',
            '%Y/%m/%d',
            '%Y-%m-%dT%H:%M:%S',
            '%Y-%m-%dT%H:%M:%SZ'
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(str(timestamp_str), fmt)
            except ValueError:
                continue
        
        # Try pandas parsing as fallback
        try:
            return pd.to_datetime(timestamp_str)
        except:
            logger.debug(f"Could not parse timestamp: {timestamp_str}")
            return None
    
    def _safe_float(self, value, default=0.0) -> float:
        """Safely convert value to float"""
        try:
            if pd.isna(value):
                return default
            return float(value)
        except (ValueError, TypeError):
            return default
    
    def _get_cursor(self):
        """Get database cursor"""
        if self.historical_db_path == ":memory:":
            return self._memory_conn.cursor()
        else:
            conn = sqlite3.connect(self.historical_db_path)
            return conn.cursor()
    
    def get_unified_data(self, 
                        hours: int = 24, 
                        include_live: bool = True,
                        resample_frequency: str = None) -> pd.DataFrame:
        """Get unified historical + live data"""
        try:
            if not self.database_ready:
                return self._get_cache_as_dataframe()
            
            cutoff_time = datetime.now() - timedelta(hours=hours)
            
            # Get data from database (historical + recent live)
            data = self._get_data_from_database(cutoff_time)
            
            # Add live cache data if requested and recent
            if include_live:
                live_data = self._get_live_data_as_dataframe(cutoff_time)
                if not live_data.empty:
                    data = pd.concat([data, live_data], ignore_index=True)
            
            if data.empty:
                return pd.DataFrame()
            
            # Process data
            data['timestamp'] = pd.to_datetime(data['timestamp'])
            data = data.sort_values('timestamp')
            data.set_index('timestamp', inplace=True)
            
            # Remove duplicates (keep latest)
            data = data[~data.index.duplicated(keep='last')]
            
            # Resample if requested
            if resample_frequency and not data.empty:
                data = self._resample_data(data, resample_frequency)
            
            return data
            
        except Exception as e:
            logger.error(f"Error getting unified data: {e}")
            return self._get_cache_as_dataframe()
    
    def _get_data_from_database(self, cutoff_time: datetime) -> pd.DataFrame:
        """Get data from database"""
        try:
            if self.historical_db_path == ":memory:":
                conn = self._memory_conn
            else:
                conn = sqlite3.connect(self.historical_db_path)
            
            query = '''
                SELECT timestamp, 
                       COALESCE(close_price, price) as price, 
                       volume, high, low, 
                       open_price as open, 
                       source
                FROM btc_prices 
                WHERE timestamp >= ? 
                ORDER BY timestamp ASC
            '''
            
            df = pd.read_sql_query(
                query, 
                conn, 
                params=(cutoff_time.strftime('%Y-%m-%d %H:%M:%S'),)
            )
            
            if self.historical_db_path != ":memory:":
                conn.close()
            
            return df
            
        except Exception as e:
            logger.error(f"Error getting data from database: {e}")
            return pd.DataFrame()
    
    def get_latest_price(self) -> Optional[PriceData]:
        """Get the most recent price data"""
        try:
            # Try live cache first
            with self.cache_lock:
                if self.live_cache:
                    return self.live_cache[-1]
            
            # Fetch fresh data if cache is empty
            price_data = self._fetch_live_price()
            if price_data:
                self._add_to_cache(price_data)
                return price_data
            
            # Fallback to database (most recent record)
            if self.database_ready:
                try:
                    if self.historical_db_path == ":memory:":
                        conn = self._memory_conn
                    else:
                        conn = sqlite3.connect(self.historical_db_path)
                    
                    cursor = conn.cursor()
                    cursor.execute('''
                        SELECT timestamp, COALESCE(close_price, price) as price, 
                               volume, high, low, source
                        FROM btc_prices 
                        ORDER BY timestamp DESC 
                        LIMIT 1
                    ''')
                    
                    result = cursor.fetchone()
                    
                    if self.historical_db_path != ":memory:":
                        conn.close()
                    
                    if result:
                        timestamp, price, volume, high, low, source = result
                        return PriceData(
                            timestamp=datetime.fromisoformat(timestamp.replace('Z', '+00:00')),
                            price=price,
                            volume=volume or 0,
                            high=high or price,
                            low=low or price,
                            source=source or 'database'
                        )
                except Exception as e:
                    logger.error(f"Error getting from database: {e}")
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting latest price: {e}")
            return None
    
    def get_statistics(self) -> dict:
        """Get comprehensive data statistics"""
        try:
            stats = {
                'database_ready': self.database_ready,
                'database_path': self.historical_db_path,
                'historical_data_loaded': self.historical_data_loaded,
                'csv_file_path': self.csv_file_path,
                'last_update': datetime.now().isoformat()
            }
            
            if self.database_ready:
                try:
                    if self.historical_db_path == ":memory:":
                        conn = self._memory_conn
                    else:
                        conn = sqlite3.connect(self.historical_db_path)
                    
                    cursor = conn.cursor()
                    
                    # Total records
                    cursor.execute("SELECT COUNT(*) FROM btc_prices")
                    stats['total_records'] = cursor.fetchone()[0]
                    
                    # Records by type
                    cursor.execute("SELECT data_type, COUNT(*) FROM btc_prices GROUP BY data_type")
                    data_types = dict(cursor.fetchall())
                    stats['data_types'] = data_types
                    
                    # Date range
                    cursor.execute("SELECT MIN(timestamp), MAX(timestamp) FROM btc_prices")
                    min_date, max_date = cursor.fetchone()
                    stats['date_range'] = {'start': min_date, 'end': max_date}
                    
                    # Price range
                    cursor.execute("SELECT MIN(price), MAX(price), AVG(price) FROM btc_prices")
                    min_price, max_price, avg_price = cursor.fetchone()
                    stats['price_range'] = {
                        'min': min_price,
                        'max': max_price,
                        'average': avg_price
                    }
                    
                    if self.historical_db_path != ":memory:":
                        conn.close()
                        
                except Exception as e:
                    logger.error(f"Error getting database stats: {e}")
                    stats['total_records'] = 0
            else:
                stats['total_records'] = 0
            
            # Live cache stats
            with self.cache_lock:
                stats['live_cache_size'] = len(self.live_cache)
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            return {'error': str(e)}
    
    # Include all the other methods from the previous version
    # (live data collection, API parsing, etc.)
    
    def _get_cache_as_dataframe(self) -> pd.DataFrame:
        """Convert live cache to DataFrame"""
        try:
            with self.cache_lock:
                if not self.live_cache:
                    return pd.DataFrame()
                
                data_dicts = [data.to_dict() for data in self.live_cache]
                df = pd.DataFrame(data_dicts)
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                df.set_index('timestamp', inplace=True)
                return df
                
        except Exception as e:
            logger.error(f"Error converting cache to DataFrame: {e}")
            return pd.DataFrame()
    
    def _get_live_data_as_dataframe(self, cutoff_time: datetime) -> pd.DataFrame:
        """Get live cache data as DataFrame"""
        try:
            with self.cache_lock:
                filtered_data = [
                    data for data in self.live_cache 
                    if data.timestamp >= cutoff_time
                ]
            
            if not filtered_data:
                return pd.DataFrame()
            
            data_dicts = [data.to_dict() for data in filtered_data]
            df = pd.DataFrame(data_dicts)
            return df
            
        except Exception as e:
            logger.error(f"Error getting live data: {e}")
            return pd.DataFrame()
    
    def _resample_data(self, df: pd.DataFrame, frequency: str) -> pd.DataFrame:
        """Resample data to specified frequency"""
        try:
            if df.empty:
                return df
            
            agg_dict = {
                'price': 'last',
                'volume': 'sum',
                'source': 'last'
            }
            
            # Add OHLC if available
            if 'high' in df.columns:
                agg_dict['high'] = 'max'
            if 'low' in df.columns:
                agg_dict['low'] = 'min'
            if 'open' in df.columns:
                agg_dict['open'] = 'first'
            else:
                agg_dict['open'] = 'first'
            
            resampled = df.resample(frequency).agg(agg_dict).dropna()
            
            # Ensure open column exists
            if 'open' not in resampled.columns:
                resampled['open'] = df['price'].resample(frequency).first()
            
            return resampled
            
        except Exception as e:
            logger.error(f"Error resampling data: {e}")
            return df
    
    def _start_live_collection(self):
        """Start background thread for live data collection"""
        def collection_loop():
            logger.info("🔄 Starting live data collection")
            while True:
                try:
                    price_data = self._fetch_live_price()
                    if price_data:
                        self._add_to_cache(price_data)
                        if self.database_ready:
                            self._save_to_database(price_data)
                    
                    time.sleep(self.live_update_interval)
                    
                except Exception as e:
                    logger.error(f"Live collection error: {e}")
                    time.sleep(60)
        
        thread = threading.Thread(target=collection_loop, daemon=True)
        thread.start()
        logger.info("✅ Live data collection started")
    
    def _fetch_live_price(self) -> Optional[PriceData]:
        """Fetch current price from external APIs"""
        for source_name, source_config in self.data_sources.items():
            try:
                if 'params' in source_config:
                    response = requests.get(
                        source_config['url'], 
                        params=source_config['params'],
                        timeout=10
                    )
                else:
                    response = requests.get(source_config['url'], timeout=10)
                
                response.raise_for_status()
                data = response.json()
                
                price_data = source_config['parser'](data, source_name)
                if price_data:
                    return price_data
                    
            except Exception as e:
                logger.debug(f"Failed to fetch from {source_name}: {e}")
                continue
        
        return None
    
    def _parse_coindesk(self, data: dict, source: str) -> Optional[PriceData]:
        """Parse CoinDesk API response"""
        try:
            price = float(data['bpi']['USD']['rate'].replace(',', ''))
            return PriceData(
                timestamp=datetime.now(),
                price=price,
                volume=50000000000,
                high=price * 1.02,
                low=price * 0.98,
                source=source
            )
        except Exception as e:
            logger.error(f"CoinDesk parsing error: {e}")
            return None
    
    def _parse_blockchain_info(self, data: dict, source: str) -> Optional[PriceData]:
        """Parse Blockchain.info API response"""
        try:
            usd_data = data['USD']
            price = float(usd_data['last'])
            return PriceData(
                timestamp=datetime.now(),
                price=price,
                volume=50000000000,
                high=price * 1.02,
                low=price * 0.98,
                source=source
            )
        except Exception as e:
            logger.error(f"Blockchain.info parsing error: {e}")
            return None
    
    def _parse_coingecko(self, data: dict, source: str) -> Optional[PriceData]:
        """Parse CoinGecko API response"""
        try:
            btc_data = data['bitcoin']
            price = float(btc_data['usd'])
            change_24h = float(btc_data.get('usd_24h_change', 0))
            
            return PriceData(
                timestamp=datetime.now(),
                price=price,
                volume=50000000000,
                high=price * (1 + abs(change_24h)/100/2),
                low=price * (1 - abs(change_24h)/100/2),
                source=source
            )
        except Exception as e:
            logger.error(f"CoinGecko parsing error: {e}")
            return None
    
    def _add_to_cache(self, price_data: PriceData):
        """Add price data to live cache"""
        try:
            with self.cache_lock:
                self.live_cache.append(price_data)
                
                # Keep only recent data in cache (last 24 hours)
                cutoff_time = datetime.now() - timedelta(hours=24)
                self.live_cache = [
                    data for data in self.live_cache 
                    if data.timestamp >= cutoff_time
                ]
                
        except Exception as e:
            logger.error(f"Error adding to cache: {e}")
    
    def _save_to_database(self, price_data: PriceData):
        """Save live data to database"""
        try:
            if not self.database_ready:
                return
            
            if self.historical_db_path == ":memory:":
                conn = self._memory_conn
            else:
                conn = sqlite3.connect(self.historical_db_path)
            
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO btc_prices 
                (timestamp, price, volume, high, low, close_price, source, data_type)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                price_data.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                price_data.price,
                price_data.volume,
                price_data.high,
                price_data.low,
                price_data.price,  # Use price as close_price for live data
                price_data.source,
                'live'
            ))
            
            if self.historical_db_path != ":memory:":
                conn.commit()
                conn.close()
            
        except Exception as e:
            logger.error(f"Error saving to database: {e}")
    
    def cleanup_old_data(self):
        """Clean up old live data beyond retention period"""
        try:
            if not self.database_ready:
                return
            
            cutoff_date = datetime.now() - timedelta(days=self.data_retention_days)
            
            if self.historical_db_path == ":memory:":
                conn = self._memory_conn
            else:
                conn = sqlite3.connect(self.historical_db_path)
            
            cursor = conn.cursor()
            cursor.execute('''
                DELETE FROM btc_prices 
                WHERE data_type = 'live' AND timestamp < ?
            ''', (cutoff_date.strftime('%Y-%m-%d %H:%M:%S'),))
            
            deleted_count = cursor.rowcount
            
            if self.historical_db_path != ":memory:":
                conn.commit()
                conn.close()
            
            if deleted_count > 0:
                logger.info(f"Cleaned up {deleted_count} old live data records")
            
        except Exception as e:
            logger.error(f"Error cleaning up old data: {e}")


# For backward compatibility, alias the enhanced class
DataManager = EnhancedDataManager