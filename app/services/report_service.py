from datetime import UTC, datetime
from typing import Any

import httpx

from app.core.logging import get_logger
from app.core.exceptions import AIError
from app.config.settings import settings
from app.models.schemas import AnalysisReportDB, AnalysisRequest, JsonAnalysisRequest, MicrobiotaInput, MicrobiotaReport, AnalysisReport  #NutricionistInfo, PatientInfo
from app.repositories.report_repository import AnalysisReportDict, ReportRepository
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

    
    async def process_json_save_and_send(self, request: JsonAnalysisRequest) -> AnalysisReport: 
        """
        Biotasys JSON Input pipeline:
        Interpretación directa con Gemini 3 Pro para obtener el análisis clínico.
        """
        try:
            logger.info("Processing JSON raw input")
            
            # STEP 1: Normalize raw_json into AnalysisRequest (if not already)            
            try:
                microbiota_data = MicrobiotaInput.model_validate(request.raw_json)
                logger.info("Input data validated as MicrobiotaInput structure")
            except Exception as e:
                logger.info(f"Input data is unstructured or has field mismatches. Normalizing via AI")
                microbiota_data = await self.ai.analyze_laboratory_json(request.raw_json)
            
            # STEP 2: Expert Interpretation (Gemini 3 Pro)
            microbiota_interpretation = await self.ai.interpret_microbiota_data(microbiota_data)
        
            # STEP 3: Persistence in database
            report = AnalysisReport(
                study_id=request.study_id,
                study_code=request.study_code,
                nutricionist_id=request.nutricionist_id,
                patient_id=request.patient_id,
                data=microbiota_data,
                interpretation=microbiota_interpretation,
                file_url="https://example.com/report.pdf",  # Placeholder
                study_date=request.study_date.isoformat(),
            )

            saved_report = await self.repository.save_json_report(report, request)
            validated_report = AnalysisReportDB.model_validate(saved_report)

            # STEP 4: Callback to Backend Nest
            await self.post_to_backend_nest(validated_report, report.study_id)

            return validated_report
        
        except Exception as e:
            logger.error(f"JSON pipeline failed: {str(e)}")
            # If it's already a BiotasysException, let it bubble up to the controller
            raise e

    async def post_to_backend_nest(self, validated_report: AnalysisReportDB, study_id: str) -> None:
        """Envía el reporte generado al Backend Nest vía POST."""

        if not settings.backend_nest_url:
            logger.error("Backend Nest URL is not defined")
            return
        
        callback_url = f"{settings.backend_nest_url}/studies/{study_id}/processing-result"

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                await client.post(
                    callback_url,
                    json=validated_report.model_dump(mode="json"),
                    headers={
                        "Content-Type": "application/json",
                        "X-API-KEY": settings.jwt_secret_key,
                    },
                )
                logger.info(f"Callback to Backend Nest successful for url: {callback_url}")

        except Exception as e:
            # Log pero NO re-lanzar: el reporte ya se guardó, el callback es best-effort
            logger.error(f"Error en callback a Backend Nest: {str(e)}")

    async def get_report(self, report_id: str) -> dict[str, Any] | None:
        """Fetch a report by its ID through the repository."""
        return await self.repository.get_report_by_id(report_id)
    
    async def get_report_by_study_code(self, study_code: str) -> dict[str, Any] | None:
        """Fetch a report by its study code through the repository."""
        return await self.repository.get_report_by_study_code(study_code)

    async def process_and_save(self, raw_text: str, user_id: str | None = None) -> dict[str, Any]:
        # Keep legacy method for backward compatibility if needed,
        # but the main entry point is now process_url_and_save.
        pass

# Global instance
report_service = ReportService()
