# 🚀 Template FastAPI AI: Python + FastAPI + OpenRouter

¡Bienvenido! Este es un proyecto template moderno diseñado para desarrolladores que quieren construir aplicaciones web con IA integrada usando FastAPI, uv y OpenRouter.

## 📋 Descripción del Proyecto

Esta es una aplicación completa de API REST con integración de IA que incluye:

- **Backend**: Python 3.13+ + FastAPI + Google Gemini 2.0
- **Package Manager**: uv (ultra-rápido)
- **AI Integration**: Google GenAI SDK (Moderno / Gemini 2.0)
- **Database**: SQLAlchemy 2.0 (Async) + Supabase
- **Configuration**: Environment-based con Pydantic Settings
- **Documentation**: Auto-generada con Swagger UI y ReDoc
- **Containerization**: Docker y Docker Compose listos
- **Development Tools**: Testing, linting, type checking (Ruff, Mypy) configurados

## 🗂️ Estructura del Proyecto

```
template-python-fastapi/
├── main.py                  # Aplicación principal FastAPI
├── app/                     # Paquete principal de la aplicación
│   ├── __init__.py         # Inicialización del paquete
│   ├── api/                # Endpoints de la API
│   │   ├── __init__.py
│   │   ├── dependencies.py # Dependencias de la API
│   │   └── v1/            # API v1 endpoints
│   │       ├── __init__.py
│   │       ├── chat.py     # Endpoints de chat
│   │       └── health.py   # Health check endpoints
│   ├── config/             # Configuración
│   │   ├── __init__.py
│   │   └── settings.py    # Settings de la aplicación
│   ├── core/               # Componentes core
│   │   ├── __init__.py
│   │   ├── logging.py      # Configuración de logging
│   │   └── security.py    # Utilidades de seguridad
│   ├── models/             # Modelos de datos
│   │   ├── __init__.py
│   │   └── schemas.py      # Modelos Pydantic
│   └── services/           # Lógica de negocio
│       ├── __init__.py
│       └── ai_service.py  # Servicio de IA
├── pyproject.toml          # Configuración del proyecto (para uv)
├── uv.lock                 # Lockfile de dependencias
├── Dockerfile              # Configuración Docker
├── docker-compose.yml      # Orquestación Docker Compose
├── .dockerignore           # Archivos ignorados por Docker
├── .gitignore             # Archivos ignorados por Git
├── env.example            # Plantilla de variables de entorno
└── README.md              # Documentación principal
```

## 🛠️ Tecnologías Utilizadas

### Core Framework

- **Python 3.13+**: Versión de vanguardia con mejoras de rendimiento y JIT
- **FastAPI 0.129+**: Framework web moderno y asíncrono
- **Pydantic 2.12+**: Validación de datos y settings
- **SQLAlchemy 2.0**: ORM potente en modo asíncrono
- **Uvicorn**: Servidor ASGI de alto rendimiento
- **Passlib**: Utilidades de seguridad y hashing

### Package Management

- **uv**: Gestor de paquetes ultra-rápido (único soportado)
- **pyproject.toml**: Configuración moderna de proyecto

### AI Integration

- **Google GenAI SDK**: Integración nativa con Gemini 2.0
- **httpx**: Cliente HTTP asíncrono para APIs
- **Modelos soportados**: Gemini 2.0 Flash, Pro, Lite, etc.

### Development & Deployment

- **Docker**: Contenerización
- **Docker Compose**: Orquestación multi-contenedor
- **python-dotenv**: Gestión de variables de entorno
- **Logging**: Sistema de logging estructurado
- **CORS**: Soporte para Cross-Origin Resource Sharing

## 🚀 Configuración

```bash
# 1. Instalar uv (si no lo tienes)
# Windows:
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
# Linux/macOS:
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. Clonar y configurar
git clone <repository-url>
cd template-python-fastapi
cp env.example .env

# 3. Sincronizar dependencias (crea .venv automáticamente)
uv sync

# 4. Ejecutar la aplicación
uv run fastapi dev main.py
```

## 🔧 Configuración de Variables de Entorno

Edita el archivo `.env` con tu configuración:

```env
# Gemini API Configuration
GEMINI_API_KEY=your_gemini_api_key_here
MODEL_NAME=gemini-2.0-flash-lite

# Database Configuration (Supabase)
# IMPORTANTE: Usar postgresql+asyncpg:// para modo asíncrono
DATABASE_URL=postgresql+asyncpg://postgres.[ID]:[PASS]@[HOST]:[PORT]/postgres

# Supabase Configuration (Legacy/REST)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-service-role-key

# FastAPI Configuration
APP_NAME=Biotasys AI
DEBUG=true
```

## 🗄️ Base de Datos y Driver Asíncrono

Para mantener el principio de **Async-First** y evitar bloqueos en el bucle de eventos (Event Loop) de FastAPI, el proyecto utiliza SQLAlchemy en modo asíncrono.

### ⚠️ Regla de Oro del Driver
- **Prohibido**: `psycopg2`. Es un driver síncrono. Si se utiliza dentro de funciones `async def`, bloqueará todo el servidor por cada consulta, destruyendo el rendimiento de FastAPI.
- **Obligatorio**: `asyncpg`. Es el driver de alto rendimiento diseñado específicamente para Python asíncrono.

### Configuración de la URL de Conexión
La variable `DATABASE_URL` debe usar siempre el protocolo `postgresql+asyncpg://`. 

Ejemplo correcto:
`DATABASE_URL=postgresql+asyncpg://user:password@host:port/dbname`

## 📚 Documentación de la API

Una vez ejecutada la aplicación,访问:

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **OpenAPI Schema**: `http://localhost:8000/openapi.json`

## 🤖 Endpoints de IA

### Chat Completions

```bash
POST /api/v1/chat/completions
Content-Type: application/json

{
  "model": "openai/gpt-3.5-turbo",
  "messages": [
    {"role": "user", "content": "¡Hola! ¿Cómo estás?"}
  ],
  "max_tokens": 1000,
  "temperature": 0.7
}
```

### Listar Modelos Disponibles

```bash
GET /api/v1/chat/models
```

### Health Check

```bash
GET /api/v1/health
```

## 🐳 Docker (Opcional)

### Usar Docker Compose para Desarrollo

```bash
# Configurar variables de entorno
cp env.example .env
# Editar .env con tu API key

# Iniciar aplicación con Docker
docker-compose up --build

# Ejecutar en modo detached
docker-compose up --build -d

# Ver logs
docker-compose logs -f

# Detener servicios
docker-compose down

# Reconstruir y empezar
docker-compose up --build --force-recreate
```

### Docker Manual

```bash
# Construir imagen
docker build -t fastapi-ai-template .

# Ejecutar contenedor
docker run -p 8000:8000 \
  -e OPENROUTER_API_KEY=your_api_key_here \
  fastapi-ai-template
```

## 🧪 Testing

```bash
# Instalar dependencias de desarrollo
uv sync --dev

# Ejecutar tests
uv run pytest

# Con coverage
uv run pytest --cov=.
```

## 📈 Ventajas de uv

- **10-100x más rápido** en instalación de dependencias
- Mejor resolución de dependencias
- Cache inteligente
- Integración nativa con pyproject.toml
- Gestión automática de entornos virtuales y versiones de Python

## 🔍 Ejemplos de Uso

### Cliente Python

```python
import httpx

async def chat_with_ai():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/api/v1/chat/completions",
            json={
                "model": "openai/gpt-3.5-turbo",
                "messages": [
                    {"role": "user", "content": "Explica la relatividad"}
                ]
            }
        )
        return response.json()

# Ejecutar
import asyncio
result = asyncio.run(chat_with_ai())
print(result)
```

### Cliente curl

```bash
# Health check
curl http://localhost:8000/api/v1/health

# Chat completion
curl -X POST "http://localhost:8000/api/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "openai/gpt-3.5-turbo",
    "messages": [
      {"role": "user", "content": "Hola!"}
    ]
  }'

# Listar modelos
curl http://localhost:8000/api/v1/chat/models
```

## 🚀 Despliegue en Producción

### Variables de Entorno en Producción

Asegúrate de configurar estas variables en tu entorno de producción:

```bash
OPENROUTER_API_KEY=tu_api_key_secreta
DEBUG=false
APP_NAME=Tu App en Producción
```

### Consideraciones de Seguridad

- Nunca exponer `.env` en control de versiones
- Usar API keys restringidas en producción
- Configurar CORS adecuadamente para tu dominio
- Implementar rate limiting en producción
- Usar HTTPS en producción

## 🤝 Contribuir

1. Fork del repositorio
2. Crear feature branch: `git checkout -b feature/nueva-funcionalidad`
3. Commit cambios: `git commit -am 'Agregar nueva funcionalidad'`
4. Push al branch: `git push origin feature/nueva-funcionalidad`
5. Submit Pull Request

## 📝 Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo [LICENSE](LICENSE) para más detalles.

## 🔗 Enlaces Útiles

- **FastAPI Documentation**: https://fastapi.tiangolo.com/
- **OpenRouter API**: https://openrouter.ai/docs
- **uv Documentation**: https://github.com/astral-sh/uv
- **Pydantic Documentation**: https://pydantic-docs.helpmanual.io/
- **Docker Documentation**: https://docs.docker.com/

---

**¡Listo para construir tu próxima aplicación con IA! 🎉**
