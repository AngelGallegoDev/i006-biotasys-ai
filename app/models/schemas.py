"""Pydantic models for request/response schemas."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator


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
    technology: str = Field(default="No disponible")
    region: str = Field(default="No disponible")
    platform: str = Field(default="No disponible")
    total_reads: int = Field(default=0)
    filtered_reads: int = Field(default=0)


class DiversityIndices(BaseModel):
    """Ecological diversity and richness metrics."""
    shannon_index: float = Field(default=0.0)
    simpson_index: float = Field(default=0.0)
    observed_otus: int = Field(default=0)


class TaxonomicAbundance(BaseModel):
    """Relative abundance of a taxonomic unit."""
    name: str = Field(..., description="Name of the taxon")
    abundance: float = Field(..., description="Relative abundance percentage")


class TaxonomicComposition(BaseModel):
    """Distribution of bacteria across different levels."""
    phyla: list[TaxonomicAbundance] = Field(default_factory=list)
    firmicutes_bacteroidetes_ratio: float = Field(default=0.0)
    predominant_genera: list[TaxonomicAbundance] = Field(default_factory=list)
    detected_species: list[TaxonomicAbundance] = Field(default_factory=list)
    other_phyla_abundance: float = Field(default=0.0, description="Cumulative abundance of all other phyla not explicitly listed")


class OpportunisticPathogen(BaseModel):
    """Status of a specific opportunistic microorganism."""
    genus: str = Field(..., description="Genus name")
    species: str = Field(default="spp.")
    status: str = Field(default="No detectado")
    note: str | None = None


class FunctionalMarkerItem(BaseModel):
    """Evaluation of a specific functional pathway or gene."""
    marker_name: str
    status: str = Field(default="Normal")
    value: str | None = None


class FunctionalMarkers(BaseModel):
    """Functional and microbiological markers."""
    butyrate_producers: str = Field(default="No disponible")
    propionate_producers: str = Field(default="No disponible")
    suggested_enterotype: str = Field(default="No disponible")
    opportunistic_microorganisms: list[OpportunisticPathogen] = Field(default_factory=list)
    functional_markers_list: list[FunctionalMarkerItem] = Field(default_factory=list)
    # PICRUSt Functional Genes
    carbohydrate_metabolism: str = Field(default="No disponible", description="Inferred metabolic level for Carbohydrates")
    lipid_metabolism: str = Field(default="No disponible", description="Inferred metabolic level for Lipids")
    vitamin_b_synthesis: str = Field(default="No disponible", description="Inferred level for Vitamin B Group synthesis")


class StudyMetadata(BaseModel):
    """Administrative and demographic metadata."""
    study_code: str = Field(default="No disponible")
    lab_internal_code: str = Field(default="No disponible")
    patient_id: str = Field(default="No disponible")
    sex: str = Field(default="No disponible")
    age: int = Field(default=0)
    sample_collection_date: datetime | None = None
    sample_reception_date: datetime | None = None
    sample_type: str = Field(default="Materia fecal")
    sample_collection_method: str = Field(default="No disponible")
    transport_conditions: str = Field(default="No disponible")
    sample_status: str = Field(default="No disponible")


class ClinicalContext(BaseModel):
    """Clinical history and observations."""
    inflammatory_markers: str = Field(default="No disponible")
    antibiotic_use: bool = Field(default=False)
    probiotic_use: bool = Field(default=False)
    dietary_pattern: str = Field(default="No disponible")
    lab_observations: str = Field(default="No disponible")


class ClinicalObservation(BaseModel):
    """A technical observation or alert."""
    title: str
    severity: str
    description: str


class FunctionalInterpretation(BaseModel):
    """Interpretation of metabolic pathways."""
    pathway: str
    status: str
    note: str


class DiversityDiagnosis(BaseModel):
    """Structured interpretation of diversity metrics."""
    score: float = Field(..., description="The calculated diversity score (e.g. Shannon)")
    interpretation: str = Field(..., description="Qualitative assessment (e.g. 'High', 'Low', 'Optimal')")
    clinical_implication: str = Field(..., description="What this means for the patient")


class MetabolicFunction(BaseModel):
    """Inferred metabolic capability based on bacterial abundance."""
    pathway: str = Field(..., description="Metabolic pathway (e.g. 'Butyrate Production')")
    status: str = Field(..., description="Activity level (e.g. 'Reduced', 'Normal', 'Enhanced')")
    associated_bacteria: list[str] = Field(default_factory=list, description="Bacteria driving this finding")
    implication: str = Field(..., description="Biological consequence")


class EnterotypeClassification(BaseModel):
    """Enterotype classification based on dominant genera."""
    enterotype: str = Field(..., description="Primary enterotype (e.g. 'Bacteroides')")
    confidence: str = Field(default="Medium", description="Confidence level of classification")
    description: str = Field(..., description="Characteristics of this enterotype")


class MicrobiotaInterpretation(BaseModel):
    """Advanced technical report generated by Gemini 3 Pro."""
    summary: str = Field(..., description="Executive summary of the microbiota status")
    diversity_diagnosis: DiversityDiagnosis
    enterotype_analysis: EnterotypeClassification
    taxonomic_balance: list[ClinicalObservation] = Field(default_factory=list)
    metabolic_potential: list[MetabolicFunction] = Field(default_factory=list)
    opportunistic_risk: list[ClinicalObservation] = Field(default_factory=list)
    final_technical_notes: str


class MicrobiotaReport(BaseModel):
    """Full structured microbiota report."""
    metadata: StudyMetadata = Field(default_factory=StudyMetadata)
    sequencing: SequencingData = Field(default_factory=SequencingData)
    diversity: DiversityIndices = Field(default_factory=DiversityIndices)
    taxonomy: TaxonomicComposition = Field(default_factory=TaxonomicComposition)
    functionality: FunctionalMarkers = Field(default_factory=FunctionalMarkers)
    clinical_context: ClinicalContext = Field(default_factory=ClinicalContext)
    interpretation: MicrobiotaInterpretation | None = None
    engine_version: str = Field(default="1.2.5")
    processed_at: datetime = Field(default_factory=datetime.now)


class AnalysisRequest(BaseModel):
    """Payload requirement from Backend A to Backend B."""
    file_url: str
    documento_id: str
    empresa_id: str
    doctor_id: str
    fecha_envio: datetime
