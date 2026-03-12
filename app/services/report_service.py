import base64
from datetime import UTC, datetime
from typing import Any

import httpx

from app.core.logging import get_logger
from app.core.exceptions import AIError
from app.config.settings import settings
from app.models.schemas import AnalysisReportDB, AnalysisRequest, JsonAnalysisRequest, MicrobiotaInput, MicrobiotaReport, AnalysisReport
from app.repositories.report_repository import AnalysisReportDict, ReportRepository
from app.services.pdf_service import pdf_service
from app.services.ai_service import AIService, ai_service
from app.services.microbiota_normalizer import prenormalize_microbiota

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

    
    async def process_json_save_and_send(self, request: JsonAnalysisRequest) -> AnalysisReportDB: 
        """
        Biotasys JSON Input pipeline:
        """
        try:
            logger.info("Processing JSON raw input")
            
            # STEP 1: Normalize raw_json into AnalysisRequest (if not already) 

            normalized_json = prenormalize_microbiota(request.raw_json)

            try:
                microbiota_data = MicrobiotaInput.model_validate(normalized_json)
                logger.info("Input data validated as MicrobiotaInput structure")
            except Exception as e:
                logger.info(f"Fallback: Normalizing via AI due to validation error: {str(e)}")
                microbiota_data = await self.ai.analyze_laboratory_json(normalized_json)
            
            # STEP 2: Expert Interpretation 
            microbiota_interpretation = await self.ai.interpret_microbiota_data(microbiota_data)
            
            # STEP 3: Construir el objeto reporte INICIAL (sin file_url aún)
            report = AnalysisReport(
                study_id=request.study_id,
                study_code=request.study_code,
                nutricionist_id=request.nutricionist_id,
                patient_id=request.patient_id,
                data=microbiota_data,
                interpretation=microbiota_interpretation,
                file_url="", 
                study_date=request.study_date.isoformat(),
            )
            
            # STEP 4: Generar el PDF visual en memoria usando el reporte
            pdf_buffer = pdf_service.generate_microbiota_pdf(report)
            pdf_filename = f"microbiota_{report.study_code}.pdf"

            # STEP 5: Subir PDF a Storage y obtener la URL
            pdf_bytes = pdf_buffer.getvalue() 
            pdf_url = await self.repository.upload_pdf_to_storage(pdf_bytes, pdf_filename)

            # Actualizar el reporte con la URL real
            report.file_url = pdf_url
            
            # STEP 6: Persistence in database
            saved_report = await self.repository.save_json_report(report, request)
            validated_report = AnalysisReportDB.model_validate(saved_report)

            # STEP 7: Callback to Backend Nest
            await self.post_to_backend_nest(validated_report, report.study_id)

            # Devolver el reporte codificado
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
