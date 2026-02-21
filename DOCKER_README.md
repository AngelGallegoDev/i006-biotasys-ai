# Biotasys AI - Guía de Inicio Rápido con UV 🚀

Esta guía explica cómo configurar y arrancar el backend utilizando `uv`, el gestor de paquetes de Python ultra rápido.

## 1. Instalación de UV
Si no tienes `uv` instalado, ejecuta este comando en PowerShell:
```powershell

powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

```
*Nota: Reinicia la terminal después de la instalación.*

## 2. Configuración del Entorno
Si es la primera vez o si ves errores del tipo "invalid Python environment", limpia y sincroniza:

```powershell
# 1. Eliminar venv corrupto (si existe)
rm -r -Force .venv

# 2. Sincronizar dependencias (y descargar Python 3.12 si falta)
uv sync

# 3. Configurar variables de entorno
cp env.example .env
```

## 3. Ejecución del Servidor
Para desarrollo con recarga automática:
```powershell
uv run uvicorn main:app --reload --port 8000
```

Para ejecutar vía script directo:
```powershell
uv run python main.py
```

## 4. Tests y Calidad
```powershell
# Ejecutar tests
uv run pytest

# Formatear código
uv run ruff format .
```