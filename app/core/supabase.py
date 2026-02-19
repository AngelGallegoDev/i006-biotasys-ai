"""Supabase client configuration."""

from supabase import Client, create_client

from app.config.settings import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

def get_supabase_client() -> Client:
    """
    Initialize and return a Supabase client.
    """
    try:
        client = create_client(settings.supabase_url, settings.supabase_key)
        return client
    except Exception as e:
        logger.error(f"Failed to create Supabase client: {str(e)}")
        raise e

# Create a singleton instance if needed or use as a dependency
supabase: Client = get_supabase_client()
