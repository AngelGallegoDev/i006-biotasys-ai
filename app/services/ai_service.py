"""AI service for Gemini integration using the modern google-genai SDK."""

import time
import uuid

from google import genai
from google.genai import types

from app.config.settings import settings
from app.core.logging import get_logger
from app.core.security import mask_api_key
from app.models.schemas import (
    MicrobiotaReport,
    MicrobiotaInterpretation,
)

logger = get_logger(__name__)


class AIService:
    """
    Service for interacting with Google Gemini API.
    Biotasys Dual Engine:
    - Extraction: Gemini 2.5 Flash Lite
    - Interpretation: Gemini 3 Pro
    """

    def __init__(self):
        """Initialize the Gemini AI service."""
        self.client = genai.Client(api_key=settings.gemini_api_key)
        self.extractor_model = settings.extraction_model
        self.interpreter_model = settings.interpretation_model
        logger.info(
            f"AI Service initialized. Models: Extractor={self.extractor_model}, Interpreter={self.interpreter_model}"
        )

    async def analyze_microbiota_document(self, file_bytes: bytes, mime_type: str) -> MicrobiotaReport:
        """
        Extract structured data from report (PDF/Image) using the high-speed extractor.
        """
        try:
            logger.info(f"Extracting data using {self.extractor_model}")
            
            system_instruction = (
                "Eres un experto Bioinformático. Tu tarea es la EXTRACCIÓN de datos técnicos. "
                "Sé preciso con los números y nombres de bacterias. Si no está, usa 0 o 'No disponible'."
            )

            contents = [
                types.Content(
                    role="user",
                    parts=[
                        types.Part.from_bytes(data=file_bytes, mime_type=mime_type),
                        types.Part.from_text(text="Extrae la información técnica del informe de microbiota.")
                    ]
                )
            ]

            response = await self.client.aio.models.generate_content(
                model=self.extractor_model,
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    response_mime_type="application/json",
                    response_schema=MicrobiotaReport,
                    temperature=0.1,
                ),
            )
            return response.parsed

        except Exception as e:
            logger.error(f"Extraction error: {str(e)}")
            raise e

    async def interpret_microbiota_data(self, data: MicrobiotaReport) -> MicrobiotaInterpretation:
        """
        Generate advanced clinical reasoning using the powerful Gemini 3 Pro interpreter.
        """
        try:
            logger.info(f"Interpreting data using {self.interpreter_model}")
            
            system_instruction = (
                "Eres un Bioinformático Senior en Biotasys. Tu tarea es INTERPRETAR los datos de microbiota. "
                "Genera un informe técnico jerárquico siguiendo el PRD de Biotasys. "
                "Criterios: Analizar diversidad (Shannon/Simpson), balance taxonómico (F/B), "
                "peligro de oportunistas y perfil metabólico. "
                "NO emitir diagnósticos médicos ni recomendaciones de tratamiento, solo observaciones técnicas. "
                "Usa un tono profesional, jerárquico y estructurado."
            )

            # Pass the extracted JSON to the interpreter
            prompt = f"Basado en los siguientes datos técnicos extraídos, genera la interpretación técnica detallada:\n\n{data.model_dump_json()}"

            response = await self.client.aio.models.generate_content(
                model=self.interpreter_model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    response_mime_type="application/json",
                    response_schema=MicrobiotaInterpretation,
                    temperature=0.7,  # Slight creative temperature for synthesis
                    # Thinking Level can be added here if supported by the SDK
                ),
            )
            return response.parsed

        except Exception as e:
            logger.error(f"Interpretation error: {str(e)}")
            raise e

    async def analyze_microbiota_report(self, raw_text: str) -> MicrobiotaReport:
        """
        Analyze a raw microbiota document (PDF or Image) and extract structured data.
        Uses Gemini's multimodal capability.
        """
        try:
            logger.info(f"Starting multimodal extraction from document: {mime_type}")
            
            system_instruction = (
                "Eres un experto Bioinformático y Analista de Microbiota en Biotasys. "
                "Se te proporcionará un informe de laboratorio (PDF o Imagen). "
                "Tu tarea es extraer con precisión absoluta los datos técnicos. "
                "Busca métricas de diversidad, abundancias taxonómicas y marcadores funcionales. "
                "Ignora gráficos decorativos y enfócate en las tablas y valores numéricos. "
                "Si un valor no está presente, usa 0 para números y 'No disponible' para texto."
            )

            # Gemini 2.0 supports PDF and Images directly in the parts list
            contents = [
                types.Content(
                    role="user",
                    parts=[
                        types.Part.from_bytes(data=file_bytes, mime_type=mime_type),
                        types.Part.from_text(text="Extrae toda la información estructurada de este informe de microbiota.")
                    ]
                )
            ]

            response = await self.client.aio.models.generate_content(
                model=self.model_name,
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    response_mime_type="application/json",
                    response_schema=MicrobiotaReport,
                    temperature=0.1,
                ),
            )

            structured_data = response.parsed
            logger.info("Successfully extracted structured data from document")
            return structured_data

        except Exception as e:
            error_msg = f"Error in multimodal document analysis: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)

    async def health_check(self) -> bool:
        """Check if the AI service is healthy."""
        try:
            # Check if we can reach the model
            self.client.models.get(model=self.model_name)
            return True
        except Exception as e:
            logger.error(f"Gemini service health check failed: {str(e)}")
            return False

    async def close(self):
        """Close method for interface consistency (genai.Client handles connection pooling)."""
        logger.info("Gemini service client shutdown triggered")


# Global AI service instance
ai_service = AIService()
