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
        print(f"DEBUG: Initializing AIService with extractor={self.extractor_model}, interpreter={self.interpreter_model}")
        logger.info(
            f"AI Service initialized. Ready for Extraction ({self.extractor_model}) and Interpretation ({self.interpreter_model})"
        )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(Exception),
        reraise=True
    )
    async def analyze_microbiota_document(self, file_bytes: bytes, mime_type: str) -> MicrobiotaReport:
        """
        Extract structured data from report (PDF/Image) using the high-speed extractor.
        """
        try:
            logger.info(f"Extracting technical data using {self.extractor_model}")
            
            system_instruction = (
                "Eres un experto Bioinformático. Tu tarea es extraer datos de un informe de laboratorio de microbiota. "
                "Genera una respuesta JSON que cumpla ESTRICTAMENTE con el esquema proporcionado. "
                "No inventes datos. Si un campo no se encuentra, usa valores por defecto (0 para números, 'No disponible' para texto). "
                "Presta especial atención a: 1. Gestión de la muestra (método, transporte, estado), 2. Otros phyla, 3. Genes funcionales (PICRUSt)."
            )

            contents = [
                types.Content(
                    role="user",
                    parts=[
                        types.Part.from_bytes(data=file_bytes, mime_type=mime_type),
                        types.Part.from_text(text="Analiza este documento y extrae la información técnica en formato JSON.")
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
            
            if not response.parsed:
                # Log what we actually got
                raw_text = getattr(response, 'text', "No text field available")
                logger.error(f"Extraction failed to parse into schema. Raw output might be: {raw_text[:500]}")
                raise AIError("Extraction failed: Output did not match technical schema. Please check the document format.")

            return response.parsed

        except Exception as e:
            logger.error(f"Extraction error: {str(e)}")
            if isinstance(e, AIError):
                raise e
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
        if not data:
            raise AIError("Interpretation failed: Input data is null")

        try:
            logger.info(f"Interpreting data using {self.interpreter_model}")
            
            system_instruction = (
                "Eres un Bioinformático Senior en Biotasys. Tu tarea es INTERPRETAR los datos de microbiota para generar INSIGHTS ESTRUCTURADOS. "
                "No escribas bloques de texto vacíos. Usa los modelos: "
                "1. DiversityDiagnosis: Evalúa Shannon/Simpson. Define si es 'Alta', 'Baja', 'Normal'. "
                "2. EnterotypeClassification: Identifica si es Bacteroides, Prevotella o Ruminococcus. "
                "3. MetabolicFunction: Infiere producción de Butirato, Propionato, Triptófano basándote en géneros clave (Roseburia, Faecalibacterium, etc). "
                "4. ClinicalObservation: Genera alertas para Ratios F/B alterados o patógenos detectados. "
                "NO inventes datos. Si no hay evidencia clara, usa 'Indeterminado'."
                "NO emitas diagnósticos médicos ('Tiene Diabetes'), solo observaciones técnicas ('Asociado a resistencia a insulina')."
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

            if not response.parsed:
                raise AIError("Interpretation failed: Gemini returned null parsed data.")

            return response.parsed

        except Exception as e:
            logger.error(f"Interpretation error: {str(e)}")
            if isinstance(e, AIError):
                raise e
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
