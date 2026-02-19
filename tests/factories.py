"""Factories for generating mock data using polyfactory."""

from datetime import datetime, UTC
from polyfactory.factories.pydantic_factory import ModelFactory
from app.models.schemas import (
    MicrobiotaReport,
    TaxonomicComposition,
    TaxonomicAbundance,
    DiversityIndices,
    SequencingData,
    StudyMetadata,
    ClinicalContext,
    FunctionalMarkers,
    MicrobiotaInterpretation
)

class MicrobiotaReportFactory(ModelFactory[MicrobiotaReport]):
    __model__ = MicrobiotaReport

    @classmethod
    def build(cls, **kwargs) -> MicrobiotaReport:
        # High-rigor manual building for critical clinical fields to avoid validation errors
        report = super().build(**kwargs)
        
        # Override with biologically valid data
        report.diversity.shannon_index = 3.5
        report.diversity.simpson_index = 0.95
        report.diversity.observed_otus = 1200
        
        report.sequencing.total_reads = 50000
        report.sequencing.filtered_reads = 45000
        
        # Taxonomy fix
        report.taxonomy.phyla = [
            TaxonomicAbundance(name="Firmicutes", abundance=60.0),
            TaxonomicAbundance(name="Bacteroidetes", abundance=30.0),
            TaxonomicAbundance(name="Actinobacteria", abundance=5.0)
        ]
        report.taxonomy.firmicutes_bacteroidetes_ratio = 2.0
        report.taxonomy.other_phyla_abundance = 5.0
        
        report.metadata.sample_collection_method = "Toma directa con hisopo"
        report.metadata.transport_conditions = "Refrigerado 4°C"
        report.metadata.sample_status = "Aceptable"
        
        report.functionality.carbohydrate_metabolism = "Normal"
        report.functionality.lipid_metabolism = "Aumentado"
        report.functionality.vitamin_b_synthesis = "Reducido"
        
        return report
