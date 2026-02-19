from unittest.mock import AsyncMock, MagicMock

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)

def test_health_check(mocker):
    """Test the health check endpoint with mocked dependencies."""
    # Mock AI Service
    # Note: Import inside the endpoint requires patching the full path where it's used
    mock_ai = mocker.patch("app.api.v1.health.ai_service")
    mock_ai.health_check = AsyncMock(return_value=True)

    # Mock Supabase
    mock_db = mocker.patch("app.api.v1.health.supabase")
    mock_db.table.return_value.select.return_value.limit.return_value.execute.return_value = MagicMock()

    response = client.get("/api/v1/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["database"]["connected"] is True
    assert data["ai_service"]["connected"] is True
