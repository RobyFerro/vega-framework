"""Base settings class using Pydantic"""
from pydantic_settings import BaseSettings as PydanticBaseSettings, SettingsConfigDict


class BaseSettings(PydanticBaseSettings):
    """
    Base class for application settings.

    Automatically loads configuration from:
    - Environment variables
    - .env file (if present)

    Features:
    - Type validation via Pydantic
    - Environment variable mapping
    - Default values
    - Nested configuration

    Example:
        from vega.settings import BaseSettings
        from pydantic import Field

        class Settings(BaseSettings):
            # Required settings
            database_url: str

            # Optional with defaults
            app_name: str = Field(default="my-app")
            debug: bool = Field(default=False)
            port: int = Field(default=8000)

            # External services
            stripe_api_key: str = Field(default="")
            sendgrid_api_key: str = Field(default="")

        # Usage
        settings = Settings()  # Loads from environment/.env
        print(settings.database_url)
    """

    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        extra='ignore',  # Ignore extra fields in .env
        validate_default=False  # Don't validate default values
    )
