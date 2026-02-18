"""AI service for Gemini integration using the modern google-genai SDK."""

import time
import uuid
from typing import List

from google import genai
from google.genai import types

from app.config.settings import settings
from app.core.logging import get_logger
from app.core.security import mask_api_key
from app.models.schemas import ChatRequest, ChatResponse, ModelInfo

logger = get_logger(__name__)


class AIService:
    """Service for interacting with Google Gemini API via the new google-genai SDK."""

    def __init__(self):
        """Initialize the Gemini AI service."""
        self.client = genai.Client(api_key=settings.gemini_api_key)
        self.model_name = settings.model_name
        logger.info(
            f"AI Service initialized with Gemini API key: {mask_api_key(settings.gemini_api_key)}"
        )

    async def chat_completion(self, request: ChatRequest) -> ChatResponse:
        """Create a chat completion using Gemini API (Async)."""

        try:
            logger.info(f"Sending chat completion request for model: {self.model_name}")

            # Use requested model if provided, else use default from settings
            model_id = (
                request.model
                if request.model and "gemini" in request.model.lower()
                else self.model_name
            )

            # Format messages for the new SDK
            contents = []
            for msg in request.messages:
                role = "user" if msg.role == "user" else "model"
                contents.append(types.Content(role=role, parts=[types.Part(text=msg.content)]))

            # Call Gemini via async client
            response = await self.client.aio.models.generate_content(
                model=model_id,
                contents=contents,
                config=types.GenerateContentConfig(
                    max_output_tokens=request.max_tokens,
                    temperature=request.temperature,
                ),
            )

            chat_response = ChatResponse(
                id=str(uuid.uuid4()),
                created=int(time.time()),
                model=model_id,
                choices=[
                    {
                        "message": {"role": "assistant", "content": response.text},
                        "finish_reason": "stop",
                    }
                ],
                usage={
                    "total_tokens": response.usage_metadata.total_token_count if response.usage_metadata else 0
                },
            )

            logger.info(f"Chat completion successful: {chat_response.id}")
            return chat_response

        except Exception as e:
            error_msg = f"Error calling Gemini API: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)

    async def list_models(self) -> List[ModelInfo]:
        """List available Gemini models."""
        try:
            logger.info("Fetching available models from Gemini")
            models = []
            # Note: list() is usually sync in this SDK but can be iterated
            for m in self.client.models.list():
                models.append(
                    ModelInfo(
                        id=m.name,
                        name=m.display_name or m.name,
                        description=m.description or "",
                        pricing={"info": "Refer to Google Cloud pricing"},
                    )
                )
            return models
        except Exception as e:
            error_msg = f"Error fetching models: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)

    async def health_check(self) -> bool:
        """Check if the AI service is healthy."""
        try:
            # Check if we can reach the model
            self.client.models.get(model=self.model_name)
            return True
        except Exception as e:
            logger.error(f"Gemini service health check failed: {str(e)}")
            return False

    async def close(self):
        """Close method for interface consistency (genai.Client handles connection pooling)."""
        logger.info("Gemini service client shutdown triggered")


# Global AI service instance
ai_service = AIService()
