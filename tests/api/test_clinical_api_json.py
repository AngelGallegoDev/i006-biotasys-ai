import pytest
from httpx import AsyncClient, ASGITransport
from main import app
from unittest.mock import AsyncMock
from app.config.settings import settings

@pytest.fixture
def mock_report_service(mocker):
    """Mock the ReportService instance."""
    return mocker.patch("app.api.v1.clinical.report_service")

@pytest.mark.asyncio
async def test_process_report_json_endpoint_success(mock_report_service):
    """Test the POST /clinical/process-report-json endpoint with mocked service and valid API Key."""
    # Setup mock response from service
    mock_report_service.process_json_and_save = AsyncMock(return_value={"id": "mock-report-id"})

    # Example raw_json payload (simulating microbiota data)
    raw_json = {
        "metadata": {
            "study_code": "TEST001",
            "patient_id": "PAT123",
            "sex": "F",
            "age": 30,
            "nutritionist": "Dr. Smith"
        },
        "sequencing": {
            "technology": "16S rRNA",
            "total_reads": 100000
        },
        "diversity": {
            "shannon_index": 3.5,
            "simpson_index": 0.95,
            "observed_otus": 150
        },
        "taxonomy": {
            "phyla": [
                {"name": "Firmicutes", "abundance": 45.0},
                {"name": "Bacteroidetes", "abundance": 35.0}
            ],
            "firmicutes_bacteroidetes_ratio": 1.29
        }
    }

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post(
            "/api/v1/clinical/process-report-json",
            json=raw_json,
            headers={"X-API-KEY": settings.jwt_secret_key}
        )

    # Assert
    assert response.status_code == 200
    assert response.json()["id"] == "mock-report-id"
    mock_report_service.process_json_and_save.assert_called_once()

@pytest.mark.asyncio
async def test_get_report_endpoint_not_found(mock_report_service):
    """Test the GET /clinical/report/{id} endpoint with valid API Key but nonexistent resource."""
    # Setup mock: service returns None
    mock_report_service.get_report = AsyncMock(return_value=None)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get(
            "/api/v1/clinical/report/nonexistent-id",
            headers={"X-API-KEY": settings.jwt_secret_key}
        )

    # Assert
    assert response.status_code == 404
    assert response.json()["error"] == "ResourceNotFoundError"
    assert "not found" in response.json()["message"]