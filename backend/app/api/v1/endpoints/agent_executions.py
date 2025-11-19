"""Agent execution endpoints with HITL support."""

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.core.websocket import ws_manager
from app.models.user import User
from app.schemas.agent_execution import (
    AgentExecutionResponse,
    AgentExecutionListItem,
    ApprovalRequest,
    ApprovalResponse,
)
from app.services.agent_execution_service import AgentExecutionService

router = APIRouter(prefix="/agent-executions", tags=["agent-executions"])


@router.get("/{execution_id}", response_model=AgentExecutionResponse)
async def get_execution(
    execution_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get agent execution details.

    Returns full details about an agent execution including:
    - Execution status and timings
    - HITL approval information
    - Execution plan (if any)
    - Performance statistics
    - Tools and subagents used
    """
    service = AgentExecutionService(db, ws_manager)
    execution_data = service.get_execution_with_details(execution_id)

    if not execution_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Execution {execution_id} not found"
        )

    # Verify user has access to this execution
    execution = service.get_execution(execution_id)
    if execution.conversation.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to view this execution"
        )

    return execution_data


@router.post("/{execution_id}/approve", response_model=ApprovalResponse)
async def approve_execution(
    execution_id: UUID,
    approval: ApprovalRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Approve or reject an agent execution plan (HITL checkpoint).

    This is the core HITL endpoint. When an agent creates a plan and pauses,
    the user reviews it and either:
    - Approves it (agent continues execution)
    - Modifies it (agent uses modified plan)
    - Rejects it (execution is cancelled)

    Args:
        execution_id: The execution to approve/reject
        approval: Approval decision and optional modified plan

    Returns:
        Approval response with updated execution status

    Raises:
        404: Execution not found
        403: User doesn't own this execution
        400: Execution is not awaiting approval
    """
    service = AgentExecutionService(db, ws_manager)

    try:
        # Approve or reject the execution
        execution = await service.approve_execution(
            execution_id=execution_id,
            user=current_user,
            approved=approval.approved,
            modified_plan=approval.modified_plan.dict() if approval.modified_plan else None,
        )

        # Prepare response
        if approval.approved:
            message = "Execution approved and resumed"
            if approval.modified_plan:
                message = "Execution approved with modified plan and resumed"
        else:
            message = "Execution rejected and cancelled"

        return ApprovalResponse(
            execution_id=execution.id,
            status=execution.status,
            approved=approval.approved,
            message=message,
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )


@router.post("/{execution_id}/cancel")
async def cancel_execution(
    execution_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Cancel a running or paused execution.

    Args:
        execution_id: The execution to cancel

    Returns:
        Cancellation confirmation

    Raises:
        404: Execution not found
        403: User doesn't own this execution
        400: Execution is already completed/failed
    """
    service = AgentExecutionService(db, ws_manager)
    execution = service.get_execution(execution_id)

    if not execution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Execution {execution_id} not found"
        )

    # Verify user owns this execution
    if execution.conversation.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to cancel this execution"
        )

    # Check if execution can be cancelled
    if execution.is_completed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot cancel a completed execution"
        )

    # Cancel the execution
    await service.fail_execution(
        execution_id=execution_id,
        error_message="Cancelled by user",
    )

    return {
        "execution_id": str(execution_id),
        "status": "cancelled",
        "message": "Execution cancelled successfully"
    }


@router.get("/conversation/{conversation_id}", response_model=List[AgentExecutionListItem])
async def list_conversation_executions(
    conversation_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all agent executions for a conversation.

    Args:
        conversation_id: The conversation ID

    Returns:
        List of executions for this conversation

    Raises:
        404: Conversation not found
        403: User doesn't own this conversation
    """
    from app.models.conversation import Conversation
    from app.models.agent_execution import AgentExecution

    # Verify conversation exists and user has access
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id
    ).first()

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation {conversation_id} not found"
        )

    if conversation.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to view this conversation"
        )

    # Get all executions for this conversation
    executions = db.query(AgentExecution).filter(
        AgentExecution.conversation_id == conversation_id
    ).order_by(AgentExecution.started_at.desc()).all()

    return [
        AgentExecutionListItem(
            id=execution.id,
            conversation_id=execution.conversation_id,
            agent_type=execution.agent_type,
            status=execution.status,
            started_at=execution.started_at,
            completed_at=execution.completed_at,
            is_awaiting_approval=execution.is_awaiting_approval,
            total_duration_ms=execution.total_duration_ms,
        )
        for execution in executions
    ]
