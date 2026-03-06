# import pytest
# from httpx import AsyncClient, ASGITransport
# from main import app
# from unittest.mock import AsyncMock
# from app.config.settings import settings

# @pytest.fixture
# def mock_report_service(mocker):
#     """Mock the ReportService instance."""
#     return mocker.patch("app.api.v1.clinical.report_service")

# @pytest.mark.asyncio
# async def test_process_report_endpoint_success(mock_report_service):
#     """Test the POST /clinical/process-report endpoint with mocked service and valid API Key."""
#     # Setup mock response from service
#     mock_report_service.process_url_and_save = AsyncMock(return_value={"id": "mock-report-id"})
    
#     async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
#         response = await ac.post(
#             "/api/v1/clinical/process-report", 
#             json={
#                 "file_url": "https://example.com/report.pdf",
#                 "documento_id": "DOC123",
#                 "empresa_id": "EMP1",
#                 "doctor_id": "DOC1",
#                 "fecha_envio": "2024-02-18T12:00:00"
#             },
#             headers={"X-API-KEY": settings.jwt_secret_key}
#         )
    
#     # Assert
#     assert response.status_code == 200
#     assert response.json()["id"] == "mock-report-id"
#     mock_report_service.process_url_and_save.assert_called_once()

# @pytest.mark.asyncio
# async def test_get_report_endpoint_not_found(mock_report_service):
#     """Test the GET /clinical/report/{id} endpoint with valid API Key but nonexistent resource."""
#     # Setup mock: service returns None
#     mock_report_service.get_report = AsyncMock(return_value=None)
    
#     async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
#         response = await ac.get(
#             "/api/v1/clinical/report/nonexistent-id",
#             headers={"X-API-KEY": settings.jwt_secret_key}
#         )
    
#     # Assert
#     assert response.status_code == 404
#     assert response.json()["error"] == "ResourceNotFoundError"
#     assert "not found" in response.json()["message"]
