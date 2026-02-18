"""Health check API endpoints."""

from fastapi import APIRouter
from datetime import datetime

from app.models.schemas import HealthResponse
from app.config.settings import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/health", tags=["health"])


@router.get("", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint.

    Returns the current health status of the service and its dependencies.
    """
    from app.services.ai_service import ai_service
    from app.core.supabase import supabase
    
    db_status = {"connected": False}
    try:
        # Check Supabase connection (lightweight call)
        # We just check if we can get the schema
        supabase.table("_non_existent_").select("*").limit(0).execute()
        db_status["connected"] = True
    except Exception as e:
        # If it's a "table not found" error, it actually means we connected successfully
        if "PGRST205" in str(e) or "not find the table" in str(e).lower():
            db_status["connected"] = True
        else:
            logger.error(f"DB Health check failed: {str(e)}")
            db_status["error"] = str(e)

    ai_status = {"connected": False}
    try:
        is_ai_healthy = await ai_service.health_check()
        ai_status["connected"] = is_ai_healthy
    except Exception as e:
        logger.error(f"AI Service Health check failed: {str(e)}")
        ai_status["error"] = str(e)

    overall_status = "healthy"
    if not db_status["connected"] or not ai_status["connected"]:
        overall_status = "degraded"

    return HealthResponse(
        status=overall_status,
        timestamp=datetime.now(),
        version=settings.app_version,
        message="Service status report",
        database=db_status,
        ai_service=ai_status
    )
