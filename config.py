"""
Configuration management for the Perplexity 2.0 backend application.
Handles environment variables, API keys, and application settings.
"""

from pydantic_settings import BaseSettings
from pydantic import Field
import logging


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # LLM Configuration
    llm_model: str = Field(
        default="meta-llama/llama-4-scout-17b-16e-instruct",
        alias="LLM_MODEL"
    )
    llm_provider: str = Field(default="groq", alias="LLM_PROVIDER")
    groq_api_key: str = Field(alias="GROQ_API_KEY")

    # Tool Configuration
    tavily_api_key: str = Field(alias="TAVILY_API_KEY")
    tavily_max_results: int = Field(default=4, alias="TAVILY_MAX_RESULTS")

    # Server Configuration
    host: str = Field(default="0.0.0.0", alias="HOST")
    port: int = Field(default=8000, alias="PORT")
    debug: bool = Field(default=False, alias="DEBUG")

    # CORS Configuration
    cors_origins: list[str] = Field(
        default=["*"],
        alias="CORS_ORIGINS"
    )
    cors_methods: list[str] = Field(
        default=["*"],
        alias="CORS_METHODS"
    )
    cors_headers: list[str] = Field(
        default=["*"],
        alias="CORS_HEADERS"
    )

    # Logging Configuration
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


def get_settings() -> Settings:
    """Factory function to get application settings."""
    return Settings()


def setup_logging(log_level: str = "INFO") -> logging.Logger:
    """Configure application logging."""
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    return logging.getLogger(__name__)
