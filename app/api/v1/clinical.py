"""Endpoints for clinical and microbiota data processing."""

from fastapi import APIRouter, HTTPException, Depends, File, UploadFile
from pydantic import BaseModel, Field
from typing import Any

from app.models.schemas import MicrobiotaReport, ErrorResponse
from app.services.report_service import ReportService, report_service
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/clinical", tags=["clinical"])


@router.post(
    "/process-report",
    response_model=dict[str, Any],
    responses={
        422: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
)
async def process_microbiota_document(
    request: AnalysisRequest,
    service: ReportService = Depends(lambda: report_service)
):
    """
    Biotasys Engine - Main Entry Point for Backend A.
    Receives a document URL, extracts structured microbiota data, and persists it.
    """
    try:
        logger.info(f"Received request for document: {request.documento_id}")
        result = await service.process_url_and_save(request)
        return result
    except Exception as e:
        logger.error(f"Engine failure for doc {request.documento_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/report/{report_id}", response_model=dict[str, Any])
async def get_report(
    report_id: str,
    service: ReportService = Depends(lambda: report_service)
):
    """Retrieves a previously processed report by its Engine ID."""
    try:
        # Note: In a full implementation, we would add the get_report method to the service
        # for now we access the repository directly for the check.
        result = await service.repository.client.table("microbiota_reports").select("*").eq("id", report_id).single().execute()
        if not result.data:
            raise HTTPException(status_code=404, detail="Report not found")
        return result.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
