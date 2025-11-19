"""Application configuration management."""

from functools import lru_cache
from typing import List, Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # Application
    APP_NAME: str = "Ask My Docs"
    DEBUG: bool = False
    VERSION: str = "1.0.0"
    ENVIRONMENT: Literal["development", "staging", "production"] = "development"

    # Database
    DATABASE_URL: str
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 10
    DATABASE_URL_ASYNC: str | None = None

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # LLM Configuration (Primary: Google Vertex AI)
    # Google Cloud service account credentials
    GOOGLE_CREDENTIALS_PATH: str  # Path to service account JSON file
    GOOGLE_PROJECT_ID: str  # GCP project ID
    GOOGLE_LOCATION: str = "us-central1"  # Vertex AI location for LLM
    GOOGLE_EMBEDDING_LOCATION: str = "us-central1"  # Vertex AI location for embeddings

    # Optional: Alternative providers
    ANTHROPIC_API_KEY: str | None = None
    OPENAI_API_KEY: str | None = None

    # Model Selection - Vertex AI models
    LLM_PROVIDER: str = "google"  # google, anthropic, or openai
    GEMINI_MODEL_NAME: str = "gemini-2.5-pro"  # Default Vertex AI model
    DEFAULT_MODEL: str = "gemini-2.5-pro"
    SIMPLE_QUERY_MODEL: str = "gemini-2.0-flash-001"  # Fast model for simple queries
    COMPLEX_QUERY_MODEL: str = "gemini-2.5-pro"  # Advanced model for complex queries

    # Model parameters
    GEMINI_TEMPERATURE: float = 0.2
    GEMINI_TOP_P: float = 0.95

    # Embedding configuration
    GOOGLE_EMBEDDING_MODEL_NAME: str = "text-embedding-005"  # Vertex AI embedding model
    EMBEDDING_MODEL: str = "text-embedding-005"  # Alias for backward compatibility
    EMBEDDING_PROVIDER: str = "google"  # google or openai

    # Vector Database (Using PGVector - embeddings stored directly in PostgreSQL)
    VECTOR_DB_TYPE: Literal["pgvector", "chromadb", "pinecone"] = "pgvector"

    # ChromaDB (Not used - replaced by PGVector)
    # CHROMA_PERSIST_DIRECTORY: str = "./data/chroma"
    # CHROMA_COLLECTION_NAME: str = "document_chunks"

    # Pinecone (Optional)
    PINECONE_API_KEY: str | None = None
    PINECONE_ENVIRONMENT: str | None = None
    PINECONE_INDEX_NAME: str | None = None

    # File Storage
    STORAGE_TYPE: Literal["local", "s3"] = "local"

    # Local Storage
    LOCAL_STORAGE_PATH: str = "./data/documents"
    LOCAL_EXPORT_PATH: str = "./data/exports"

    # AWS S3 (Optional)
    AWS_ACCESS_KEY_ID: str | None = None
    AWS_SECRET_ACCESS_KEY: str | None = None
    AWS_REGION: str | None = None
    S3_BUCKET: str | None = None
    S3_EXPORT_BUCKET: str | None = None

    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"
    CELERY_TASK_TRACK_STARTED: bool = True
    CELERY_TASK_TIME_LIMIT: int = 3600  # 1 hour

    # Document Processing
    MAX_UPLOAD_SIZE: int = 104857600  # 100MB in bytes
    ALLOWED_FILE_TYPES: str = "pdf,docx,pptx,xlsx,txt,md,jpg,png"
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200
    TESSERACT_PATH: str = "/usr/bin/tesseract"
    OCR_LANGUAGE: str = "eng"

    # WebSocket
    WS_HEARTBEAT_INTERVAL: int = 30
    WS_MESSAGE_QUEUE_SIZE: int = 100

    # CORS
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:5173"
    ALLOWED_METHODS: str = "GET,POST,PUT,PATCH,DELETE,OPTIONS"
    ALLOWED_HEADERS: str = "*"

    # Logging
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    LOG_FORMAT: Literal["json", "text"] = "json"
    LOG_FILE: str = "./logs/app.log"

    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = 60
    RATE_LIMIT_BURST: int = 100

    # Email (Optional)
    SMTP_HOST: str | None = None
    SMTP_PORT: int = 587
    SMTP_USER: str | None = None
    SMTP_PASSWORD: str | None = None
    SMTP_FROM: str | None = None

    # Monitoring (Optional)
    SENTRY_DSN: str | None = None
    ANALYTICS_ENABLED: bool = False

    # Feature Flags
    ENABLE_DOCUMENT_AUTO_TAGGING: bool = True
    ENABLE_HITL: bool = True
    ENABLE_EXPORT_PDF: bool = True
    ENABLE_EXPORT_MARKDOWN: bool = True
    ENABLE_MCP_SERVER: bool = False

    # Development
    SEED_DATABASE: bool = False
    ENABLE_DOCS: bool = True

    @property
    def allowed_file_types_list(self) -> List[str]:
        """Get allowed file types as a list."""
        if isinstance(self.ALLOWED_FILE_TYPES, str):
            return [ext.strip() for ext in self.ALLOWED_FILE_TYPES.split(",")]
        return self.ALLOWED_FILE_TYPES

    @property
    def cors_origins(self) -> List[str]:
        """Get CORS origins as a list."""
        if isinstance(self.ALLOWED_ORIGINS, str):
            return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]
        return self.ALLOWED_ORIGINS

    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.ENVIRONMENT == "development"

    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.ENVIRONMENT == "production"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance.

    Using lru_cache ensures settings are loaded only once
    and reused throughout the application lifecycle.
    """
    return Settings()


# Convenience export
settings = get_settings()
