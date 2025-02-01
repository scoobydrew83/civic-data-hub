"""Test suite for Civic Data Hub API."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import json
from src.api.main import app

client = TestClient(app)

@pytest.fixture
def mock_db_pool():
    """Mock database pool for testing."""
    async def mock_fetch(*args, **kwargs):
        if "districts" in args[0]:
            return [
                {
                    "id": 1,
                    "name": "Test District",
                    "district_type": "state_house",
                    "state_fips": "17",
                    "district_code": "HD-1",
                    "geometry": json.dumps({
                        "type": "MultiPolygon",
                        "coordinates": [[[[0, 0], [0, 1], [1, 1], [1, 0], [0, 0]]]]
                    })
                }
            ]
        elif "officials" in args[0]:
            return [
                {
                    "id": 1,
                    "full_name": "John Doe",
                    "office_title": "State Representative",
                    "party": "Independent",
                    "email": "john.doe@state.gov",
                    "phone": "555-0123",
                    "website": "https://doe.gov"
                }
            ]
        return []

    pool_mock = MagicMock()
    conn_mock = MagicMock()
    conn_mock.fetch = mock_fetch
    conn_mock.fetchrow = mock_fetch
    pool_mock.acquire.return_value.__aenter__.return_value = conn_mock
    return pool_mock

@pytest.mark.asyncio
async def test_lookup_representatives(mock_db_pool):
    """Test the representative lookup endpoint."""
    with patch('src.api.main.geocode_address', return_value=(40.7128, -74.0060)):
        app.state.pool = mock_db_pool
        response = client.get("/api/v1/lookup?address=123 Main St, New York, NY")
        assert response.status_code == 200
        data = response.json()
        assert "districts" in data
        assert "officials" in data
        assert len(data["districts"]) > 0
        assert len(data["officials"]) > 0
        assert data["districts"][0]["name"] == "Test District"
        assert data["officials"][0]["full_name"] == "John Doe"

@pytest.mark.asyncio
async def test_get_district_boundaries(mock_db_pool):
    """Test the district boundaries endpoint."""
    app.state.pool = mock_db_pool
    response = client.get("/api/v1/districts?lat=40.7128&lng=-74.0060")
    assert response.status_code == 200
    data = response.json()
    assert data["type"] == "FeatureCollection"
    assert len(data["features"]) > 0
    assert data["features"][0]["properties"]["name"] == "Test District"
    assert "geometry" in data["features"][0]

@pytest.mark.asyncio
async def test_bulk_lookup(mock_db_pool):
    """Test the bulk lookup endpoint."""
    with patch('src.api.main.geocode_address', return_value=(40.7128, -74.0060)):
        app.state.pool = mock_db_pool
        response = client.get("/api/v1/bulk-lookup?addresses=123 Main St, NY&addresses=456 Elm St, NY")
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert len(data["results"]) == 2
        for result in data["results"]:
            assert "address" in result
            assert "result" in result or "error" in result

@pytest.mark.asyncio
async def test_get_official_details(mock_db_pool):
    """Test the official details endpoint."""
    app.state.pool = mock_db_pool
    response = client.get("/api/v1/official/1")
    assert response.status_code == 200
    data = response.json()
    assert "official" in data
    assert "offices" in data
    assert data["official"]["full_name"] == "John Doe"

@pytest.mark.asyncio
async def test_invalid_address():
    """Test handling of invalid addresses."""
    with patch('src.api.main.geocode_address', side_effect=Exception("Invalid address")):
        response = client.get("/api/v1/lookup?address=Invalid Address")
        assert response.status_code == 408 or response.status_code == 404

@pytest.mark.asyncio
async def test_no_districts_found(mock_db_pool):
    """Test handling when no districts are found."""
    async def mock_fetch_empty(*args, **kwargs):
        return []

    pool_mock = MagicMock()
    conn_mock = MagicMock()
    conn_mock.fetch = mock_fetch_empty
    conn_mock.fetchrow = mock_fetch_empty
    pool_mock.acquire.return_value.__aenter__.return_value = conn_mock

    with patch('src.api.main.geocode_address', return_value=(0, 0)):
        app.state.pool = pool_mock
        response = client.get("/api/v1/lookup?address=123 Main St")
        assert response.status_code == 404
        assert "No districts found" in response.json()["detail"]