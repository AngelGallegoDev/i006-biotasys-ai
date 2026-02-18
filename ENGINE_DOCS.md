# 🩺 Biotasys Engine: Microservicio de IA B2B - Manual de Integración

## 📌 Introducción
El **Biotasys Engine** es un microservicio especializado en la extracción y normalización de datos de microbiota intestinal mediante IA Multimodal (**Gemini 2.5 Flash Lite**). Este manual define el contrato técnico para que el **Backend A** (Sistema de Gestión) se comunique correctamente con el **Backend B** (Motor de IA).

---

## 🚀 Arquitectura de Comunicación: Dual Engine Biotasys
El motor funciona bajo un modelo de **Oleadas de Inteligencia**:
1. **Extractor (Gemini 2.5 Flash Lite)**: Procesa la visión del PDF/Imagen para extraer tablas numéricas con latencia mínima.
2. **Interpreter (Gemini 3 Pro)**: Toma los datos extraídos y realiza razonamiento clínico profundo para generar el informe técnico jerárquico.

---

## 🛠️ Contrato de API

### 1. Ingesta, Extracción e Interpretación
**Endpoint:** `POST /api/v1/clinical/process-report`

#### Payload de Entrada (JSON)
```json
{
  "file_url": "https://[project].supabase.co/storage/v1/object/public/reports/informe_001.pdf",
  "documento_id": "doc_88273x",
  "empresa_id": "emp_coaxios_01",
  "doctor_id": "doc_perez_99",
  "fecha_envio": "2026-02-18T15:30:00Z"
}
```

#### Respuesta Exitosa (200 OK)
```json
{
  "engine_status": "success",
  "report_id": "uuid-interno-engine",
  "documento_id_origen": "doc_88273x",
  "data": {
    "metadata": { ... },
    "sequencing": { ... },
    "diversity": { ... },
    "taxonomy": { ... },
    "interpretation": {
      "summary": "Microbiota con signos de disbiosis leve...",
      "diversity_analysis": "Riqueza observada por debajo del percentil 25...",
      "taxonomic_balance": [
        { "title": "Ratio F/B Elevado", "severity": "Warning", "description": "Asociado a inflamación de bajo grado." }
      ],
      "metabolic_profile": [
        { "pathway": "Butyrate Production", "status": "Reduced", "note": "Baja presencia de Roseburia." }
      ],
      "opportunistic_risk": [...],
      "final_technical_notes": "Se sugiere seguimiento clínico."
    },
    "engine_version": "1.2.0 (Dual Engine: Flash-Lite + 3-Pro)",
    "processed_at": "2026-02-18T16:30:00Z"
  }
}
```

---

## 🛡️ Reglas de Validación y Errores

1. **Error 422 (Unprocessable Entity)**: Si faltan IDs obligatorios o el formato de fecha es inválido.
2. **Error 500 (Engine Failure)**:
   - URL de archivo inaccesible (404 en Storage).
   - Documento corrupto o ilegible por la IA.
   - Error de conexión con Supabase DB.

---

## 📝 Notas para el Equipo de Desarrollo (Backend A)
- **Signed URLs**: Se recomienda enviar URLs firmadas si el bucket de Supabase es privado.
- **Idempotencia**: Si se envía el mismo `documento_id` dos veces, el Engine generará un nuevo registro (versión) a menos que se implemente lógica de deduplicación en el futuro.
- **Latencia**: El proceso de análisis multimodal + persistencia toma entre 3 y 8 segundos. Se recomienda un loader en el frontend.

---
*Biotasys Engine v1.0.0 - Documentación Generada por Antigravity Protocol*
