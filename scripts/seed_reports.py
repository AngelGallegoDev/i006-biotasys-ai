"""Script to seed Supabase with mock microbiota reports using polyfactory."""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from tests.factories import MicrobiotaReportFactory
from app.repositories.report_repository import ReportRepository
from app.core.logging import get_logger

logger = get_logger(__name__)

async def seed_reports(count: int = 5):
    """Generates and saves a specified number of mock reports."""
    repo = ReportRepository()
    logger.info(f"🚀 Seeding {count} mock reports into Supabase...")

    for i in range(count):
        # Generate mock report
        mock_report = MicrobiotaReportFactory.build()
        
        try:
            # Save to repository
            result = await repo.save_report(mock_report)
            logger.info(f"✅ [{i+1}/{count}] Saved report: {result.get('study_code')} (ID: {result.get('id')})")
        except Exception as e:
            logger.error(f"❌ Failed to save report {i+1}: {str(e)}")

    logger.info("✨ Seeding complete!")

if __name__ == "__main__":
    asyncio.run(seed_reports(5))
