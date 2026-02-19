"""Endpoints for clinical and microbiota data processing."""

from fastapi import APIRouter, HTTPException, Depends, Security
from typing import Any

from app.models.schemas import AnalysisRequest, ErrorResponse
from app.services.report_service import ReportService, report_service
from app.core.logging import get_logger
from app.core.exceptions import ResourceNotFoundError
from app.core.security import get_api_key

logger = get_logger(__name__)

# Protect all clinical endpoints with API Key validation
router = APIRouter(
    prefix="/clinical", 
    tags=["clinical"],
    dependencies=[Security(get_api_key)]
)


@router.post(
    "/process-report",
    response_model=dict[str, Any],
    responses={
        422: {"model": ErrorResponse},
        401: {"model": ErrorResponse}, # Unauthorized
        403: {"model": ErrorResponse}, # Forbidden
        500: {"model": ErrorResponse},
    },
)
async def process_microbiota_document(
    request: AnalysisRequest,
    service: ReportService = Depends(lambda: report_service)
):
    """
    Biotasys Engine - Main Entry Point for Backend A.
    Protected: Requires X-API-KEY header from a Certified Entity.
    """
    try:
        logger.info(f"Certified request for document: {request.documento_id}")
        result = await service.process_url_and_save(request)
        return result
    except Exception as e:
        logger.error(f"Engine failure for doc {request.documento_id}: {str(e)}")
        raise e


@router.get("/report/{report_id}", response_model=dict[str, Any])
async def get_report(
    report_id: str,
    service: ReportService = Depends(lambda: report_service)
):
    """
    Retrieves a report. Protected: Requires X-API-KEY.
    """
    report = await service.get_report(report_id)
    if not report:
        raise ResourceNotFoundError(f"Report with ID {report_id} not found")
    return report
