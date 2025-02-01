"""Test suite for data synchronization functionality."""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import json
import asyncio
from datetime import datetime
from src.sync.core import DataSync

@pytest.fixture
def mock_config():
    """Create mock configuration for testing."""
    return {
        "db_config": {
            "host": "localhost",
            "port": 5432,
            "user": "test",
            "password": "test",
            "database": "test_db"
        },
        "source_config": {
            "openstates": {
                "api_key": "test_key",
                "base_url": "https://v3.openstates.org"
            }
        }
    }

@pytest.fixture
def mock_openstates_data():
    """Create mock OpenStates API response data."""
    return [
        {
            "name": "John Smith",
            "title": "State Senator",
            "district_id": 1,
            "party": "Independent",
            "email": "john.smith@state.gov",
            "phone": "555-0123",
            "website": "https://smith.gov",
            "source": "openstates",
            "source_id": "123"
        }
    ]

@pytest.fixture
def mock_census_data():
    """Create mock Census TIGER/Line data."""
    return [
        {
            "type": "state_senate",
            "state": "17",
            "code": "SD-1",
            "name": "State Senate District 1",
            "geometry": {
                "type": "MultiPolygon",
                "coordinates": [[[[0, 0], [0, 1], [1, 1], [1, 0], [0, 0]]]]
            }
        }
    ]

@pytest.fixture
def mock_db_pool():
    """Create mock database pool."""
    pool = AsyncMock()
    
    # Mock connection context manager
    conn = AsyncMock()
    pool.acquire.return_value.__aenter__.return_value = conn
    
    # Mock database operations
    conn.execute = AsyncMock()
    conn.fetch = AsyncMock()
    conn.fetchrow = AsyncMock()
    
    return pool

@pytest.mark.asyncio
async def test_fetch_openstates_data(mock_config):
    """Test fetching data from OpenStates API."""
    sync = DataSync(mock_config["db_config"], mock_config["source_config"])
    
    mock_response = MagicMock()
    mock_response.status = 200
    mock_response.json = AsyncMock(return_value=[{"id": 1, "name": "Test Data"}])
    
    mock_session = MagicMock()
    mock_session.get.return_value.__aenter__.return_value = mock_response
    
    with patch('aiohttp.ClientSession', return_value=mock_session):
        data = await sync.fetch_openstates_data()
        assert len(data) == 1
        assert data[0]["name"] == "Test Data"

@pytest.mark.asyncio
async def test_update_districts(mock_config, mock_db_pool, mock_census_data):
    """Test updating district information in database."""
    sync = DataSync(mock_config["db_config"], mock_config["source_config"])
    sync.pool = mock_db_pool
    
    await sync.update_districts(mock_census_data)
    
    # Verify database was called with correct parameters
    conn = mock_db_pool.acquire.return_value.__aenter__.return_value
    assert conn.execute.called
    call_args = conn.execute.call_args_list[0]
    assert "INSERT INTO districts" in call_args[0][0]
    assert call_args[0][1] == "state_senate"  # First parameter should be district_type

@pytest.mark.asyncio
async def test_update_officials(mock_config, mock_db_pool, mock_openstates_data):
    """Test updating official information in database."""
    sync = DataSync(mock_config["db_config"], mock_config["source_config"])
    sync.pool = mock_db_pool
    
    await sync.update_officials(mock_openstates_data)
    
    # Verify database was called with correct parameters
    conn = mock_db_pool.acquire.return_value.__aenter__.return_value
    assert conn.execute.called
    call_args = conn.execute.call_args_list[0]
    assert "INSERT INTO officials" in call_args[0][0]
    assert call_args[0][1] == "John Smith"  # First parameter should be full_name

@pytest.mark.asyncio
async def test_sync_all(mock_config, mock_db_pool):
    """Test full sync process."""
    sync = DataSync(mock_config["db_config"], mock_config["source_config"])
    
    # Mock all the component functions
    sync.init_db_pool = AsyncMock(return_value=mock_db_pool)
    sync.fetch_openstates_data = AsyncMock(return_value=[])
    sync.fetch_census_data = AsyncMock(return_value=[])
    sync.update_districts = AsyncMock()
    sync.update_officials = AsyncMock()
    
    await sync.sync_all()
    
    # Verify all components were called
    assert sync.init_db_pool.called
    assert sync.fetch_openstates_data.called
    assert sync.fetch_census_data.called
    assert sync.update_districts.called
    assert sync.update_officials.called

@pytest.mark.asyncio
async def test_sync_error_handling(mock_config, mock_db_pool):
    """Test error handling during sync."""
    sync = DataSync(mock_config["db_config"], mock_config["source_config"])
    sync.pool = mock_db_pool
    
    # Mock fetch_openstates_data to raise an exception
    sync.fetch_openstates_data = AsyncMock(side_effect=Exception("API Error"))
    
    await sync.sync_all()
    
    # Verify error was recorded in database
    conn = mock_db_pool.acquire.return_value.__aenter__.return_value
    assert conn.execute.called
    call_args = conn.execute.call_args_list[-1]
    assert "UPDATE data_sources" in call_args[0][0]
    assert call_args[0][1] == "error"  # Status should be error

@pytest.mark.asyncio
async def test_data_source_tracking(mock_config, mock_db_pool):
    """Test tracking of data source sync status."""
    sync = DataSync(mock_config["db_config"], mock_config["source_config"])
    sync.pool = mock_db_pool
    
    # Mock successful sync
    sync.fetch_openstates_data = AsyncMock(return_value=[])
    sync.fetch_census_data = AsyncMock(return_value=[])
    sync.update_districts = AsyncMock()
    sync.update_officials = AsyncMock()
    
    await sync.sync_all()
    
    # Verify sync status was updated
    conn = mock_db_pool.acquire.return_value.__aenter__.return_value
    assert conn.execute.called
    
    # Check initial status update
    first_call = conn.execute.call_args_list[0]
    assert "INSERT INTO data_sources" in first_call[0][0]
    assert first_call[0][3] == "running"
    
    # Check final status update
    last_call = conn.execute.call_args_list[-1]
    assert "UPDATE data_sources" in last_call[0][0]
    assert last_call[0][1] == "success"

if __name__ == "__main__":
    pytest.main(["-v", "test_sync.py"])