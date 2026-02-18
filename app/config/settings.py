"""Application settings and configuration."""


from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    app_name: str = "FastAPI AI Template"
    app_version: str = "1.0.0"
    debug: bool = True

    # Gemini Configuration
    gemini_api_key: str
    model_name: str = "gemini-2.0-flash-lite-preview-02-05"

    # JWT Configuration
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 30

    # Supabase Configuration
    supabase_url: str
    supabase_key: str

    # Database Configuration (SQLAlchemy)
    database_url: str

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
