from typing import Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """
        Application configuration settings using Pydantic BaseSettings.
    """
    PROJECT_NAME: str
    ELASTICSEARCH_URL: str
    ELASTICSEARCH_API_KEY: Optional[str] = None

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()