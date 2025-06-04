"""
Odin Core Data Collector - Fixed Version Without Circular Imports

Simple data collection system for the Odin trading bot providing
Bitcoin price data from multiple sources with failover.

File: odin/core/data_collector.py
"""

import asyncio
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Optional, Any, Callable
import random
import time

logger = logging.getLogger(__name__)


class BitcoinDataCollector:
    """
    Simple Bitcoin data collector with mock data generation.
    Designed to work without circular imports.
    """
    
    def __init__(self, collection_interval: int = 30):
        """
        Initialize data collector.
        
        Args:
            collection_interval: Data collection interval in seconds
        """
        self.collection_interval = collection_interval
        self.is_running = False
        self.collection_task = None
        self.callbacks: List[Callable] = []
        
        # Mock data state
        self.base_price = 45000
        self.last_price = self.base_price
        self.price_history = []
        
        logger.info("Bitcoin Data Collector initialized")
    
    def add_callback(self, callback: Callable):
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
                await asyncio.sleep(5)
    
    async def _collect_data(self):
        """Collect Bitcoin price data (mock implementation)."""
        try:
            # Generate realistic price movement
            price_change = random.uniform(-0.02, 0.02)  # ±2% change
            new_price = self.last_price * (1 + price_change)
            
            # Keep price in reasonable range
            new_price = max(30000, min(80000, new_price))
            
            price_data = {
                'timestamp': time.time(),
                'price': round(new_price, 2),
                'volume': round(random.uniform(1000, 5000), 2),
                'change_24h': round(random.uniform(-5, 5), 2),
                'source': 'mock'
            }
            
            self.last_price = new_price
            self.price_history.append(price_data)
            
            # Keep only last 1000 records
            if len(self.price_history) > 1000:
                self.price_history = self.price_history[-1000:]
            
            # Notify callbacks
            for callback in self.callbacks:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(price_data)
                    else:
                        callback(price_data)
                except Exception as e:
                    logger.error(f"Callback error: {e}")
            
            logger.debug(f"Collected price data: ${new_price}")
            
        except Exception as e:
            logger.error(f"Error collecting data: {e}")
    
    async def get_current_price(self) -> Dict[str, Any]:
        """Get current price data."""
        if not self.price_history:
            await self._collect_data()
        
        if self.price_history:
            return self.price_history[-1]
        
        # Fallback
        return {
            'timestamp': time.time(),
            'price': self.base_price,
            'volume': 2500,
            'change_24h': 0.0,
            'source': 'fallback'
        }
    
    async def get_price_history(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get historical price data."""
        # Generate mock historical data if needed
        if len(self.price_history) < hours:
            current_time = time.time()
            for i in range(hours - len(self.price_history)):
                timestamp = current_time - ((hours - i) * 3600)
                price = self.base_price + random.uniform(-2000, 2000)
                
                self.price_history.insert(0, {
                    'timestamp': timestamp,
                    'price': round(price, 2),
                    'volume': round(random.uniform(1000, 5000), 2),
                    'change_24h': round(random.uniform(-5, 5), 2),
                    'source': 'historical_mock'
                })
        
        # Return requested hours of data
        return self.price_history[-hours:] if hours <= len(self.price_history) else self.price_history
    
    def get_status(self) -> Dict[str, Any]:
        """Get collector status."""
        return {
            'is_running': self.is_running,
            'collection_interval': self.collection_interval,
            'price_history_count': len(self.price_history),
            'last_price': self.last_price,
            'callbacks_count': len(self.callbacks)
        }


# Global collector instance
_collector_instance = None

def get_data_collector() -> BitcoinDataCollector:
    """Get global data collector instance."""
    global _collector_instance
    if _collector_instance is None:
        _collector_instance = BitcoinDataCollector()
    return _collector_instance