"""
Real Bitcoin Data Collector
Fetches live Bitcoin data from multiple sources with fallback to mock data.
"""

import asyncio
import logging
import random
import time
import aiohttp
from typing import Dict, Any, List, Callable, Optional

logger = logging.getLogger(__name__)

class RealBitcoinDataCollector:
    """Real Bitcoin data collector with multiple data sources."""
    
    def __init__(self, collection_interval: int = 30):
        self.collection_interval = collection_interval
        self.is_running = False
        self.collection_task = None
        self.callbacks: List[Callable] = []
        
        # Data sources (in priority order)
        self.data_sources = [
            {
                'name': 'coinbase',
                'url': 'https://api.coinbase.com/v2/exchange-rates?currency=BTC',
                'parser': self._parse_coinbase_data
            },
            {
                'name': 'coingecko',
                'url': 'https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd&include_24hr_change=true&include_24hr_vol=true',
                'parser': self._parse_coingecko_data
            },
            {
                'name': 'binance',
                'url': 'https://api.binance.us/api/v3/ticker/24hr?symbol=BTCUSD',
                'parser': self._parse_binance_data
            }
        ]
        
        # Fallback data
        self.last_known_price = 45000
        self.price_history = []
        
        logger.info("Real Bitcoin Data Collector initialized")
    
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
            return
        
        self.is_running = True
        self.collection_task = asyncio.create_task(self._collection_loop())
        logger.info("Real data collection started")
    
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
        """Main collection loop."""
        while self.is_running:
            try:
                await self._collect_real_data()
                await asyncio.sleep(self.collection_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Collection error: {e}")
                await asyncio.sleep(5)
    
    async def _collect_real_data(self):
        """Collect real Bitcoin data from APIs."""
        price_data = None
        
        # Try each data source
        for source in self.data_sources:
            try:
                price_data = await self._fetch_from_source(source)
                if price_data:
                    logger.debug(f"Got real data from {source['name']}: ${price_data['price']}")
                    break
            except Exception as e:
                logger.warning(f"Failed to get data from {source['name']}: {e}")
                continue
        
        # Fallback to mock data if all sources fail
        if not price_data:
            logger.warning("All real data sources failed, using mock data")
            price_data = self._generate_mock_data()
        
        # Update tracking
        self.last_known_price = price_data['price']
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
    
    async def _fetch_from_source(self, source: dict) -> Optional[Dict[str, Any]]:
        """Fetch data from a specific source."""
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
            async with session.get(source['url']) as response:
                if response.status == 200:
                    data = await response.json()
                    return source['parser'](data)
                else:
                    raise Exception(f"HTTP {response.status}")
    
    def _parse_coinbase_data(self, data: dict) -> Dict[str, Any]:
        """Parse Coinbase API response."""
        try:
            rates = data['data']['rates']
            price = float(rates['USD'])
            
            return {
                'timestamp': time.time(),
                'price': price,
                'volume': None,  # Coinbase rates API doesn't include volume
                'change_24h': None,
                'source': 'coinbase'
            }
        except (KeyError, ValueError) as e:
            raise Exception(f"Failed to parse Coinbase data: {e}")
    
    def _parse_coingecko_data(self, data: dict) -> Dict[str, Any]:
        """Parse CoinGecko API response."""
        try:
            bitcoin_data = data['bitcoin']
            price = float(bitcoin_data['usd'])
            change_24h = float(bitcoin_data.get('usd_24h_change', 0))
            volume = float(bitcoin_data.get('usd_24h_vol', 0))
            
            return {
                'timestamp': time.time(),
                'price': price,
                'volume': volume,
                'change_24h': change_24h,
                'source': 'coingecko'
            }
        except (KeyError, ValueError) as e:
            raise Exception(f"Failed to parse CoinGecko data: {e}")
    
    def _parse_binance_data(self, data: dict) -> Dict[str, Any]:
        """Parse Binance API response."""
        try:
            price = float(data['lastPrice'])
            change_24h = float(data['priceChangePercent'])
            volume = float(data['volume'])
            
            return {
                'timestamp': time.time(),
                'price': price,
                'volume': volume,
                'change_24h': change_24h,
                'source': 'binance'
            }
        except (KeyError, ValueError) as e:
            raise Exception(f"Failed to parse Binance data: {e}")
    
    def _generate_mock_data(self) -> Dict[str, Any]:
        """Generate realistic mock data as fallback."""
        # Use last known price with small random movement
        change = random.uniform(-0.01, 0.01)  # ±1% change
        new_price = self.last_known_price * (1 + change)
        new_price = max(30000, min(80000, new_price))  # Reasonable bounds
        
        return {
            'timestamp': time.time(),
            'price': round(new_price, 2),
            'volume': round(random.uniform(1000, 5000), 2),
            'change_24h': round(random.uniform(-5, 5), 2),
            'source': 'mock_fallback'
        }
    
    async def get_current_price(self) -> Dict[str, Any]:
        """Get current price."""
        if not self.price_history:
            await self._collect_real_data()
        
        return self.price_history[-1] if self.price_history else {
            'timestamp': time.time(),
            'price': self.last_known_price,
            'volume': 2500,
            'change_24h': 0.0,
            'source': 'fallback'
        }
    
    async def get_price_history(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get historical data."""
        # For real historical data, you'd typically call another API
        # For now, return recent collected data or generate mock history
        
        if len(self.price_history) >= hours:
            return self.price_history[-hours:]
        
        # Generate mock historical data to fill gaps
        mock_history = []
        current_time = time.time()
        base_price = self.last_known_price
        
        for i in range(hours - len(self.price_history)):
            timestamp = current_time - ((hours - i) * 3600)
            # Generate realistic price movement
            change = random.uniform(-0.02, 0.02)
            price = base_price * (1 + change)
            price = max(30000, min(80000, price))
            
            mock_history.append({
                'timestamp': timestamp,
                'price': round(price, 2),
                'volume': round(random.uniform(1000, 5000), 2),
                'change_24h': round(random.uniform(-5, 5), 2),
                'source': 'mock_historical'
            })
            base_price = price
        
        return mock_history + self.price_history
    
    async def get_historical_ohlc(self, timeframe: str = "1h", limit: int = 100) -> List[Dict[str, Any]]:
        """Get OHLC historical data (would typically use a different API)."""
        # This would typically call a different API endpoint for OHLC data
        # For now, generate mock OHLC from price data
        
        ohlc_data = []
        current_time = time.time()
        base_price = self.last_known_price
        
        for i in range(limit):
            timestamp = current_time - (i * 3600)  # 1 hour intervals
            
            # Generate realistic OHLC
            open_price = base_price
            close_price = open_price * (1 + random.uniform(-0.02, 0.02))
            high_price = max(open_price, close_price) * (1 + random.uniform(0, 0.01))
            low_price = min(open_price, close_price) * (1 - random.uniform(0, 0.01))
            volume = random.uniform(100, 1000)
            
            ohlc_data.append({
                'timestamp': timestamp,
                'open': round(open_price, 2),
                'high': round(high_price, 2),
                'low': round(low_price, 2),
                'close': round(close_price, 2),
                'volume': round(volume, 2),
                'source': 'mock_ohlc'
            })
            
            base_price = close_price
        
        return list(reversed(ohlc_data))  # Chronological order
    
    def get_data_source_status(self) -> Dict[str, Any]:
        """Get status of data sources."""
        return {
            'sources': [source['name'] for source in self.data_sources],
            'last_successful_source': getattr(self, 'last_source', 'unknown'),
            'price_history_count': len(self.price_history),
            'last_price': self.last_known_price,
            'collection_running': self.is_running
        }

# Global instance
_collector = None

def get_data_collector() -> RealBitcoinDataCollector:
    """Get global collector instance."""
    global _collector
    if _collector is None:
        _collector = RealBitcoinDataCollector()
    return _collector