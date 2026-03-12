"""Main FastAPI application."""

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from postgrest.exceptions import APIError as SupabaseAPIError

from app.api.v1 import api_router
from app.config.settings import settings
from app.core.logging import get_logger, setup_logging
from app.models.schemas import AnalysisReport, RootResponse
from app.services import pdf_service, report_service
from app.services.ai_service import ai_service
from app.core.exceptions import (
    supabase_exception_handler, 
    biotasys_exception_handler,
    BiotasysException
)

# Setup logging
setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    yield
    # Shutdown
    await ai_service.close()
    logger.info("Application shutdown complete")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="FastAPI Biotasys AI Dual Engine",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.cors_allow_methods,
    allow_headers=settings.cors_allow_headers,
)

# Include API routers
app.include_router(api_router)

# Register exception handlers
app.add_exception_handler(BiotasysException, biotasys_exception_handler)
app.add_exception_handler(SupabaseAPIError, supabase_exception_handler)


@app.get("/", response_model=RootResponse)
async def read_root():
    """Root endpoint with basic information."""
    return RootResponse(
        message="Biotasys AI - Processing System",
        version=settings.app_version,
        docs="/docs",
        health="/api/v1/health"
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )
