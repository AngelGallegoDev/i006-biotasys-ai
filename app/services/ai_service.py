"""AI service for Gemini integration."""

import google.generativeai as genai
import uuid
import time
from datetime import datetime
from typing import List, Dict, Any, Optional

from app.config.settings import settings
from app.models.schemas import ChatRequest, ChatResponse, ModelInfo
from app.core.logging import get_logger
from app.core.security import mask_api_key

logger = get_logger(__name__)


class AIService:
    """Service for interacting with Google Gemini API."""
    
    def __init__(self):
        """Initialize the Gemini AI service."""
        genai.configure(api_key=settings.gemini_api_key)
        self.model_name = settings.model_name
        logger.info(f"AI Service initialized with Gemini API key: {mask_api_key(settings.gemini_api_key)}")
    
    async def chat_completion(self, request: ChatRequest) -> ChatResponse:
        """Create a chat completion using Gemini API."""
        
        try:
            logger.info(f"Sending chat completion request for model: {self.model_name}")
            
            # Use requested model if provided, else use default from settings
            model_id = request.model if request.model and "gemini" in request.model.lower() else self.model_name
            model = genai.GenerativeModel(model_id)
            
            # Format history for Gemini
            # Gemini expects 'user' and 'model' roles
            history = []
            for msg in request.messages[:-1]:
                role = "user" if msg.role == "user" else "model"
                history.append({"role": role, "parts": [msg.content]})
            
            chat = model.start_chat(history=history)
            
            last_message = request.messages[-1].content
            
            # Using run_in_executor might be safer for sync SDK calls, 
            # but Gemini SDK often handles async internally or is lightweight enough.
            # For strictness, we'll call it directly since it's the standard way in early implementations.
            response = await chat.send_message_async(
                last_message,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=request.max_tokens,
                    temperature=request.temperature,
                )
            )
            
            chat_response = ChatResponse(
                id=str(uuid.uuid4()),
                created=int(time.time()),
                model=model_id,
                choices=[{
                    "message": {
                        "role": "assistant",
                        "content": response.text
                    },
                    "finish_reason": "stop"
                }],
                usage={"total_tokens": 0} # Gemini SDK usage details vary by version
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
            for m in genai.list_models():
                if 'generateContent' in m.supported_generation_methods:
                    models.append(ModelInfo(
                        id=m.name,
                        name=m.display_name,
                        description=m.description,
                        pricing={"info": "Refer to Google Cloud pricing"}
                    ))
            return models
        except Exception as e:
            error_msg = f"Error fetching models: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)
    
    async def health_check(self) -> bool:
        """Check if the AI service is healthy."""
        try:
            # Simple model list check
            genai.get_model(self.model_name)
            return True
        except Exception as e:
            logger.error(f"Gemini service health check failed: {str(e)}")
            return False
    
    async def close(self):
        """Close method for interface consistency."""
        logger.info("Gemini service client 'closed'")


# Global AI service instance
ai_service = AIService()
