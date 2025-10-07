"""Application settings for test-router-project"""
from vega.settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application configuration"""

    # Application
    app_name: str = Field(default="test-router-project")
    debug: bool = Field(default=False)

    # Add your settings here
    # database_url: str = Field(...)
    # api_key: str = Field(...)


# Global settings instance
settings = Settings()
