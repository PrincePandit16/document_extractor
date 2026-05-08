from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import List
import os


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # App
    APP_NAME: str = "DocExtractor"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    SECRET_KEY: str = "dev-secret-key"

    # Database
    DATABASE_URL: str = "postgresql://postgres:password@localhost:5432/doc_extractor"

    # Groq LLM
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama3-70b-8192"

    # OCR
    OCR_ENGINE: str = "tesseract"
    TESSERACT_CMD: str = "/usr/bin/tesseract"

    # File Upload
    UPLOAD_DIR: str = "./uploads"
    MAX_FILE_SIZE_MB: int = 10
    ALLOWED_EXTENSIONS: List[str] = ["pdf", "png", "jpg", "jpeg"]

    # API
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000

settings = Settings()

# Ensure upload directory exists
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
