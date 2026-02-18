"""Chat repository for Supabase persistence."""

from datetime import datetime
from typing import Any, Dict, List

from app.core.logging import get_logger
from app.repositories.base import BaseRepository

logger = get_logger(__name__)

class ChatRepository(BaseRepository):
    """Repository for managing chat history and sessions in Supabase."""

    async def save_message(self, session_id: str, role: str, content: str) -> Dict[str, Any]:
        """
        Saves a chat message to the database.
        Note: Table 'messages' must exist in Supabase.
        """
        try:
            data = {
                "session_id": session_id,
                "role": role,
                "content": content,
                "created_at": datetime.now().isoformat()
            }
            # This is a sync call in current supabase-py, but we wrap it
            result = self.client.table("messages").insert(data).execute()
            return result.data[0] if result.data else {}
        except Exception as e:
            logger.error(f"Error saving message: {str(e)}")
            # In a real app we might raise or handle this differently
            return {}

    async def get_history(self, session_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Retrieves chat history for a session."""
        try:
            result = self.client.table("messages") \
                .select("*") \
                .eq("session_id", session_id) \
                .order("created_at", desc=False) \
                .limit(limit) \
                .execute()
            return result.data
        except Exception as e:
            logger.error(f"Error fetching history: {str(e)}")
            return []
