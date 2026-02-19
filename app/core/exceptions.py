"""Global exception handlers and custom exception hierarchy."""

from fastapi import Request, status
from fastapi.responses import JSONResponse
from postgrest.exceptions import APIError as SupabaseAPIError
from app.core.logging import get_logger

logger = get_logger(__name__)

class BiotasysException(Exception):
    """Base exception for all Biotasys Engine errors."""
    def __init__(self, message: str, details: str | None = None):
        super().__init__(message)
        self.message = message
        self.details = details

class AIError(BiotasysException):
    """Raised when an external AI service (Gemini) fails or returns invalid data."""
    pass

class ValidationError(BiotasysException):
    """Raised when data doesn't meet clinical or technical requirements."""
    pass

class DatabaseError(BiotasysException):
    """Raised when persistence in Supabase fails."""
    pass

class ResourceNotFoundError(BiotasysException):
    """Raised when a report or document is not found."""
    pass

async def biotasys_exception_handler(request: Request, exc: BiotasysException):
    """Universal handler for Biotasys custom exceptions."""
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    
    if isinstance(exc, ResourceNotFoundError):
        status_code = status.HTTP_404_NOT_FOUND
    elif isinstance(exc, ValidationError):
        status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    elif isinstance(exc, AIError):
        status_code = status.HTTP_502_BAD_GATEWAY
    elif isinstance(exc, DatabaseError):
        status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    logger.error(f"Engine Error [{exc.__class__.__name__}]: {exc.message} | Details: {exc.details}")
    
    return JSONResponse(
        status_code=status_code,
        content={
            "error": exc.__class__.__name__,
            "message": exc.message,
            "details": exc.details,
            "path": request.url.path
        }
    )

async def supabase_exception_handler(request: Request, exc: SupabaseAPIError):
    """Specific handler for raw Supabase/Postgrest errors."""
    error_code = getattr(exc, "code", "UNKNOWN")
    message = getattr(exc, "message", "Database connection error")
    
    logger.error(f"Supabase Raw Error [{error_code}]: {message}")
    
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    if error_code == "PGRST116":  # Not found
        status_code = status.HTTP_404_NOT_FOUND
        message = "The requested resource was not found in the database."

    return JSONResponse(
        status_code=status_code,
        content={
            "error": "DatabaseError",
            "message": message,
            "code": error_code
        }
    )
