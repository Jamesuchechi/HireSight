"""Application settings without requiring Pydantic/BaseSettings.

This file provides a simple, environment-driven `Settings` object used
by the backend. It intentionally avoids requiring `pydantic` so the
project runs with a minimum of dependencies during development.
"""

import os
from pathlib import Path
from functools import lru_cache

# Load .env file if it exists
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).resolve().parent.parent.parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
except ImportError:
    pass


class Settings:
    """Central configuration for the application."""

    # Project paths
    BASE_DIR = Path(__file__).resolve().parent.parent
    UPLOADS_DIR = BASE_DIR / "uploads"
    EMBEDDINGS_CACHE_DIR = BASE_DIR / "embeddings_cache"

    # Database
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./resumes.db")

    # Ensure directories exist
    EMBEDDINGS_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

    # API Settings
    API_TITLE = "HireSight API"
    API_VERSION = "0.1.0"
    API_DESCRIPTION = "AI-Powered Resume Screening Engine"

    # Upload settings
    MAX_UPLOAD_SIZE = int(os.getenv("MAX_UPLOAD_SIZE", 10 * 1024 * 1024))  # 10 MB default
    ALLOWED_EXTENSIONS = {".pdf", ".docx", ".doc"}

    # Application URLs
    APP_URL = os.getenv("APP_URL", "http://localhost:8000")
    FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")
    EMAIL_VERIFICATION_PATH = os.getenv("EMAIL_VERIFICATION_PATH", "/auth/verify-email")

    # NLP/Embedding settings
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
    EMBEDDING_DIMENSION = int(os.getenv("EMBEDDING_DIMENSION", 384))

    # Scoring weights
    SCORE_WEIGHTS = {
        "semantic_similarity": float(os.getenv("W_SEMANTIC", 0.40)),
        "skill_match": float(os.getenv("W_SKILL", 0.30)),
        "experience_relevance": float(os.getenv("W_EXPERIENCE", 0.20)),
        "education_fit": float(os.getenv("W_EDUCATION", 0.10)),
    }

    # Background jobs
    REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

    # Misc
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    ALLOWED_ORIGINS = os.getenv(
        "ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:5173"
    ).split(",")
    TESTING = os.getenv("TESTING", "False") == "True"
    SECRET_KEY = os.getenv("SECRET_KEY", "change-this-secret")
    JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 60 * 8))
    REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", 7))

    # Cookie settings
    REFRESH_TOKEN_COOKIE_NAME = os.getenv("REFRESH_TOKEN_COOKIE_NAME", "hiresight_refresh_token")
    REFRESH_TOKEN_COOKIE_SECURE = os.getenv("REFRESH_TOKEN_COOKIE_SECURE", "False").lower() in ("1", "true", "yes")
    REFRESH_TOKEN_COOKIE_SAMESITE = os.getenv("REFRESH_TOKEN_COOKIE_SAMESITE", "lax")
    REFRESH_TOKEN_COOKIE_PATH = os.getenv("REFRESH_TOKEN_COOKIE_PATH", "/api")
    REFRESH_TOKEN_COOKIE_MAX_AGE = REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60

    # Login throttling
    MAX_LOGIN_ATTEMPTS = int(os.getenv("MAX_LOGIN_ATTEMPTS", 5))
    LOGIN_LOCK_MINUTES = int(os.getenv("LOGIN_LOCK_MINUTES", 30))

    # Registration rate limiting
    REGISTRATION_MAX_ATTEMPTS_PER_HOUR = int(os.getenv("REGISTRATION_MAX_PER_HOUR", 5))
    REGISTRATION_WINDOW_SECONDS = int(os.getenv("REGISTRATION_WINDOW_SECONDS", 3600))

    # Password reset
    PASSWORD_RESET_TOKEN_EXPIRE_HOURS = int(os.getenv("PASSWORD_RESET_TOKEN_EXPIRE_HOURS", 1))

    # Email delivery
    EMAIL_FROM_NAME = os.getenv("EMAIL_FROM_NAME", "HireSight")
    EMAIL_FROM_ADDRESS = os.getenv("EMAIL_FROM_ADDRESS", "no-reply@hiresight.io")
    SMTP_HOST = os.getenv("SMTP_HOST")
    SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
    SMTP_USERNAME = os.getenv("SMTP_USERNAME")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
    SMTP_USE_TLS = os.getenv("SMTP_USE_TLS", "True").lower() in ("1", "true", "yes")
    SMTP_TIMEOUT = int(os.getenv("SMTP_TIMEOUT", 15))


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
