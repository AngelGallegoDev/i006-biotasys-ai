"""AI service for Gemini integration using the modern google-genai SDK."""

from google import genai
from google.genai import types
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from app.config.settings import settings
from app.core.logging import get_logger
from app.core.exceptions import AIError
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

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(Exception),  # Better: capture specific SDK errors if possible
        reraise=True
    )
    async def analyze_microbiota_document(self, file_bytes: bytes, mime_type: str) -> MicrobiotaReport:
        """
        Extract structured data from report (PDF/Image) using the high-speed extractor.
        """
        try:
            logger.info(f"Extracting technical data using {self.extractor_model}")
            
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
            raise AIError("Gemini Extraction Engine failed", details=str(e))

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(Exception),
        reraise=True
    )
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

            prompt = f"Basado en los siguientes datos técnicos extraídos, genera la interpretación técnica detallada:\n\n{data.model_dump_json()}"

            response = await self.client.aio.models.generate_content(
                model=self.interpreter_model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    response_mime_type="application/json",
                    response_schema=MicrobiotaInterpretation,
                    temperature=0.7,
                ),
            )
            return response.parsed

        except Exception as e:
            logger.error(f"Interpretation error: {str(e)}")
            raise AIError("Gemini Interpretation Engine failed", details=str(e))

    async def health_check(self) -> bool:
        """Check if the Gemini service is reachable."""
        try:
            await self.client.aio.models.get(model=self.extractor_model)
            return True
        except Exception:
            return False

    async def close(self):
        """Logging shutdown."""
        logger.info("Gemini service client shutdown")


# Global AI service instance
ai_service = AIService()
