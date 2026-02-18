from typing import Any

import httpx

from app.core.logging import get_logger
from app.models.schemas import AnalysisRequest, MicrobiotaReport
from app.repositories.report_repository import ReportRepository
from app.services.ai_service import AIService, ai_service

logger = get_logger(__name__)

class ReportService:
    """Orchestrator for Biotasys Engine analysis workflows."""

    def __init__(self, ai: AIService = ai_service):
        self.ai = ai
        self.repository = ReportRepository()

    async def process_url_and_save(self, request: AnalysisRequest) -> dict[str, Any]:
        """
        Biotasys Dual Engine Pipeline:
        1. Extraction (Gemini 2.5 Flash Lite) -> Technical Data.
        2. Interpretation (Gemini 3 Pro) -> Expert Conclusions.
        """
        try:
            logger.info(f"🚀 Launching Dual Engine for: {request.documento_id}")

            # STEP 1: Download
            async with httpx.AsyncClient() as client:
                response = await client.get(request.file_url)
                if response.status_code != 200:
                    raise Exception(f"Storage unavailable: {response.status_code}")
                file_bytes = response.content

            mime_type = "application/pdf" if request.file_url.lower().endswith(".pdf") else "image/jpeg"

            # STEP 2: Technical Extraction (Gemini 2.5 Flash Lite)
            report: MicrobiotaReport = await self.ai.analyze_microbiota_document(file_bytes, mime_type)

            # STEP 3: Expert Interpretation (Gemini 3 Pro)
            # This is where we make the data "shine"
            interpretation = await self.ai.interpret_microbiota_data(report)

            # Join the data
            report.interpretation = interpretation
            report.engine_version = "1.2.0 (Dual Engine: Flash-Lite + 3-Pro)"

            # STEP 4: Persistence with Metadata
            saved_report = await self.repository.save_report(report, request)

            logger.info(f"✨ Clinical analysis completed and persisted for {request.documento_id}")

            return {
                "engine_status": "success",
                "report_id": saved_report.get("id"),
                "documento_id_origen": request.documento_id,
                "data": report
            }
        except Exception as e:
            logger.error(f"Engine pipeline failed: {str(e)}")
            raise e

    async def get_report(self, report_id: str) -> dict[str, Any] | None:
        """Fetch a report by its ID through the repository."""
        return await self.repository.get_report_by_id(report_id)

    async def process_and_save(self, raw_text: str, user_id: str | None = None) -> dict[str, Any]:
        # Keep legacy method for backward compatibility if needed,
        # but the main entry point is now process_url_and_save.
        pass

# Global instance
report_service = ReportService()
