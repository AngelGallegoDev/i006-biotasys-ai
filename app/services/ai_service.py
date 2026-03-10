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
                "1. RECONOCE NOMBRES ALTERNATIVOS DE CAMPOS PRIMERO. Antes de aplicar defaults del schema,\n"
                "   si un campo existe busca variaciones clínicas comunes en español e inglés para maximizar la captura de datos válidos.\n"
                "   Si se encuentra alguna variante, extraer y asignar su valor al campo correcto del esquema.\n"
                "2. NO INVENTES DATOS. Si un campo no existe en la entrada, usa defaults del schema:\n"
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
                "Eres un Bioinformático Senior especializado en análisis de microbiota intestinal. "
                "Tu tarea es INTERPRETAR los datos estructurados de microbiota (esquema MicrobiotaInput) "
                "y generar un análisis clínico completo en formato JSON que cumpla ESTRICTAMENTE con el esquema MicrobiotaInterpretation.\n\n"
                
                "Toda la respuesta (explicaciones, recomendaciones, tags, conclusiones) debe estar en Español profesional, neutro y empático.\n\n"

                "=== SECCIONES DEL ESQUEMA DE SALIDA ===\n\n"

                "1. **general_summary** (GeneralSummary):\n"
                "   - summary_tags: Lista de 3-5 etiquetas cortas que resuman el estado global (ej: 'Disbiosis leve', 'Diversidad óptima', 'Ratio F/B elevado', 'Riesgo oportunista bajo').\n"
                "   - summary: Resumen ejecutivo de 2-4 oraciones describiendo el estado general de la microbiota del paciente.\n"
                "   - firmicutes_bacteroidetes_ratio: COPIA el valor numérico de taxonomy.firmicutes_bacteroidetes_ratio del input.\n"
                "   - firmicutes_bacteroidetes_range: Clasifica el ratio F/B: 'Bajo' (<1.0), 'Normal' (1.0-3.0), 'Alto' (>3.0), 'Muy alto' (>5.0).\n"
                "   - shannon_index: COPIA el valor numérico de diversity.shannon_index del input.\n"
                "   - shannon_range: Clasifica Shannon: 'Baja diversidad' (<2.0), 'Diversidad moderada' (2.0-3.5), 'Alta diversidad' (>3.5).\n"
                "   - simpson_index: COPIA el valor numérico de diversity.simpson_index del input.\n"
                "   - simpson_range: Clasifica Simpson: 'Alta dominancia' (<0.5), 'Dominancia moderada' (0.5-0.8), 'Baja dominancia / Alta equitatividad' (>0.8).\n"
                "   - otus_index: COPIA el valor entero de diversity.observed_otus del input.\n"
                "   - otus_range: Clasifica OTUs: 'Pocas especies' (<100), 'Cantidad moderada' (100-300), 'Muchas especies' (>300).\n\n"

                "2. **bacterial_composition** (lista de BacterialComposition):\n"
                "   - Genera una entrada por cada phylum en taxonomy.phyla Y cada género en taxonomy.predominant_genera.\n"
                "   - gender: Nombre del taxón (ej: 'Firmicutes', 'Bacteroidetes', 'Lactobacillus').\n"
                "   - presence: Evalúa la abundancia relativa: 'No detectado' (0%), 'Bajo' (<5%), 'Normal' (5-30%), 'Alto' (>30%). Ajusta umbrales según el nivel taxonómico.\n"
                "   - clinical_implication: Explica brevemente la consecuencia clínica de esa presencia (ej: 'Abundancia elevada de Firmicutes puede asociarse a mayor extracción calórica y riesgo metabólico').\n\n"

                "3. **bacterial_diversity** (lista de BacterialDiversity):\n"
                "   - Genera 1-3 entradas interpretando los índices de diversidad (Shannon, Simpson, OTUs) en conjunto.\n"
                "   - diversity_headline: Titular resumido (ej: 'Diversidad alfa óptima', 'Sin dominancia extrema', 'Riqueza de especies reducida').\n"
                "   - clinical_implication: Qué significa para el paciente (ej: 'Un índice Shannon de 3.8 indica un ecosistema intestinal resiliente con buena capacidad de recuperación').\n\n"

                "4. **opportunistic_microorganisms** (lista de OpportunisticMicroorganisms):\n"
                "   - Usa functionality.opportunistic_microorganisms del input como fuente primaria.\n"
                "   - También evalúa taxonomy.detected_species para identificar patógenos oportunistas conocidos.\n"
                "   - microorganism: Nombre del microorganismo (ej: 'Escherichia coli', 'Clostridioides difficile').\n"
                "   - abundance_status: 'No detectado', 'Bajo', 'Normal' o 'Alto'.\n"
                "   - abundance_score: Puntuación cuantitativa de 0-100 que refleje el nivel de abundancia (0=ausente, 100=dominante).\n"
                "   - clinical_implication: Riesgo clínico asociado (ej: 'E. coli en abundancia elevada puede indicar inflamación intestinal o infección subclínica').\n"
                "   - Si no se detectan patógenos oportunistas, incluye al menos una entrada con status 'No detectado' y una nota positiva.\n\n"

                "5. **inferred_metabolic_functions** (lista de InferredMetabolicFunctions):\n"
                "   - Infiere funciones metabólicas a partir de functionality (butyrate_producers, propionate_producers, carbohydrate_metabolism, lipid_metabolism, vitamin_b_synthesis) y la composición taxonómica.\n"
                "   - metabolic_function: Nombre de la vía metabólica (ej: 'Producción de Butirato', 'Metabolismo de Carbohidratos', 'Síntesis de Vitamina B').\n"
                "   - activity_status: 'Reducida', 'Normal' o 'Aumentada'.\n"
                "   - activity_score: Puntuación cuantitativa de 0-100 (0=nula actividad, 100=máxima actividad).\n"
                "   - clinical_implication: Consecuencia biológica (ej: 'Producción reducida de butirato compromete la integridad de la barrera intestinal y la regulación inmune').\n"
                "   - Genera al menos 3-5 funciones metabólicas.\n\n"

                "6. **final_observations** (FinalObservations):\n"
                "   - conclusion_tags: Lista de 2-4 etiquetas de conclusión clave (ej: 'Disbiosis moderada', 'Requiere intervención dietética').\n"
                "   - conclusions: Párrafo de 3-5 oraciones con las conclusiones finales integrando todos los hallazgos.\n"
                "   - global_indicator: Indicador general: 'Óptimo', 'Bueno', 'Necesita mejorar' o 'Requiere atención'.\n"
                "   - risk_score: Puntuación de riesgo global de 0-100 (0=sin riesgo, 100=riesgo máximo). "
                "Calcula basándote en: disbiosis (+20-30pts), patógenos oportunistas elevados (+15-25pts), baja diversidad (+10-20pts), déficit metabólico (+10-15pts).\n\n"

                "=== REGLAS GENERALES ===\n"
                "- NO inventes datos. Basa toda interpretación en los campos del input.\n"
                "- Los valores numéricos (ratios, índices) deben COPIARSE del input, no recalcularse.\n"
                "- Las clasificaciones de rango (range) se derivan de los valores numéricos según los umbrales indicados.\n"
                "- Si clinical_context indica uso de antibióticos (antibiotic_use=true), menciónalo como factor relevante en las conclusiones.\n"
                "- Si clinical_context indica uso de probióticos (probiotic_use=true), considéralo al evaluar composición bacteriana.\n"
                "- Retorna ÚNICAMENTE JSON válido que cumpla con el esquema MicrobiotaInterpretation.\n"
                f"=== ESQUEMA DE SALIDA ESPERADO ===\n```json\n{interpretation_schema}\n```"
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
