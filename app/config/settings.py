"""Application settings and configuration."""


from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    app_name: str = "FastAPI AI Template"
    app_version: str = "1.0.0"
    debug: bool = True

    # Gemini Configuration
    gemini_api_key: str
    extraction_model: str = "gemini-2.5-flash-lite"
    interpretation_model: str = "gemini-2.5-flash"

    # JWT Configuration
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 30

    # Backend Nest Configuration
    backend_nest_url: str | None = None

    # Supabase Configuration
    supabase_url: str
    supabase_key: str

    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = Field(default=8000, alias="API_PORT")
    render_port: int | None = Field(default=None, alias="PORT")

    # CORS Configuration
    cors_origins: list[str] = ["*"]
    cors_allow_credentials: bool = True
    cors_allow_methods: list[str] = ["*"]
    cors_allow_headers: list[str] = ["*"]

    # Logging Configuration
    log_level: str = "INFO"

    @model_validator(mode="after")
    def prefer_render_port(self) -> "Settings":
        """Allow Render's PORT to override the local API_PORT setting."""
        if self.render_port is not None:
            self.api_port = self.render_port
        return self

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore",
        populate_by_name=True,
    )


# Global settings instance
settings = Settings()
