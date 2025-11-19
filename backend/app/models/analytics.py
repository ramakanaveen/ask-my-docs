"""Analytics, feedback, export, and audit models."""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import INET, JSONB, UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class QAAnalytics(Base):
    """Q&A analytics for compliance and system improvement."""

    __tablename__ = "qa_analytics"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # References
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )
    conversation_id = Column(
        UUID(as_uuid=True),
        ForeignKey("conversations.id"),
        nullable=False,
        index=True,
    )
    message_id = Column(
        UUID(as_uuid=True),
        ForeignKey("messages.id"),
        nullable=False,
        index=True,
    )
    agent_execution_id = Column(
        UUID(as_uuid=True),
        ForeignKey("agent_executions.id"),
        nullable=True,
    )

    # Query details
    question = Column(Text, nullable=False)
    question_length = Column(Integer, nullable=True)
    question_tokens = Column(Integer, nullable=True)

    # Systems queried
    systems_queried = Column(JSONB, nullable=True)  # Array of system IDs

    # Answer details
    answer = Column(Text, nullable=False)
    answer_length = Column(Integer, nullable=True)
    answer_tokens = Column(Integer, nullable=True)

    # Documents used
    documents_used = Column(JSONB, nullable=True)
    """
    Example structure:
    [
        {
            "document_id": "uuid",
            "document_name": "Installation Guide",
            "relevance_score": 0.94,
            "chunks_used": 5
        }
    ]
    """
    total_documents_used = Column(Integer, nullable=True)
    total_chunks_used = Column(Integer, nullable=True)

    # Performance metrics
    response_time_ms = Column(Integer, nullable=True, index=True)
    retrieval_time_ms = Column(Integer, nullable=True)
    llm_time_ms = Column(Integer, nullable=True)

    # Model info
    model_name = Column(String(100), nullable=True)
    total_tokens_used = Column(Integer, nullable=True)
    estimated_cost_usd = Column(Numeric(10, 6), nullable=True)

    # User feedback
    user_rating = Column(String(50), nullable=True, index=True)  # thumbs_up, thumbs_down, neutral
    user_feedback_text = Column(Text, nullable=True)
    feedback_received_at = Column(DateTime, nullable=True)

    # Quality indicators
    has_citations = Column(Boolean, nullable=True)
    citation_count = Column(Integer, nullable=True)

    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    conversation = relationship("Conversation", foreign_keys=[conversation_id])
    message = relationship("Message", foreign_keys=[message_id])
    agent_execution = relationship("AgentExecution", foreign_keys=[agent_execution_id])

    def __repr__(self) -> str:
        return f"<QAAnalytics(id={self.id}, user_id={self.user_id})>"


class UserFeedback(Base):
    """User feedback and corrections."""

    __tablename__ = "user_feedback"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # References
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )
    message_id = Column(
        UUID(as_uuid=True),
        ForeignKey("messages.id"),
        nullable=True,
        index=True,
    )

    # Feedback type
    feedback_type = Column(
        String(50),
        nullable=False,
        index=True,
    )  # 'rating', 'correction', 'feature_request', 'bug_report'

    # Rating feedback
    rating = Column(String(50), nullable=True)  # 'thumbs_up', 'thumbs_down', 'neutral'

    # Text feedback
    feedback_text = Column(Text, nullable=True)

    # Structured feedback (for corrections)
    feedback_data = Column(JSONB, nullable=True)
    """
    Example for corrections:
    {
        "incorrect_claim": "The revenue increased by 50%",
        "correct_information": "The revenue increased by 15%",
        "source_document_id": "uuid",
        "page_number": 12
    }
    """

    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Response tracking
    addressed = Column(Boolean, default=False, index=True)
    addressed_at = Column(DateTime, nullable=True)
    addressed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    resolution_notes = Column(Text, nullable=True)

    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    message = relationship("Message", foreign_keys=[message_id])
    resolver = relationship("User", foreign_keys=[addressed_by])

    def __repr__(self) -> str:
        return f"<UserFeedback(id={self.id}, type={self.feedback_type})>"


class Export(Base):
    """Export generation and tracking."""

    __tablename__ = "exports"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # References
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )
    message_id = Column(
        UUID(as_uuid=True),
        ForeignKey("messages.id"),
        nullable=False,
        index=True,
    )

    # Export details
    export_format = Column(
        String(20),
        nullable=False,
    )  # 'pdf', 'markdown', 'html', 'docx'
    file_path = Column(String(1000), nullable=False)  # S3 key or local path
    file_size_bytes = Column(Integer, nullable=True)

    # Export configuration
    include_charts = Column(Boolean, default=True)
    include_citations = Column(Boolean, default=True)
    styling_template = Column(String(100), nullable=True)  # 'professional', 'minimal', 'corporate'

    # Version exported
    message_version = Column(Integer, default=1)

    # Generation tracking
    status = Column(
        String(50),
        default="pending",
        nullable=False,
        index=True,
    )  # 'pending', 'generating', 'completed', 'failed'
    generated_at = Column(DateTime, nullable=True)
    generation_error = Column(Text, nullable=True)

    # Download tracking
    download_count = Column(Integer, default=0)
    last_downloaded_at = Column(DateTime, nullable=True)

    # Expiry (auto-delete after 30 days)
    expires_at = Column(DateTime, nullable=True, index=True)

    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    message = relationship("Message", foreign_keys=[message_id])

    def __repr__(self) -> str:
        return f"<Export(id={self.id}, format={self.export_format}, status={self.status})>"

    @property
    def is_expired(self) -> bool:
        """Check if export has expired."""
        if self.expires_at:
            return datetime.utcnow() > self.expires_at
        return False


class AuditLog(Base):
    """Audit log for compliance and security."""

    __tablename__ = "audit_logs"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Who & What
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True)
    action = Column(
        String(100),
        nullable=False,
        index=True,
    )  # 'user.login', 'document.upload', 'system.assign', etc.
    entity_type = Column(String(50), nullable=True)  # 'user', 'document', 'system', 'conversation'
    entity_id = Column(UUID(as_uuid=True), nullable=True)

    # Details
    old_values = Column(JSONB, nullable=True)
    new_values = Column(JSONB, nullable=True)
    changes = Column(JSONB, nullable=True)

    # Context
    ip_address = Column(INET, nullable=True)
    user_agent = Column(Text, nullable=True)

    # Result
    success = Column(Boolean, default=True)
    error_message = Column(Text, nullable=True)

    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationships
    user = relationship("User", foreign_keys=[user_id])

    def __repr__(self) -> str:
        return f"<AuditLog(id={self.id}, action={self.action}, user_id={self.user_id})>"
