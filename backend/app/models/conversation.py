"""Conversation and Message models for HITL-aware messaging."""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class Conversation(Base):
    """Conversation (session) model for organizing messages."""

    __tablename__ = "conversations"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # User relationship
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Conversation metadata
    title = Column(String(500), nullable=True)  # Auto-generated from first message

    # System filters applied to this conversation
    system_filters = Column(ARRAY(UUID(as_uuid=True)), nullable=True)

    # Statistics
    message_count = Column(Integer, default=0, nullable=False)
    total_tokens_used = Column(Integer, default=0, nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    # Archive/delete
    is_archived = Column(Boolean, default=False, index=True)
    archived_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User", back_populates="conversations")
    messages = relationship(
        "Message",
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="Message.created_at",
    )
    agent_executions = relationship(
        "AgentExecution",
        back_populates="conversation",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Conversation(id={self.id}, user_id={self.user_id}, messages={self.message_count})>"


class Message(Base):
    """Message model with rich content support for HITL workflow."""

    __tablename__ = "messages"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Conversation relationship
    conversation_id = Column(
        UUID(as_uuid=True),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Message details
    role = Column(
        String(20),
        nullable=False,
        index=True,
    )  # 'user', 'assistant', 'system'
    content = Column(Text, nullable=False)

    # Rich content for agent outputs (charts, tables, formatted sections)
    rich_content = Column(JSONB, nullable=True)
    """
    Example rich_content structure:
    {
        "sections": [
            {
                "type": "text",
                "content": "Analysis summary..."
            },
            {
                "type": "chart",
                "spec": {
                    "type": "line",
                    "title": "Revenue Trend",
                    "data": {...}
                }
            },
            {
                "type": "table",
                "headers": ["Q1", "Q2", "Q3", "Q4"],
                "rows": [[...]]
            }
        ],
        "citations": [
            {
                "document_id": "uuid",
                "document_name": "Q1_2023.pdf",
                "page": 12,
                "excerpt": "Revenue increased by..."
            }
        ]
    }
    """

    # Agent execution reference (for assistant messages)
    agent_execution_id = Column(
        UUID(as_uuid=True),
        ForeignKey("agent_executions.id"),
        nullable=True,
        index=True,
    )

    # Token usage
    prompt_tokens = Column(Integer, nullable=True)
    completion_tokens = Column(Integer, nullable=True)
    total_tokens = Column(Integer, nullable=True)

    # Citations/sources
    source_documents = Column(JSONB, nullable=True)
    """
    Example source_documents structure:
    [
        {
            "document_id": "uuid",
            "document_name": "Installation Guide",
            "chunk_ids": ["uuid1", "uuid2"],
            "relevance_score": 0.94
        }
    ]
    """

    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Version tracking (for edits)
    current_version = Column(Integer, default=1, nullable=False)

    # Relationships
    conversation = relationship("Conversation", back_populates="messages")
    agent_execution = relationship("AgentExecution", back_populates="message")
    edits = relationship(
        "MessageEdit",
        back_populates="message",
        cascade="all, delete-orphan",
        order_by="MessageEdit.version_number",
    )

    def __repr__(self) -> str:
        return f"<Message(id={self.id}, role={self.role}, conversation_id={self.conversation_id})>"

    @property
    def has_edits(self) -> bool:
        """Check if message has been edited."""
        return self.current_version > 1


class MessageEdit(Base):
    """Message edit history for version tracking."""

    __tablename__ = "message_edits"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Message relationship
    message_id = Column(
        UUID(as_uuid=True),
        ForeignKey("messages.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Version number
    version_number = Column(Integer, nullable=False)

    # Edit details
    original_content = Column(Text, nullable=False)
    original_rich_content = Column(JSONB, nullable=True)
    edited_content = Column(Text, nullable=False)
    edited_rich_content = Column(JSONB, nullable=True)

    # Who made the edit
    edited_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )
    edited_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Edit metadata
    edit_reason = Column(String(500), nullable=True)
    changes_summary = Column(Text, nullable=True)

    # Relationships
    message = relationship("Message", back_populates="edits")
    editor = relationship("User", foreign_keys=[edited_by])

    # Constraints
    from sqlalchemy import UniqueConstraint

    __table_args__ = (
        UniqueConstraint("message_id", "version_number", name="unique_message_version"),
    )

    def __repr__(self) -> str:
        return f"<MessageEdit(message_id={self.message_id}, version={self.version_number})>"
