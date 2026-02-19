from unittest.mock import AsyncMock, MagicMock
import pytest
from app.services.ai_service import AIService
from app.models.schemas import MicrobiotaReport, MicrobiotaInterpretation

@pytest.fixture
def mock_genai_client(mocker):
    """Mock google.genai.Client."""
    mock_client_class = mocker.patch("app.services.ai_service.genai.Client")
    mock_instance = MagicMock()
    mock_client_class.return_value = mock_instance
    return mock_instance

@pytest.mark.asyncio
async def test_analyze_microbiota_document_success(mock_genai_client):
    """Test successful extraction using the Dual Engine's extractor."""
    # Setup mock response
    mock_response = MagicMock()
    mock_response.parsed = MagicMock(spec=MicrobiotaReport)
    
    # Mock aio client call: await client.aio.models.generate_content
    mock_genai_client.aio.models.generate_content = AsyncMock(return_value=mock_response)

    service = AIService()
    
    # Execute
    result = await service.analyze_microbiota_document(b"fake_pdf_content", "application/pdf")

    # Assert
    assert result == mock_response.parsed
    mock_genai_client.aio.models.generate_content.assert_called_once()
    # Verify it used the extractor model
    args, kwargs = mock_genai_client.aio.models.generate_content.call_args
    assert kwargs['model'] == service.extractor_model

@pytest.mark.asyncio
async def test_interpret_microbiota_data_success(mock_genai_client):
    """Test successful interpretation using the Dual Engine's interpreter."""
    mock_response = MagicMock()
    mock_response.parsed = MagicMock(spec=MicrobiotaInterpretation)
    
    mock_genai_client.aio.models.generate_content = AsyncMock(return_value=mock_response)

    service = AIService()
    mock_report = MagicMock(spec=MicrobiotaReport)
    mock_report.model_dump_json.return_value = "{}"

    # Execute
    result = await service.interpret_microbiota_data(mock_report)

    # Assert
    assert result == mock_response.parsed
    # Verify it used the interpreter model
    args, kwargs = mock_genai_client.aio.models.generate_content.call_args
    assert kwargs['model'] == service.interpreter_model

@pytest.mark.asyncio
async def test_health_check_healthy(mock_genai_client):
    """Test health check when Gemini is reachable."""
    # Note: health_check uses aio.models.get
    mock_genai_client.aio.models.get = AsyncMock(return_value=MagicMock())

    service = AIService()
    is_healthy = await service.health_check()

    assert is_healthy is True
    mock_genai_client.aio.models.get.assert_called_once_with(model=service.extractor_model)
