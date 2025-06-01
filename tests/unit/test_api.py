import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

from odin.api.app import create_app
from odin.core.models import PriceData
from datetime import datetime

@pytest.fixture
def client():
    """Test client for API."""
    app = create_app()
    return TestClient(app)

class TestHealthEndpoints:
    """Test health check endpoints."""
    
    def test_health_check(self, client):
        """Test main health check endpoint."""
        with patch('odin.api.dependencies.get_database') as mock_db, \
             patch('odin.api.dependencies.get_data_collector') as mock_collector:
            
            # Mock database
            mock_db.return_value.get_data_stats = AsyncMock(return_value={
                'total_records': 1000,
                'newest_record': '2024-01-01T00:00:00'
            })
            
            # Mock data collector
            mock_collector.return_value.get_collection_stats = AsyncMock(return_value={
                'collection_count': 100
            })
            
            response = client.get("/api/health")
            assert response.status_code == 200
            
            data = response.json()
            assert data['success'] is True
            assert 'uptime' in data['data']
            assert 'version' in data['data']

class TestDataEndpoints:
    """Test data endpoints."""
    
    def test_get_current_data(self, client):
        """Test current data endpoint."""
        mock_price = PriceData(
            timestamp=datetime.utcnow(),
            price=50000.0,
            volume=1000000000.0,
            high=51000.0,
            low=49000.0,
            change_24h=2.5,
            source="test"
        )
        
        with patch('odin.api.dependencies.get_database') as mock_db, \
             patch('odin.api.dependencies.get_data_collector') as mock_collector:
            
            mock_collector.return_value.get_latest_price = AsyncMock(return_value=mock_price)
            mock_db.return_value.get_data_stats = AsyncMock(return_value={'total_records': 1000})
            
            response = client.get("/api/current")
            assert response.status_code == 200
            
            data = response.json()
            assert data['success'] is True
            assert data['data']['price'] == 50000.0
            assert data['data']['source'] == "test"
    
    def test_get_price_history(self, client):
        """Test price history endpoint."""
        import pandas as pd
        
        # Create mock historical data
        mock_df = pd.DataFrame({
            'price': [50000, 50100, 50200],
            'volume': [1000000, 1000100, 1000200],
            'source': ['test', 'test', 'test']
        }, index=pd.date_range('2024-01-01', periods=3, freq='H'))
        
        with patch('odin.api.dependencies.get_database') as mock_db:
            mock_db.return_value.get_price_history = AsyncMock(return_value=mock_df)
            
            response = client.get("/api/history/24")
            assert response.status_code == 200
            
            data = response.json()
            assert data['success'] is True
            assert len(data['data']['history']) == 3
            assert data['data']['count'] == 3
    
    def test_invalid_hours_parameter(self, client):
        """Test validation of hours parameter."""
        response = client.get("/api/history/200")  # Too high
        assert response.status_code == 422  # Validation error
        
        response = client.get("/api/history/0")  # Too low
        assert response.status_code == 422