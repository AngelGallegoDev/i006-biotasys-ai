"""Pydantic models for request/response schemas."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Health check response model."""
    status: str = Field(..., description="Service status")
    timestamp: datetime = Field(..., description="Response timestamp")
    version: str = Field(..., description="Application version")
    message: str | None = Field(default=None, description="Additional status message")
    database: dict[str, Any] | None = Field(default=None, description="Database status")
    ai_service: dict[str, Any] | None = Field(default=None, description="AI service status")


class ErrorResponse(BaseModel):
    """Error response model."""
    error: str = Field(..., description="Error type")
    detail: str | None = Field(default=None, description="Error details")
    timestamp: datetime = Field(default_factory=datetime.now, description="Error timestamp")


class RootResponse(BaseModel):
    """Root endpoint response model."""
    message: str = Field(..., description="Welcome message")
    version: str = Field(..., description="Application version")
    docs: str = Field(..., description="Documentation URL")
    health: str = Field(..., description="Health check URL")


# --- Biotasys Specific Schemas ---

class SequencingData(BaseModel):
    """Technical sequencing and quality metadata."""
    technology: str = Field(..., description="Analysis technology (e.g., 16S rRNA)")
    region: str = Field(..., description="Sequenced region (e.g., V3–V4)")
    platform: str = Field(..., description="Sequencing platform (e.g., Illumina)")
    total_reads: int = Field(..., description="Total obtained reads")
    filtered_reads: int = Field(..., description="Filtered reads after quality check")


class DiversityIndices(BaseModel):
    """Ecological diversity and richness metrics."""
    shannon_index: float = Field(..., description="Shannon alpha diversity index")
    simpson_index: float = Field(..., description="Simpson alpha diversity index")
    observed_otus: int = Field(..., description="Observed richness (OTUs)")


class TaxonomicAbundance(BaseModel):
    """Relative abundance of a taxonomic unit."""
    name: str = Field(..., description="Name of the taxon")
    abundance: float = Field(..., description="Relative abundance percentage")


class TaxonomicComposition(BaseModel):
    """Distribution of bacteria across different levels."""
    phyla: list[TaxonomicAbundance] = Field(..., description="Phyla relative abundance")
    firmicutes_bacteroidetes_ratio: float = Field(..., description="F/B ratio")
    predominant_genera: list[TaxonomicAbundance] = Field(..., description="Predominant genera")
    detected_species: list[TaxonomicAbundance] = Field(..., description="Detected species")


class FunctionalMarkers(BaseModel):
    """Functional and microbiological markers."""
    butyrate_producers: str = Field(..., description="Butyrate producing bacteria status")
    propionate_producers: str = Field(..., description="Propionate producing bacteria status")
    suggested_enterotype: str = Field(..., description="Suggested enterotype (e.g., Type Bacteroides)")
    opportunistic_microorganisms: list[dict[str, str]] = Field(..., description="Opportunistic pathogens status")
    functional_genes: dict[str, str] = Field(..., description="Inferred functional genes (PICRUSt)")


class StudyMetadata(BaseModel):
    """Administrative and demographic metadata."""
    study_code: str = Field(..., description="Biotasys study code")
    lab_internal_code: str = Field(..., description="Internal laboratory code")
    patient_id: str = Field(..., description="Patient identifier")
    sex: str = Field(..., description="Patient sex")
    age: int = Field(..., description="Patient age")
    sample_collection_date: datetime = Field(..., description="Date of sample collection")
    sample_reception_date: datetime = Field(..., description="Date of sample reception")
    sample_type: str = Field(default="Materia fecal")


class ClinicalContext(BaseModel):
    """Clinical history and observations."""
    inflammatory_markers: str = Field(..., description="Associated inflammatory markers")
    antibiotic_use: bool = Field(..., description="Recent use of antibiotics")
    probiotic_use: bool = Field(..., description="Use of probiotics")
    dietary_pattern: str = Field(..., description="Declared dietary pattern")
    lab_observations: str = Field(..., description="Lab technical observations")


class ClinicalObservation(BaseModel):
    """A technical observation or alert."""
    title: str = Field(..., description="Observation title")
    severity: str = Field(..., description="Level: Info, Warning, Alert")
    description: str = Field(..., description="Technical explanation")


class FunctionalInterpretation(BaseModel):
    """Interpretation of metabolic pathways."""
    pathway: str
    status: str = Field(..., description="Evaluation: Optimal, Reduced, Enhanced")
    note: str


class MicrobiotaInterpretation(BaseModel):
    """Advanced technical report generated by Gemini 3 Pro."""
    summary: str = Field(..., description="Qualitative general overview")
    diversity_analysis: str = Field(..., description="Technical interpretation of richness and homogeneity")
    taxonomic_balance: list[ClinicalObservation] = Field(..., description="Alerts on dominance or ratios")
    metabolic_profile: list[FunctionalInterpretation] = Field(..., description="Assessment of functional genes")
    opportunistic_risk: list[ClinicalObservation] = Field(..., description="Pathogen alerts")
    final_technical_notes: str = Field(..., description="Synthesized technical closure")


class MicrobiotaReport(BaseModel):
    """Full structured microbiota report with its technical interpretation."""
    metadata: StudyMetadata
    sequencing: SequencingData
    diversity: DiversityIndices
    taxonomy: TaxonomicComposition
    functionality: FunctionalMarkers
    clinical_context: ClinicalContext
    interpretation: MicrobiotaInterpretation | None = Field(default=None, description="Detailed analysis from Gemini 3 Pro")
    engine_version: str = Field(default="1.1.0", description="Version of the analysis engine")
    processed_at: datetime = Field(default_factory=datetime.now)


class AnalysisRequest(BaseModel):
    """Payload requirement from Backend A to Backend B (Biotasys Engine)."""
    file_url: str = Field(..., description="The Supabase Storage URL of the PDF/Image")
    documento_id: str = Field(..., description="Unique ID of the report in the source system")
    empresa_id: str = Field(..., description="Clinic/Lab owner ID")
    doctor_id: str = Field(..., description="Requesting doctor ID")
    fecha_envio: datetime = Field(..., description="Original timestamp from system A")
