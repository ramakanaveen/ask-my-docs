# REST API Specification

Complete REST API endpoints for Ask My Docs.

## Base URL

```
Development: http://localhost:8000/api/v1
Production: https://api.askmydocs.com/api/v1
```

## Authentication

All endpoints (except auth) require JWT token in header:
```
Authorization: Bearer <jwt_token>
```

---

## 1. Authentication Endpoints

### POST /auth/register

Register a new user.

**Request:**
```json
{
  "email": "david@company.com",
  "username": "david",
  "password": "SecurePass123!",
  "full_name": "David Chen"
}
```

**Response (201 Created):**
```json
{
  "id": "uuid",
  "email": "david@company.com",
  "username": "david",
  "full_name": "David Chen",
  "role": "system_user",
  "is_active": true,
  "is_verified": false,
  "created_at": "2024-01-15T10:30:00Z",
  "personal_system": {
    "id": "uuid",
    "name": "personal",
    "display_name": "Personal Documents"
  }
}
```

**Notes:**
- Auto-creates personal system for user
- Auto-assigns user to personal system with full permissions
- Default role: `system_user`

---

### POST /auth/login

Login and receive JWT token.

**Request:**
```json
{
  "username": "david",
  "password": "SecurePass123!"
}
```

**Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600,
  "refresh_token": "uuid",
  "user": {
    "id": "uuid",
    "email": "david@company.com",
    "username": "david",
    "full_name": "David Chen",
    "role": "system_user"
  }
}
```

---

### POST /auth/refresh

Refresh JWT token.

**Request:**
```json
{
  "refresh_token": "uuid"
}
```

**Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

---

### POST /auth/logout

Logout and invalidate tokens.

**Request:**
```json
{
  "refresh_token": "uuid"
}
```

**Response (204 No Content)**

---

## 2. User Management

### GET /users/me

Get current user profile.

**Response (200 OK):**
```json
{
  "id": "uuid",
  "email": "david@company.com",
  "username": "david",
  "full_name": "David Chen",
  "role": "system_user",
  "is_active": true,
  "is_verified": true,
  "created_at": "2024-01-15T10:30:00Z",
  "last_login_at": "2024-01-20T09:15:00Z",
  "preferences": {
    "theme": "light",
    "notifications_enabled": true,
    "default_systems": ["system-a-uuid"]
  },
  "accessible_systems": [
    {
      "id": "uuid",
      "name": "system-a",
      "display_name": "System A",
      "can_upload": false,
      "can_edit": false,
      "can_query": true
    },
    {
      "id": "uuid",
      "name": "personal",
      "display_name": "Personal Documents",
      "is_personal": true,
      "can_upload": true,
      "can_edit": true,
      "can_query": true
    }
  ]
}
```

---

### PATCH /users/me

Update current user profile.

**Request:**
```json
{
  "full_name": "David T. Chen",
  "preferences": {
    "theme": "dark",
    "default_systems": ["system-a-uuid", "personal-uuid"]
  }
}
```

**Response (200 OK):**
```json
{
  "id": "uuid",
  "email": "david@company.com",
  "username": "david",
  "full_name": "David T. Chen",
  "preferences": {
    "theme": "dark",
    "notifications_enabled": true,
    "default_systems": ["system-a-uuid", "personal-uuid"]
  }
}
```

---

### GET /users (Admin only)

List all users.

**Query Parameters:**
- `role` (optional): Filter by role
- `is_active` (optional): Filter by active status
- `page` (default: 1)
- `limit` (default: 50, max: 100)

**Response (200 OK):**
```json
{
  "users": [
    {
      "id": "uuid",
      "username": "david",
      "email": "david@company.com",
      "full_name": "David Chen",
      "role": "system_user",
      "is_active": true,
      "created_at": "2024-01-15T10:30:00Z",
      "last_login_at": "2024-01-20T09:15:00Z",
      "system_count": 2
    }
  ],
  "total": 50,
  "page": 1,
  "pages": 1
}
```

---

## 3. Systems Management

### GET /systems

Get all systems accessible to current user.

**Query Parameters:**
- `include_personal` (default: true): Include personal system
- `can_upload` (optional): Filter by upload permission

**Response (200 OK):**
```json
{
  "systems": [
    {
      "id": "uuid",
      "name": "system-a",
      "display_name": "System A",
      "description": "Production database system documentation",
      "icon": "server",
      "color": "#3B82F6",
      "is_personal": false,
      "is_active": true,
      "document_count": 145,
      "permissions": {
        "can_upload": false,
        "can_edit": false,
        "can_query": true
      }
    },
    {
      "id": "uuid",
      "name": "personal",
      "display_name": "Personal Documents",
      "is_personal": true,
      "owner_user_id": "current-user-uuid",
      "document_count": 12,
      "permissions": {
        "can_upload": true,
        "can_edit": true,
        "can_query": true
      }
    }
  ]
}
```

---

### POST /systems (Admin/Doc Manager)

Create a new system.

**Request:**
```json
{
  "name": "system-c",
  "display_name": "System C",
  "description": "New system documentation",
  "icon": "cloud",
  "color": "#10B981"
}
```

**Response (201 Created):**
```json
{
  "id": "uuid",
  "name": "system-c",
  "display_name": "System C",
  "description": "New system documentation",
  "icon": "cloud",
  "color": "#10B981",
  "is_personal": false,
  "is_active": true,
  "created_at": "2024-01-20T10:00:00Z",
  "created_by": "admin-uuid"
}
```

---

### GET /systems/{system_id}

Get system details.

**Response (200 OK):**
```json
{
  "id": "uuid",
  "name": "system-a",
  "display_name": "System A",
  "description": "Production database system documentation",
  "icon": "server",
  "color": "#3B82F6",
  "is_personal": false,
  "is_active": true,
  "document_count": 145,
  "tag_count": 12,
  "user_count": 25,
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-20T10:00:00Z",
  "tags": [
    {
      "id": "uuid",
      "name": "Installation",
      "color": "#3B82F6",
      "document_count": 15
    }
  ],
  "recent_documents": [
    {
      "id": "uuid",
      "title": "System A v2.5 Installation Guide",
      "uploaded_at": "2024-01-19T14:30:00Z",
      "uploaded_by": "maria"
    }
  ]
}
```

---

### POST /systems/{system_id}/users (Admin only)

Assign users to a system.

**Request:**
```json
{
  "user_id": "david-uuid",
  "can_upload": false,
  "can_edit": false,
  "can_query": true
}
```

**Response (201 Created):**
```json
{
  "user_id": "david-uuid",
  "system_id": "system-a-uuid",
  "can_upload": false,
  "can_edit": false,
  "can_query": true,
  "assigned_at": "2024-01-20T10:00:00Z",
  "assigned_by": "admin-uuid"
}
```

---

## 4. Documents

### POST /documents/upload

Upload documents (multi-part form data).

**Request (multipart/form-data):**
```
files: [File, File, ...]
system_id: uuid
tags: ["Installation", "API"]  (optional)
auto_tag: true  (optional, default: false)
```

**Response (202 Accepted):**
```json
{
  "documents": [
    {
      "id": "uuid",
      "filename": "system_a_install.pdf",
      "system_id": "system-a-uuid",
      "status": "pending",
      "uploaded_at": "2024-01-20T10:00:00Z",
      "processing_job_id": "celery-task-id"
    }
  ],
  "message": "Documents queued for processing. You'll receive a notification when ready."
}
```

**Notes:**
- Immediately returns with `pending` status
- Background Celery task processes documents
- WebSocket notification sent when processing completes
- If `auto_tag: true`, AI suggests tags based on content

---

### GET /documents

List documents.

**Query Parameters:**
- `system_id` (optional): Filter by system
- `tags` (optional): Filter by tags (comma-separated)
- `status` (optional): Filter by status
- `search` (optional): Search in title/filename
- `page` (default: 1)
- `limit` (default: 50, max: 100)
- `sort_by` (default: uploaded_at)
- `sort_order` (default: desc)

**Response (200 OK):**
```json
{
  "documents": [
    {
      "id": "uuid",
      "system_id": "system-a-uuid",
      "system_name": "System A",
      "filename": "system_a_install.pdf",
      "title": "System A Installation Guide",
      "file_type": "pdf",
      "file_size_bytes": 2457600,
      "page_count": 45,
      "status": "ready",
      "version": 1,
      "tags": [
        {"id": "uuid", "name": "Installation", "color": "#3B82F6"}
      ],
      "uploaded_by": {
        "id": "uuid",
        "username": "maria",
        "full_name": "Maria Johnson"
      },
      "uploaded_at": "2024-01-20T10:00:00Z",
      "processing_completed_at": "2024-01-20T10:02:30Z"
    }
  ],
  "total": 145,
  "page": 1,
  "pages": 3
}
```

---

### GET /documents/{document_id}

Get document details.

**Response (200 OK):**
```json
{
  "id": "uuid",
  "system_id": "system-a-uuid",
  "system_name": "System A",
  "filename": "system_a_install.pdf",
  "original_filename": "System A Installation Guide v2.5.pdf",
  "file_path": "s3://bucket/documents/...",
  "file_type": "pdf",
  "file_size_bytes": 2457600,
  "mime_type": "application/pdf",
  "title": "System A Installation Guide",
  "description": "Comprehensive installation guide for System A v2.5",
  "page_count": 45,
  "word_count": 12500,
  "version": 1,
  "status": "ready",
  "tags": [
    {"id": "uuid", "name": "Installation", "color": "#3B82F6"},
    {"id": "uuid", "name": "v2.5", "color": "#10B981"}
  ],
  "uploaded_by": {
    "id": "uuid",
    "username": "maria",
    "full_name": "Maria Johnson"
  },
  "uploaded_at": "2024-01-20T10:00:00Z",
  "processing_completed_at": "2024-01-20T10:02:30Z",
  "extracted_metadata": {
    "author": "Maria Johnson",
    "created_date": "2024-01-15",
    "modified_date": "2024-01-19"
  },
  "chunk_count": 89,
  "download_url": "https://api.askmydocs.com/api/v1/documents/uuid/download",
  "version_history": []
}
```

---

### GET /documents/{document_id}/download

Download original document file.

**Response (200 OK):**
- Content-Type: Based on file type
- Content-Disposition: attachment; filename="original_filename.pdf"
- Binary file data

---

### PATCH /documents/{document_id}

Update document metadata (requires can_edit permission).

**Request:**
```json
{
  "title": "System A Installation Guide v2.5",
  "description": "Updated installation guide",
  "tags": ["Installation", "v2.5", "Linux"]
}
```

**Response (200 OK):**
```json
{
  "id": "uuid",
  "title": "System A Installation Guide v2.5",
  "description": "Updated installation guide",
  "tags": [
    {"id": "uuid", "name": "Installation"},
    {"id": "uuid", "name": "v2.5"},
    {"id": "uuid", "name": "Linux"}
  ],
  "last_edited_by": "maria-uuid",
  "last_edited_at": "2024-01-20T11:00:00Z"
}
```

---

### DELETE /documents/{document_id}

Soft delete a document (requires can_edit permission).

**Response (204 No Content)**

**Notes:**
- Sets `is_deleted = true` and `deleted_at = now()`
- Document chunks remain in vector DB but are excluded from searches
- Can be restored by admin

---

## 5. Tags

### GET /tags

Get all tags for accessible systems.

**Query Parameters:**
- `system_id` (optional): Filter by system

**Response (200 OK):**
```json
{
  "tags": [
    {
      "id": "uuid",
      "system_id": "system-a-uuid",
      "name": "Installation",
      "color": "#3B82F6",
      "document_count": 15,
      "created_at": "2024-01-10T00:00:00Z"
    }
  ]
}
```

---

### POST /tags

Create a new tag (requires can_upload permission on system).

**Request:**
```json
{
  "system_id": "system-a-uuid",
  "name": "Troubleshooting",
  "color": "#EF4444"
}
```

**Response (201 Created):**
```json
{
  "id": "uuid",
  "system_id": "system-a-uuid",
  "name": "Troubleshooting",
  "color": "#EF4444",
  "document_count": 0,
  "created_at": "2024-01-20T11:00:00Z",
  "created_by": "maria-uuid"
}
```

---

## 6. Conversations

### POST /conversations

Create a new conversation.

**Request:**
```json
{
  "system_filters": ["system-a-uuid", "personal-uuid"],
  "title": "System A Installation Questions"  // optional
}
```

**Response (201 Created):**
```json
{
  "id": "uuid",
  "user_id": "david-uuid",
  "title": "System A Installation Questions",
  "system_filters": ["system-a-uuid", "personal-uuid"],
  "message_count": 0,
  "created_at": "2024-01-20T11:00:00Z",
  "updated_at": "2024-01-20T11:00:00Z"
}
```

---

### GET /conversations

List user's conversations.

**Query Parameters:**
- `is_archived` (default: false)
- `page` (default: 1)
- `limit` (default: 20, max: 50)

**Response (200 OK):**
```json
{
  "conversations": [
    {
      "id": "uuid",
      "title": "System A Installation Questions",
      "system_filters": ["system-a-uuid"],
      "systems": [
        {"id": "uuid", "display_name": "System A"}
      ],
      "message_count": 15,
      "total_tokens_used": 45000,
      "created_at": "2024-01-20T11:00:00Z",
      "updated_at": "2024-01-20T14:30:00Z",
      "last_message_preview": "To install System A on Ubuntu, first ensure..."
    }
  ],
  "total": 5,
  "page": 1,
  "pages": 1
}
```

---

### GET /conversations/{conversation_id}

Get conversation with all messages.

**Response (200 OK):**
```json
{
  "id": "uuid",
  "title": "System A Installation Questions",
  "system_filters": ["system-a-uuid"],
  "systems": [
    {"id": "uuid", "display_name": "System A", "icon": "server"}
  ],
  "message_count": 15,
  "total_tokens_used": 45000,
  "created_at": "2024-01-20T11:00:00Z",
  "updated_at": "2024-01-20T14:30:00Z",
  "messages": [
    {
      "id": "uuid",
      "role": "user",
      "content": "How do I install System A on Ubuntu?",
      "created_at": "2024-01-20T11:00:00Z"
    },
    {
      "id": "uuid",
      "role": "assistant",
      "content": "To install System A on Ubuntu...",
      "rich_content": {
        "sections": [...],
        "citations": [...]
      },
      "source_documents": [...],
      "agent_execution_id": "uuid",
      "current_version": 1,
      "created_at": "2024-01-20T11:00:15Z",
      "has_edits": false
    }
  ]
}
```

---

### DELETE /conversations/{conversation_id}

Archive a conversation.

**Response (204 No Content)**

---

## 7. Messages

### POST /conversations/{conversation_id}/messages

Send a message (ask a question).

**Request:**
```json
{
  "content": "How do I install System A on Ubuntu?",
  "agent_config": {
    "complexity": "auto",  // or "simple", "moderate", "complex"
    "model": "auto"  // or specific model name
  }
}
```

**Response (202 Accepted):**
```json
{
  "message": {
    "id": "uuid",
    "conversation_id": "conversation-uuid",
    "role": "user",
    "content": "How do I install System A on Ubuntu?",
    "created_at": "2024-01-20T11:00:00Z"
  },
  "agent_execution": {
    "id": "uuid",
    "status": "running",
    "agent_type": "simple",
    "model_name": "claude-haiku",
    "started_at": "2024-01-20T11:00:00Z"
  },
  "websocket_channel": "execution:uuid"
}
```

**Notes:**
- Returns immediately with 202 Accepted
- Agent execution happens asynchronously
- Client subscribes to WebSocket for real-time updates
- When complete, assistant message is added to conversation

---

### GET /messages/{message_id}

Get specific message with full details.

**Response (200 OK):**
```json
{
  "id": "uuid",
  "conversation_id": "uuid",
  "role": "assistant",
  "content": "To install System A on Ubuntu...",
  "rich_content": {
    "sections": [
      {
        "type": "text",
        "content": "## Installation Steps\n\n1. Update package lists..."
      },
      {
        "type": "code",
        "language": "bash",
        "content": "sudo apt-get update\nsudo apt-get install system-a"
      }
    ],
    "citations": [
      {
        "document_id": "uuid",
        "document_name": "System A Installation Guide",
        "page": 12,
        "excerpt": "First, update your package lists...",
        "relevance_score": 0.94
      }
    ]
  },
  "source_documents": [
    {
      "document_id": "uuid",
      "document_name": "System A Installation Guide",
      "chunk_ids": ["uuid1", "uuid2"],
      "relevance_score": 0.94
    }
  ],
  "agent_execution_id": "uuid",
  "prompt_tokens": 1200,
  "completion_tokens": 800,
  "total_tokens": 2000,
  "current_version": 1,
  "created_at": "2024-01-20T11:00:15Z"
}
```

---

### PATCH /messages/{message_id}

Edit an assistant message (creates new version).

**Request:**
```json
{
  "edited_content": "To install System A on Ubuntu 22.04...",
  "edited_rich_content": {
    "sections": [...]
  },
  "edit_reason": "Updated for Ubuntu 22.04 specifically"
}
```

**Response (200 OK):**
```json
{
  "id": "uuid",
  "content": "To install System A on Ubuntu 22.04...",
  "rich_content": {...},
  "current_version": 2,
  "edited_by": "david-uuid",
  "edited_at": "2024-01-20T12:00:00Z",
  "edit": {
    "id": "edit-uuid",
    "version_number": 2,
    "edit_reason": "Updated for Ubuntu 22.04 specifically"
  }
}
```

---

### GET /messages/{message_id}/versions

Get all versions of a message.

**Response (200 OK):**
```json
{
  "message_id": "uuid",
  "current_version": 2,
  "versions": [
    {
      "version_number": 1,
      "content": "To install System A on Ubuntu...",
      "rich_content": {...},
      "created_at": "2024-01-20T11:00:15Z"
    },
    {
      "version_number": 2,
      "content": "To install System A on Ubuntu 22.04...",
      "rich_content": {...},
      "edited_by": {
        "id": "uuid",
        "username": "david",
        "full_name": "David Chen"
      },
      "edited_at": "2024-01-20T12:00:00Z",
      "edit_reason": "Updated for Ubuntu 22.04 specifically"
    }
  ]
}
```

---

## 8. Agent Executions

### GET /agent-executions/{execution_id}

Get agent execution details.

**Response (200 OK):**
```json
{
  "id": "uuid",
  "conversation_id": "uuid",
  "message_id": "uuid",
  "agent_type": "complex",
  "model_name": "claude-sonnet-4",
  "planning_enabled": true,
  "filesystem_enabled": true,
  "status": "completed",
  "started_at": "2024-01-20T11:00:00Z",
  "completed_at": "2024-01-20T11:02:45Z",
  "total_duration_ms": 165000,
  "plan_json": {
    "todos": [
      {"content": "Extract Q1 2023 financial data", "status": "completed"},
      {"content": "Extract Q2 2023 financial data", "status": "completed"},
      {"content": "Calculate YoY growth rates", "status": "completed"},
      {"content": "Generate trend visualizations", "status": "completed"}
    ]
  },
  "hitl_approved_at": "2024-01-20T11:00:30Z",
  "hitl_approved_by": "david-uuid",
  "subagents_used": ["pdf-extraction-agent", "trend-analysis-agent", "chart-generation-agent"],
  "llm_calls_count": 12,
  "total_tokens_used": 45000,
  "tools_called": [
    {"tool_name": "semantic_search", "call_count": 5, "avg_duration_ms": 230},
    {"tool_name": "extract_pdf_tables", "call_count": 4, "avg_duration_ms": 1200},
    {"tool_name": "write_file", "call_count": 4, "avg_duration_ms": 50}
  ],
  "execution_trace": {
    "steps": [...]
  }
}
```

---

### POST /agent-executions/{execution_id}/approve

Approve agent plan (Human-in-the-Loop).

**Request:**
```json
{
  "approved": true,
  "modified_plan": null  // Optional: Modified todo list
}
```

**Response (200 OK):**
```json
{
  "id": "uuid",
  "status": "running",
  "hitl_approved_at": "2024-01-20T11:00:30Z",
  "hitl_approved_by": "david-uuid",
  "message": "Agent execution resumed"
}
```

---

### POST /agent-executions/{execution_id}/cancel

Cancel a running agent execution.

**Response (200 OK):**
```json
{
  "id": "uuid",
  "status": "cancelled",
  "message": "Agent execution cancelled"
}
```

---

## 9. Exports

### POST /messages/{message_id}/export

Export a message as PDF or Markdown.

**Request:**
```json
{
  "format": "pdf",  // or "markdown", "html", "docx"
  "include_charts": true,
  "include_citations": true,
  "styling_template": "professional"  // or "minimal", "corporate"
}
```

**Response (202 Accepted):**
```json
{
  "export": {
    "id": "uuid",
    "message_id": "message-uuid",
    "export_format": "pdf",
    "status": "pending",
    "created_at": "2024-01-20T12:00:00Z"
  },
  "websocket_channel": "export:uuid",
  "message": "Export generation started. You'll receive a notification when ready."
}
```

---

### GET /exports/{export_id}

Get export status and download link.

**Response (200 OK):**
```json
{
  "id": "uuid",
  "message_id": "uuid",
  "export_format": "pdf",
  "file_path": "s3://bucket/exports/...",
  "file_size_bytes": 1245000,
  "status": "completed",
  "generated_at": "2024-01-20T12:00:45Z",
  "download_url": "https://api.askmydocs.com/api/v1/exports/uuid/download",
  "download_count": 0,
  "expires_at": "2024-02-19T12:00:45Z"
}
```

---

### GET /exports/{export_id}/download

Download exported file.

**Response (200 OK):**
- Content-Type: application/pdf (or appropriate type)
- Content-Disposition: attachment; filename="financial_analysis_2024-01-20.pdf"
- Binary file data

---

## 10. Feedback

### POST /messages/{message_id}/feedback

Submit feedback on a message.

**Request:**
```json
{
  "feedback_type": "rating",  // or "correction", "feature_request"
  "rating": "thumbs_up",  // or "thumbs_down", "neutral"
  "feedback_text": "Very helpful answer!",
  "feedback_data": null  // For structured feedback (corrections)
}
```

**Response (201 Created):**
```json
{
  "id": "uuid",
  "message_id": "message-uuid",
  "feedback_type": "rating",
  "rating": "thumbs_up",
  "feedback_text": "Very helpful answer!",
  "created_at": "2024-01-20T12:00:00Z"
}
```

---

## 11. Analytics (Admin only)

### GET /analytics/overview

Get system-wide analytics.

**Query Parameters:**
- `start_date` (default: 30 days ago)
- `end_date` (default: today)
- `system_id` (optional): Filter by system

**Response (200 OK):**
```json
{
  "period": {
    "start_date": "2024-01-01",
    "end_date": "2024-01-31"
  },
  "metrics": {
    "total_conversations": 450,
    "total_messages": 2340,
    "total_users": 125,
    "active_users": 89,
    "total_documents": 567,
    "avg_response_time_ms": 1234,
    "avg_tokens_per_query": 2500,
    "total_cost_usd": 125.45,
    "positive_feedback_rate": 0.87
  },
  "top_systems": [
    {
      "system_id": "uuid",
      "system_name": "System A",
      "query_count": 890,
      "unique_users": 67
    }
  ],
  "top_documents": [
    {
      "document_id": "uuid",
      "document_title": "System A Installation Guide",
      "query_count": 234,
      "avg_relevance": 0.92
    }
  ]
}
```

---

### GET /analytics/users/{user_id}

Get user-specific analytics.

**Query Parameters:**
- `start_date` (default: 30 days ago)
- `end_date` (default: today)

**Response (200 OK):**
```json
{
  "user": {
    "id": "uuid",
    "username": "david",
    "full_name": "David Chen"
  },
  "period": {
    "start_date": "2024-01-01",
    "end_date": "2024-01-31"
  },
  "metrics": {
    "total_conversations": 15,
    "total_messages": 78,
    "total_tokens_used": 125000,
    "avg_response_time_ms": 1150,
    "systems_queried": ["System A", "Personal"],
    "most_active_time": "14:00-16:00 UTC",
    "feedback_given": 42,
    "positive_feedback_rate": 0.93
  },
  "top_topics": [
    {"topic": "Installation", "query_count": 28},
    {"topic": "Troubleshooting", "query_count": 15}
  ]
}
```

---

## Error Responses

All endpoints follow consistent error format:

### 400 Bad Request
```json
{
  "error": "validation_error",
  "message": "Invalid request parameters",
  "details": {
    "field": "email",
    "error": "Invalid email format"
  }
}
```

### 401 Unauthorized
```json
{
  "error": "unauthorized",
  "message": "Authentication required"
}
```

### 403 Forbidden
```json
{
  "error": "forbidden",
  "message": "You don't have permission to access this system",
  "details": {
    "required_permission": "can_upload",
    "system_id": "uuid"
  }
}
```

### 404 Not Found
```json
{
  "error": "not_found",
  "message": "Document not found",
  "resource_type": "document",
  "resource_id": "uuid"
}
```

### 409 Conflict
```json
{
  "error": "conflict",
  "message": "A system with this name already exists"
}
```

### 429 Too Many Requests
```json
{
  "error": "rate_limit_exceeded",
  "message": "Too many requests",
  "retry_after": 60
}
```

### 500 Internal Server Error
```json
{
  "error": "internal_error",
  "message": "An unexpected error occurred",
  "request_id": "uuid"
}
```

---

## Rate Limiting

- **Authentication**: 5 requests/minute per IP
- **Document Upload**: 20 uploads/hour per user
- **Messages**: 100 messages/hour per user
- **General API**: 1000 requests/hour per user

Headers included in responses:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 87
X-RateLimit-Reset: 1674123456
```

---

**Last Updated**: 2025-11-15
**API Version**: v1
**Status**: Complete specification
