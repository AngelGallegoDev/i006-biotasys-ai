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

        async def upsert_entity(table: str, entity_id: str, default_name: str, extra_data: dict | None = None) -> str:
            """Ensures an entity exists in the master table, creating it if necessary."""
            safe_id = ensure_uuid(entity_id)
            try:
                # Check if exists
                existing = self.client.table(table).select("id").eq("id", safe_id).maybe_single().execute()
                if not existing.data:
                    # Create placeholder
                    insert_data = {"id": safe_id, "name": default_name}
                    if extra_data:
                        insert_data.update(extra_data)
                    self.client.table(table).insert(insert_data).execute()
                    logger.info(f"Created master entity in {table}: {default_name} ({safe_id})")
                return safe_id
            except Exception as e:
                logger.warning(f"Failed to upsert entity in {table}: {str(e)}")
                return safe_id

        try:
            report_id = str(uuid.uuid4())
            
            # Extract basic data
            raw_patient_id = report.metadata.patient_id if report.metadata else "Unknown"
            
            # 1. Handle Hierarchy (Company & Collaborator)
            final_company_id = None
            final_user_id = ensure_uuid("SYSTEM-INTERNAL")

            if metadata:
                # Ensure Company exists
                final_company_id = await upsert_entity(
                    "companies", 
                    metadata.empresa_id, 
                    f"Empresa {metadata.empresa_id[:8]}"
                )
                
                # Ensure Collaborator exists and is linked
                final_user_id = await upsert_entity(
                    "collaborators", 
                    metadata.doctor_id, 
                    f"Dr. {metadata.doctor_id[:8]}",
                    {"company_id": final_company_id}
                )

            data = {
                "id": report_id,
                "report_data": report.model_dump(mode="json"),
                "created_at": datetime.now(UTC).isoformat(),
                "patient_id": ensure_uuid(raw_patient_id),
                "company_id": final_company_id,
                "user_id": final_user_id,
                "study_code": metadata.documento_id if metadata else (report.metadata.study_code if report.metadata else f"REF-{report_id[:8]}")
            }

            result = self.client.table("microbiota_reports").insert(data).execute()
            logger.info(f"Report saved with Hierarchy [Co: {final_company_id} | Usr: {final_user_id}]")
            return result.data[0] if result.data else {}
        except Exception as e:
            logger.error(f"Persistence Failure (Hierarchy): {str(e)}")
            raise DatabaseError("Failed to save report hierarchy in Supabase", details=str(e))

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
