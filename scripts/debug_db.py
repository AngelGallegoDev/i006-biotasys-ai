import asyncio
import uuid
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from app.core.supabase import supabase
from app.core.logging import setup_logging, get_logger

setup_logging()
logger = get_logger(__name__)

async def debug_db():
    name = "CLINICA_SIMULADA_A"
    # Match the logic in ReportRepository
    safe_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, name))
    
    logger.info(f"Checking access for Company: {name} ({safe_id})")
    
    try:
        # Try a direct upsert
        logger.info("Attempting Upsert...")
        result = supabase.table("companies").upsert({"id": safe_id, "name": name}, on_conflict="id").execute()
        logger.info(f"Upsert result: {result.data}")
        
        # Verify it's there
        check = supabase.table("companies").select("*").eq("id", safe_id).execute()
        logger.info(f"Verification fetch: {check.data}")
        
    except Exception as e:
        logger.error(f"DATABASE DEBUG FAILED: {str(e)}")

if __name__ == "__main__":
    asyncio.run(debug_db())
