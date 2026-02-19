import pytest
from httpx import AsyncClient, ASGITransport
from main import app

@pytest.mark.asyncio
async def test_endpoint_unauthorized_without_key():
    """
    SECURITY TEST: Ensure clinical endpoints return 401 if NO API key is provided.
    """
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/clinical/report/any-id")
    
    assert response.status_code == 401
    assert "Missing Certification Key" in response.json()["detail"]

@pytest.mark.asyncio
async def test_endpoint_forbidden_with_invalid_key():
    """
    SECURITY TEST: Ensure clinical endpoints return 403 if WRONG API key is provided.
    """
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get(
            "/api/v1/clinical/report/any-id", 
            headers={"X-API-KEY": "fake_key_123"}
        )
    
    assert response.status_code == 403
    assert "Not a Certified Biotasys Entity" in response.json()["detail"]

@pytest.mark.asyncio
async def test_endpoint_authorized_with_correct_key(mocker):
    """
    SECURITY TEST: Ensure clinical endpoints work if the correct API key is provided.
    """
    # Mock the report service to avoid db calls
    mocker.patch("app.api.v1.clinical.report_service.get_report", return_value={"id": "found"})
    from app.config.settings import settings
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get(
            "/api/v1/clinical/report/any-id", 
            headers={"X-API-KEY": settings.jwt_secret_key}
        )
    
    # It should pass security (404 because report is not real, but NOT 401/403)
    assert response.status_code in [200, 404]
