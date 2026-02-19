import asyncio
import os
from dotenv import load_dotenv
from app.services.ai_service import AIService
from app.models.schemas import MicrobiotaReport

load_dotenv(override=True)

async def test_extraction():
    ai = AIService()
    print(f"Testing with extractor: {ai.extractor_model}")
    print(f"Testing with interpreter: {ai.interpreter_model}")
    
    # Just check if health check works (which checks model availability)
    try:
        is_ok = await ai.health_check()
        print(f"Health check: {'SUCCESS' if is_ok else 'FAILED'}")
    except Exception as e:
        print(f"Health check error: {e}")

if __name__ == "__main__":
    asyncio.run(test_extraction())
