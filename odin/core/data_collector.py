"""
Odin Core Data Collector - Real-time Bitcoin Data Collection and Processing (FIXED VERSION)

Comprehensive data collection system for the Odin trading bot providing
real-time Bitcoin price data, technical indicators, and market information
from multiple sources with failover and validation.
"""

import asyncio
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Optional, Any, Callable, Set
from decimal import Decimal
import aiohttp
import websockets
import pandas as pd
import numpy as np
from statistics import mean, stdev
import random

# FIXED: Use correct imports
from .database import DatabaseManager
from .models import PriceData, OHLCData, MarketDepth, DataSourceStatus, DataCollectionResult
from .exceptions import (
    DataCollectorException, 
    MarketDataException, 
    DataValidationException, 
    DataSourceException
)

logger = logging.getLogger(__name__)


class DataSource:
    """Base class for data sources."""
    
    def __init__(self, name: str, priority: int = 1, enabled: bool = True):
        self.name = name
        self.priority = priority  # Lower = higher priority
        self.enabled = enabled
        self.last_update = None
        self.error_count = 0
        self.max_errors = 5
        
    async def get_price(self) -> Optional[PriceData]:
        """Get current price data."""
        raise NotImplementedError
    
    async def get_ohlc(self, timeframe: str = "1h", limit: int = 100) -> List[OHLCData]:
        """Get OHLC data."""
        raise NotImplementedError
    
    async def get_depth(self) -> Optional[MarketDepth]:
        """Get market depth data."""
        raise NotImplementedError
    
    def is_healthy(self) -> bool:
        """Check if data source is healthy."""
        if not self.enabled:
            return False
        
        # Check error count
        if self.error_count >= self.max_errors:
            return False
        
        # Check last update time (should be within 5 minutes)
        if self.last_update:
            time_since_update = datetime.now(timezone.utc) - self.last_update
            if time_since_update > timedelta(minutes=5):
                return False
        
        return True
    
    def record_success(self):
        """Record successful data fetch."""
        self.last_update = datetime.now(timezone.utc)
        self.error_count = max(0, self.error_count - 1)  # Gradually reduce error count
    
    def record_error(self):
        """Record data fetch error."""
        self.error_count += 1
        logger.warning(f"Data source {self.name} error count: {self.error_count}")


class MockDataSource(DataSource):
    """Mock data source for testing and fallback."""
    
    def __init__(self, name: str = "mock", priority: int = 99):
        super().__init__(name, priority)
        self.base_price = 45000.0
        self.last_price = self.base_price
    
    async def get_price(self) -> Optional[PriceData]:
        """Get mock price data."""
        try:
            # Simulate price movement
            change = random.uniform(-100, 100)
            self.last_price = max(20000, min(80000, self.last_price + change))
            
            price_data = PriceData(
                symbol="BTC-USD",
                price=round(self.last_price, 2),
                volume=round(random.uniform(800, 1200), 2),
                bid=round(self.last_price * 0.999, 2),
                ask=round(self.last_price * 1.001, 2),
                source=self.name,
                timestamp=datetime.now(timezone.utc)
            )
            
            self.record_success()
            return price_data
            
        except Exception as e:
            self.record_error()
            logger.error(f"Mock price fetch error: {e}")
            raise DataSourceException(self.name, str(e))
    
    async def get_ohlc(self, timeframe: str = "1h", limit: int = 100) -> List[OHLCData]:
        """Get mock OHLC data."""
        try:
            ohlc_data = []
            current_time = datetime.now(timezone.utc)
            price = self.last_price
            
            # Parse timeframe to minutes
            timeframe_minutes = {
                "1m": 1, "5m": 5, "15m": 15, "30m": 30,
                "1h": 60, "4h": 240, "1d": 1440
            }.get(timeframe, 60)
            
            for i in range(limit):
                timestamp = current_time - timedelta(minutes=i * timeframe_minutes)
                
                # Generate OHLC data
                open_price = price + random.uniform(-50, 50)
                high_price = open_price + random.uniform(0, 100)
                low_price = open_price - random.uniform(0, 100)
                close_price = open_price + random.uniform(-75, 75)
                volume = random.uniform(100, 500)
                
                ohlc = OHLCData(
                    symbol="BTC-USD",
                    timeframe=timeframe,
                    timestamp=timestamp,
                    open=round(open_price, 2),
                    high=round(high_price, 2),
                    low=round(low_price, 2),
                    close=round(close_price, 2),
                    volume=round(volume, 2)
                )
                ohlc_data.append(ohlc)
                
                # Update price for next iteration
                price = close_price
            
            self.record_success()
            return sorted(ohlc_data, key=lambda x: x.timestamp)
            
        except Exception as e:
            self.record_error()
            logger.error(f"Mock OHLC fetch error: {e}")
            raise DataSourceException(self.name, str(e))
    
    async def get_depth(self) -> Optional[MarketDepth]:
        """Get mock market depth data."""
        try:
            # Generate mock order book
            mid_price = self.last_price
            
            bids = []
            asks = []
            
            # Generate bids (below mid price)
            for i in range(10):
                price = mid_price - (i + 1) * 10
                size = random.uniform(0.1, 2.0)
                bids.append([price, size])
            
            # Generate asks (above mid price)
            for i in range(10):
                price = mid_price + (i + 1) * 10
                size = random.uniform(0.1, 2.0)
                asks.append([price, size])
            
            depth = MarketDepth(
                symbol="BTC-USD",
                bids=bids,
                asks=asks,
                timestamp=datetime.now(timezone.utc),
                source=self.name
            )
            
            self.record_success()
            return depth
            
        except Exception as e:
            self.record_error()
            logger.error(f"Mock depth fetch error: {e}")
            raise DataSourceException(self.name, str(e))


class CoinbaseDataSource(DataSource):
    """Coinbase data source."""
    
    def __init__(self):
        super().__init__("coinbase", priority=1)
        self.base_url = "https://api.exchange.coinbase.com"
        self.ws_url = "wss://ws-feed.exchange.coinbase.com"
    
    async def get_price(self) -> Optional[PriceData]:
        """Get current price from Coinbase."""
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                async with session.get(f"{self.base_url}/products/BTC-USD/ticker") as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        price_data = PriceData(
                            symbol="BTC-USD",
                            price=float(data["price"]),
                            volume=float(data["volume"]),
                            bid=float(data["bid"]) if data.get("bid") else None,
                            ask=float(data["ask"]) if data.get("ask") else None,
                            source="coinbase",
                            timestamp=datetime.now(timezone.utc)
                        )
                        
                        self.record_success()
                        return price_data
                    else:
                        raise DataSourceException(self.name, f"API error: {response.status}")
                        
        except Exception as e:
            self.record_error()
            logger.error(f"Coinbase price fetch error: {e}")
            raise DataSourceException(self.name, str(e))
    
    async def get_ohlc(self, timeframe: str = "1h", limit: int = 100) -> List[OHLCData]:
        """Get OHLC data from Coinbase."""
        try:
            # Map timeframe to Coinbase granularity
            granularity_map = {
                "1m": 60, "5m": 300, "15m": 900, "30m": 1800,
                "1h": 3600, "4h": 14400, "1d": 86400
            }
            
            granularity = granularity_map.get(timeframe, 3600)
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:
                url = f"{self.base_url}/products/BTC-USD/candles"
                params = {
                    "granularity": granularity,
                    "limit": min(limit, 300)  # Coinbase limit
                }
                
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        ohlc_data = []
                        for candle in data:
                            timestamp, low, high, open_price, close, volume = candle
                            
                            ohlc = OHLCData(
                                symbol="BTC-USD",
                                timeframe=timeframe,
                                timestamp=datetime.fromtimestamp(timestamp, tz=timezone.utc),
                                open=float(open_price),
                                high=float(high),
                                low=float(low),
                                close=float(close),
                                volume=float(volume)
                            )
                            ohlc_data.append(ohlc)
                        
                        self.record_success()
                        return sorted(ohlc_data, key=lambda x: x.timestamp)
                    else:
                        raise DataSourceException(self.name, f"OHLC API error: {response.status}")
                        
        except Exception as e:
            self.record_error()
            logger.error(f"Coinbase OHLC fetch error: {e}")
            raise DataSourceException(self.name, str(e))
    
    async def get_depth(self) -> Optional[MarketDepth]:
        """Get market depth from Coinbase."""
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                async with session.get(f"{self.base_url}/products/BTC-USD/book?level=2") as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        bids = [[float(price), float(size)] for price, size, _ in data["bids"]]
                        asks = [[float(price), float(size)] for price, size, _ in data["asks"]]
                        
                        depth = MarketDepth(
                            symbol="BTC-USD",
                            bids=bids,
                            asks=asks,
                            timestamp=datetime.now(timezone.utc),
                            source="coinbase"
                        )
                        
                        self.record_success()
                        return depth
                    else:
                        raise DataSourceException(self.name, f"Depth API error: {response.status}")
                        
        except Exception as e:
            self.record_error()
            logger.error(f"Coinbase depth fetch error: {e}")
            raise DataSourceException(self.name, str(e))


class TechnicalIndicators:
    """Technical indicators calculator."""
    
    @staticmethod
    def sma(prices: List[float], period: int) -> List[float]:
        """Simple Moving Average."""
        if len(prices) < period:
            return []
        
        sma_values = []
        for i in range(period - 1, len(prices)):
            sma = mean(prices[i - period + 1:i + 1])
            sma_values.append(sma)
        
        return sma_values
    
    @staticmethod
    def ema(prices: List[float], period: int) -> List[float]:
        """Exponential Moving Average."""
        if len(prices) < period:
            return []
        
        multiplier = 2 / (period + 1)
        ema_values = []
        
        # First EMA value is SMA
        first_ema = mean(prices[:period])
        ema_values.append(first_ema)
        
        for i in range(period, len(prices)):
            ema = (prices[i] * multiplier) + (ema_values[-1] * (1 - multiplier))
            ema_values.append(ema)
        
        return ema_values
    
    @staticmethod
    def rsi(prices: List[float], period: int = 14) -> List[float]:
        """Relative Strength Index."""
        if len(prices) < period + 1:
            return []
        
        price_changes = [prices[i] - prices[i-1] for i in range(1, len(prices))]
        gains = [change if change > 0 else 0 for change in price_changes]
        losses = [-change if change < 0 else 0 for change in price_changes]
        
        rsi_values = []
        
        # First RSI calculation
        avg_gain = mean(gains[:period])
        avg_loss = mean(losses[:period])
        
        if avg_loss == 0:
            rsi_values.append(100)
        else:
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
            rsi_values.append(rsi)
        
        # Subsequent RSI calculations
        for i in range(period, len(gains)):
            avg_gain = (avg_gain * (period - 1) + gains[i]) / period
            avg_loss = (avg_loss * (period - 1) + losses[i]) / period
            
            if avg_loss == 0:
                rsi_values.append(100)
            else:
                rs = avg_gain / avg_loss
                rsi = 100 - (100 / (1 + rs))
                rsi_values.append(rsi)
        
        return rsi_values
    
    @staticmethod
    def macd(prices: List[float], fast: int = 12, slow: int = 26, signal: int = 9) -> Dict[str, List[float]]:
        """MACD indicator."""
        if len(prices) < slow:
            return {"macd": [], "signal": [], "histogram": []}
        
        ema_fast = TechnicalIndicators.ema(prices, fast)
        ema_slow = TechnicalIndicators.ema(prices, slow)
        
        # Align EMAs (slow EMA starts later)
        start_index = slow - fast
        ema_fast_aligned = ema_fast[start_index:]
        
        macd_line = [fast_val - slow_val for fast_val, slow_val in zip(ema_fast_aligned, ema_slow)]
        signal_line = TechnicalIndicators.ema(macd_line, signal)
        
        # Calculate histogram
        histogram = []
        signal_start = len(macd_line) - len(signal_line)
        for i in range(len(signal_line)):
            histogram.append(macd_line[signal_start + i] - signal_line[i])
        
        return {
            "macd": macd_line,
            "signal": signal_line,
            "histogram": histogram
        }
    
    @staticmethod
    def bollinger_bands(prices: List[float], period: int = 20, std_dev: float = 2) -> Dict[str, List[float]]:
        """Bollinger Bands."""
        if len(prices) < period:
            return {"upper": [], "middle": [], "lower": []}
        
        middle_band = TechnicalIndicators.sma(prices, period)
        
        upper_band = []
        lower_band = []
        
        for i in range(period - 1, len(prices)):
            price_slice = prices[i - period + 1:i + 1]
            std = stdev(price_slice)
            sma = middle_band[i - period + 1]
            
            upper_band.append(sma + (std_dev * std))
            lower_band.append(sma - (std_dev * std))
        
        return {
            "upper": upper_band,
            "middle": middle_band,
            "lower": lower_band
        }


class DataCollector:
    """Main data collection and processing engine."""
    
    def __init__(self, database: DatabaseManager, collection_interval: int = 30):
        """
        Initialize data collector.
        
        Args:
            database: Database instance
            collection_interval: Data collection interval in seconds
        """
        self.database = database
        self.collection_interval = collection_interval
        
        # Data sources
        self.data_sources: List[DataSource] = [
            CoinbaseDataSource(),
            MockDataSource(),  # Fallback source
        ]
        
        # Sort by priority
        self.data_sources.sort(key=lambda x: x.priority)
        
        # Collection state
        self.is_running = False
        self.collection_task = None
        self.callbacks: List[Callable] = []
        
        # Data cache
        self.latest_price: Optional[PriceData] = None
        self.price_history: List[Dict] = []
        
        logger.info(f"Data collector initialized with {len(self.data_sources)} sources")
    
    def add_callback(self, callback: Callable[[PriceData], None]):
        """Add callback for new price data."""
        self.callbacks.append(callback)
    
    def remove_callback(self, callback: Callable):
        """Remove price data callback."""
        if callback in self.callbacks:
            self.callbacks.remove(callback)
    
    async def start_collection(self):
        """Start data collection."""
        if self.is_running:
            logger.warning("Data collection already running")
            return
        
        self.is_running = True
        self.collection_task = asyncio.create_task(self._collection_loop())
        logger.info("Data collection started")
    
    async def stop_collection(self):
        """Stop data collection."""
        if not self.is_running:
            return
        
        self.is_running = False
        if self.collection_task:
            self.collection_task.cancel()
            try:
                await self.collection_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Data collection stopped")
    
    async def _collection_loop(self):
        """Main data collection loop."""
        while self.is_running:
            try:
                await self._collect_data()
                await asyncio.sleep(self.collection_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Data collection error: {e}")
                await asyncio.sleep(5)  # Brief pause before retry
    
    async def _collect_data(self):
        """Collect data from sources."""
        price_data = None
        
        # Try data sources in priority order
        for source in self.data_sources:
            if not source.is_healthy():
                logger.debug(f"Skipping unhealthy source: {source.name}")
                continue
            
            try:
                price_data = await source.get_price()
                if price_data:
                    logger.debug(f"Got price data from {source.name}: ${price_data.price}")
                    break
            except Exception as e:
                logger.warning(f"Failed to get data from {source.name}: {e}")
                continue
        
        if not price_data:
            raise MarketDataException("All data sources failed")
        
        # Validate data
        await self._validate_price_data(price_data)
        
        # Calculate technical indicators
        await self._calculate_indicators(price_data)
        
        # Save to database (if available)
        try:
            self.database.add_price_data(
                price_data.timestamp,
                price_data.price,
                price_data.volume
            )
        except Exception as e:
            logger.error(f"Failed to save price data: {e}")
        
        # Update cache
        self.latest_price = price_data
        
        # Notify callbacks
        for callback in self.callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(price_data)
                else:
                    callback(price_data)
            except Exception as e:
                logger.error(f"Callback error: {e}")
    
    async def _validate_price_data(self, price_data: PriceData):
        """Validate price data."""
        # Basic validation
        if price_data.price <= 0:
            raise DataValidationException("Invalid price: must be positive")
        
        if price_data.volume and price_data.volume < 0:
            raise DataValidationException("Invalid volume: must be non-negative")
        
        # Price range validation (Bitcoin price should be reasonable)
        if price_data.price < 1000 or price_data.price > 1000000:
            raise DataValidationException(f"Price out of reasonable range: ${price_data.price}")
        
        # Bid/ask validation
        if price_data.bid and price_data.ask:
            if price_data.bid >= price_data.ask:
                raise DataValidationException("Invalid bid/ask: bid >= ask")
            
            spread_pct = (price_data.ask - price_data.bid) / price_data.price
            if spread_pct > 0.01:  # 1% spread threshold
                logger.warning(f"Large spread detected: {spread_pct:.2%}")
        
        # Compare with recent prices for anomaly detection
        if self.latest_price:
            time_diff = (price_data.timestamp - self.latest_price.timestamp).total_seconds()
            if time_diff > 0:  # Only check if newer
                price_change = abs(price_data.price - self.latest_price.price) / self.latest_price.price
                
                # Allow larger changes for longer time differences
                max_change = 0.05 + (time_diff / 3600) * 0.02  # 5% + 2% per hour
                
                if price_change > max_change:
                    logger.warning(
                        f"Large price change detected: {price_change:.2%} "
                        f"from ${self.latest_price.price} to ${price_data.price}"
                    )
    
    async def _calculate_indicators(self, price_data: PriceData):
        """Calculate technical indicators."""
        try:
            # Get recent price history from database
            recent_prices_data = self.database.get_recent_prices(limit=200)
            
            if len(recent_prices_data) < 20:
                logger.debug("Insufficient price history for indicators")
                return
            
            # Extract prices
            prices = [float(p['price']) for p in recent_prices_data]
            prices.append(price_data.price)  # Add current price
            
            # Calculate indicators
            if len(prices) >= 5:
                sma_5 = TechnicalIndicators.sma(prices, 5)
                if sma_5:
                    price_data.sma_5 = sma_5[-1]
            
            if len(prices) >= 20:
                sma_20 = TechnicalIndicators.sma(prices, 20)
                if sma_20:
                    price_data.sma_20 = sma_20[-1]
                
                bb = TechnicalIndicators.bollinger_bands(prices, 20)
                if bb["upper"]:
                    price_data.bb_upper = bb["upper"][-1]
                    price_data.bb_lower = bb["lower"][-1]
            
            if len(prices) >= 12:
                ema_12 = TechnicalIndicators.ema(prices, 12)
                if ema_12:
                    price_data.ema_12 = ema_12[-1]
            
            if len(prices) >= 26:
                ema_26 = TechnicalIndicators.ema(prices, 26)
                if ema_26:
                    price_data.ema_26 = ema_26[-1]
                
                macd_data = TechnicalIndicators.macd(prices, 12, 26, 9)
                if macd_data["macd"]:
                    price_data.macd = macd_data["macd"][-1]
                if macd_data["signal"]:
                    price_data.macd_signal = macd_data["signal"][-1]
            
            if len(prices) >= 14:
                rsi = TechnicalIndicators.rsi(prices, 14)
                if rsi:
                    price_data.rsi = rsi[-1]
            
            logger.debug(f"Calculated indicators for price: ${price_data.price}")
            
        except Exception as e:
            logger.error(f"Error calculating indicators: {e}")
    
    async def get_current_price(self, force_refresh: bool = False) -> Optional[PriceData]:
        """Get current price data."""
        if force_refresh or not self.latest_price:
            await self._collect_data()
        
        return self.latest_price
    
    async def get_ohlc_data(
        self, 
        timeframe: str = "1h", 
        limit: int = 100
    ) -> List[OHLCData]:
        """Get OHLC data from sources."""
        for source in self.data_sources:
            if not source.is_healthy():
                continue
            
            try:
                ohlc_data = await source.get_ohlc(timeframe, limit)
                if ohlc_data:
                    # Calculate indicators for OHLC data
                    await self._calculate_ohlc_indicators(ohlc_data)
                    return ohlc_data
            except Exception as e:
                logger.warning(f"Failed to get OHLC from {source.name}: {e}")
                continue
        
        raise MarketDataException("Failed to get OHLC data from all sources")
    
    async def _calculate_ohlc_indicators(self, ohlc_data: List[OHLCData]):
        """Calculate indicators for OHLC data."""
        if len(ohlc_data) < 20:
            return
        
        # Extract close prices
        close_prices = [float(candle.close) for candle in ohlc_data]
        
        # Calculate indicators
        sma_20 = TechnicalIndicators.sma(close_prices, 20)
        ema_12 = TechnicalIndicators.ema(close_prices, 12)
        ema_26 = TechnicalIndicators.ema(close_prices, 26)
        rsi = TechnicalIndicators.rsi(close_prices, 14)
        macd_data = TechnicalIndicators.macd(close_prices, 12, 26, 9)
        bb = TechnicalIndicators.bollinger_bands(close_prices, 20)
        
        # Add indicators to candles
        for i, candle in enumerate(ohlc_data):
            if i < len(sma_20):
                candle.sma_20 = sma_20[i]
            
            if i < len(ema_12):
                candle.ema_12 = ema_12[i]
            
            if i < len(ema_26):
                candle.ema_26 = ema_26[i]
            
            if i < len(rsi):
                candle.rsi = rsi[i]
            
            macd_index = i - (len(close_prices) - len(macd_data["macd"]))
            if macd_index >= 0 and macd_index < len(macd_data["macd"]):
                candle.macd = macd_data["macd"][macd_index]
            
            signal_index = i - (len(close_prices) - len(macd_data["signal"]))
            if signal_index >= 0 and signal_index < len(macd_data["signal"]):
                candle.macd_signal = macd_data["signal"][signal_index]
            
            bb_index = i - (len(close_prices) - len(bb["upper"]))
            if bb_index >= 0 and bb_index < len(bb["upper"]):
                candle.bb_upper = bb["upper"][bb_index]
                candle.bb_lower = bb["lower"][bb_index]
    
    async def get_market_depth(self) -> Optional[MarketDepth]:
        """Get market depth data."""
        for source in self.data_sources:
            if not source.is_healthy():
                continue
            
            try:
                depth = await source.get_depth()
                if depth:
                    return depth
            except Exception as e:
                logger.warning(f"Failed to get depth from {source.name}: {e}")
                continue
        
        raise MarketDataException("Failed to get market depth from all sources")
    
    def get_source_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all data sources."""
        status = {}
        for source in self.data_sources:
            status[source.name] = {
                "enabled": source.enabled,
                "healthy": source.is_healthy(),
                "priority": source.priority,
                "error_count": source.error_count,
                "last_update": source.last_update.isoformat() if source.last_update else None
            }
        return status
    
    async def health_check(self) -> Dict[str, Any]:
        """Comprehensive health check."""
        healthy_sources = sum(1 for source in self.data_sources if source.is_healthy())
        
        return {
            "is_running": self.is_running,
            "healthy_sources": healthy_sources,
            "total_sources": len(self.data_sources),
            "latest_price": self.latest_price.price if self.latest_price else None,
            "last_collection": self.latest_price.timestamp.isoformat() if self.latest_price else None,
            "collection_interval": self.collection_interval,
            "source_status": self.get_source_status()
        }