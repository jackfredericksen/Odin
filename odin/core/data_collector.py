"""Data collection for Odin trading bot."""

import asyncio
from datetime import datetime
from typing import Dict, List, Optional

import httpx
import structlog

from odin.config import get_settings
from odin.core.database import get_database
from odin.core.exceptions import DataCollectionError, ExternalAPIError
from odin.core.models import PriceData

logger = structlog.get_logger(__name__)


class APIClient:
    """HTTP client for external APIs."""
    
    def __init__(self) -> None:
        """Initialize API client."""
        self.client: Optional[httpx.AsyncClient] = None
        
    async def startup(self) -> None:
        """Start the HTTP client."""
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(30.0),
            limits=httpx.Limits(max_keepalive_connections=5, max_connections=10),
            headers={
                "User-Agent": "Odin-Trading-Bot/2.0.0",
                "Accept": "application/json",
            }
        )
    
    async def shutdown(self) -> None:
        """Shutdown the HTTP client."""
        if self.client:
            await self.client.aclose()
            self.client = None
    
    async def get(self, url: str, **kwargs) -> httpx.Response:
        """Make GET request."""
        if not self.client:
            raise RuntimeError("HTTP client not initialized")
        
        try:
            response = await self.client.get(url, **kwargs)
            response.raise_for_status()
            return response
        except httpx.HTTPStatusError as e:
            raise ExternalAPIError(
                message=f"HTTP error {e.response.status_code}",
                api_name=url,
                status_code=e.response.status_code,
                response_text=e.response.text,
            )
        except httpx.RequestError as e:
            raise ExternalAPIError(
                message=f"Request error: {e}",
                api_name=url,
            )


class DataSource:
    """Base class for data sources."""
    
    def __init__(self, client: APIClient) -> None:
        """Initialize data source."""
        self.client = client
        self.name = self.__class__.__name__.lower().replace('datasource', '')
    
    async def fetch_price(self) -> Optional[PriceData]:
        """Fetch price data from source."""
        raise NotImplementedError


class CoinDeskDataSource(DataSource):
    """CoinDesk API data source."""
    
    async def fetch_price(self) -> Optional[PriceData]:
        """Fetch price from CoinDesk API."""
        try:
            settings = get_settings()
            response = await self.client.get(settings.coindesk_api_url)
            data = response.json()
            
            price = float(data['bpi']['USD']['rate'].replace(',', ''))
            
            # CoinDesk provides limited data, estimate others
            price_data = PriceData(
                timestamp=datetime.utcnow(),
                price=price,
                volume=None,  # Not available
                high=price * 1.02,  # Estimated
                low=price * 0.98,   # Estimated
                change_24h=None,    # Not available
                source="coindesk",
            )
            
            logger.debug("CoinDesk price fetched", price=price)
            return price_data
            
        except Exception as e:
            logger.warning("CoinDesk API failed", error=str(e))
            return None


class BlockchainInfoDataSource(DataSource):
    """Blockchain.info API data source."""
    
    async def fetch_price(self) -> Optional[PriceData]:
        """Fetch price from Blockchain.info API."""
        try:
            settings = get_settings()
            response = await self.client.get(settings.blockchain_api_url)
            data = response.json()
            
            usd_data = data['USD']
            price = float(usd_data['last'])
            
            price_data = PriceData(
                timestamp=datetime.utcnow(),
                price=price,
                volume=None,  # Not available
                high=price * 1.02,  # Estimated
                low=price * 0.98,   # Estimated
                change_24h=None,    # Not available
                source="blockchain_info",
            )
            
            logger.debug("Blockchain.info price fetched", price=price)
            return price_data
            
        except Exception as e:
            logger.warning("Blockchain.info API failed", error=str(e))
            return None


class CoinGeckoDataSource(DataSource):
    """CoinGecko API data source."""
    
    async def fetch_price(self) -> Optional[PriceData]:
        """Fetch price from CoinGecko API."""
        try:
            settings = get_settings()
            url = f"{settings.coingecko_api_url}/simple/price"
            params = {
                'ids': 'bitcoin',
                'vs_currencies': 'usd',
                'include_24hr_change': 'true',
                'include_24hr_vol': 'true',
            }
            
            response = await self.client.get(url, params=params)
            data = response.json()
            
            btc_data = data['bitcoin']
            price = float(btc_data['usd'])
            change_24h = float(btc_data.get('usd_24h_change', 0))
            volume_24h = btc_data.get('usd_24h_vol')
            
            price_data = PriceData(
                timestamp=datetime.utcnow(),
                price=price,
                volume=volume_24h,
                high=price * (1 + abs(change_24h) / 100 / 2),  # Estimated
                low=price * (1 - abs(change_24h) / 100 / 2),   # Estimated
                change_24h=change_24h,
                source="coingecko",
            )
            
            logger.debug("CoinGecko price fetched", 
                        price=price, 
                        change_24h=change_24h)
            return price_data
            
        except Exception as e:
            logger.warning("CoinGecko API failed", error=str(e))
            return None


class DataCollector:
    """Main data collector with multi-source fallback."""
    
    def __init__(self) -> None:
        """Initialize data collector."""
        self.settings = get_settings()
        self.client = APIClient()
        self.database: Optional[object] = None
        self.data_sources: Dict[str, DataSource] = {}
        self.last_successful_source: Optional[str] = None
        self.collection_count = 0
        
    async def startup(self) -> None:
        """Start the data collector."""
        await self.client.startup()
        self.database = await get_database()
        
        # Initialize data sources
        self.data_sources = {
            "coindesk": CoinDeskDataSource(self.client),
            "blockchain_info": BlockchainInfoDataSource(self.client),
            "coingecko": CoinGeckoDataSource(self.client),
        }
        
        logger.info("Data collector started", 
                   sources=list(self.data_sources.keys()))
    
    async def shutdown(self) -> None:
        """Shutdown the data collector."""
        await self.client.shutdown()
        logger.info("Data collector shutdown")
    
    async def collect_data(self) -> Optional[PriceData]:
        """Collect price data with fallback sources."""
        source_order = self.settings.data_sources.copy()
        
        # Try last successful source first if available
        if (self.last_successful_source and 
            self.last_successful_source in source_order):
            source_order.remove(self.last_successful_source)
            source_order.insert(0, self.last_successful_source)
        
        for source_name in source_order:
            if source_name not in self.data_sources:
                logger.warning("Unknown data source", source=source_name)
                continue
            
            try:
                source = self.data_sources[source_name]
                price_data = await source.fetch_price()
                
                if price_data:
                    # Save to database
                    if self.database:
                        await self.database.save_price_data(price_data)
                    
                    self.last_successful_source = source_name
                    self.collection_count += 1
                    
                    logger.info("Price data collected",
                              price=price_data.price,
                              source=source_name,
                              collection_count=self.collection_count)
                    
                    return price_data
                
            except Exception as e:
                logger.warning("Data source failed",
                             source=source_name,
                             error=str(e))
                continue
        
        # All sources failed
        logger.error("All data sources failed")
        raise DataCollectionError("Failed to collect data from any source")
    
    async def get_latest_price(self) -> Optional[PriceData]:
        """Get the latest price from database."""
        if not self.database:
            return None
        
        try:
            recent_prices = await self.database.get_recent_prices(limit=1)
            return recent_prices[0] if recent_prices else None
        except Exception as e:
            logger.error("Failed to get latest price", error=str(e))
            return None
    
    async def get_collection_stats(self) -> Dict[str, any]:
        """Get data collection statistics."""
        if not self.database:
            return {}
        
        try:
            db_stats = await self.database.get_data_stats()
            return {
                **db_stats,
                "collection_count": self.collection_count,
                "last_successful_source": self.last_successful_source,
                "available_sources": list(self.data_sources.keys()),
                "configured_sources": self.settings.data_sources,
            }
        except Exception as e:
            logger.error("Failed to get collection stats", error=str(e))
            return {
                "collection_count": self.collection_count,
                "last_successful_source": self.last_successful_source,
                "error": str(e),
            }