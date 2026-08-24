import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """
        Application configuration settings using Pydantic BaseSettings.
    """
    PROJECT_NAME: str 
    ELASTICSEARCH_URL: str

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()