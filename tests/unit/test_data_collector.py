import pytest
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime

from odin.core.data_collector import (
    DataCollector, 
    CoinDeskDataSource,
    BlockchainInfoDataSource,
    CoinGeckoDataSource,
    APIClient
)
from odin.core.models import PriceData
from odin.core.exceptions import DataCollectionError, ExternalAPIError

class TestAPIClient:
    """Test APIClient."""
    
    @pytest.mark.asyncio
    async def test_startup_shutdown(self):
        """Test client startup and shutdown."""
        client = APIClient()
        
        # Test startup
        await client.startup()
        assert client.client is not None
        
        # Test shutdown
        await client.shutdown()
        assert client.client is None

class TestCoinDeskDataSource:
    """Test CoinDesk data source."""
    
    @pytest.fixture
    async def client(self):
        client = APIClient()
        await client.startup()
        yield client
        await client.shutdown()
    
    @pytest.fixture
    def data_source(self, client):
        return CoinDeskDataSource(client)
    
    @pytest.mark.asyncio
    async def test_fetch_price_success(self, data_source):
        """Test successful price fetch."""
        mock_response = Mock()
        mock_response.json.return_value = {
            'bpi': {
                'USD': {
                    'rate': '50,000.00'
                }
            }
        }
        
        with patch.object(data_source.client, 'get', return_value=mock_response):
            price_data = await data_source.fetch_price()
            
            assert price_data is not None
            assert isinstance(price_data, PriceData)
            assert price_data.price == 50000.0
            assert price_data.source == "coindesk"
    
    @pytest.mark.asyncio
    async def test_fetch_price_failure(self, data_source):
        """Test price fetch failure."""
        with patch.object(data_source.client, 'get', side_effect=Exception("API Error")):
            price_data = await data_source.fetch_price()
            assert price_data is None

class TestDataCollector:
    """Test DataCollector."""
    
    @pytest.mark.asyncio
    async def test_startup_shutdown(self, test_database):
        """Test collector startup and shutdown."""
        collector = DataCollector()
        
        # Test startup
        await collector.startup()
        assert collector.client.client is not None
        assert collector.database is not None
        assert len(collector.data_sources) > 0
        
        # Test shutdown
        await collector.shutdown()
        assert collector.client.client is None
    
    @pytest.mark.asyncio
    async def test_collect_data_success(self, test_database):
        """Test successful data collection."""
        collector = DataCollector()
        await collector.startup()
        
        # Mock successful data source
        mock_price_data = PriceData(
            timestamp=datetime.utcnow(),
            price=50000.0,
            volume=1000000000.0,
            high=51000.0,
            low=49000.0,
            change_24h=2.5,
            source="test"
        )
        
        with patch.object(collector.data_sources['coindesk'], 'fetch_price', 
                         return_value=mock_price_data):
            result = await collector.collect_data()
            
            assert result is not None
            assert result.price == 50000.0
            assert result.source == "test"
            assert collector.last_successful_source == "coindesk"
        
        await collector.shutdown()
    
    @pytest.mark.asyncio
    async def test_collect_data_all_sources_fail(self, test_database):
        """Test data collection when all sources fail."""
        collector = DataCollector()
        await collector.startup()
        
        # Mock all sources to return None
        for source in collector.data_sources.values():
            with patch.object(source, 'fetch_price', return_value=None):
                pass
        
        with pytest.raises(DataCollectionError):
            await collector.collect_data()
        
        await collector.shutdown()