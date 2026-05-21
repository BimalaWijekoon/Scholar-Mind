"""
ScholarMind Configuration Settings
"""

from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import field_validator
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Application
    APP_NAME: str = "ScholarMind"
    APP_ENV: str = "development"
    DEBUG: bool = True
    SECRET_KEY: str = "change-this-in-production"
    
    # API
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_PREFIX: str = "/api/v1"
    
    # Google Gemini (Required for LLM features)
    GOOGLE_API_KEY: str = ""
    
    # Neo4j Knowledge Graph
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "scholarmind123"
    
    # PostgreSQL Database
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "scholarmind"
    POSTGRES_USER: str = "scholarmind"
    POSTGRES_PASSWORD: str = "scholarmind123"
    DATABASE_URL: str = "postgresql+asyncpg://scholarmind:scholarmind123@localhost:5432/scholarmind"
    
    # Redis Cache & Message Broker
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/1"
    
    # MinIO Object Storage
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "scholarmind"
    MINIO_SECRET_KEY: str = "scholarmind123"
    MINIO_BUCKET: str = "documents"
    MINIO_SECURE: bool = False
    
    # Vector Store (ChromaDB)
    VECTOR_STORE_TYPE: str = "chromadb"
    CHROMA_PERSIST_DIRECTORY: str = "./data/chroma"
    CHROMA_COLLECTION_NAME: str = "scholarmind_docs"
    
    # File Storage
    UPLOAD_DIR: str = "./data/uploads"
    PROCESSED_DIR: str = "./data/processed"
    EMBEDDINGS_DIR: str = "./data/embeddings"
    MAX_UPLOAD_SIZE_MB: int = 100
    
    # ML Models
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    SPACY_MODEL: str = "en_core_web_sm"
    RERANKER_MODEL: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173"]
    
    # Frontend
    FRONTEND_URL: str = "http://localhost:5173"
    
    @field_validator('CORS_ORIGINS', mode='before')
    @classmethod
    def parse_cors_origins(cls, v):
        """Parse CORS origins from string or list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(',')]
        return v
    
    @field_validator('SECRET_KEY', mode='after')
    @classmethod
    def validate_secret_key(cls, v, info):
        """Warn if SECRET_KEY is still the default insecure value."""
        insecure_defaults = {
            "change-this-in-production",
            "change-this-in-production-use-a-random-string",
        }
        if v in insecure_defaults:
            import warnings
            warnings.warn(
                "SECRET_KEY is set to an insecure default. "
                "Generate a strong random key for production: "
                "python -c \"import secrets; print(secrets.token_urlsafe(64))\"",
                UserWarning,
                stacklevel=2,
            )
        return v
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"  # Ignore extra fields in .env


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
