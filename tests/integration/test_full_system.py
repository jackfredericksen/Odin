import pytest
import asyncio
from datetime import datetime

from odin.core.database import Database
from odin.core.data_collector import DataCollector
from odin.strategies import MovingAverageStrategy
from odin.core.models import PriceData

class TestFullSystemIntegration:
    """Integration tests for the complete system."""
    
    @pytest.mark.asyncio
    async def test_data_collection_to_database(self, test_settings):
        """Test data collection and storage pipeline."""
        # Initialize components
        db = Database()
        await db.init()
        
        collector = DataCollector()
        await collector.startup()
        
        try:
            # Create sample price data
            price_data = PriceData(
                timestamp=datetime.utcnow(),
                price=50000.0,
                volume=1000000000.0,
                high=51000.0,
                low=49000.0,
                change_24h=2.5,
                source="test"
            )
            
            # Save to database
            success = await db.save_price_data(price_data)
            assert success
            
            # Retrieve from database
            recent_prices = await db.get_recent_prices(limit=1)
            assert len(recent_prices) == 1
            assert recent_prices[0].price == 50000.0
            
        finally:
            await collector.shutdown()
    
    @pytest.mark.asyncio
    async def test_strategy_with_real_data(self, test_database, sample_price_data):
        """Test strategy execution with real data flow."""
        # Add sample data to database
        await test_database.save_price_data(sample_price_data)
        
        # Add more sample data for strategy calculation
        for i in range(25):  # Enough for MA calculation
            price_data = PriceData(
                timestamp=datetime.utcnow(),
                price=50000.0 + i * 10,  # Trending upward
                volume=1000000000.0,
                high=51000.0 + i * 10,
                low=49000.0 + i * 10,
                change_24h=2.5,
                source="test"
            )
            await test_database.save_price_data(price_data)
        
        # Initialize strategy
        strategy = MovingAverageStrategy(short_window=5, long_window=10)
        await strategy.initialize()
        
        # Test market analysis
        analysis = await strategy.analyze_current_market()
        assert analysis is not None
        assert analysis.current_price > 0
        assert analysis.data_points >= 20
    
    @pytest.mark.asyncio
    async def test_concurrent_data_collection(self, test_database):
        """Test concurrent data collection operations."""
        collectors = []
        
        try:
            # Create multiple collectors
            for _ in range(3):
                collector = DataCollector()
                await collector.startup()
                collectors.append(collector)
            
            # Simulate concurrent collection
            tasks = []
            for collector in collectors:
                # Mock the collect_data method to avoid external API calls
                async def mock_collect():
                    price_data = PriceData(
                        timestamp=datetime.utcnow(),
                        price=50000.0,
                        volume=1000000000.0,
                        high=51000.0,
                        low=49000.0,
                        change_24h=2.5,
                        source="concurrent_test"
                    )
                    await test_database.save_price_data(price_data)
                    return price_data
                
                tasks.append(mock_collect())
            
            # Execute concurrently
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Check results
            assert len(results) == 3
            for result in results:
                assert not isinstance(result, Exception)
            
        finally:
            # Cleanup
            for collector in collectors:
                await collector.shutdown()