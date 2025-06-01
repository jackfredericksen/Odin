import asyncio
import pytest
import tempfile
from pathlib import Path

from odin.config import Settings
from odin.core.database import Database
from odin.core.data_collector import DataCollector

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def test_settings():
    """Test settings with temporary database."""
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "test.db"
        
        yield Settings(
            database_url=f"sqlite:///{db_path}",
            data_update_interval=1,
            log_level="DEBUG",
            api_port=5001,  # Different port for testing
        )

@pytest.fixture
async def test_database(test_settings):
    """Test database instance."""
    # Mock the settings
    import odin.config
    original_settings = odin.config.settings
    odin.config.settings = test_settings
    
    try:
        db = Database()
        await db.init()
        yield db
    finally:
        # Restore original settings
        odin.config.settings = original_settings

@pytest.fixture
async def test_data_collector(test_database):
    """Test data collector instance."""
    collector = DataCollector()
    await collector.startup()
    yield collector
    await collector.shutdown()

@pytest.fixture
def sample_price_data():
    """Sample price data for testing."""
    from datetime import datetime
    from odin.core.models import PriceData
    
    return PriceData(
        timestamp=datetime.utcnow(),
        price=50000.0,
        volume=1000000000.0,
        high=51000.0,
        low=49000.0,
        change_24h=2.5,
        source="test"
    )
