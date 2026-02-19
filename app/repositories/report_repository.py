"""Report repository for microbiota analysis persistence."""

import uuid
from datetime import UTC, datetime
from typing import Any

from app.core.logging import get_logger
from app.core.exceptions import DatabaseError
from app.models.schemas import AnalysisRequest, MicrobiotaReport
from app.repositories.base import BaseRepository

logger = get_logger(__name__)


class ReportRepository(BaseRepository):
    """Repository for managing analyzed microbiota reports in Supabase."""

    async def save_report(self, report: MicrobiotaReport, metadata: AnalysisRequest | None = None) -> dict[str, Any]:
        """
        Saves a structured microbiota report linking it to the source document and hierarchy.
        Maps Backend A metadata to existing Supabase columns with UUID safety.
        """
        def ensure_uuid(val: str) -> str:
            try:
                return str(uuid.UUID(val))
            except (ValueError, AttributeError):
                # Generate a deterministic UUID if it's just a string like "DR_REVISOR_01"
                return str(uuid.uuid5(uuid.NAMESPACE_DNS, str(val)))

        try:
            report_id = str(uuid.uuid4())
            
            # Extract basic data
            raw_patient_id = report.metadata.patient_id if report.metadata else "Unknown"
            
            data = {
                "id": report_id,
                "report_data": report.model_dump(mode="json"),
                "created_at": datetime.now(UTC).isoformat(),
                "patient_id": ensure_uuid(raw_patient_id),
            }

            # Optional mapping if metadata is provided (Backend A simulation)
            if metadata:
                data["study_code"] = metadata.documento_id
                data["user_id"] = ensure_uuid(metadata.doctor_id)
            else:
                # Fallback to report metadata for seeds/fallback
                data["study_code"] = report.metadata.study_code if report.metadata else f"REF-{report_id[:8]}"
                data["user_id"] = ensure_uuid("SYSTEM_INTERNAL")

            result = self.client.table("microbiota_reports").insert(data).execute()
            logger.info(f"Report saved successfully in Supabase: {data.get('study_code')}")
            return result.data[0] if result.data else {}
        except Exception as e:
            logger.error(f"Persistence Failure: {str(e)}")
            raise DatabaseError("Failed to save report in Supabase", details=str(e))

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
        """Retrieves a single report by its Engine ID."""
        try:
            result = (
                self.client.table("microbiota_reports")
                .select("*")
                .eq("id", report_id)
                .single()
                .execute()
            )
            return result.data if result.data else None
        except Exception as e:
            logger.error(f"Error fetching report {report_id}: {str(e)}")
            # For a single fetch, returning None is often cleaner,
            # but we could also raise ResourceNotFoundError if we want strictly 404s.
            return None
