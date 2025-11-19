"""Document, DocumentChunk, Tag, and DocumentTag models."""

import uuid
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector

from app.core.database import Base


class Document(Base):
    """Document model for storing document metadata."""

    __tablename__ = "documents"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # System relationship
    system_id = Column(
        UUID(as_uuid=True),
        ForeignKey("systems.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # File information
    filename = Column(String(500), nullable=False)
    original_filename = Column(String(500), nullable=False)
    file_path = Column(String(1000), nullable=False)  # S3 key or local path
    file_size_bytes = Column(BigInteger, nullable=False)
    file_type = Column(String(50), nullable=False, index=True)  # pdf, docx, etc.
    mime_type = Column(String(100), nullable=True)

    # Document metadata
    title = Column(String(500), nullable=True)
    description = Column(String, nullable=True)

    # Version tracking
    version = Column(Integer, default=1, nullable=False)
    parent_document_id = Column(
        UUID(as_uuid=True),
        ForeignKey("documents.id"),
        nullable=True,
    )

    # Processing status
    status = Column(
        String(50),
        default="pending",
        nullable=False,
        index=True,
    )  # pending, processing, ready, failed
    processing_started_at = Column(DateTime, nullable=True)
    processing_completed_at = Column(DateTime, nullable=True)
    processing_error = Column(String, nullable=True)

    # Extracted metadata
    page_count = Column(Integer, nullable=True)
    word_count = Column(Integer, nullable=True)
    extracted_metadata = Column(JSONB, nullable=True)

    # Upload tracking
    uploaded_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )
    uploaded_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Edit tracking
    last_edited_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    last_edited_at = Column(DateTime, nullable=True)

    # Soft delete
    is_deleted = Column(Boolean, default=False, index=True)
    deleted_at = Column(DateTime, nullable=True)
    deleted_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    # Relationships
    system = relationship("System", back_populates="documents")
    uploader = relationship(
        "User",
        foreign_keys=[uploaded_by],
        back_populates="documents_uploaded",
    )
    editor = relationship("User", foreign_keys=[last_edited_by])
    deleter = relationship("User", foreign_keys=[deleted_by])
    parent_document = relationship("Document", remote_side=[id])
    chunks = relationship(
        "DocumentChunk",
        back_populates="document",
        cascade="all, delete-orphan",
    )
    tag_associations = relationship(
        "DocumentTag",
        back_populates="document",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Document(id={self.id}, filename={self.filename}, status={self.status})>"


class DocumentChunk(Base):
    """Document chunk model for vector database sync."""

    __tablename__ = "document_chunks"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Document relationship
    document_id = Column(
        UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Chunk content
    chunk_index = Column(Integer, nullable=False)  # Order within document
    content = Column(String, nullable=False)
    content_hash = Column(String(64), nullable=True, index=True)  # SHA-256

    # Chunk metadata
    start_char_index = Column(Integer, nullable=True)
    end_char_index = Column(Integer, nullable=True)
    page_number = Column(Integer, nullable=True)
    section_title = Column(String(500), nullable=True)

    # Embedding info (PGVector - stored directly in PostgreSQL)
    embedding_model = Column(String(100), default="text-embedding-3-small")
    embedding = Column(Vector(1536))  # OpenAI embeddings are 1536 dimensions
    embedded_at = Column(DateTime, nullable=True)

    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    document = relationship("Document", back_populates="chunks")

    # Constraints
    __table_args__ = (
        UniqueConstraint("document_id", "chunk_index", name="unique_chunk_per_document"),
    )

    def __repr__(self) -> str:
        return f"<DocumentChunk(id={self.id}, document_id={self.document_id}, index={self.chunk_index})>"


class Tag(Base):
    """Tag model for organizing documents within systems."""

    __tablename__ = "tags"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # System relationship
    system_id = Column(
        UUID(as_uuid=True),
        ForeignKey("systems.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    # Tag details
    name = Column(String(100), nullable=False)
    color = Column(String(7), nullable=True)  # Hex color for UI

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    # Relationships
    system = relationship("System", back_populates="tags")
    creator = relationship("User", foreign_keys=[created_by])
    document_associations = relationship(
        "DocumentTag",
        back_populates="tag",
        cascade="all, delete-orphan",
    )

    # Constraints
    __table_args__ = (UniqueConstraint("system_id", "name", name="unique_tag_per_system"),)

    def __repr__(self) -> str:
        return f"<Tag(id={self.id}, name={self.name}, system_id={self.system_id})>"


class DocumentTag(Base):
    """Many-to-many relationship between documents and tags."""

    __tablename__ = "document_tags"

    # Composite primary key
    document_id = Column(
        UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        primary_key=True,
    )
    tag_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tags.id", ondelete="CASCADE"),
        primary_key=True,
    )

    # Metadata
    added_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    added_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    # Relationships
    document = relationship("Document", back_populates="tag_associations")
    tag = relationship("Tag", back_populates="document_associations")
    adder = relationship("User", foreign_keys=[added_by])

    def __repr__(self) -> str:
        return f"<DocumentTag(document_id={self.document_id}, tag_id={self.tag_id})>"
