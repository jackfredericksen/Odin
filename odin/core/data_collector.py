"""
Odin Core Data Collector - Real-time Bitcoin Data Collection with WebSocket Broadcasting
Clean version without circular imports.

Enhanced data collector that fetches Bitcoin price data from multiple sources
and broadcasts updates to WebSocket clients in real-time.

File: odin/core/data_collector.py
Author: Odin Development Team
License: MIT
"""

import asyncio
import aiohttp
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
import time
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Database imports
try:
    from .database import get_database
except ImportError:
    get_database = None

# WebSocket broadcasting imports - no circular imports
WEBSOCKET_AVAILABLE = False
broadcast_price_update = None
broadcast_system_alert = None
ws_manager = None

try:
    # Use absolute import path - most reliable
    from odin.api.routes.websocket import (
        broadcast_price_update, 
        broadcast_system_alert,
        manager as ws_manager
    )
    WEBSOCKET_AVAILABLE = True
    logger.info("WebSocket module loaded successfully")
except ImportError as e:
    # Create dummy functions if WebSocket is not available
    logger.warning(f"WebSocket module not available: {e}")
    
    async def broadcast_price_update(*args, **kwargs):
        """Dummy function when WebSocket is not available."""
        pass
    
    async def broadcast_system_alert(*args, **kwargs):
        """Dummy function when WebSocket is not available."""
        pass
    
    class DummyManager:
        def get_connection_count(self):
            return 0
    
    ws_manager = DummyManager()

@dataclass
class PriceData:
    """Bitcoin price data structure."""
    timestamp: datetime
    price: float
    volume: Optional[float] = None
    market_cap: Optional[float] = None
    source: str = "unknown"
    high_24h: Optional[float] = None
    low_24h: Optional[float] = None
    change_24h: Optional[float] = None

class DataCollector:
    """
    Real-time Bitcoin data collector with WebSocket broadcasting.
    
    Fetches price data from multiple sources and broadcasts updates
    to connected WebSocket clients.
    """
    
    def __init__(self, update_interval: int = 30):
        """
        Initialize data collector.
        
        Args:
            update_interval: Seconds between data updates
        """
        self.update_interval = update_interval
        self.session: Optional[aiohttp.ClientSession] = None
        self.database = None
        self.is_running = False
        self.collection_task: Optional[asyncio.Task] = None
        
        # Data sources configuration
        self.sources = {
            "coinbase": {
                "url": "https://api.coinbase.com/v2/exchange-rates?currency=BTC",
                "parser": self._parse_coinbase_data
            },
            "coingecko": {
                "url": "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd&include_24hr_change=true&include_24hr_vol=true",
                "parser": self._parse_coingecko_data
            },
            "binance": {
                "url": "https://api.binance.com/api/v3/ticker/24hr?symbol=BTCUSDT",
                "parser": self._parse_binance_data
            }
        }
        
        # Statistics tracking
        self.stats = {
            "total_updates": 0,
            "successful_updates": 0,
            "failed_updates": 0,
            "last_update": None,
            "last_price": None,
            "sources_status": {}
        }
        
        # Rate limiting
        self.last_request_time = {}
        self.min_request_interval = 1.0  # Minimum 1 second between requests per source
        
        logger.info(f"Data collector initialized with {update_interval}s update interval")
    
    async def start(self):
        """Start the data collection process."""
        if self.is_running:
            logger.warning("Data collector is already running")
            return
        
        try:
            # Initialize HTTP session
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=10),
                headers={
                    "User-Agent": "Odin-Trading-Bot/2.0"
                }
            )
            
            # Initialize database connection
            if get_database:
                try:
                    self.database = get_database()
                    logger.info("Database connection initialized")
                except Exception as e:
                    logger.warning(f"Database initialization failed: {e}")
            
            # Start collection task
            self.is_running = True
            self.collection_task = asyncio.create_task(self._collection_loop())
            
            logger.info("🚀 Data collector started")
            
            # Broadcast system alert if WebSocket is available
            if WEBSOCKET_AVAILABLE and broadcast_system_alert:
                await broadcast_system_alert(
                    "Data Collector Started",
                    "Real-time Bitcoin data collection is now active",
                    "success"
                )
            
        except Exception as e:
            logger.error(f"Failed to start data collector: {e}")
            raise
    
    async def stop(self):
        """Stop the data collection process."""
        if not self.is_running:
            return
        
        logger.info("🔄 Stopping data collector...")
        self.is_running = False
        
        # Cancel collection task
        if self.collection_task:
            self.collection_task.cancel()
            try:
                await self.collection_task
            except asyncio.CancelledError:
                pass
        
        # Close HTTP session
        if self.session:
            await self.session.close()
        
        logger.info("✅ Data collector stopped")
        
        # Broadcast system alert if WebSocket is available
        if WEBSOCKET_AVAILABLE and broadcast_system_alert:
            await broadcast_system_alert(
                "Data Collector Stopped",
                "Real-time Bitcoin data collection has been stopped",
                "warning"
            )
    
    async def _collection_loop(self):
        """Main data collection loop."""
        while self.is_running:
            try:
                start_time = time.time()
                
                # Collect data from all sources
                price_data = await self._collect_from_all_sources()
                
                if price_data:
                    # Save to database
                    if self.database:
                        await self._save_to_database(price_data)
                    
                    # Broadcast to WebSocket clients
                    await self._broadcast_price_update(price_data)
                    
                    # Update statistics
                    self.stats["successful_updates"] += 1
                    self.stats["last_update"] = datetime.now(timezone.utc)
                    self.stats["last_price"] = price_data.price
                    
                    logger.debug(f"Price update: ${price_data.price:.2f} from {price_data.source}")
                else:
                    self.stats["failed_updates"] += 1
                    logger.warning("Failed to collect price data from any source")
                
                self.stats["total_updates"] += 1
                
                # Calculate sleep time to maintain consistent interval
                elapsed = time.time() - start_time
                sleep_time = max(0, self.update_interval - elapsed)
                
                if sleep_time > 0:
                    await asyncio.sleep(sleep_time)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in collection loop: {e}")
                self.stats["failed_updates"] += 1
                await asyncio.sleep(5)  # Wait before retrying
    
    async def _collect_from_all_sources(self) -> Optional[PriceData]:
        """Collect data from all configured sources and return the best result."""
        tasks = []
        
        for source_name, source_config in self.sources.items():
            task = asyncio.create_task(
                self._collect_from_source(source_name, source_config)
            )
            tasks.append(task)
        
        # Wait for all tasks to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Find the best result (most complete data)
        best_result = None
        best_score = 0
        
        for i, result in enumerate(results):
            source_name = list(self.sources.keys())[i]
            
            if isinstance(result, Exception):
                logger.warning(f"Source {source_name} failed: {result}")
                self.stats["sources_status"][source_name] = "error"
                continue
            
            if result is None:
                self.stats["sources_status"][source_name] = "no_data"
                continue
            
            # Score based on data completeness
            score = self._score_price_data(result)
            
            if score > best_score:
                best_result = result
                best_score = score
            
            self.stats["sources_status"][source_name] = "success"
        
        return best_result
    
    async def _collect_from_source(self, source_name: str, source_config: Dict) -> Optional[PriceData]:
        """Collect data from a single source."""
        try:
            # Rate limiting check
            current_time = time.time()
            last_request = self.last_request_time.get(source_name, 0)
            
            if current_time - last_request < self.min_request_interval:
                await asyncio.sleep(self.min_request_interval - (current_time - last_request))
            
            # Make HTTP request
            async with self.session.get(source_config["url"]) as response:
                if response.status == 200:
                    data = await response.json()
                    self.last_request_time[source_name] = time.time()
                    
                    # Parse data using source-specific parser
                    return source_config["parser"](data, source_name)
                else:
                    logger.warning(f"Source {source_name} returned status {response.status}")
                    return None
        
        except Exception as e:
            logger.error(f"Error collecting from {source_name}: {e}")
            return None
    
    def _parse_coinbase_data(self, data: Dict, source: str) -> Optional[PriceData]:
        """Parse Coinbase API response."""
        try:
            rates = data.get("data", {}).get("rates", {})
            usd_rate = float(rates.get("USD", 0))
            
            if usd_rate > 0:
                # Coinbase gives BTC->USD rate, so we need the inverse
                price = 1.0 / usd_rate
                
                return PriceData(
                    timestamp=datetime.now(timezone.utc),
                    price=price,
                    source=source
                )
        except Exception as e:
            logger.error(f"Error parsing Coinbase data: {e}")
        
        return None
    
    def _parse_coingecko_data(self, data: Dict, source: str) -> Optional[PriceData]:
        """Parse CoinGecko API response."""
        try:
            bitcoin_data = data.get("bitcoin", {})
            price = bitcoin_data.get("usd")
            change_24h = bitcoin_data.get("usd_24h_change")
            
            if price:
                return PriceData(
                    timestamp=datetime.now(timezone.utc),
                    price=float(price),
                    change_24h=float(change_24h) if change_24h else None,
                    source=source
                )
        except Exception as e:
            logger.error(f"Error parsing CoinGecko data: {e}")
        
        return None
    
    def _parse_binance_data(self, data: Dict, source: str) -> Optional[PriceData]:
        """Parse Binance API response."""
        try:
            price = data.get("lastPrice")
            volume = data.get("volume")
            high_24h = data.get("highPrice")
            low_24h = data.get("lowPrice")
            change_24h = data.get("priceChangePercent")
            
            if price:
                return PriceData(
                    timestamp=datetime.now(timezone.utc),
                    price=float(price),
                    volume=float(volume) if volume else None,
                    high_24h=float(high_24h) if high_24h else None,
                    low_24h=float(low_24h) if low_24h else None,
                    change_24h=float(change_24h) if change_24h else None,
                    source=source
                )
        except Exception as e:
            logger.error(f"Error parsing Binance data: {e}")
        
        return None
    
    def _score_price_data(self, price_data: PriceData) -> int:
        """Score price data based on completeness."""
        score = 1  # Base score for having a price
        
        if price_data.volume is not None:
            score += 1
        if price_data.change_24h is not None:
            score += 1
        if price_data.high_24h is not None:
            score += 1
        if price_data.low_24h is not None:
            score += 1
        
        return score
    
    async def _save_to_database(self, price_data: PriceData):
        """Save price data to database."""
        if not self.database:
            return
        
        try:
            success = self.database.add_price_data(
                timestamp=price_data.timestamp,
                price=price_data.price,
                volume=price_data.volume,
                market_cap=price_data.market_cap
            )
            
            if success:
                logger.debug(f"Saved price data: ${price_data.price:.2f} from {price_data.source}")
            else:
                logger.warning("Failed to save price data to database")
                
        except Exception as e:
            logger.error(f"Database save error: {e}")
    
    async def _broadcast_price_update(self, price_data: PriceData):
        """Broadcast price update to WebSocket clients."""
        if not WEBSOCKET_AVAILABLE or not broadcast_price_update:
            return
        
        # Only broadcast if there are connected clients
        if ws_manager and ws_manager.get_connection_count() == 0:
            return
        
        try:
            # Prepare broadcast data
            broadcast_data = {
                "price": price_data.price,
                "volume": price_data.volume,
                "change_24h": price_data.change_24h,
                "high_24h": price_data.high_24h,
                "low_24h": price_data.low_24h,
                "source": price_data.source,
                "timestamp": price_data.timestamp.timestamp(),
                "market_cap": price_data.price * 19700000 if price_data.price else None  # Approximate BTC supply
            }
            
            await broadcast_price_update(broadcast_data)
            logger.debug(f"Broadcasted price update: ${price_data.price:.2f} to {ws_manager.get_connection_count()} clients")
            
        except Exception as e:
            logger.error(f"WebSocket broadcast error: {e}")
    
    async def get_current_price(self) -> Optional[Dict[str, Any]]:
        """Get the most recent price data."""
        if self.database:
            try:
                price_data = self.database.get_current_price()
                if price_data:
                    return {
                        "price": price_data["price"],
                        "timestamp": price_data["timestamp"],
                        "volume": price_data.get("volume"),
                        "market_cap": price_data.get("market_cap")
                    }
            except Exception as e:
                logger.error(f"Error getting current price from database: {e}")
        
        # Fallback: return last collected price
        if self.stats["last_price"]:
            return {
                "price": self.stats["last_price"],
                "timestamp": self.stats["last_update"].timestamp() if self.stats["last_update"] else time.time(),
                "source": "collector_cache"
            }
        
        return None
    
    async def get_price_history(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get historical price data."""
        if not self.database:
            return []
        
        try:
            price_history = self.database.get_recent_prices(limit=hours)
            return [
                {
                    "timestamp": item["timestamp"],
                    "price": item["price"],
                    "volume": item.get("volume")
                }
                for item in price_history
            ]
        except Exception as e:
            logger.error(f"Error getting price history: {e}")
            return []
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get data collector statistics."""
        return {
            "is_running": self.is_running,
            "update_interval": self.update_interval,
            "total_updates": self.stats["total_updates"],
            "successful_updates": self.stats["successful_updates"],
            "failed_updates": self.stats["failed_updates"],
            "success_rate": (
                (self.stats["successful_updates"] / self.stats["total_updates"] * 100)
                if self.stats["total_updates"] > 0 else 0
            ),
            "last_update": self.stats["last_update"].isoformat() if self.stats["last_update"] else None,
            "last_price": self.stats["last_price"],
            "sources_status": self.stats["sources_status"],
            "websocket_available": WEBSOCKET_AVAILABLE,
            "websocket_clients": ws_manager.get_connection_count() if ws_manager else 0,
            "database_connected": self.database is not None
        }
    
    async def force_update(self) -> Optional[PriceData]:
        """Force an immediate data collection update."""
        logger.info("Force updating price data...")
        
        try:
            price_data = await self._collect_from_all_sources()
            
            if price_data:
                # Save to database
                if self.database:
                    await self._save_to_database(price_data)
                
                # Broadcast to WebSocket clients
                await self._broadcast_price_update(price_data)
                
                # Update statistics
                self.stats["successful_updates"] += 1
                self.stats["last_update"] = datetime.now(timezone.utc)
                self.stats["last_price"] = price_data.price
                
                logger.info(f"Force update successful: ${price_data.price:.2f} from {price_data.source}")
                return price_data
            else:
                logger.warning("Force update failed: no data collected")
                self.stats["failed_updates"] += 1
                return None
                
        except Exception as e:
            logger.error(f"Force update error: {e}")
            self.stats["failed_updates"] += 1
            return None
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on data collector."""
        health_status = {
            "status": "healthy" if self.is_running else "stopped",
            "is_running": self.is_running,
            "session_active": self.session is not None and not self.session.closed,
            "database_connected": self.database is not None,
            "websocket_available": WEBSOCKET_AVAILABLE,
            "last_update_ago": None,
            "sources_health": {}
        }
        
        # Check last update recency
        if self.stats["last_update"]:
            time_since_update = datetime.now(timezone.utc) - self.stats["last_update"]
            health_status["last_update_ago"] = int(time_since_update.total_seconds())
            
            # Mark as unhealthy if no updates for too long
            if time_since_update > timedelta(minutes=5):
                health_status["status"] = "stale"
        
        # Check source health
        for source_name in self.sources.keys():
            source_status = self.stats["sources_status"].get(source_name, "unknown")
            health_status["sources_health"][source_name] = source_status
        
        # Overall health determination
        if health_status["status"] == "healthy":
            failed_sources = sum(1 for status in health_status["sources_health"].values() 
                               if status == "error")
            if failed_sources >= len(self.sources) / 2:  # More than half failed
                health_status["status"] = "degraded"
        
        return health_status
    
    async def restart(self):
        """Restart the data collector."""
        logger.info("Restarting data collector...")
        
        await self.stop()
        await asyncio.sleep(2)  # Brief pause
        await self.start()
        
        logger.info("Data collector restarted successfully")
    
    async def update_sources(self, new_sources: Dict[str, Dict]):
        """Update data sources configuration."""
        logger.info("Updating data sources configuration...")
        self.sources.update(new_sources)
        logger.info(f"Now using {len(self.sources)} data sources: {list(self.sources.keys())}")
    
    async def set_update_interval(self, interval: int):
        """Change the update interval."""
        if interval < 5:
            raise ValueError("Update interval cannot be less than 5 seconds")
        
        self.update_interval = interval
        logger.info(f"Update interval changed to {interval} seconds")
        
        # If running, restart with new interval
        if self.is_running:
            await self.restart()

# Convenience functions for external use
async def start_data_collection(update_interval: int = 30) -> DataCollector:
    """Start data collection with specified interval."""
    collector = DataCollector(update_interval)
    await collector.start()
    return collector

async def get_live_bitcoin_price() -> Optional[Dict[str, Any]]:
    """Get live Bitcoin price (one-time fetch)."""
    collector = DataCollector()
    
    try:
        # Initialize session temporarily
        collector.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10))
        
        # Collect data
        price_data = await collector._collect_from_all_sources()
        
        if price_data:
            return {
                "price": price_data.price,
                "volume": price_data.volume,
                "change_24h": price_data.change_24h,
                "high_24h": price_data.high_24h,
                "low_24h": price_data.low_24h,
                "source": price_data.source,
                "timestamp": price_data.timestamp.timestamp()
            }
        
        return None
        
    finally:
        # Cleanup session
        if collector.session:
            await collector.session.close()

# Global collector instance for singleton pattern
_global_collector: Optional[DataCollector] = None

async def get_global_collector() -> DataCollector:
    """Get or create global data collector instance."""
    global _global_collector
    
    if _global_collector is None:
        _global_collector = DataCollector()
        await _global_collector.start()
    
    return _global_collector

async def stop_global_collector():
    """Stop global data collector instance."""
    global _global_collector
    
    if _global_collector:
        await _global_collector.stop()
        _global_collector = None

# Export main components
__all__ = [
    "DataCollector",
    "PriceData", 
    "start_data_collection",
    "get_live_bitcoin_price",
    "get_global_collector",
    "stop_global_collector"
]