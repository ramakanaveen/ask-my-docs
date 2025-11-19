"""Agent execution service with Human-in-the-Loop (HITL) workflow."""

from datetime import datetime
from typing import Dict, Any, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.agent_execution import AgentExecution, AgentFilesystem
from app.models.conversation import Conversation, Message
from app.models.user import User
from app.core.websocket import WebSocketManager


class AgentExecutionService:
    """Service for managing agent executions with HITL support.

    This service implements the core Human-in-the-Loop workflow:
    1. Create execution record
    2. Agent creates plan
    3. PAUSE for user approval
    4. User approves/modifies plan
    5. Resume execution
    6. Return results
    """

    def __init__(self, db: Session, ws_manager: WebSocketManager):
        self.db = db
        self.ws_manager = ws_manager

    async def create_execution(
        self,
        conversation_id: UUID,
        agent_type: str,
        model_name: str,
        planning_enabled: bool = False,
        filesystem_enabled: bool = False,
    ) -> AgentExecution:
        """Create a new agent execution record.

        Args:
            conversation_id: The conversation this execution belongs to
            agent_type: Type of agent ('simple', 'moderate', 'complex')
            model_name: LLM model to use
            planning_enabled: Whether agent uses planning (HITL)
            filesystem_enabled: Whether agent uses filesystem

        Returns:
            Created AgentExecution instance
        """
        execution = AgentExecution(
            conversation_id=conversation_id,
            agent_type=agent_type,
            model_name=model_name,
            planning_enabled=planning_enabled,
            filesystem_enabled=filesystem_enabled,
            status="running" if not planning_enabled else "planning",
            started_at=datetime.utcnow(),
        )

        self.db.add(execution)
        self.db.commit()
        self.db.refresh(execution)

        return execution

    async def pause_for_approval(
        self,
        execution_id: UUID,
        plan: Dict[str, Any],
        user_id: UUID,
    ) -> AgentExecution:
        """Pause execution and wait for human approval.

        This is the core HITL checkpoint. Agent has created a plan
        and now waits for user to approve before proceeding.

        Args:
            execution_id: The execution to pause
            plan: The plan created by the agent (todos)
            user_id: User who will approve

        Returns:
            Updated AgentExecution instance
        """
        execution = self.db.query(AgentExecution).filter(
            AgentExecution.id == execution_id
        ).first()

        if not execution:
            raise ValueError(f"Execution {execution_id} not found")

        # Update execution to paused state
        execution.status = "paused"
        execution.plan_json = plan
        execution.hitl_paused_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(execution)

        # Notify user via WebSocket
        await self.ws_manager.send_to_user(
            user_id=str(user_id),
            message={
                "type": "agent.execution.awaiting_approval",
                "channel": f"execution:{execution_id}",
                "data": {
                    "execution_id": str(execution_id),
                    "status": "paused",
                    "plan": plan,
                    "approval_required": True,
                    "paused_at": execution.hitl_paused_at.isoformat(),
                },
                "timestamp": datetime.utcnow().isoformat(),
            }
        )

        return execution

    async def approve_execution(
        self,
        execution_id: UUID,
        user: User,
        approved: bool = True,
        modified_plan: Optional[Dict[str, Any]] = None,
    ) -> AgentExecution:
        """Approve (or reject) an execution plan.

        Args:
            execution_id: The execution to approve
            user: User approving the execution
            approved: Whether user approved (True) or rejected (False)
            modified_plan: Optional modified plan from user

        Returns:
            Updated AgentExecution instance

        Raises:
            ValueError: If execution not found or not awaiting approval
            PermissionError: If user doesn't own the conversation
        """
        execution = self.db.query(AgentExecution).filter(
            AgentExecution.id == execution_id
        ).first()

        if not execution:
            raise ValueError(f"Execution {execution_id} not found")

        if not execution.is_awaiting_approval:
            raise ValueError(f"Execution {execution_id} is not awaiting approval")

        # Verify user owns this conversation
        conversation = self.db.query(Conversation).filter(
            Conversation.id == execution.conversation_id
        ).first()

        if conversation.user_id != user.id:
            raise PermissionError("You don't have permission to approve this execution")

        if approved:
            # User approved - resume execution
            execution.status = "running"
            execution.hitl_approved_at = datetime.utcnow()
            execution.hitl_approved_by = user.id

            # If user modified the plan, update it
            if modified_plan:
                execution.plan_json = modified_plan

            # Notify via WebSocket
            await self.ws_manager.send_to_user(
                user_id=str(user.id),
                message={
                    "type": "agent.execution.approved",
                    "channel": f"execution:{execution_id}",
                    "data": {
                        "execution_id": str(execution_id),
                        "status": "running",
                        "approved_by": str(user.id),
                        "approved_at": execution.hitl_approved_at.isoformat(),
                        "plan_modified": modified_plan is not None,
                    },
                    "timestamp": datetime.utcnow().isoformat(),
                }
            )

        else:
            # User rejected - cancel execution
            execution.status = "cancelled"
            execution.error_message = "User rejected the execution plan"

            await self.ws_manager.send_to_user(
                user_id=str(user.id),
                message={
                    "type": "agent.execution.cancelled",
                    "channel": f"execution:{execution_id}",
                    "data": {
                        "execution_id": str(execution_id),
                        "status": "cancelled",
                        "reason": "User rejected plan",
                    },
                    "timestamp": datetime.utcnow().isoformat(),
                }
            )

        self.db.commit()
        self.db.refresh(execution)

        return execution

    async def complete_execution(
        self,
        execution_id: UUID,
        message_id: UUID,
        total_tokens: int,
        total_duration_ms: int,
        llm_calls_count: int = 1,
        tools_called: Optional[Dict[str, Any]] = None,
        subagents_used: Optional[list] = None,
    ) -> AgentExecution:
        """Mark execution as completed.

        Args:
            execution_id: The execution to complete
            message_id: The message created with results
            total_tokens: Total tokens used
            total_duration_ms: Total execution time in milliseconds
            llm_calls_count: Number of LLM calls made
            tools_called: Tools used during execution
            subagents_used: Subagents spawned during execution

        Returns:
            Updated AgentExecution instance
        """
        execution = self.db.query(AgentExecution).filter(
            AgentExecution.id == execution_id
        ).first()

        if not execution:
            raise ValueError(f"Execution {execution_id} not found")

        execution.status = "completed"
        execution.message_id = message_id
        execution.completed_at = datetime.utcnow()
        execution.total_tokens_used = total_tokens
        execution.total_duration_ms = total_duration_ms
        execution.llm_calls_count = llm_calls_count

        if tools_called:
            execution.tools_called = tools_called

        if subagents_used:
            execution.subagents_used = subagents_used

        self.db.commit()
        self.db.refresh(execution)

        # Get conversation for user_id
        conversation = self.db.query(Conversation).filter(
            Conversation.id == execution.conversation_id
        ).first()

        # Notify via WebSocket
        await self.ws_manager.send_to_user(
            user_id=str(conversation.user_id),
            message={
                "type": "agent.execution.completed",
                "channel": f"execution:{execution_id}",
                "data": {
                    "execution_id": str(execution_id),
                    "message_id": str(message_id),
                    "status": "completed",
                    "completed_at": execution.completed_at.isoformat(),
                    "total_duration_ms": total_duration_ms,
                    "stats": {
                        "llm_calls": llm_calls_count,
                        "total_tokens": total_tokens,
                        "duration_seconds": total_duration_ms / 1000.0,
                        "subagents_used": len(subagents_used) if subagents_used else 0,
                    },
                },
                "timestamp": datetime.utcnow().isoformat(),
            }
        )

        return execution

    async def fail_execution(
        self,
        execution_id: UUID,
        error_message: str,
        error_stack_trace: Optional[str] = None,
    ) -> AgentExecution:
        """Mark execution as failed.

        Args:
            execution_id: The execution that failed
            error_message: Error message
            error_stack_trace: Optional stack trace for debugging

        Returns:
            Updated AgentExecution instance
        """
        execution = self.db.query(AgentExecution).filter(
            AgentExecution.id == execution_id
        ).first()

        if not execution:
            raise ValueError(f"Execution {execution_id} not found")

        execution.status = "failed"
        execution.completed_at = datetime.utcnow()
        execution.error_message = error_message
        execution.error_stack_trace = error_stack_trace

        # Calculate duration
        if execution.started_at:
            duration = (execution.completed_at - execution.started_at).total_seconds() * 1000
            execution.total_duration_ms = int(duration)

        self.db.commit()
        self.db.refresh(execution)

        # Get conversation for user_id
        conversation = self.db.query(Conversation).filter(
            Conversation.id == execution.conversation_id
        ).first()

        # Notify via WebSocket
        await self.ws_manager.send_to_user(
            user_id=str(conversation.user_id),
            message={
                "type": "agent.execution.failed",
                "channel": f"execution:{execution_id}",
                "data": {
                    "execution_id": str(execution_id),
                    "status": "failed",
                    "error": {
                        "message": error_message,
                        "occurred_at": execution.completed_at.isoformat(),
                    },
                },
                "timestamp": datetime.utcnow().isoformat(),
            }
        )

        return execution

    async def send_progress_update(
        self,
        execution_id: UUID,
        current_step: str,
        step_number: int,
        total_steps: int,
        message: str,
    ) -> None:
        """Send progress update via WebSocket.

        Args:
            execution_id: The execution in progress
            current_step: Current step description
            step_number: Current step number
            total_steps: Total number of steps
            message: Progress message to display
        """
        execution = self.db.query(AgentExecution).filter(
            AgentExecution.id == execution_id
        ).first()

        if not execution:
            return

        conversation = self.db.query(Conversation).filter(
            Conversation.id == execution.conversation_id
        ).first()

        await self.ws_manager.send_to_user(
            user_id=str(conversation.user_id),
            message={
                "type": "agent.execution.progress",
                "channel": f"execution:{execution_id}",
                "data": {
                    "execution_id": str(execution_id),
                    "status": "running",
                    "current_step": {
                        "step_number": step_number,
                        "total_steps": total_steps,
                        "description": current_step,
                        "message": message,
                        "percentage": int((step_number / total_steps) * 100),
                    },
                },
                "timestamp": datetime.utcnow().isoformat(),
            }
        )

    def get_execution(self, execution_id: UUID) -> Optional[AgentExecution]:
        """Get execution by ID.

        Args:
            execution_id: The execution ID

        Returns:
            AgentExecution instance or None
        """
        return self.db.query(AgentExecution).filter(
            AgentExecution.id == execution_id
        ).first()

    def get_execution_with_details(self, execution_id: UUID) -> Optional[Dict[str, Any]]:
        """Get execution with full details.

        Args:
            execution_id: The execution ID

        Returns:
            Dict with execution details or None
        """
        execution = self.get_execution(execution_id)

        if not execution:
            return None

        return {
            "id": str(execution.id),
            "conversation_id": str(execution.conversation_id),
            "message_id": str(execution.message_id) if execution.message_id else None,
            "agent_type": execution.agent_type,
            "model_name": execution.model_name,
            "planning_enabled": execution.planning_enabled,
            "filesystem_enabled": execution.filesystem_enabled,
            "status": execution.status,
            "started_at": execution.started_at.isoformat(),
            "completed_at": execution.completed_at.isoformat() if execution.completed_at else None,
            # HITL fields
            "hitl": {
                "paused_at": execution.hitl_paused_at.isoformat() if execution.hitl_paused_at else None,
                "approved_at": execution.hitl_approved_at.isoformat() if execution.hitl_approved_at else None,
                "approved_by": str(execution.hitl_approved_by) if execution.hitl_approved_by else None,
                "is_awaiting_approval": execution.is_awaiting_approval,
                "is_approved": execution.is_approved,
            },
            "plan": execution.plan_json,
            "performance": {
                "total_duration_ms": execution.total_duration_ms,
                "duration_seconds": execution.duration_seconds,
                "llm_calls_count": execution.llm_calls_count,
                "total_tokens_used": execution.total_tokens_used,
            },
            "tools_called": execution.tools_called,
            "subagents_used": execution.subagents_used,
            "error": {
                "message": execution.error_message,
                "stack_trace": execution.error_stack_trace,
            } if execution.error_message else None,
        }
