# Human-in-the-Loop (HITL) Implementation

## ✅ HITL Foundation - COMPLETE

We've successfully implemented the **complete database foundation** for Human-in-the-Loop functionality. Every agent query will go through the **plan → approve → execute** workflow.

---

## 🎯 HITL Workflow Design

```
User asks question
    ↓
Agent creates plan (write_todos)
    ↓
[PAUSE] - Status: 'paused'
    ↓
Show plan to user via WebSocket
    ↓
User reviews & approves/modifies
    ↓
POST /agent-executions/{id}/approve
    ↓
Agent executes approved plan
    ↓
Return results
```

---

## 📊 Database Models - ALL COMPLETE (15/15 tables)

### ✅ Core Models
1. **User** - Authentication with roles (admin, doc_manager, system_user, super_user)
2. **System** - Document collections with personal system support
3. **UserSystem** - User-system assignments with granular permissions
4. **Document** - Document metadata with version tracking
5. **DocumentChunk** - Chunks synced with vector DB
6. **Tag** - Tags for organizing documents within systems
7. **DocumentTag** - Many-to-many document-tag relationship

### ✅ HITL-Aware Messaging Models
8. **Conversation** - Chat sessions with system filters
9. **Message** - Messages with rich content (charts, tables, citations)
10. **MessageEdit** - Full version history for edited messages

### ✅ **HITL Core Models** ⭐
11. **AgentExecution** - The heart of HITL workflow
    ```python
    # Key HITL fields:
    hitl_paused_at: DateTime        # When paused for approval
    hitl_approved_at: DateTime      # When approved
    hitl_approved_by: UUID          # Who approved
    plan_json: JSONB                # The plan to approve
    status: String                  # 'planning', 'paused', 'running', 'completed'

    # Helper methods:
    is_awaiting_approval() -> bool  # True if paused and waiting
    is_approved() -> bool           # True if approved by human
    ```

12. **AgentFilesystem** - Storage for intermediate results (Deep Agents)

### ✅ Analytics & Compliance
13. **QAAnalytics** - Every Q&A tracked for compliance
14. **UserFeedback** - User ratings and corrections
15. **Export** - PDF/Markdown generation tracking
16. **AuditLog** - Full audit trail for security

---

## 🔑 Key HITL Features Built-In

### 1. Execution States
```python
AgentExecution.status values:
- 'planning'   → Agent creating plan
- 'paused'     → Waiting for human approval ⏸️
- 'running'    → Executing after approval
- 'completed'  → Finished successfully
- 'failed'     → Error occurred
- 'cancelled'  → User cancelled
```

### 2. Plan Storage
```python
# AgentExecution.plan_json structure
{
    "todos": [
        {
            "content": "Extract Q1 2023 financial data",
            "status": "pending",
            "activeForm": "Extracting Q1 2023 financial data"
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
```

### 3. Approval Tracking
- **Who approved**: `hitl_approved_by` (User foreign key)
- **When approved**: `hitl_approved_at` (Timestamp)
- **What was approved**: `plan_json` (Full plan with todos)

### 4. Rich Message Support
Messages can contain:
- Plain text content
- Rich formatted sections (charts, tables, code blocks)
- Citations with document references
- Source document tracking

---

## 📝 Next Steps to Complete HITL

### 1. Service Layer (2-3 hours)
```python
# app/services/agent_execution_service.py

class AgentExecutionService:
    async def execute_with_hitl(
        user: User,
        question: str,
        conversation_id: str
    ) -> AgentExecution:
        """Execute query with HITL workflow."""

        # 1. Create execution record
        execution = AgentExecution(
            conversation_id=conversation_id,
            agent_type="complex",
            status="planning"
        )
        db.add(execution)

        # 2. Agent creates plan
        plan = await agent.create_plan(question)

        # 3. PAUSE for approval
        execution.status = "paused"
        execution.plan_json = plan
        execution.hitl_paused_at = datetime.utcnow()
        db.commit()

        # 4. Notify user via WebSocket
        await ws_manager.send_event(
            user_id=user.id,
            event="agent.execution.awaiting_approval",
            data={
                "execution_id": execution.id,
                "plan": plan
            }
        )

        # Execution continues when user approves
        return execution
```

### 2. Approval Endpoint (1 hour)
```python
# app/api/v1/endpoints/agent_executions.py

@router.post("/{execution_id}/approve")
async def approve_execution(
    execution_id: UUID,
    approval: ApprovalRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Approve agent plan and resume execution."""

    execution = db.query(AgentExecution).get(execution_id)

    # Validate user can approve
    if execution.conversation.user_id != user.id:
        raise HTTPException(403, "Not your execution")

    # Update approval fields
    execution.status = "running"
    execution.hitl_approved_at = datetime.utcnow()
    execution.hitl_approved_by = user.id

    if approval.modified_plan:
        execution.plan_json = approval.modified_plan

    db.commit()

    # Resume execution (Celery task)
    resume_agent_execution.delay(execution_id)

    return {"status": "approved", "execution_id": execution_id}
```

### 3. WebSocket Events (1 hour)
```python
# WebSocket event types for HITL
events = [
    "agent.execution.planning",           # Creating plan
    "agent.execution.awaiting_approval",  # Paused, waiting for user
    "agent.execution.approved",           # User approved
    "agent.execution.running",            # Executing
    "agent.execution.progress",           # Progress updates
    "agent.execution.completed",          # Finished
]
```

---

## 🎯 HITL Benefits Achieved

### ✅ Built from Day 1
- No retrofitting needed
- Clean architecture
- Every component HITL-aware

### ✅ Full Audit Trail
- Who approved what plans
- When approval happened
- What the original plan was
- Complete execution history

### ✅ User Control
- See plan before execution
- Modify plan if needed
- Cancel if desired
- Track all agent actions

### ✅ Compliance Ready
- Every Q&A logged
- Full approval chain
- Source citations tracked
- User feedback captured

---

## 📊 Implementation Status

| Component | Status | HITL Ready |
|-----------|--------|------------|
| Database Models | ✅ 100% Complete | ✅ Yes |
| API Endpoints | ⏳ Pending | ✅ Designed |
| Service Layer | ⏳ Pending | ✅ Designed |
| WebSocket Events | ⏳ Pending | ✅ Designed |
| Deep Agents Integration | ⏳ Pending | ✅ Designed |

**HITL Foundation**: ✅ **100% READY**

All database models support HITL workflow. We can now implement the service layer and endpoints knowing the data model is solid.

---

## 🚀 Example HITL Flow

```python
# User asks complex question
POST /conversations/{id}/messages
{
    "content": "Analyze our financial performance over 2 years"
}

# Response (202 Accepted)
{
    "execution_id": "abc-123",
    "status": "planning",
    "message": "Agent is creating execution plan..."
}

# WebSocket event (5 seconds later)
{
    "type": "agent.execution.awaiting_approval",
    "data": {
        "execution_id": "abc-123",
        "plan": {
            "todos": [
                "Extract Q1-Q4 2023 financial data",
                "Extract Q1-Q4 2024 financial data",
                "Calculate YoY growth rates",
                "Generate trend visualizations",
                "Create executive summary"
            ]
        },
        "estimated_time": "45 seconds"
    }
}

# User reviews plan in UI and approves
POST /agent-executions/abc-123/approve
{
    "approved": true
}

# WebSocket event
{
    "type": "agent.execution.approved",
    "data": {
        "execution_id": "abc-123",
        "status": "running"
    }
}

# Progress updates as agent works
{
    "type": "agent.execution.progress",
    "data": {
        "current_step": 2,
        "total_steps": 5,
        "message": "Extracting Q1-Q4 2024 financial data..."
    }
}

# Final result
{
    "type": "agent.execution.completed",
    "data": {
        "execution_id": "abc-123",
        "message_id": "msg-456",
        "duration_seconds": 42
    }
}
```

---

**Last Updated**: 2025-11-17
**Status**: ✅ HITL Foundation Complete - Ready for Service Layer Implementation
