import pytest
from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)

def test_health_check_endpoint():
    """Test /health endpoint returns HTTP 200 and healthy status."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "FinAnalyst" in data["service"]

def test_history_list_endpoint():
    """Test GET /api/v1/history endpoint returns a list."""
    response = client.get("/api/v1/history?limit=5")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

def test_history_detail_not_found():
    """Test GET /api/v1/history/999999 returns 404 for non-existent ID."""
    response = client.get("/api/v1/history/999999")
    assert response.status_code == 404
    data = response.json()
    assert "not found" in data["detail"].lower()

def test_analyze_empty_ticker_validation():
    """Test POST /api/v1/analyze with empty ticker returns HTTP 400."""
    payload = {
        "ticker": "   ",
        "market": "VN",
        "analysis_mode": "full"
    }
    response = client.post("/api/v1/analyze", data=payload)
    assert response.status_code == 400
    data = response.json()
    assert "mã cổ phiếu" in data["detail"].lower() or "ticker" in data["detail"].lower()
