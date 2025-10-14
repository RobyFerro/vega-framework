"""Base settings class using Pydantic"""
import sys

# Import BaseSettings from pydantic v1 (default) or pydantic-settings v2 (if available)
# This provides compatibility with both versions:
# - Pydantic v1: BaseSettings is in pydantic package (PASE/OS400 compatible)
# - Pydantic v2: BaseSettings moved to separate pydantic-settings package
try:
    # Try pydantic v1 first (default for maximum compatibility)
    from pydantic import BaseSettings as PydanticBaseSettings
    PYDANTIC_SETTINGS_V2 = False
    SettingsConfigDict = None
except ImportError:
    try:
        # Fall back to pydantic-settings v2 (if installed)
        from pydantic_settings import BaseSettings as PydanticBaseSettings, SettingsConfigDict
        PYDANTIC_SETTINGS_V2 = True
    except ImportError:
        print("ERROR: pydantic (with BaseSettings) is required", file=sys.stderr)
        sys.exit(1)


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

    # Configuration compatible with both pydantic-settings v1 and v2
    if PYDANTIC_SETTINGS_V2:
        model_config = SettingsConfigDict(
            env_file='.env',
            env_file_encoding='utf-8',
            extra='ignore',  # Ignore extra fields in .env
            validate_default=False  # Don't validate default values
        )
    else:
        # Pydantic Settings v1 uses Config class
        class Config:
            env_file = '.env'
            env_file_encoding = 'utf-8'
            extra = 'ignore'
            validate_all = False
