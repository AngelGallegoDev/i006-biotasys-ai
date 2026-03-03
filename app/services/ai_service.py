import json
from typing import Any

"""AI service for Gemini integration using the modern google-genai SDK."""
from typing import Any
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
    MicrobiotaInput,
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
                "PRESTA ESPECIAL ATENCIÓN A: "
                "1. Gestión de la muestra (método, transporte, estado). "
                "2. Otros phyla (calcula la abundancia acumulada de filos no listados). "
                "3. Ratio Firmicutes/Bacteroidetes: Si el ratio no aparece explícitamente pero tienes las abundancias de ambos filos, CALCÚLALO (Firmicutes / Bacteroidetes). "
                "4. Genes funcionales (PICRUSt)."
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
    async def analyze_laboratory_json(self, raw_json: dict[str, Any]) -> MicrobiotaInput:
        """
        Parse and normalize raw laboratory JSON into MicrobiotaReport structure.
        """
        try:
            logger.info(f"Normalizing raw laboratory JSON using {self.extractor_model}")
            
            import json
            
            # Generate the JSON schema from the actual Pydantic model
            microbiota_input_schema = MicrobiotaInput.model_json_schema()
            json_schema = json.dumps(microbiota_input_schema, indent=2, ensure_ascii=False)

            system_instruction = (
                "Eres un experto en normalización de datos de laboratorio de microbiota. "
                "Tu tarea es transformar datos crudos (sin estructura definida) en un formato JSON estructurado "
                "que cumpla ESTRICTAMENTE con el siguiente esquema Pydantic:\n\n"
                f"```json\n{json_schema}\n```\n\n"
                
                "REGLAS CRÍTICAS:\n"
                "1. NO INVENTES DATOS. Si un campo no existe en la entrada, usa defaults del schema:\n"
                "   - Números: 0\n"
                "   - Strings: 'No disponible'\n"
                "   - Listas: [] (vacío)\n"
                "   - Booleanos: false\n"
                "2. CALCULA el ratio Firmicutes/Bacteroidetes si tienes ambos valores (Firmicutes / Bacteroidetes).\n"
                "3. Normaliza fechas al formato ISO 8601 (YYYY-MM-DDTHH:MM:SSZ).\n"
                "4. Abundancias taxonómicas: Asegúrate de que sumen aproximadamente 100%.\n"
                "5. Valida que 'observed_otus' sea un entero positivo.\n"
                "6. Retorna ÚNICAMENTE JSON válido que pase validación con el esquema anterior.\n"
            )    

            prompt = (
                f"Transforma los siguientes datos crudos de laboratorio al esquema MicrobiotaInput:\n\n"
                f"=== DATOS DE ENTRADA ===\n"
                f"{json.dumps(raw_json, indent=2, ensure_ascii=False)}\n\n"
                f"=== RESPUESTA (JSON ESTRUCTURADO) ===\n"
            )

            response = await self.client.aio.models.generate_content(
                model=self.extractor_model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    response_mime_type="application/json",
                    response_schema=MicrobiotaInput,
                    temperature=0.1,
                ),
            )

            if not response.parsed:
                raw_text = getattr(response, 'text', "No text field available")
                logger.error(f"JSON normalization failed. Raw output: {raw_text[:500]}")
                raise AIError("JSON normalization failed: Output did not match MicrobiotaInput schema.")

            logger.info(f"Successfully normalized JSON to MicrobiotaInput")
            return response.parsed

        except Exception as e:
            logger.error(f"Laboratory JSON analysis error: {str(e)}")
            if isinstance(e, AIError):
                raise e
            raise AIError("Gemini JSON Normalization Engine failed", details=str(e))

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(Exception),
        reraise=True
    )
    async def interpret_microbiota_data(self, microbiota_data: MicrobiotaInput) -> MicrobiotaInterpretation:
        """
        Generate advanced clinical reasoning using the powerful Gemini 3 Pro interpreter.
        """
        if not microbiota_data:
            raise AIError("Interpretation failed: Input data is null")
        
        try:
            logger.info(f"Interpreting data using {self.interpreter_model}")

            import json
            
            # Generate the Interpretation schema from the actual Pydantic model
            microbiota_interpretation_schema = MicrobiotaInterpretation.model_json_schema()
            interpretation_schema = json.dumps(microbiota_interpretation_schema, indent=2, ensure_ascii=False)
            
            system_instruction = (
                "Eres un Bioinformático Senior. Tu tarea es INTERPRETAR los datos de microbiota para generar INSIGHTS ESTRUCTURADOS y ACCIONABLES. "
                "CRÍTICO: Toda la respuesta (explicaciones, recomendaciones) debe ser en un Español profesional, neutro y empático. "
                "Usa los nuevos modelos definidos: "
                "1. GutHealthScore: Calcula un puntaje de 0-100. 100=Perfecto. Resta puntos por disbiosis, patógenos o baja diversidad. "
                "   - 'label': Excelente (>90), Bueno (>70), Regular (>50), Pobre (<50). "
                "   - 'breakdown': Explica brevemente por qué se restaron puntos. "
                "2. DietaryRecommendation: Genera 3-5 recomendaciones ESPECÍFICAS basadas en los hallazgos. "
                "   - Si falta Butirato -> Recomendar almidón resistente (papa fría, plátano verde). "
                "   - Si hay inflamación -> Recomendar Omega-3, Cúrcuma. "
                "   - Usa 'action': 'Aumentar', 'Reducir' o 'Evitar'. "
                "3. SupplementSuggestion: Sugiere probióticos/prebióticos solo si hay evidencia de déficit. "
                "   - Ej: 'Lactobacillus rhamnosus' si hay permeabilidad intestinal. "
                "4. DiversityDiagnosis y EnterotypeClassification: Mantén el rigor técnico previo. "
                "NO inventes datos. Si no hay evidencia clara para una recomendación, no la hagas.\n\n"
                f"ESQUEMA DE SALIDA ESPERADO:\n```json\n{interpretation_schema}\n```"
            )

            prompt = (
                f"Basado en los siguientes datos técnicos de microbiota extraídos, genera la interpretación clínica detallada:\n\n"
                f"=== DATOS TÉCNICOS EXTRAÍDOS ===\n"
                f"{microbiota_data}\n\n"
                f"=== INTERPRETACIÓN (JSON ESTRUCTURADO) ===\n"
            )

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
            
            logger.info(f"Successfully interpreted microbiota data")
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
