"""Pydantic schemas for agent execution and HITL."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


# ============================================================================
# Agent Execution Schemas
# ============================================================================

class AgentExecutionBase(BaseModel):
    """Base schema for agent execution."""
    pass


class AgentExecutionCreate(BaseModel):
    """Schema for creating an agent execution."""
    conversation_id: UUID
    agent_type: str = Field(..., description="Agent type: simple, moderate, or complex")
    model_name: str = Field(..., description="LLM model name")
    planning_enabled: bool = False
    filesystem_enabled: bool = False


class PlanTodoItem(BaseModel):
    """Schema for a single todo item in the plan."""
    content: str = Field(..., description="Todo item description (imperative form)")
    status: str = Field(default="pending", description="Status: pending, in_progress, completed")
    activeForm: str = Field(..., description="Present continuous form for display during execution")


class ExecutionPlan(BaseModel):
    """Schema for agent execution plan."""
    todos: List[PlanTodoItem] = Field(..., description="List of steps to execute")
    estimated_duration_ms: Optional[int] = Field(None, description="Estimated execution time")
    requires_approval: bool = Field(True, description="Whether this plan requires human approval")


class ApprovalRequest(BaseModel):
    """Schema for approving/rejecting an execution."""
    approved: bool = Field(..., description="True to approve, False to reject")
    modified_plan: Optional[ExecutionPlan] = Field(None, description="Modified plan if user changed it")
    notes: Optional[str] = Field(None, description="Optional notes from approver")


class HITLInfo(BaseModel):
    """Schema for HITL-related information."""
    paused_at: Optional[datetime] = None
    approved_at: Optional[datetime] = None
    approved_by: Optional[UUID] = None
    is_awaiting_approval: bool = False
    is_approved: bool = False


class PerformanceStats(BaseModel):
    """Schema for execution performance statistics."""
    total_duration_ms: Optional[int] = None
    duration_seconds: Optional[float] = None
    llm_calls_count: int = 0
    total_tokens_used: int = 0


class ToolCall(BaseModel):
    """Schema for tool usage information."""
    tool_name: str
    call_count: int
    avg_duration_ms: int


class ExecutionError(BaseModel):
    """Schema for execution error information."""
    message: str
    stack_trace: Optional[str] = None


class AgentExecutionResponse(BaseModel):
    """Schema for agent execution response."""
    id: UUID
    conversation_id: UUID
    message_id: Optional[UUID] = None
    agent_type: str
    model_name: str
    planning_enabled: bool
    filesystem_enabled: bool
    status: str
    started_at: datetime
    completed_at: Optional[datetime] = None

    # HITL information
    hitl: HITLInfo

    # Plan
    plan: Optional[ExecutionPlan] = None

    # Performance
    performance: PerformanceStats

    # Tools and subagents
    tools_called: Optional[List[ToolCall]] = None
    subagents_used: Optional[List[str]] = None

    # Error information
    error: Optional[ExecutionError] = None

    class Config:
        from_attributes = True


class AgentExecutionListItem(BaseModel):
    """Schema for agent execution in list view."""
    id: UUID
    conversation_id: UUID
    agent_type: str
    status: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    is_awaiting_approval: bool
    total_duration_ms: Optional[int] = None

    class Config:
        from_attributes = True


# ============================================================================
# WebSocket Event Schemas
# ============================================================================

class WebSocketMessage(BaseModel):
    """Base schema for WebSocket messages."""
    type: str = Field(..., description="Event type")
    channel: Optional[str] = Field(None, description="Channel name")
    data: Dict[str, Any] = Field(..., description="Event data")
    timestamp: str = Field(..., description="ISO timestamp")


class ExecutionPlanEvent(BaseModel):
    """Schema for execution plan WebSocket event."""
    execution_id: UUID
    status: str
    plan: ExecutionPlan
    approval_required: bool
    paused_at: str


class ExecutionProgressEvent(BaseModel):
    """Schema for execution progress WebSocket event."""
    execution_id: UUID
    status: str
    current_step: Dict[str, Any]


class ExecutionCompletedEvent(BaseModel):
    """Schema for execution completed WebSocket event."""
    execution_id: UUID
    message_id: UUID
    status: str
    completed_at: str
    stats: PerformanceStats


class ExecutionFailedEvent(BaseModel):
    """Schema for execution failed WebSocket event."""
    execution_id: UUID
    status: str
    error: ExecutionError


# ============================================================================
# Request/Response for specific endpoints
# ============================================================================

class CreateExecutionRequest(BaseModel):
    """Request to create and start an agent execution."""
    question: str = Field(..., min_length=1, max_length=10000, description="User's question")
    conversation_id: UUID = Field(..., description="Conversation ID")
    force_complexity: Optional[str] = Field(
        None,
        description="Force specific complexity: simple, moderate, or complex"
    )


class CreateExecutionResponse(BaseModel):
    """Response after creating an execution."""
    execution_id: UUID
    status: str
    message: str
    websocket_channel: str


class ApprovalResponse(BaseModel):
    """Response after approving/rejecting an execution."""
    execution_id: UUID
    status: str
    approved: bool
    message: str


class ProgressUpdate(BaseModel):
    """Schema for manual progress updates."""
    current_step: str = Field(..., description="Description of current step")
    step_number: int = Field(..., ge=1, description="Current step number")
    total_steps: int = Field(..., ge=1, description="Total number of steps")
    message: str = Field(..., description="Progress message")
