from unittest.mock import AsyncMock, MagicMock
import pytest
from pydantic import ValidationError
from app.services.ai_service import AIService
from app.core.exceptions import AIError

@pytest.fixture
def mock_genai_client(mocker):
    return mocker.patch("app.services.ai_service.genai.Client")

@pytest.mark.asyncio
async def test_ai_service_handles_invalid_json_structure(mock_genai_client):
    """
    RIGOR TEST: Ensure AIError is raised if Gemini returns a JSON 
    that fails Pydantic validation (e.g. missing required clinical fields).
    """
    # Mock response to return junk that won't match MicrobiotaReport
    mock_response = MagicMock()
    # Simulate a pydantic validation error during parsing
    # In the real SDK, response.parsed would raise this if it's not valid
    type(mock_response).parsed = PropertyMock(side_effect=ValidationError.from_exception_data(
        title="MicrobiotaReport", line_errors=[]
    ))
    
    mock_genai_client.return_value.aio.models.generate_content = AsyncMock(return_value=mock_response)
    
    service = AIService()
    
    with pytest.raises(AIError) as exc:
        await service.analyze_microbiota_document(b"fake", "application/pdf")
    
    assert "Gemini Extraction Engine failed" in exc.value.message

from unittest.mock import PropertyMock # Needed for side_effect on property
