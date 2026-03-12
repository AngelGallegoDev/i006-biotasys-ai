"""Report repository for microbiota analysis persistence."""

import uuid
import asyncio
from datetime import UTC, datetime
from typing import Any, Optional, TypedDict, cast

from app.core.logging import get_logger
from app.core.exceptions import DatabaseError, ValidationError
from app.models.schemas import AnalysisRequest, MicrobiotaInput, MicrobiotaInterpretation, MicrobiotaReport, JsonAnalysisRequest, AnalysisReport
from app.repositories.base import BaseRepository

logger = get_logger(__name__)

# TypedDict para tipado estricto de respuestas
class ReportDict(TypedDict):
    id: str
    report_data: dict[str, Any]
    created_at: str
    patient_id: str
    company_id: Optional[str]
    user_id: str
    study_code: str

class AnalysisReportDict(TypedDict):
    id: str
    study_id: str
    study_code: str
    nutricionist_id: str
    patient_id: str
    data: MicrobiotaInput
    interpretation: MicrobiotaInterpretation
    file_url: str
    study_date: str
    created_at: str
    

class ReportRepository(BaseRepository):
    """Repository for managing analyzed microbiota reports in Supabase."""

    async def save_report(
        self, 
        report: MicrobiotaReport, 
        metadata: Optional[AnalysisRequest] = None
    ) -> ReportDict:
        # NUEVA: Validación de entrada
        if not report.metadata or report.metadata.patient_id == "No disponible":
            raise ValidationError("Patient ID requerido para persistir informe")

        report_id = str(uuid.uuid4())
        patient_id = self._ensure_uuid(report.metadata.patient_id)

        try:
            # PASO 1: Jerarquía (modularizado)
            final_company_id = None
            final_user_id = self._ensure_uuid("SYSTEM-INTERNAL")  # Default fallback

            if metadata:
                final_company_id = await self._ensure_company(metadata.empresa_id, metadata)
                final_user_id = await self._ensure_collaborator(metadata.doctor_id, final_company_id)

            # PASO 2: Preparar datos del informe
            data: dict[str, Any] = {
                "id": report_id,
                "report_data": report.model_dump(mode="json"),
                "created_at": datetime.now(UTC).isoformat(),
                "patient_id": patient_id,
                "company_id": final_company_id,
                "user_id": final_user_id,
                "study_code": metadata.documento_id if metadata else report.metadata.study_code
            }

            # PASO 3: Insertar informe
            result = await asyncio.to_thread(
                lambda: self.client.table("microbiota_reports").insert(data).execute()
            )

            logger.info(f"✅ Informe guardado [{report_id[:8]}] Co:{final_company_id} Usr:{final_user_id}")
            return cast(ReportDict, result.data[0]) if result.data else {}

        except Exception as e:
            logger.error(f"❌ Error guardando informe {report_id}: {str(e)}")
            raise DatabaseError("Error persistiendo informe", details=str(e)) from e

    async def save_json_report(
        self,
        report: AnalysisReport,
        metadata: JsonAnalysisRequest,
    ) -> AnalysisReportDict:
        """Persist an AnalysisReport into the analysis_reports table."""

        if not report.patient_id:
            raise ValidationError("Patient ID is required to persist a JSON report")

        report_id = str(uuid.uuid4())

        try:
            data: AnalysisReportDict = {
                "id": report_id,
                "study_id": report.study_id,
                "study_code": report.study_code,
                "nutricionist_id": report.nutricionist_id,
                "patient_id": report.patient_id,
                "data": report.data.model_dump(mode="json"),
                "interpretation": report.interpretation.model_dump(mode="json"),
                "file_url": report.file_url,
                "study_date": report.study_date.isoformat(),
                "created_at": datetime.now(UTC).isoformat(),
            }

            db_result = await asyncio.to_thread(
                lambda: self.client
                    .table("analysis_reports")
                    .insert(data)
                    .execute()
            )

            logger.info(
                f"✅ JSON report saved [{report_id[:8]}] "
                f"Study:{report.study_code} Patient:{report.patient_id[:8]}"
            )
            
            if not db_result.data:
                raise DatabaseError("Insert succeeded but returned no data")

            result = db_result.data[0]
            result.pop("id", None)
            result.pop("study_id", None)
            return result

        except Exception as e:
            logger.error(f"❌ Error saving JSON report {report_id}: {str(e)}")
            raise DatabaseError(
                "Failed to persist JSON analysis report", details=str(e)
            ) from e

    async def get_reports_by_patient(self, patient_id: str) -> list[dict[str, Any]]:
        """Retrieves history of reports for a specific patient."""
        try:
            result = (
                self.client.table("microbiota_reports")
                .select("*")
                .eq("patient_id", patient_id)
                .order("created_at", desc=True)
                .execute()
            )
            return result.data
        except Exception as e:
            logger.error(f"Error fetching patient reports: {str(e)}")
            return []

    async def get_report_by_id(self, report_id: str) -> dict[str, Any] | None:
        """Retrieves a single report by its Engine ID (UUID) or Study Code."""
        try:
            # 1. Attempt lookup by primary UUID
            try:
                # Check if it's a valid UUID string
                uuid.UUID(report_id)
                result = (
                    self.client.table("microbiota_reports")
                    .select("*")
                    .eq("id", report_id)
                    .maybe_single()
                    .execute()
                )
                if result.data: return result.data
            except ValueError:
                pass # Not a UUID, proceed to study_code check

            # 2. Attempt lookup by study_code (Backend A - documento_id)
            result = (
                self.client.table("microbiota_reports")
                .select("*")
                .eq("study_code", report_id)
                .order("created_at", desc=True) # Get the latest version
                .limit(1)
                .execute()
            )
            return result.data[0] if result.data else None

        except Exception as e:
            logger.error(f"Error fetching report {report_id}: {str(e)}")
            return None
        
    async def get_report_by_study_code(self, study_code: str) -> dict[str, Any] | None:
        """Retrieves a single report by its study_code."""
        try:
            result = (
                self.client.table("analysis_reports")
                .select("*")
                .eq("study_code", study_code)
                .limit(1)
                .execute()
            )

            return result.data[0] if result.data else None

        except Exception as e:
            logger.error(f"Error fetching report {study_code}: {str(e)}")
            return None
        
    async def upload_pdf_to_storage(self, pdf_bytes: bytes, filename: str) -> str:
        """Sube un archivo PDF al bucket 'reports' y devuelve la URL pública."""
        try:
            result = await asyncio.to_thread(
                lambda: self.client.storage.from_("reports").upload(
                    path=filename,
                    file=pdf_bytes,
                    file_options={"content-type": "application/pdf", "upsert": "true"}
                )
            )
            
            # Obtener URL pública
            public_url = self.client.storage.from_("reports").get_public_url(filename)
            logger.info(f"✅ PDF guardado en Storage: {public_url}")
            
            return public_url
            
        except Exception as e:
            logger.error(f"❌ Error subiendo PDF a Storage: {str(e)}")
            raise DatabaseError("Error uploading PDF to storage", details=str(e)) from e

