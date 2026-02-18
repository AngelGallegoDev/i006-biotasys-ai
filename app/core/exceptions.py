"""Global exception handlers for the application."""

from fastapi import Request, status
from fastapi.responses import JSONResponse
from postgrest.exceptions import APIError
from app.core.logging import get_logger

logger = get_logger(__name__)

async def supabase_exception_handler(request: Request, exc: APIError):
    """
    Handle errors specifically from the Supabase/PostgREST client.
    """
    error_code = exc.code
    message = exc.message
    details = exc.details
    
    logger.error(f"Supabase API Error [{error_code}]: {message} - {details}")

    # Map PostgREST error codes to HTTP status codes
    # Ref: https://postgrest.org/en/stable/errors.html
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    
    if error_code == "PGRST116": # Resource not found
        status_code = status.HTTP_404_NOT_FOUND
    elif error_code.startswith("23"): # Integrity constraint violations (e.g., 23505 Unique Violation)
        status_code = status.HTTP_409_CONFLICT
    elif error_code == "42501": # Insufficient privilege (RLS)
        status_code = status.HTTP_403_FORBIDDEN
    elif error_code in ["PGRST100", "PGRST102"]: # Invalid filter or query
        status_code = status.HTTP_400_BAD_REQUEST

    return JSONResponse(
        status_code=status_code,
        content={
            "error": "Database Error",
            "message": message,
            "code": error_code,
            "details": details
        }
    )

async def generic_exception_handler(request: Request, exc: Exception):
    """
    Catch-all for any other unhandled exceptions.
    """
    logger.error(f"Unhandled Exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred."
        }
    )
