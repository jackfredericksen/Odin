# Enhanced Data Collection System for Odin AI/ML Features
# Combines multiple free data sources for comprehensive Bitcoin data

import yfinance as yf
import requests
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
import time
import logging
from typing import Dict, List, Optional
import numpy as np

class EnhancedBitcoinDataCollector:
    """
    Multi-source Bitcoin data collector for Odin trading bot
    Uses yfinance, CoinGecko API, and other free sources
    """
    
    def __init__(self, db_path: str = "data/bitcoin_enhanced.db"):
        self.db_path = db_path
        self.logger = self._setup_logging()
        
        # Free API endpoints
        self.coingecko_base = "https://api.coingecko.com/api/v3"
        self.backup_apis = [
            "https://api.coindesk.com/v1/bpi/historical/close.json",
            "https://min-api.cryptocompare.com/data"
        ]
        
        # Initialize database
        self._init_database()
        
    def _setup_logging(self):
        logging.basicConfig(level=logging.INFO)
        return logging.getLogger(__name__)
        
    def _init_database(self):
        """Initialize enhanced database schema"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Enhanced table with ML-ready features
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bitcoin_enhanced (
                timestamp DATETIME PRIMARY KEY,
                
                -- OHLCV Data
                open REAL,
                high REAL,
                low REAL,
                close REAL,
                volume REAL,
                
                -- Additional Price Data
                market_cap REAL,
                total_volume_24h REAL,
                
                -- Technical Indicators (pre-calculated)
                rsi_14 REAL,
                ma_20 REAL,
                ma_50 REAL,
                bollinger_upper REAL,
                bollinger_lower REAL,
                macd REAL,
                macd_signal REAL,
                
                -- Market Data
                price_change_24h REAL,
                price_change_percentage_24h REAL,
                market_cap_rank INTEGER,
                
                -- Volume Analytics
                volume_ma_20 REAL,
                volume_ratio REAL,
                
                -- Data Quality
                data_source TEXT,
                quality_score REAL,
                
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Index for fast queries
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON bitcoin_enhanced(timestamp)')
        conn.commit()
        conn.close()
        
    def get_yfinance_data(self, start_date: str = "2015-01-01", end_date: str = None) -> pd.DataFrame:
        """
        Get comprehensive Bitcoin data from Yahoo Finance
        Covers: 2015 to present, daily OHLCV data
        """
        try:
            if end_date is None:
                end_date = datetime.now().strftime("%Y-%m-%d")
                
            self.logger.info(f"Fetching yfinance data from {start_date} to {end_date}")
            
            # Get Bitcoin data
            btc = yf.Ticker("BTC-USD")
            
            # Historical OHLCV data
            hist_data = btc.history(start=start_date, end=end_date, interval="1d")
            
            # Current info for additional context
            try:
                info = btc.info
                market_cap = info.get('marketCap', None)
            except:
                market_cap = None
                
            # Clean and prepare data
            df = hist_data.copy()
            df['market_cap'] = market_cap
            df['data_source'] = 'yfinance'
            df['quality_score'] = 0.95  # High quality from Yahoo Finance
            
            return df
            
        except Exception as e:
            self.logger.error(f"yfinance data fetch failed: {e}")
            return pd.DataFrame()
    
    def get_coingecko_data(self, days: int = 365) -> pd.DataFrame:
        """
        Get Bitcoin data from CoinGecko API
        Free tier: 50 calls/minute, comprehensive market data
        """
        try:
            self.logger.info(f"Fetching CoinGecko data for last {days} days")
            
            # Market chart data (price, market cap, volume)
            url = f"{self.coingecko_base}/coins/bitcoin/market_chart"
            params = {
                'vs_currency': 'usd',
                'days': days,
                'interval': 'daily'
            }
            
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            # Convert to DataFrame
            prices = data['prices']
            market_caps = data['market_caps']
            volumes = data['total_volumes']
            
            df_data = []
            for i, (price_data, mc_data, vol_data) in enumerate(zip(prices, market_caps, volumes)):
                timestamp = datetime.fromtimestamp(price_data[0] / 1000)
                df_data.append({
                    'timestamp': timestamp,
                    'close': price_data[1],
                    'market_cap': mc_data[1],
                    'total_volume_24h': vol_data[1],
                    'data_source': 'coingecko',
                    'quality_score': 0.9
                })
            
            df = pd.DataFrame(df_data)
            df.set_index('timestamp', inplace=True)
            
            # Get current market data for additional context
            current_url = f"{self.coingecko_base}/coins/bitcoin"
            current_response = requests.get(current_url)
            
            if current_response.status_code == 200:
                current_data = current_response.json()
                market_data = current_data.get('market_data', {})
                
                # Add latest data to most recent row
                if not df.empty:
                    latest_idx = df.index[-1]
                    df.loc[latest_idx, 'price_change_24h'] = market_data.get('price_change_24h', {}).get('usd', 0)
                    df.loc[latest_idx, 'price_change_percentage_24h'] = market_data.get('price_change_percentage_24h', {}).get('usd', 0)
                    df.loc[latest_idx, 'market_cap_rank'] = market_data.get('market_cap_rank', 1)
            
            return df
            
        except Exception as e:
            self.logger.error(f"CoinGecko data fetch failed: {e}")
            return pd.DataFrame()
    
    def get_historical_complete_dataset(self) -> pd.DataFrame:
        """
        Get complete Bitcoin historical dataset from inception to present
        Combines multiple sources for comprehensive coverage
        """
        try:
            self.logger.info("Building complete historical dataset...")
            
            # 1. Get yfinance data (2015-present, most reliable)
            yf_data = self.get_yfinance_data(start_date="2015-01-01")
            
            # 2. Get CoinGecko data for additional market metrics
            cg_data = self.get_coingecko_data(days=365)  # Last year for market data
            
            # 3. For pre-2015 data, use CoinGecko's max history
            early_cg_data = self.get_coingecko_data(days='max')  # CoinGecko has data from 2013
            
            # Combine datasets intelligently
            combined_data = self._merge_data_sources(yf_data, cg_data, early_cg_data)
            
            # Add technical indicators
            combined_data = self._add_technical_indicators(combined_data)
            
            # Add volume analytics
            combined_data = self._add_volume_analytics(combined_data)
            
            return combined_data
            
        except Exception as e:
            self.logger.error(f"Failed to build complete dataset: {e}")
            return pd.DataFrame()
    
    def _merge_data_sources(self, yf_data: pd.DataFrame, cg_current: pd.DataFrame, cg_historical: pd.DataFrame) -> pd.DataFrame:
        """Intelligently merge data from multiple sources"""
        
        # Start with yfinance as primary source (most reliable OHLCV)
        base_df = yf_data.copy()
        
        # Fill missing market cap data from CoinGecko
        for idx, row in base_df.iterrows():
            if pd.isna(row['market_cap']) and idx in cg_current.index:
                base_df.loc[idx, 'market_cap'] = cg_current.loc[idx, 'market_cap']
                
        # Add CoinGecko-specific fields
        cg_fields = ['total_volume_24h', 'price_change_24h', 'price_change_percentage_24h', 'market_cap_rank']
        for field in cg_fields:
            if field in cg_current.columns:
                base_df[field] = base_df.index.map(lambda x: cg_current.loc[x, field] if x in cg_current.index else np.nan)
        
        return base_df
    
    def _add_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add pre-calculated technical indicators for ML"""
        df = df.copy()
        
        # RSI
        df['rsi_14'] = self._calculate_rsi(df['Close'], 14)
        
        # Moving Averages
        df['ma_20'] = df['Close'].rolling(window=20).mean()
        df['ma_50'] = df['Close'].rolling(window=50).mean()
        
        # Bollinger Bands
        df['bollinger_upper'], df['bollinger_lower'] = self._calculate_bollinger_bands(df['Close'], 20, 2)
        
        # MACD
        df['macd'], df['macd_signal'] = self._calculate_macd(df['Close'])
        
        return df
    
    def _add_volume_analytics(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add volume-based features for ML"""
        df = df.copy()
        
        # Volume moving average
        df['volume_ma_20'] = df['Volume'].rolling(window=20).mean()
        
        # Volume ratio (current vs average)
        df['volume_ratio'] = df['Volume'] / df['volume_ma_20']
        
        return df
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate RSI indicator"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))
    
    def _calculate_bollinger_bands(self, prices: pd.Series, period: int = 20, std_dev: float = 2):
        """Calculate Bollinger Bands"""
        ma = prices.rolling(window=period).mean()
        std = prices.rolling(window=period).std()
        upper = ma + (std * std_dev)
        lower = ma - (std * std_dev)
        return upper, lower
    
    def _calculate_macd(self, prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9):
        """Calculate MACD indicator"""
        ema_fast = prices.ewm(span=fast).mean()
        ema_slow = prices.ewm(span=slow).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal).mean()
        return macd_line, signal_line
    
    def save_to_database(self, df: pd.DataFrame):
        """Save enhanced dataset to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            
            # Prepare data for database
            db_df = df.copy()
            db_df.reset_index(inplace=True)
            
            # Rename columns to match database schema
            column_mapping = {
                'Open': 'open',
                'High': 'high', 
                'Low': 'low',
                'Close': 'close',
                'Volume': 'volume'
            }
            db_df.rename(columns=column_mapping, inplace=True)
            
            # Insert data
            db_df.to_sql('bitcoin_enhanced', conn, if_exists='replace', index=False)
            
            self.logger.info(f"Saved {len(db_df)} records to database")
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Database save failed: {e}")
    
    def get_ml_ready_features(self, lookback_days: int = 365) -> pd.DataFrame:
        """
        Get ML-ready feature set for training
        Returns clean, properly formatted data for AI models
        """
        try:
            conn = sqlite3.connect(self.db_path)
            
            end_date = datetime.now()
            start_date = end_date - timedelta(days=lookback_days)
            
            query = """
                SELECT * FROM bitcoin_enhanced 
                WHERE timestamp >= ? AND timestamp <= ?
                ORDER BY timestamp
            """
            
            df = pd.read_sql_query(query, conn, params=[start_date, end_date])
            conn.close()
            
            # Convert timestamp to datetime index
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df.set_index('timestamp', inplace=True)
            
            # Add derived features for ML
            df = self._add_ml_features(df)
            
            # Clean data for ML (remove NaN, infinite values)
            df = df.replace([np.inf, -np.inf], np.nan)
            df = df.dropna()
            
            return df
            
        except Exception as e:
            self.logger.error(f"ML feature extraction failed: {e}")
            return pd.DataFrame()
    
    def _add_ml_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add additional features specifically for ML models"""
        df = df.copy()
        
        # Price momentum features
        df['price_momentum_1d'] = df['close'].pct_change(1)
        df['price_momentum_7d'] = df['close'].pct_change(7)
        df['price_momentum_30d'] = df['close'].pct_change(30)
        
        # Volatility features
        df['volatility_7d'] = df['close'].rolling(7).std()
        df['volatility_30d'] = df['close'].rolling(30).std()
        
        # Support/Resistance levels
        df['support_level'] = df['low'].rolling(20).min()
        df['resistance_level'] = df['high'].rolling(20).max()
        
        # Time-based features
        df['day_of_week'] = df.index.dayofweek
        df['month'] = df.index.month
        df['quarter'] = df.index.quarter
        
        return df

# Usage Example for Odin Integration
def setup_enhanced_data_collection():
    """Setup enhanced data collection for Odin AI features"""
    
    # Initialize collector
    collector = EnhancedBitcoinDataCollector("data/bitcoin_enhanced.db")
    
    # Get complete historical dataset
    print("Fetching complete Bitcoin dataset...")
    complete_data = collector.get_historical_complete_dataset()
    
    if not complete_data.empty:
        print(f"Retrieved {len(complete_data)} days of Bitcoin data")
        
        # Save to database
        collector.save_to_database(complete_data)
        
        # Get ML-ready features
        ml_features = collector.get_ml_ready_features(lookback_days=1000)
        print(f"ML-ready dataset: {len(ml_features)} samples, {len(ml_features.columns)} features")
        
        # Display sample of data
        print("\nSample of available features:")
        print(ml_features.head())
        print("\nFeature columns:")
        print(ml_features.columns.tolist())
        
        return collector, ml_features
    else:
        print("Failed to retrieve data")
        return None, None

if __name__ == "__main__":
    # Run the enhanced data collection
    collector, ml_data = setup_enhanced_data_collection()