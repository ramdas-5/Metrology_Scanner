"""
Central application configuration.
Values are loaded from environment variables / a .env file so that the
same code can be deployed to different environments (local, staging, prod)
without any code changes.
"""

import os
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # --- Security ---
    SECRET_KEY: str = "change-this-to-a-long-random-string"
    ALGORITHM: str = "HS256"
    # 7 days by default so an inspector stays logged in across short backend
    # restarts / overnight breaks instead of being logged out every 8 hours.
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080

    # --- Database ---
    DATABASE_URL: str = "sqlite:///./metrology.db"

    # --- CORS ---
    CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173"

    # --- ML model ---
    MODEL_PATH: str = "app/ml/label_classifier.h5"
    MODEL_CLASS_NAMES: str = "Non-Compliant Label,Compliant Label"
    MODEL_INPUT_SIZE: int = 224

    # --- OCR ---
    TESSERACT_CMD: str = ""
    # Which OCR engine to prefer when pulling "as much text as possible" off an
    # image: "auto" (PaddleOCR if installed, else Tesseract), "paddle", "tesseract".
    OCR_ENGINE: str = "auto"

    # --- AI structured extraction (OpenRouter) ---
    # Leave OPENROUTER_API_KEY empty to disable the LLM pipeline and fall back
    # to the regex-based declaration parser + rule engine.
    OPENROUTER_API_KEY: str = ""
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
    OPENROUTER_MODEL: str = "openai/gpt-4o-mini"
    AI_TIMEOUT_SECONDS: int = 90

    # --- Dedupe / cache ---
    # When the OCR text of a new image is >= this % similar (0-100) to an already
    # saved scan, return the saved result from the DB instead of calling the AI
    # again (saves an OpenRouter API call).
    SIMILARITY_THRESHOLD: int = 80
    # Only compare against the most recent N saved scans for speed.
    SIMILARITY_SEARCH_LIMIT: int = 500

    # --- Storage ---
    UPLOAD_DIR: str = "app/uploads"
    REPORTS_DIR: str = "app/reports"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def cors_origin_list(self):
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def model_class_name_list(self):
        return [c.strip() for c in self.MODEL_CLASS_NAMES.split(",") if c.strip()]


settings = Settings()

os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(settings.REPORTS_DIR, exist_ok=True)
