import json
from typing import Any
from app.services.microbiota_normalizer import prenormalize_microbiota


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
    # async def analyze_microbiota_document(self, file_bytes: bytes, mime_type: str) -> MicrobiotaReport:
    #     """
    #     Extract structured data from report (PDF/Image) using the high-speed extractor.
    #     """
    #     try:
    #         logger.info(f"Extracting technical data using {self.extractor_model}")
            
    #         system_instruction = (
    #             "Eres un experto Bioinformático. Tu tarea es extraer datos de un informe de laboratorio de microbiota. "
    #             "Genera una respuesta JSON que cumpla ESTRICTAMENTE con el esquema proporcionado. "
    #             "No inventes datos. Si un campo no se encuentra, usa valores por defecto (0 para números, 'No disponible' para texto). "
    #             "PRESTA ESPECIAL ATENCIÓN A: "
    #             "1. Gestión de la muestra (método, transporte, estado). "
    #             "2. Otros phyla (calcula la abundancia acumulada de filos no listados). "
    #             "3. Ratio Firmicutes/Bacteroidetes: Si el ratio no aparece explícitamente pero tienes las abundancias de ambos filos, CALCÚLALO (Firmicutes / Bacteroidetes). "
    #             "4. Genes funcionales (PICRUSt)."
    #         )

    #         contents = [
    #             types.Content(
    #                 role="user",
    #                 parts=[
    #                     types.Part.from_bytes(data=file_bytes, mime_type=mime_type),
    #                     types.Part.from_text(text="Analiza este documento y extrae la información técnica en formato JSON.")
    #                 ]
    #             )
    #         ]

    #         response = await self.client.aio.models.generate_content(
    #             model=self.extractor_model,
    #             contents=contents,
    #             config=types.GenerateContentConfig(
    #                 system_instruction=system_instruction,
    #                 response_mime_type="application/json",
    #                 response_schema= None,  # No schema validation for extraction output, we will validate manually
    #                 temperature=0.1,
    #             ),
    #         )

    #         data = json.loads(response.text)
    #         return json.loads(response.text)
            
    #         # if not response.parsed:
    #         #     # Log what we actually got
    #         #     raw_text = getattr(response, 'text', "No text field available")
    #         #     logger.error(f"Extraction failed to parse into schema. Raw output might be: {raw_text[:500]}")
    #         #     raise AIError("Extraction failed: Output did not match technical schema. Please check the document format.")

    #         # return response.parsed

    #     except Exception as e:
    #         logger.error(f"Extraction error: {str(e)}")
    #         if isinstance(e, AIError):
    #             raise e
    #         raise AIError("Gemini Extraction Engine failed", details=str(e))
        
    # @retry(
    #     stop=stop_after_attempt(3),
    #     wait=wait_exponential(multiplier=1, min=2, max=10),
    #     retry=retry_if_exception_type(Exception),
    #     reraise=True
    # )
       
    async def analyze_laboratory_json(self, raw_json: dict[str, Any]) -> MicrobiotaInput:
            """
            Parse and normalize raw laboratory JSON into MicrobiotaInput structure.
            """
    
            normalized_json = prenormalize_microbiota(raw_json)
            logger.debug(json.dumps(normalized_json, indent=2))
    
            try:
                logger.info(f"Normalizing raw laboratory JSON using {self.extractor_model}")
    
                microbiota_input_schema = MicrobiotaInput.model_json_schema()
    
                system_instruction = (
                    "You are a microbiome data normalization expert.\n\n"
                    "Your task is to transform raw microbiome laboratory JSON data into the exact "
                    "MicrobiotaInput schema.\n\n"
    
                    "Rules:\n"
                    "- Do not invent values\n"
                    "- If a value is missing use defaults\n"
                    "- Compute Firmicutes/Bacteroidetes ratio when possible\n"
                    "- Return ONLY valid JSON\n"
                )
    
                prompt = f"""
                 Transform the following laboratory JSON into the MicrobiotaInput schema.
    
                    === INPUT JSON ===
                    {json.dumps(normalized_json, indent=2, ensure_ascii=False)}
                    
                    === OUTPUT ===
                    Return ONLY valid JSON matching the schema.
                    """
    
                response = await self.client.aio.models.generate_content(
                    model=self.extractor_model,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=system_instruction,
                        response_mime_type="application/json",
                        response_schema=microbiota_input_schema,
                        temperature=0.1,
                    ),
                )
    
                if not response.parsed:
                    raw_text = getattr(response, "text", "No text field available")
                    logger.error(f"JSON normalization failed. Raw output: {raw_text[:500]}")
                    raise AIError("JSON normalization failed: Output did not match MicrobiotaInput schema.")
    
                logger.info("Successfully normalized JSON to MicrobiotaInput")
    
                return MicrobiotaInput.model_validate(response.parsed)
    
            except Exception as e:
                logger.error(f"Laboratory JSON analysis error: {str(e)}")
    
                if isinstance(e, AIError):
                    raise e
    
                raise AIError("Gemini JSON Normalization Engine failed", details=str(e))

    
    async def interpret_microbiota_data(self, microbiota_data: MicrobiotaInput) -> MicrobiotaInterpretation:
        """
        Generate advanced clinical reasoning using the Gemini interpreter model.
        """

        if not microbiota_data:
            raise AIError("Interpretation failed: Input data is null")

        try:
            logger.info(f"Interpreting microbiota data using {self.interpreter_model}")

            # Convert Pydantic model -> JSON limpio
            microbiota_dict = microbiota_data.model_dump(mode="json")

            microbiota_json = json.dumps(
                microbiota_dict,
                indent=2,
                ensure_ascii=False,
            )

            logger.debug(
                "MicrobiotaInput BEFORE INTERPRETATION:\n%s",
                microbiota_json,
            )

            # Obtener schema del modelo de salida
            interpretation_schema = MicrobiotaInterpretation.model_json_schema()

            interpretation_schema_str = json.dumps(
                interpretation_schema,
                indent=2,
                ensure_ascii=False,
            )

            system_instruction = (
                "Eres un Bioinformático Senior especializado en análisis de microbiota intestinal.\n\n"

                "Tu tarea es interpretar datos estructurados de microbiota en formato MicrobiotaInput "
                "y generar un análisis clínico completo que cumpla EXACTAMENTE con el esquema "
                "MicrobiotaInterpretation.\n\n"

                "Toda la respuesta debe estar en español profesional, claro y empático.\n\n"

                "REGLAS CRÍTICAS:\n"
                "- Debes usar los datos presentes en taxonomy.phyla y taxonomy.predominant_genera.\n"
                "- Si taxonomy.phyla contiene elementos, debes generar entradas correspondientes "
                "en bacterial_composition.\n"
                "- El campo firmicutes_bacteroidetes_ratio debe copiar el valor del input si existe.\n"
                "- No ignores valores existentes.\n"
                "- No inventes datos.\n"
                "- NUNCA incluyas el patient_id ni identificadores del paciente en general_summary.summary.\n\n"

                "LÍMITES DE LISTAS:\n"
                "- bacterial_diversity: EXACTAMENTE 3 items.\n"
                "- bacterial_composition: MÁXIMO 5 items (los más relevantes clínicamente).\n"
                "- opportunistic_microorganisms: MÁXIMO 5 items (los más relevantes clínicamente).\n"
                "- inferred_metabolic_functions: MÁXIMO 5 items (las más relevantes clínicamente).\n\n"
                
                "CLASIFICACIONES:\n"
                "Firmicutes/Bacteroidetes ratio:\n"
                "- Bajo <1.0\n"
                "- Normal 1.0–3.0\n"
                "- Alto >3.0\n"
                "- Muy alto >5.0\n\n"

                "Shannon:\n"
                "- Baja diversidad <2.0\n"
                "- Diversidad moderada 2.0–3.5\n"
                "- Alta diversidad >3.5\n\n"

                "Simpson:\n"
                "- Alta dominancia <0.5\n"
                "- Dominancia moderada 0.5–0.8\n"
                "- Baja dominancia / Alta equitatividad >0.8\n\n"

                "OTUs:\n"
                "- Pocas especies <100\n"
                "- Moderada 100–300\n"
                "- Alta >300\n\n"

                "Devuelve exclusivamente JSON válido que cumpla el esquema.\n\n"

                "=== OUTPUT JSON SCHEMA ===\n"
                f"{interpretation_schema_str}"
            )
            
            prompt = (
                "Analiza los siguientes datos técnicos de microbiota y genera una interpretación clínica.\n\n"
                "=== MICROBIOTA INPUT DATA ===\n"
                f"{microbiota_json}\n\n"
                "=== OUTPUT ===\n"
                "Devuelve únicamente JSON válido compatible con el schema indicado."
            )

            response = await self.client.aio.models.generate_content(
                model=self.interpreter_model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    response_mime_type="application/json",
                    response_schema=interpretation_schema,
                    temperature=0.7,
                ),
            )

            if not getattr(response, "parsed", None):
                raw_text = getattr(response, "text", "No text returned")
                logger.error(f"Interpretation failed. Raw model output: {raw_text[:500]}")
                raise AIError("Interpretation failed: LLM returned invalid JSON.")

            logger.info("Successfully interpreted microbiota data")

            if isinstance(response.parsed, MicrobiotaInterpretation):
                return response.parsed

            return MicrobiotaInterpretation.model_validate(response.parsed)

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
