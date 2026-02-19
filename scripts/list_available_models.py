import asyncio
from google import genai
import os
from dotenv import load_dotenv

load_dotenv()

async def list_models():
    api_key = os.getenv("GEMINI_API_KEY")
    client = genai.Client(api_key=api_key)
    print(f"Checking models with API Key: {api_key[:10]}...")
    try:
        models = await client.aio.models.list()
        for m in models:
            print(f"- {m.name}")
    except Exception as e:
        print(f"Error listing models: {e}")

if __name__ == "__main__":
    asyncio.run(list_models())
