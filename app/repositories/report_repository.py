"""Report repository for microbiota analysis persistence."""

import uuid
import asyncio
from datetime import UTC, datetime
from typing import Any, Optional, TypedDict, cast

from app.core.logging import get_logger
from app.core.exceptions import DatabaseError, ValidationError
from app.models.schemas import AnalysisRequest, MicrobiotaReport
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
