import os
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    PROJECT_NAME: str = "Enterprise Intelligence Platform"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"
    SECRET_KEY: str = "insecure-default-change-me-in-production-32-chars"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    ALGORITHM: str = "HS256"

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./data/enterprise.db"

    # LLM Providers
    PRIMARY_LLM_PROVIDER: str = "groq"
    GROQ_API_KEY: Optional[str] = None
    GROQ_MODEL: str = "qwen/qwen3.8-27b"

    FALLBACK_LLM_PROVIDER: str = "groq_fallback"
    GROQ_FALLBACK_MODEL: str = "openai/gpt-oss-120b"
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-1.5-flash"

    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4o-mini"

    # Embeddings & Vector Store
    EMBEDDING_MODEL_NAME: str = "all-MiniLM-L6-v2"
    EMBEDDING_DIMENSION: int = 384
    CHROMA_PERSIST_DIR: str = "./data/chroma_storage"

    # Ingestion & Chunking
    UPLOAD_DIR: str = "./data/uploads"
    CHUNK_SIZE: int = 800
    CHUNK_OVERLAP: int = 150
    MAX_UPLOAD_SIZE_MB: int = 25
    ALLOWED_EXTENSIONS: List[str] = [".pdf", ".txt", ".md", ".csv"]

    # Retrieval & Thresholding
    SIMILARITY_THRESHOLD: float = 0.45
    HYBRID_ALPHA: float = 0.5  # 0.5 balanced dense and sparse

    # Agent Safeguards
    AGENT_MAX_ITERATIONS: int = 6
    AGENT_TIMEOUT_SECONDS: int = 45

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()

# Ensure directories exist
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(settings.CHROMA_PERSIST_DIR, exist_ok=True)
os.makedirs("./data", exist_ok=True)
