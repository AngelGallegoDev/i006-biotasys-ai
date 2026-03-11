from unittest.mock import AsyncMock, MagicMock
import pytest
import httpx
from datetime import datetime, UTC
from app.services.report_service import ReportService
from app.models.schemas import (
    AnalysisRequest, DirectAnalysisRequest, MicrobiotaReport, MicrobiotaInterpretation, 
    StudyMetadata, SequencingData, DiversityIndices, TaxonomicComposition, 
    TaxonomicAbundance, FunctionalMarkers, ClinicalContext
)

@pytest.fixture
def service(mocker):
    # Mock AI Service as a whole unit
    mock_ai = MagicMock()
    mocker.patch("app.services.report_service.ReportRepository")
    return ReportService(ai=mock_ai)

@pytest.mark.asyncio
async def test_pro_clinical_flow_full_integration(service, respx_mock):
    """
    PRO TEST: Simulate the complete clinical pipeline of Biotasys.
    """
    # 1. SETUP - Build a VALID clinical report manually to bypass random factory errors
    mock_report_base = MicrobiotaReport(
        metadata=StudyMetadata(
            study_code="BIO-123", lab_internal_code="LAB-1", patient_id="PAT-1",
            sex="M", age=30, sample_collection_date=datetime.now(UTC),
            sample_reception_date=datetime.now(UTC)
        ),
        sequencing=SequencingData(
            technology="16S", region="V3-V4", platform="Illumina",
            total_reads=50000, filtered_reads=45000
        ),
        diversity=DiversityIndices(
            shannon_index=3.5, simpson_index=0.9, observed_otus=1200
        ),
        taxonomy=TaxonomicComposition(
            phyla=[TaxonomicAbundance(name="Firmicutes", abundance=60.0)],
            firmicutes_bacteroidetes_ratio=2.0,
            predominant_genera=[],
            detected_species=[]
        ),
        functionality=FunctionalMarkers(
            butyrate_producers="Optimal", propionate_producers="Optimal",
            suggested_enterotype="Type 1", opportunistic_microorganisms=[],
            functional_markers_list=[],
            carbohydrate_metabolism="Normal",
            lipid_metabolism="Normal",
            vitamin_b_synthesis="Normal"
        ),
        clinical_context=ClinicalContext(
            inflammatory_markers="None", antibiotic_use=False,
            probiotic_use=True, dietary_pattern="Omnivore", lab_observations=""
        )
    )

    mock_interpretation = MicrobiotaInterpretation(
        summary="Optimal", diversity_analysis="Good", taxonomic_balance=[],
        metabolic_profile=[], opportunistic_risk=[], final_technical_notes="",
        gut_health_score={"value": 95.0, "label": "Excelente", "breakdown": "Everything is awesome"},
        diversity_diagnosis={"score": 3.5, "interpretation": "High", "clinical_implication": "Good resilience"},
        enterotype_analysis={"enterotype": "Bacteroides", "confidence": "High", "description": "Western diet associated"}
    )

    # 2. MOCK THE EXTERNAL WORLD
    respx_mock.get("https://biotasys.com/v1/report_123.pdf").mock(
        return_value=httpx.Response(200, content=b"PDF_BYTES_STREAM")
    )
    
    service.ai.analyze_microbiota_document = AsyncMock(return_value=mock_report_base)
    service.ai.interpret_microbiota_data = AsyncMock(return_value=mock_interpretation)
    service.repository.save_report = AsyncMock(return_value={"id": "engine_id_555"})

    analysis_request = AnalysisRequest(
        file_url="https://biotasys.com/v1/report_123.pdf",
        documento_id="B-001-X", empresa_id="CLINIC_A",
        doctor_id="DR_HOUSE", fecha_envio=datetime.now(UTC)
    )

    result = await service.process_url_and_save(analysis_request)

    # 4. RIGOROUS ASSERTIONS
    assert result["engine_status"] == "success"
    assert result["report_id"] == "engine_id_555"
    assert result["data"].interpretation.summary == "Optimal"
