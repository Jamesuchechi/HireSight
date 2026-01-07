"""Application settings without requiring Pydantic/BaseSettings.

This file provides a simple, environment-driven `Settings` object used
by the backend. It intentionally avoids requiring `pydantic` so the
project runs with a minimum of dependencies during development.
"""

import os
from pathlib import Path
from functools import lru_cache


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


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
