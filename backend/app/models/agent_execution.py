"""Agent execution models with Human-in-the-Loop (HITL) support."""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class AgentExecution(Base):
    """Agent execution tracking with HITL support.

    This model is the core of the Human-in-the-Loop workflow.
    Execution flow:
    1. Status: 'planning' - Agent creates plan
    2. Status: 'paused' - Waiting for human approval (HITL checkpoint)
    3. Status: 'running' - Executing after approval
    4. Status: 'completed' or 'failed' - Final states
    """

    __tablename__ = "agent_executions"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Conversation relationship
    conversation_id = Column(
        UUID(as_uuid=True),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Message relationship (the assistant message this execution produced)
    message_id = Column(
        UUID(as_uuid=True),
        ForeignKey("messages.id"),
        nullable=True,
    )

    # Agent configuration
    agent_type = Column(
        String(100),
        nullable=False,
        index=True,
    )  # 'simple', 'moderate', 'complex'
    model_name = Column(String(100), nullable=False)  # 'claude-haiku', 'claude-sonnet-4'

    # Deep Agents specific
    planning_enabled = Column(Boolean, default=False)
    filesystem_enabled = Column(Boolean, default=False)
    subagents_used = Column(JSONB, nullable=True)  # Array of subagent names

    # Execution tracking
    status = Column(
        String(50),
        default="running",
        nullable=False,
        index=True,
    )  # 'running', 'planning', 'paused', 'completed', 'failed', 'cancelled'
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    completed_at = Column(DateTime, nullable=True)

    # ========================================================================
    # HUMAN-IN-THE-LOOP (HITL) FIELDS - CRITICAL FOR APPROVAL WORKFLOW
    # ========================================================================

    # When execution paused for human approval
    hitl_paused_at = Column(DateTime, nullable=True)

    # When human approved the plan
    hitl_approved_at = Column(DateTime, nullable=True)

    # Who approved the execution
    hitl_approved_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True,
    )

    # The plan that was approved (or modified by user)
    plan_json = Column(JSONB, nullable=True)
    """
    Example plan_json structure:
    {
        "todos": [
            {
                "content": "Extract financial data from Q1 2023 report",
                "status": "pending",
                "activeForm": "Extracting financial data from Q1 2023 report"
            },
            {
                "content": "Calculate YoY growth rates",
                "status": "pending",
                "activeForm": "Calculating YoY growth rates"
            }
        ],
        "estimated_duration_ms": 30000,
        "requires_approval": true
    }
    """

    # Performance metrics
    total_duration_ms = Column(Integer, nullable=True)
    llm_calls_count = Column(Integer, default=0)
    total_tokens_used = Column(Integer, default=0)

    # Tools and subagents used during execution
    tools_called = Column(JSONB, nullable=True)
    """
    Example tools_called structure:
    [
        {
            "tool_name": "semantic_search",
            "call_count": 5,
            "avg_duration_ms": 230
        },
        {
            "tool_name": "extract_pdf_tables",
            "call_count": 2,
            "avg_duration_ms": 1200
        }
    ]
    """

    # Error tracking
    error_message = Column(Text, nullable=True)
    error_stack_trace = Column(Text, nullable=True)

    # Execution trace (LangGraph state snapshots for debugging)
    execution_trace = Column(JSONB, nullable=True)
    """
    Example execution_trace structure:
    {
        "steps": [
            {
                "step_id": 1,
                "timestamp": "2024-01-15T10:30:00Z",
                "node": "planner",
                "action": "write_todos",
                "output": {...}
            },
            {
                "step_id": 2,
                "timestamp": "2024-01-15T10:30:15Z",
                "node": "executor",
                "action": "spawn_subagent",
                "subagent": "pdf-extraction-agent",
                "input": {...}
            }
        ]
    }
    """

    # Relationships
    conversation = relationship("Conversation", back_populates="agent_executions")
    message = relationship("Message", back_populates="agent_execution")
    approver = relationship("User", foreign_keys=[hitl_approved_by])
    filesystem_files = relationship(
        "AgentFilesystem",
        back_populates="agent_execution",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<AgentExecution(id={self.id}, type={self.agent_type}, status={self.status})>"

    @property
    def is_awaiting_approval(self) -> bool:
        """Check if execution is paused and waiting for human approval."""
        return self.status == "paused" and self.hitl_paused_at is not None

    @property
    def is_approved(self) -> bool:
        """Check if execution has been approved by human."""
        return self.hitl_approved_at is not None and self.hitl_approved_by is not None

    @property
    def is_completed(self) -> bool:
        """Check if execution is finished (success or failure)."""
        return self.status in ["completed", "failed", "cancelled"]

    @property
    def duration_seconds(self) -> float | None:
        """Get execution duration in seconds."""
        if self.total_duration_ms:
            return self.total_duration_ms / 1000.0
        return None


class AgentFilesystem(Base):
    """Agent filesystem storage for Deep Agents intermediate results."""

    __tablename__ = "agent_filesystem"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Agent execution relationship
    agent_execution_id = Column(
        UUID(as_uuid=True),
        ForeignKey("agent_executions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # File details
    file_path = Column(String(500), nullable=False)  # e.g., "q1_2023_data.json"
    file_type = Column(String(50), nullable=True)  # 'json', 'csv', 'txt', 'md'

    # Content storage (for small files, store directly; for large, use S3)
    content = Column(Text, nullable=True)
    content_s3_key = Column(String(1000), nullable=True)
    file_size_bytes = Column(Integer, nullable=True)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_by_subagent = Column(String(100), nullable=True)  # Which subagent created this

    # Purpose/description
    description = Column(Text, nullable=True)

    # Relationships
    agent_execution = relationship("AgentExecution", back_populates="filesystem_files")

    # Constraints
    from sqlalchemy import UniqueConstraint

    __table_args__ = (
        UniqueConstraint(
            "agent_execution_id",
            "file_path",
            name="unique_file_per_execution",
        ),
    )

    def __repr__(self) -> str:
        return f"<AgentFilesystem(id={self.id}, path={self.file_path})>"
