from unittest.mock import AsyncMock, MagicMock

import pytest

from app.models.schemas import ChatMessage, ChatRequest
from app.services.ai_service import AIService


@pytest.fixture
def mock_genai_client(mocker):
    """Mock google.genai.Client."""
    # Patch genai.Client in the ai_service module
    mock_client_class = mocker.patch("app.services.ai_service.genai.Client")
    mock_instance = MagicMock()
    mock_client_class.return_value = mock_instance
    return mock_instance

@pytest.mark.asyncio
async def test_chat_completion_success(mock_genai_client):
    """Test successful chat completion with mocked Gemini (new SDK)."""
    # Setup mocks
    mock_response = MagicMock()
    mock_response.text = "Hello! I am a mocked AI."
    # Mock usage metadata
    mock_response.usage_metadata = MagicMock()
    mock_response.usage_metadata.total_token_count = 10

    # aio client call: await client.aio.models.generate_content
    mock_genai_client.aio.models.generate_content = AsyncMock(return_value=mock_response)

    service = AIService()
    request = ChatRequest(
        model="gemini-2.0-flash",
        messages=[ChatMessage(role="user", content="Hi")]
    )

    # Execute
    response = await service.chat_completion(request)

    # Assert
    assert response.choices[0]["message"]["content"] == "Hello! I am a mocked AI."
    assert response.model == "gemini-2.0-flash"
    mock_genai_client.aio.models.generate_content.assert_called_once()

@pytest.mark.asyncio
async def test_health_check_healthy(mock_genai_client):
    """Test health check when service is healthy."""
    mock_genai_client.models.get.return_value = MagicMock()

    service = AIService()
    is_healthy = await service.health_check()

    assert is_healthy is True
    mock_genai_client.models.get.assert_called_once_with(model=service.model_name)

@pytest.mark.asyncio
async def test_health_check_unhealthy(mock_genai_client):
    """Test health check when service raises exception."""
    mock_genai_client.models.get.side_effect = Exception("API Key Error")

    service = AIService()
    is_healthy = await service.health_check()

    assert is_healthy is False
