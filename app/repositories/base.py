"""Base repository class."""

from supabase import Client

from app.core.supabase import supabase


class BaseRepository:
    """Base class for all repositories."""
    def __init__(self, client: Client = supabase):
        self.client = client
