"""
Settings management for CleanArch applications

Provides base class for application settings using Pydantic.

Features:
- Environment variable loading from .env files
- Type validation
- Default values
- Settings inheritance

Example:
    from vega.settings import BaseSettings
    from pydantic import Field

    class Settings(BaseSettings):
        # Application
        app_name: str = Field(default="my-app")
        debug: bool = Field(default=False)

        # Database
        database_url: str = Field(...)

        # External services
        stripe_api_key: str = Field(...)
        sendgrid_api_key: str = Field(...)

    # Create settings instance (loads from .env)
    settings = Settings()
"""

from vega.settings.base import BaseSettings

__all__ = ["BaseSettings"]
