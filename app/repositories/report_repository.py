"""Report repository for microbiota analysis persistence."""

from datetime import UTC, datetime
from typing import Any, List
import uuid

from app.core.logging import get_logger
from app.repositories.base import BaseRepository
from app.models.schemas import MicrobiotaReport, AnalysisRequest

logger = get_logger(__name__)

class ReportRepository(BaseRepository):
    """Repository for managing analyzed microbiota reports in Supabase."""

    async def save_report(self, report: MicrobiotaReport, metadata: AnalysisRequest) -> dict[str, Any]:
        """
        Saves a structured microbiota report linking it to the source document and hierarchy.
        """
        try:
            report_id = str(uuid.uuid4())
            data = {
                "id": report_id,
                "id_documento_origen": metadata.documento_id,
                "empresa_id": metadata.empresa_id,
                "doctor_id": metadata.doctor_id,
                "file_url_origen": metadata.file_url,
                "report_data": report.model_dump(mode="json"),
                "created_at": datetime.now(UTC).isoformat()
            }
            
            result = self.client.table("microbiota_reports").insert(data).execute()
            logger.info(f"Report saved and linked: {metadata.documento_id}")
            return result.data[0] if result.data else {}
        except Exception as e:
            logger.error(f"Error saving linked report: {str(e)}")
            raise Exception(f"Database error: {str(e)}")

    async def get_reports_by_patient(self, patient_id: str) -> List[dict[str, Any]]:
        """Retrieves history of reports for a specific patient."""
        try:
            result = self.client.table("microbiota_reports") \
                .select("*") \
                .eq("patient_id", patient_id) \
                .order("created_at", desc=True) \
                .execute()
            return result.data
        except Exception as e:
            logger.error(f"Error fetching patient reports: {str(e)}")
            return []
