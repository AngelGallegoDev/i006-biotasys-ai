from unittest.mock import AsyncMock, MagicMock
import pytest
import httpx
from app.services.report_service import ReportService
from app.models.schemas import AnalysisRequest, MicrobiotaReport, MicrobiotaInterpretation

@pytest.fixture
def mock_ai_service():
    """Mock the AI Service."""
    return MagicMock()

@pytest.fixture
def service(mock_ai_service, mocker):
    """ReportService instance with mocked AI and Repository."""
    # Patch ReportRepository to avoid DB calls
    mocker.patch("app.services.report_service.ReportRepository")
    return ReportService(ai=mock_ai_service)

@pytest.mark.asyncio
async def test_process_url_and_save_success(service, mock_ai_service, respx_mock):
    """Test the full pipeline orchestrator with mocked steps."""
    # Mock Step 1: Download
    file_url = "https://biotasys.com/report.pdf"
    respx_mock.get(file_url).mock(return_value=httpx.Response(200, content=b"fake-pdf"))

    # Mock Step 2 & 3: AI Engine
    mock_report = MagicMock(spec=MicrobiotaReport)
    mock_interpretation = MagicMock(spec=MicrobiotaInterpretation)
    
    service.ai.analyze_microbiota_document = AsyncMock(return_value=mock_report)
    service.ai.interpret_microbiota_data = AsyncMock(return_value=mock_interpretation)
    
    # Mock Step 4: Repository
    service.repository.save_report = AsyncMock(return_value={"id": "saved-id"})

    request = AnalysisRequest(
        file_url=file_url,
        documento_id="DOC1",
        empresa_id="EMP1",
        doctor_id="DOC1",
        fecha_envio="2024-02-18T12:00:00"
    )

    # Execute
    result = await service.process_url_and_save(request)

    # Assert
    assert result["engine_status"] == "success"
    assert result["report_id"] == "saved-id"
    service.ai.analyze_microbiota_document.assert_called_once()
    service.ai.interpret_microbiota_data.assert_called_once()
    service.repository.save_report.assert_called_once()
