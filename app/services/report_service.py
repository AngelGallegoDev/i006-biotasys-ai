from typing import Any

import httpx

from app.core.logging import get_logger
from app.core.exceptions import AIError
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

            # STEP 1: Download with robust discovery
            async with httpx.AsyncClient(timeout=60.0) as client:
                try:
                    response = await client.get(request.file_url, follow_redirects=True)
                    if response.status_code != 200:
                        raise Exception(f"Source file unreachable (HTTP {response.status_code})")
                    
                    file_bytes = response.content
                    # Improved MIME detection using headers, falling back to extension
                    content_type = response.headers.get("Content-Type", "")
                    if "pdf" in content_type.lower():
                        mime_type = "application/pdf"
                    elif "image" in content_type.lower():
                        mime_type = content_type or "image/jpeg"
                    else:
                        mime_type = "application/pdf" if request.file_url.lower().endswith(".pdf") else "image/jpeg"
                        
                    logger.debug(f"File downloaded. Size: {len(file_bytes)} bytes. MIME: {mime_type}")
                except Exception as e:
                    raise AIError("Failed to retrieve document from storage", details=str(e))

            # STEP 2: Technical Extraction (Gemini 2.5 Flash Lite)
            report: MicrobiotaReport = await self.ai.analyze_microbiota_document(file_bytes, mime_type)

            # STEP 3: Expert Interpretation (Gemini 3 Pro)
            interpretation = await self.ai.interpret_microbiota_data(report)

            # Join the data
            report.interpretation = interpretation
            report.engine_version = "1.2.1 (Dual Engine: Flash-Lite + 3-Pro-Preview)"

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
            # If it's already a BiotasysException, let it bubble up to the controller
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
