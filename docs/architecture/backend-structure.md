# Backend Project Structure

Complete backend architecture and module organization for Ask My Docs.

## Technology Stack

- **Framework**: FastAPI 0.109+
- **Python**: 3.11+
- **ORM**: SQLAlchemy 2.0+
- **Validation**: Pydantic 2.0+
- **Migrations**: Alembic
- **Task Queue**: Celery with Redis
- **Agent Framework**: LangChain with Deep Agents
- **Vector DB**: ChromaDB (development) / Pinecone (production)
- **Storage**: Local filesystem (development) / S3 (production)

---

## Complete Directory Structure

```
backend/
├── app/
│   ├── __init__.py
│   │
│   ├── main.py                      # FastAPI application entry point
│   │
│   ├── api/                         # API layer
│   │   ├── __init__.py
│   │   ├── deps.py                  # Shared dependencies
│   │   └── v1/                      # API version 1
│   │       ├── __init__.py
│   │       ├── router.py            # Main API router
│   │       └── endpoints/           # Endpoint modules
│   │           ├── __init__.py
│   │           ├── auth.py          # Authentication endpoints
│   │           ├── users.py         # User management
│   │           ├── systems.py       # System management
│   │           ├── documents.py     # Document operations
│   │           ├── tags.py          # Tag management
│   │           ├── conversations.py # Conversation endpoints
│   │           ├── messages.py      # Message/query endpoints
│   │           ├── agent_executions.py  # Agent execution & HITL
│   │           ├── exports.py       # Export generation
│   │           ├── feedback.py      # User feedback
│   │           └── analytics.py     # Analytics (admin)
│   │
│   ├── core/                        # Core functionality
│   │   ├── __init__.py
│   │   ├── config.py                # Configuration management
│   │   ├── security.py              # Authentication & authorization
│   │   ├── database.py              # Database connection & session
│   │   ├── redis.py                 # Redis connection
│   │   ├── websocket.py             # WebSocket manager
│   │   └── exceptions.py            # Custom exceptions
│   │
│   ├── models/                      # SQLAlchemy models
│   │   ├── __init__.py
│   │   ├── user.py                  # User model
│   │   ├── system.py                # System & user_systems models
│   │   ├── document.py              # Document & document_chunks models
│   │   ├── tag.py                   # Tag & document_tags models
│   │   ├── conversation.py          # Conversation & message models
│   │   ├── agent_execution.py       # Agent execution tracking
│   │   ├── analytics.py             # QA analytics & feedback models
│   │   └── export.py                # Export models
│   │
│   ├── schemas/                     # Pydantic schemas (API contracts)
│   │   ├── __init__.py
│   │   ├── user.py                  # User request/response schemas
│   │   ├── system.py                # System schemas
│   │   ├── document.py              # Document schemas
│   │   ├── tag.py                   # Tag schemas
│   │   ├── conversation.py          # Conversation schemas
│   │   ├── message.py               # Message schemas
│   │   ├── agent_execution.py       # Agent execution schemas
│   │   ├── export.py                # Export schemas
│   │   └── common.py                # Shared schemas (pagination, etc.)
│   │
│   ├── services/                    # Business logic layer
│   │   ├── __init__.py
│   │   ├── auth_service.py          # Authentication logic
│   │   ├── user_service.py          # User management logic
│   │   ├── system_service.py        # System management logic
│   │   ├── document_service.py      # Document operations
│   │   ├── document_processor.py    # Document processing pipeline
│   │   ├── embeddings.py            # Embedding generation
│   │   ├── vector_db.py             # Vector database operations
│   │   ├── storage.py               # File storage (S3/local)
│   │   ├── permissions.py           # Permission checking
│   │   ├── conversation_service.py  # Conversation management
│   │   ├── export_service.py        # Export generation
│   │   └── analytics_service.py     # Analytics aggregation
│   │
│   ├── agents/                      # Deep Agents implementation
│   │   ├── __init__.py
│   │   ├── agent_factory.py         # Agent factory
│   │   ├── complexity_classifier.py # Query complexity classification
│   │   ├── prompts.py               # System prompts
│   │   │
│   │   ├── tools/                   # Agent tools
│   │   │   ├── __init__.py
│   │   │   ├── base.py              # Base tool class
│   │   │   ├── semantic_search.py   # Semantic search tool
│   │   │   ├── extract_data.py      # Data extraction
│   │   │   ├── pdf_extraction.py    # PDF table extraction
│   │   │   ├── chart_generation.py  # Chart spec generation
│   │   │   └── filesystem.py        # Filesystem operations
│   │   │
│   │   └── subagents/               # Specialized subagents
│   │       ├── __init__.py
│   │       ├── pdf_extraction.py    # PDF extraction subagent
│   │       ├── trend_analysis.py    # Trend analysis subagent
│   │       ├── chart_generation.py  # Chart generation subagent
│   │       └── report_synthesis.py  # Report synthesis subagent
│   │
│   ├── tasks/                       # Celery tasks
│   │   ├── __init__.py
│   │   ├── celery_app.py            # Celery application
│   │   ├── document_processing.py   # Document processing tasks
│   │   ├── agent_execution.py       # Agent execution tasks
│   │   └── export_generation.py     # Export generation tasks
│   │
│   ├── utils/                       # Utility functions
│   │   ├── __init__.py
│   │   ├── logging.py               # Logging configuration
│   │   ├── email.py                 # Email utilities
│   │   ├── validators.py            # Custom validators
│   │   ├── formatters.py            # Data formatters
│   │   └── pdf_utils.py             # PDF processing utilities
│   │
│   └── mcp/                         # MCP server (optional)
│       ├── __init__.py
│       ├── server.py                # MCP server implementation
│       └── tools.py                 # MCP tool definitions
│
├── tests/                           # Test suite
│   ├── __init__.py
│   ├── conftest.py                  # Pytest configuration & fixtures
│   │
│   ├── api/                         # API endpoint tests
│   │   ├── __init__.py
│   │   ├── test_auth.py
│   │   ├── test_documents.py
│   │   └── test_messages.py
│   │
│   ├── services/                    # Service layer tests
│   │   ├── __init__.py
│   │   ├── test_document_processor.py
│   │   └── test_permissions.py
│   │
│   ├── agents/                      # Agent tests
│   │   ├── __init__.py
│   │   ├── test_agent_factory.py
│   │   ├── test_complexity_classifier.py
│   │   └── tools/
│   │       ├── test_semantic_search.py
│   │       └── test_pdf_extraction.py
│   │
│   └── integration/                 # Integration tests
│       ├── __init__.py
│       ├── test_document_upload_flow.py
│       └── test_query_flow.py
│
├── alembic/                         # Database migrations
│   ├── versions/                    # Migration files
│   ├── env.py                       # Alembic environment
│   └── script.py.mako               # Migration template
│
├── scripts/                         # Utility scripts
│   ├── init_db.py                   # Initialize database
│   ├── seed_data.py                 # Seed test data
│   ├── create_admin.py              # Create admin user
│   └── reindex_documents.py         # Reindex vector database
│
├── .env.example                     # Environment variables template
├── .env                             # Environment variables (gitignored)
├── pyproject.toml                   # Poetry dependencies & config
├── poetry.lock                      # Locked dependencies
├── pytest.ini                       # Pytest configuration
├── alembic.ini                      # Alembic configuration
├── Dockerfile                       # Docker image definition
├── docker-compose.yml               # Docker Compose for development
└── README.md                        # Backend documentation
```

---

## Module Organization

### 1. API Layer (`app/api/`)

**Purpose**: Handle HTTP requests, validation, and responses.

**Responsibilities**:
- Route requests to appropriate endpoints
- Request validation (via Pydantic schemas)
- Authentication and authorization checks
- Dependency injection
- Response formatting

**Example Endpoint** (`app/api/v1/endpoints/messages.py`):

```python
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List

from app.schemas.message import MessageCreate, MessageResponse
from app.models.user import User
from app.api.deps import get_current_user, get_conversation
from app.services.conversation_service import ConversationService
from app.agents.agent_factory import DocumentQAAgentFactory

router = APIRouter(prefix="/conversations/{conversation_id}/messages", tags=["messages"])

@router.post("/", response_model=MessageResponse, status_code=status.HTTP_202_ACCEPTED)
async def create_message(
    conversation_id: str,
    message_in: MessageCreate,
    conversation = Depends(get_conversation),
    current_user: User = Depends(get_current_user),
    conversation_service: ConversationService = Depends()
):
    """Send a message (ask a question)."""

    # Validate conversation ownership
    if conversation.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your conversation")

    # Delegate to service layer
    return await conversation_service.create_message(
        conversation=conversation,
        user=current_user,
        content=message_in.content
    )
```

---

### 2. Core Layer (`app/core/`)

**Purpose**: Fundamental application infrastructure.

**Configuration** (`app/core/config.py`):

```python
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    """Application settings from environment variables."""

    # Application
    APP_NAME: str = "Ask My Docs"
    DEBUG: bool = False
    VERSION: str = "1.0.0"

    # Database
    DATABASE_URL: str
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 10

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # LLM
    ANTHROPIC_API_KEY: str
    DEFAULT_MODEL: str = "claude-sonnet-4"

    # Vector Database
    VECTOR_DB_TYPE: str = "chromadb"  # or "pinecone"
    CHROMA_PERSIST_DIRECTORY: str = "./data/chroma"
    PINECONE_API_KEY: str | None = None
    PINECONE_ENVIRONMENT: str | None = None

    # Storage
    STORAGE_TYPE: str = "local"  # or "s3"
    LOCAL_STORAGE_PATH: str = "./data/documents"
    S3_BUCKET: str | None = None
    AWS_ACCESS_KEY_ID: str | None = None
    AWS_SECRET_ACCESS_KEY: str | None = None

    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    class Config:
        env_file = ".env"
        case_sensitive = True

@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
```

**Database** (`app/core/database.py`):

```python
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager

from app.core.config import get_settings

settings = get_settings()

# Create engine
engine = create_engine(
    settings.DATABASE_URL,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    echo=settings.DEBUG
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()

@contextmanager
def get_db() -> Session:
    """Get database session (context manager)."""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

# Dependency for FastAPI
def get_db_dependency() -> Session:
    """Get database session (dependency injection)."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

**WebSocket** (`app/core/websocket.py`):

```python
from fastapi import WebSocket
from typing import Dict, Set
import json
import asyncio

class WebSocketManager:
    """Manage WebSocket connections and channels."""

    def __init__(self):
        # user_id -> Set[WebSocket]
        self.user_connections: Dict[str, Set[WebSocket]] = {}

        # channel -> Set[user_id]
        self.channel_subscriptions: Dict[str, Set[str]] = {}

    async def connect(self, websocket: WebSocket, user_id: str):
        """Connect a user's WebSocket."""
        await websocket.accept()

        if user_id not in self.user_connections:
            self.user_connections[user_id] = set()
        self.user_connections[user_id].add(websocket)

    async def disconnect(self, websocket: WebSocket, user_id: str):
        """Disconnect a user's WebSocket."""
        if user_id in self.user_connections:
            self.user_connections[user_id].discard(websocket)

            # Clean up channel subscriptions
            for channel, subscribers in self.channel_subscriptions.items():
                subscribers.discard(user_id)

    async def subscribe(self, user_id: str, channels: list[str]):
        """Subscribe user to channels."""
        for channel in channels:
            if channel not in self.channel_subscriptions:
                self.channel_subscriptions[channel] = set()
            self.channel_subscriptions[channel].add(user_id)

    async def send_to_user(self, user_id: str, message: dict):
        """Send message to all connections for a user."""
        if user_id in self.user_connections:
            for websocket in self.user_connections[user_id]:
                await websocket.send_json(message)

    async def send_to_channel(self, channel: str, message: dict):
        """Send message to all users subscribed to a channel."""
        if channel in self.channel_subscriptions:
            for user_id in self.channel_subscriptions[channel]:
                await self.send_to_user(user_id, message)

# Global instance
ws_manager = WebSocketManager()
```

---

### 3. Models Layer (`app/models/`)

**Purpose**: SQLAlchemy ORM models representing database tables.

**Example** (`app/models/user.py`):

```python
from sqlalchemy import Column, String, Boolean, DateTime, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from app.core.database import Base

class UserRole(str, enum.Enum):
    ADMIN = "admin"
    DOC_MANAGER = "doc_manager"
    SYSTEM_USER = "system_user"
    SUPER_USER = "super_user"

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255))

    role = Column(SQLEnum(UserRole), nullable=False, default=UserRole.SYSTEM_USER)

    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login_at = Column(DateTime, nullable=True)

    preferences = Column(JSONB, default=dict)

    # Relationships
    system_assignments = relationship("UserSystem", back_populates="user")
    conversations = relationship("Conversation", back_populates="user")
    documents_uploaded = relationship("Document", foreign_keys="Document.uploaded_by")
```

---

### 4. Schemas Layer (`app/schemas/`)

**Purpose**: Pydantic models for request/response validation.

**Example** (`app/schemas/message.py`):

```python
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID

class MessageBase(BaseModel):
    """Base message schema."""
    content: str = Field(..., min_length=1, max_length=10000)

class MessageCreate(MessageBase):
    """Schema for creating a message."""
    agent_config: Optional[Dict[str, Any]] = None

class RichContentSection(BaseModel):
    """Rich content section."""
    type: str  # "text", "code", "chart", "table"
    content: Optional[str] = None
    language: Optional[str] = None  # for code blocks
    spec: Optional[Dict[str, Any]] = None  # for charts

class SourceDocument(BaseModel):
    """Source document reference."""
    document_id: UUID
    document_name: str
    chunk_ids: List[UUID]
    relevance_score: float

class MessageResponse(BaseModel):
    """Schema for message response."""
    id: UUID
    conversation_id: UUID
    role: str
    content: str
    rich_content: Optional[Dict[str, Any]] = None
    source_documents: Optional[List[SourceDocument]] = None
    agent_execution_id: Optional[UUID] = None
    current_version: int
    created_at: datetime

    class Config:
        from_attributes = True
```

---

### 5. Services Layer (`app/services/`)

**Purpose**: Business logic and orchestration.

**Example** (`app/services/document_service.py`):

```python
from typing import List
from uuid import UUID
from fastapi import UploadFile

from app.models.document import Document
from app.models.user import User
from app.services.storage import StorageService
from app.services.document_processor import DocumentProcessor
from app.tasks.document_processing import process_document_task

class DocumentService:
    """Document management service."""

    def __init__(self):
        self.storage = StorageService()
        self.processor = DocumentProcessor()

    async def upload_documents(
        self,
        files: List[UploadFile],
        system_id: UUID,
        user: User,
        tags: List[str] = None,
        auto_tag: bool = False
    ) -> List[Document]:
        """Upload documents and queue for processing."""

        documents = []

        for file in files:
            # Save file to storage
            file_path = await self.storage.save_file(
                file=file,
                user_id=user.id,
                system_id=system_id
            )

            # Create document record
            document = Document(
                system_id=system_id,
                filename=file.filename,
                original_filename=file.filename,
                file_path=file_path,
                file_size_bytes=file.size,
                file_type=self._get_file_type(file.filename),
                uploaded_by=user.id,
                status="pending"
            )

            # Save to database
            db.add(document)
            db.flush()

            # Queue processing
            process_document_task.delay(
                document_id=str(document.id),
                auto_tag=auto_tag
            )

            documents.append(document)

        db.commit()
        return documents

    def _get_file_type(self, filename: str) -> str:
        """Determine file type from filename."""
        extension = filename.rsplit(".", 1)[-1].lower()
        return extension
```

---

### 6. Agents Layer (`app/agents/`)

**Purpose**: Deep Agents implementation and orchestration.

Structure covered in `deep-agents-implementation.md`.

---

### 7. Tasks Layer (`app/tasks/`)

**Purpose**: Asynchronous background tasks using Celery.

**Celery App** (`app/tasks/celery_app.py`):

```python
from celery import Celery
from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "ask_my_docs",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour max
)
```

**Document Processing Task** (`app/tasks/document_processing.py`):

```python
from celery import Task
from app.tasks.celery_app import celery_app
from app.services.document_processor import DocumentProcessor
from app.core.websocket import ws_manager

class DocumentProcessingTask(Task):
    """Base task for document processing with error handling."""

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Handle task failure."""
        document_id = args[0]
        # Update document status
        # Send WebSocket notification

@celery_app.task(base=DocumentProcessingTask, bind=True)
def process_document_task(self, document_id: str, auto_tag: bool = False):
    """Process document: extract, chunk, embed, index."""

    processor = DocumentProcessor()

    # Send progress updates via WebSocket
    async def progress_callback(step: str, progress: int):
        await ws_manager.send_to_channel(
            channel="document:processing",
            message={
                "type": "document.processing.progress",
                "data": {
                    "document_id": document_id,
                    "step": step,
                    "progress": progress
                }
            }
        )

    # Process document
    result = processor.process(
        document_id=document_id,
        auto_tag=auto_tag,
        progress_callback=progress_callback
    )

    return result
```

---

## Environment Setup

### `.env.example`

```bash
# Application
APP_NAME=Ask My Docs
DEBUG=False
VERSION=1.0.0

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/askmydocs

# Redis
REDIS_URL=redis://localhost:6379/0

# Security
SECRET_KEY=your-secret-key-here-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

# LLM
ANTHROPIC_API_KEY=your-anthropic-key
DEFAULT_MODEL=claude-sonnet-4

# Vector Database
VECTOR_DB_TYPE=chromadb
CHROMA_PERSIST_DIRECTORY=./data/chroma

# Storage
STORAGE_TYPE=local
LOCAL_STORAGE_PATH=./data/documents

# Celery
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2
```

---

## Development Workflow

### 1. Setup

```bash
# Install dependencies
poetry install

# Copy environment template
cp .env.example .env

# Edit .env with your settings
nano .env

# Initialize database
poetry run python scripts/init_db.py

# Run migrations
poetry run alembic upgrade head

# Create admin user
poetry run python scripts/create_admin.py
```

### 2. Run Development Server

```bash
# Terminal 1: FastAPI server
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2: Celery worker
poetry run celery -A app.tasks.celery_app worker --loglevel=info

# Terminal 3: Celery beat (scheduled tasks)
poetry run celery -A app.tasks.celery_app beat --loglevel=info
```

### 3. Run Tests

```bash
# All tests
poetry run pytest

# With coverage
poetry run pytest --cov=app --cov-report=html

# Specific test file
poetry run pytest tests/api/test_messages.py

# Specific test
poetry run pytest tests/api/test_messages.py::test_create_message
```

---

## Docker Setup

### `Dockerfile`

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install poetry

# Copy dependency files
COPY pyproject.toml poetry.lock ./

# Install dependencies
RUN poetry config virtualenvs.create false \
    && poetry install --no-dev --no-interaction --no-ansi

# Copy application
COPY app/ ./app/

# Expose port
EXPOSE 8000

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### `docker-compose.yml`

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_USER: askmydocs
      POSTGRES_PASSWORD: password
      POSTGRES_DB: askmydocs
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7
    ports:
      - "6379:6379"

  api:
    build: .
    ports:
      - "8000:8000"
    depends_on:
      - postgres
      - redis
    environment:
      DATABASE_URL: postgresql://askmydocs:password@postgres:5432/askmydocs
      REDIS_URL: redis://redis:6379/0
    volumes:
      - ./app:/app/app
      - ./data:/app/data

  worker:
    build: .
    command: celery -A app.tasks.celery_app worker --loglevel=info
    depends_on:
      - postgres
      - redis
    environment:
      DATABASE_URL: postgresql://askmydocs:password@postgres:5432/askmydocs
      REDIS_URL: redis://redis:6379/0
    volumes:
      - ./app:/app/app
      - ./data:/app/data

volumes:
  postgres_data:
```

---

## Naming Conventions

### Files
- **Python modules**: `snake_case.py`
- **Test files**: `test_<module_name>.py`
- **Migration files**: `<timestamp>_<description>.py`

### Code
- **Classes**: `PascalCase`
- **Functions/methods**: `snake_case`
- **Constants**: `UPPER_SNAKE_CASE`
- **Private methods**: `_leading_underscore`

### Database
- **Tables**: `snake_case` (plural: `users`, `documents`)
- **Columns**: `snake_case`
- **Indexes**: `idx_<table>_<column(s)>`
- **Foreign keys**: `fk_<table>_<referenced_table>`

---

## Import Organization

```python
# Standard library
import os
import json
from typing import List, Dict, Optional
from datetime import datetime

# Third-party
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

# Local application
from app.core.config import get_settings
from app.core.database import get_db
from app.models.user import User
from app.schemas.message import MessageCreate, MessageResponse
from app.services.conversation_service import ConversationService
```

---

**Last Updated**: 2025-11-15
**Status**: Complete backend structure documentation
