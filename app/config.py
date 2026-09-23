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

    # --- Database (MongoDB) ---
    # Full connection string, e.g.
    #   mongodb+srv://<user>:<pass>@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority
    # or a local server: mongodb://localhost:27017
    MONGODB_URI: str = "mongodb://localhost:27017"
    # Database (logical namespace) used for this app.
    MONGODB_DB: str = "metrology"
    # Seconds to wait for a server before raising.
    MONGODB_TIMEOUT_MS: int = 8000

    # Bootstrap admin created automatically on first start when the users
    # collection is empty, so a fresh deployment is usable immediately.
    ADMIN_EMAIL: str = "admin@metrology.gov.in"
    ADMIN_PASSWORD: str = "admin123"
    ADMIN_NAME: str = "System Administrator"

    # --- CORS ---
    # Comma separated list of frontend origins allowed to call this API.
    # Add the deployed frontend origin(s), e.g. https://my-app.vercel.app
    CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173"
    # Also accept any https://*.vercel.app origin (covers Vercel preview URLs).
    CORS_ALLOW_VERCEL: bool = True

    # --- ML model ---
    # Set CLASSIFIER_ENABLED=false to skip loading TensorFlow entirely (useful
    # on small hosts where the ~500MB runtime does not fit in memory).
    CLASSIFIER_ENABLED: bool = True
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

    # Environment files, in priority order (later wins). This project keeps a
    # dedicated .env.backend next to the frontend's .env.frontend so each
    # deployment target gets its own file; a plain .env still works.
    # Real environment variables (Render dashboard, shell) always win over
    # anything written in a file.
    model_config = SettingsConfigDict(
        env_file=(".env", ".env.backend"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def cors_origin_list(self):
        origins = [o.strip().rstrip("/") for o in self.CORS_ORIGINS.split(",") if o.strip()]
        # "*" cannot be combined with allow_credentials=True in browsers, but
        # we keep it working for the wildcard case by returning it as-is.
        return origins or ["http://localhost:5173"]

    @property
    def model_class_name_list(self):
        return [c.strip() for c in self.MODEL_CLASS_NAMES.split(",") if c.strip()]


settings = Settings()

os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(settings.REPORTS_DIR, exist_ok=True)
