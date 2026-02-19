from unittest.mock import AsyncMock, MagicMock
import pytest
import httpx
from app.services.report_service import ReportService
from app.models.schemas import AnalysisRequest

@pytest.fixture
def service(mocker):
    # Setup service with mocked dependencies
    mock_ai = MagicMock()
    mocker.patch("app.services.report_service.ReportRepository")
    return ReportService(ai=mock_ai)

@pytest.mark.asyncio
async def test_pro_resilience_on_download_failure(service, respx_mock):
    """
    RIGOR TEST: Ensure the engine fails early and safely if 
    the external PDF storage is unreachable (e.g. 403 or 404).
    """
    # 1. SETUP - Use Factory to generate 'super valid' dummy clinical data
    file_url = "https://biotasys.com/v1/private_report_secret.pdf"
    
    # 2. MOCK THE EXTERNAL WORLD (FOR FAILURE)
    respx_mock.get(file_url).mock(
        return_value=httpx.Response(403, content=b"Access Denied: Permission error")
    )
    
    # 3. SETUP THE AI (TO ENSURE IT IS NOT CALLED)
    service.ai.analyze_microbiota_document = AsyncMock()

    # 4. EXECUTE & ASSERT FAILURE
    analysis_request = AnalysisRequest(
        file_url=file_url,
        documento_id="FAIL-01",
        empresa_id="CLINIC_A",
        doctor_id="DR_STRANGE",
        fecha_envio="2026-02-18T10:00:00"
    )

    with pytest.raises(Exception) as exc:
        await service.process_url_and_save(analysis_request)

    # 5. RIGOROUS ASSERTIONS
    assert "Source file unreachable" in str(exc.value.details)
    
    # CRITICAL: Gemini AI MUST NOT be called if download fails (save tokens/money)
    service.ai.analyze_microbiota_document.assert_not_called()
    service.repository.save_report.assert_not_called()
