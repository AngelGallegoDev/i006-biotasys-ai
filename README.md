# Biotasys AI - Microbiota Analysis Engine 🧬🤖

**Biotasys Engine** es un núcleo de procesamiento clínico avanzado diseñado para la extracción e interpretación técnica de informes de microbiota. Utiliza una arquitectura de **Dual Engine** sobre Google Gemini para transformar datos no estructurados (PDF/Imágenes) en informes bioinformáticos de alta precisión.

---

## 🚀 Arquitectura Dual Engine

El sistema orquestado en `AIService` utiliza dos modelos especializados para maximizar la velocidad y la profundidad analítica:

1.  **Extraction Engine (Gemini 2.5 Flash Lite):** Optimizado para la extracción masiva de datos estructurados (abundancias taxonómicas, índices de diversidad, marcadores funcionales) con latencia mínima.
2.  **Interpretation Engine (Gemini 3 Pro):** Consultoría técnica de alto nivel que genera razonamiento clínico sobre el balance taxonómico, riesgos de oportunistas y perfiles metabólicos siguiendo el PRD de Biotasys.

---

## 🛠️ Tech Stack & Rigor Técnico

*   **Backend:** FastAPI (Python 3.11+) - Async-first architecture.
*   **AI SDK:** `google-genai` (Modern SDK integration).
*   **Database & Persistence:** Supabase (PostgreSQL + RLS).
*   **Validation:** Pydantic V2 (Strict typing for clinical schemas).
*   **Linter & Formatter:** Ruff (High-performance linting).
*   **Testing:** Pytest (Unit, Integration, API & Resilience battery).

---

## 📦 Estructura del Proyecto (Clean Architecture)

```text
app/
├── api/v1/             # Routers (Endpoints: Health, Clinical)
├── core/               # Security, Logging, Custom Exceptions
├── config/             # Settings (Pydantic Settings)
├── models/             # Clinical Schemas (MicrobiotaReport, Diversity, etc.)
├── repositories/       # Data Access Layer (Supabase Persistence)
└── services/           # Business Logic & AI Orchestration
tests/
├── unit/               # Mocks for AI and Repositories
├── integration/        # Full Pipeline & Resilience (Early Failure)
└── api/                # Endpoint validation (HTTPX)
```

---

## 🛡️ Protocolo de Resiliencia y Errores

El motor implementa una jerarquía de excepciones propia (**BiotasysException**) para garantizar que el Frontend reciba diagnósticos claros:

*   `AIError`: Fallos en el motor de Gemini o validación de salida.
*   `DatabaseError`: Problemas de persistencia en la capa de datos.
*   `ResourceNotFoundError`: Recursos clínicos inexistentes (404 personalizado).
*   `ValidationError`: Datos que no cumplen con el rigor técnico requerido.

---

## 🚦 Quick Start

### 1. Variables de Entorno
Crea un archivo `.env` basado en `env.example`:
```env
GEMINI_API_KEY=tu_clave_aqui
EXTRACTION_MODEL=gemini-2.5-flash-lite
INTERPRETATION_MODEL=gemini-3-pro
SUPABASE_URL=...
SUPABASE_KEY=...
```

### 2. Instalación y Ejecución
```bash
# Instalar dependencias
pip install -e .

# Ejecutar el servidor (Development)
python main.py
```

### 3. Ejecutar Batería de Tests (Rigor Pro)
```bash
# Ejecutar todos los niveles de prueba
pytest

# Ejecutar con reporte de cobertura
pytest --cov=app tests/
```

---

## 📄 API Endpoints Principales

*   `POST /api/v1/clinical/process-report`: Orquestación completa (Descarga -> Extracción -> Interpretación -> Guardado).
*   `GET /api/v1/clinical/report/{id}`: Recuperación de informes procesados.
*   `GET /api/v1/health`: Estado de salud del sistema y conectividad con la IA.

---

## ⚠️ Mandatos de Desarrollo (The Purge)

1.  **Async-First:** Prohibido código bloqueante en la capa de servicios.
2.  **KISS:** No añadir complejidad innecesaria (ej. capas de "Chat" genéricas).
3.  **Rigor:** Cualquier cambio en los modelos `MicrobiotaReport` debe ser validado por la batería de tests unitarios antes del commit.

---
**Biotasys AI** - *The future of Microbiota Interpretation.*