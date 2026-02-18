"""Security utilities for the Biotasys AI Engine."""

from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader
from app.config.settings import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# Standard header for API Keys: X-API-KEY
API_KEY_NAME = "X-API-KEY"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

# This could be moved to a Supabase table 'api_keys' in the next sprint
# For now, we use a Master Key or a list from env for simplicity (KISS)
ALLOWED_API_KEYS = [settings.jwt_secret_key] # Example: reusing secret or a new env var

async def get_api_key(api_key: str = Security(api_key_header)):
    """
    Security Dependency: Ensures only 'Certified Entities' can access the engine.
    - Validates X-API-KEY in the header.
    - Checks against the list of authorized certificates.
    """
    if not api_key:
        logger.warning("Access attempt without API Key")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Certification Key (X-API-KEY header)",
        )
    
    # Logic: Search for the key in allowed entities
    # Note: In production, this would be: 
    # client = await repository.verify_client_key(api_key)
    if api_key not in ALLOWED_API_KEYS:
        logger.error(f"Unauthorized access attempt with key: {mask_api_key(api_key)}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Not a Certified Biotasys Entity",
        )
    
    return api_key

def mask_api_key(api_key: str) -> str:
    """Mask API key for logging purposes."""
    if not api_key or len(api_key) < 8:
        return "***"
    return f"{api_key[:4]}...{api_key[-4:]}"
