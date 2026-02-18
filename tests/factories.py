"""Factories for generating mock data using polyfactory."""

from datetime import datetime
from polyfactory.factories.pydantic_factory import ModelFactory
from polyfactory.decorators import post_generated
from app.models.schemas import (
    MicrobiotaReport, 
    StudyMetadata, 
    SequencingData, 
    DiversityIndices, 
    TaxonomicComposition,
    TaxonomicAbundance,
    FunctionalMarkers,
    ClinicalContext
)

class TaxonomicAbundanceFactory(ModelFactory[TaxonomicAbundance]):
    __model__ = TaxonomicAbundance

class TaxonomicCompositionFactory(ModelFactory[TaxonomicComposition]):
    __model__ = TaxonomicComposition
    
    @post_generated
    @classmethod
    def phyla(cls, name: str, **kwargs) -> list[TaxonomicAbundance]:
        # Generate semi-realistic phyla
        return [
            TaxonomicAbundance(name="Firmicutes", abundance=45.0),
            TaxonomicAbundance(name="Bacteroidetes", abundance=40.0),
            TaxonomicAbundance(name="Actinobacteria", abundance=10.0),
            TaxonomicAbundance(name="Others", abundance=5.0),
        ]

class MicrobiotaReportFactory(ModelFactory[MicrobiotaReport]):
    __model__ = MicrobiotaReport
    
    @classmethod
    def study_code(cls) -> str:
        return f"BIO-{datetime.now().year}-TEST-{cls.__random__.randint(1000, 9999)}"
