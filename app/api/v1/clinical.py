"""Endpoints for clinical and microbiota data processing."""

from fastapi import APIRouter, HTTPException, Depends, Security
from typing import Any

from app.models.schemas import JsonAnalysisRequest, AnalysisRequest, AnalysisReport, AnalysisReportDB, ErrorResponse
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
    deprecated=True, # Punto de entrada original para el análisis de archivos PDF.
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
    
@router.post(
    "/process-report-json",
    response_model=AnalysisReportDB,
    responses={
        422: {"model": ErrorResponse},
        401: {"model": ErrorResponse}, # Unauthorized
        403: {"model": ErrorResponse}, # Forbidden
        500: {"model": ErrorResponse},
    },
)
async def process_microbiota_json(
    request: JsonAnalysisRequest,
    service: ReportService = Depends(lambda: report_service)
):
    """
    Punto de entrada directo a través de JSON para Backend A.
    Protected: Requires X-API-KEY header from a Certified Entity.
    """
    try:
        logger.info(f"Certified JSON request for raw json data")
        result = await service.process_json_save_and_send(request)
        return result
    except Exception as e:
        logger.error(f"JSON engine failure for raw json data: {str(e)}")
        raise e


@router.get("/report/{report_id}", 
    response_model=AnalysisReport
)
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

@router.get("/analysis-reports/{study_code}", 
    response_model=AnalysisReport
)
async def get_report_by_study_code(
    study_code: str,
    service: ReportService = Depends(lambda: report_service)
):
    """
    Retrieves a report. Protected: Requires X-API-KEY.
    """
    report = await service.get_report_by_study_code(study_code)
    if not report:
        raise ResourceNotFoundError(f"Report with study code {study_code} not found")
    return report
