from typing import Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """
        Application configuration settings using Pydantic BaseSettings.
    """
    PROJECT_NAME: str
    ELASTICSEARCH_URL: str
    ELASTICSEARCH_API_KEY: Optional[str] = None
    JWT_SECRET: Optional[str] = None
    ALLOWED_ORIGINS: str = "http://localhost:3000"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()