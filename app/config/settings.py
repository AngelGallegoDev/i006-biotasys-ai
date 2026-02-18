"""Application settings and configuration."""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    app_name: str = "FastAPI AI Template"
    app_version: str = "1.0.0"
    debug: bool = True
    
    # OpenRouter Configuration
    openrouter_api_key: str
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    model_name: str = "deepseek/deepseek-r1-0528:free"

    # JWT Configuration
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 30

    # Supabase Configuration
    supabase_url: str
    supabase_key: str

    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    
    # CORS Configuration
    cors_origins: list[str] = ["*"]
    cors_allow_credentials: bool = True
    cors_allow_methods: list[str] = ["*"]
    cors_allow_headers: list[str] = ["*"]
    
    # Logging Configuration
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
