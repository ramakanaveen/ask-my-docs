# Database Schema Design

Complete database schema for Ask My Docs with Deep Agents support.

## Overview

This schema supports:
- System-centric permissions with multi-system access
- Personal document collections per user
- Deep Agents execution tracking and filesystem storage
- Complete Q&A audit trail for compliance
- Message editing and version tracking
- Export history with professional formatting
- User feedback and analytics

## Technology Stack

- **Primary Database**: PostgreSQL 15+
- **Vector Database**: ChromaDB (or Pinecone/Weaviate)
- **Cache Layer**: Redis
- **File Storage**: S3 (or local filesystem for development)

---

## Core Tables

### 1. Users Table

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),

    -- Role: 'admin', 'doc_manager', 'system_user', 'super_user'
    role VARCHAR(50) NOT NULL DEFAULT 'system_user',

    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_login_at TIMESTAMP WITH TIME ZONE,

    -- Preferences
    preferences JSONB DEFAULT '{
        "theme": "light",
        "notifications_enabled": true,
        "default_systems": []
    }'::jsonb
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_is_active ON users(is_active);
```

**Sample Data:**
```sql
INSERT INTO users (email, username, full_name, role) VALUES
('admin@company.com', 'admin', 'System Admin', 'admin'),
('maria@company.com', 'maria', 'Maria Johnson', 'doc_manager'),
('david@company.com', 'david', 'David Chen', 'system_user'),
('sarah@company.com', 'sarah', 'Sarah Williams', 'super_user');
```

---

### 2. Systems Table

```sql
CREATE TABLE systems (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    display_name VARCHAR(255) NOT NULL,
    description TEXT,

    -- Personal system flag
    is_personal BOOLEAN DEFAULT FALSE,
    owner_user_id UUID REFERENCES users(id) ON DELETE CASCADE,

    -- System metadata
    icon VARCHAR(100), -- e.g., 'server', 'database', 'cloud'
    color VARCHAR(7), -- hex color for UI

    is_active BOOLEAN DEFAULT TRUE,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by UUID REFERENCES users(id),

    -- Ensure system names are unique
    -- Personal systems can have same name (e.g., "Personal") but different owners
    CONSTRAINT unique_system_name UNIQUE (name, is_personal, owner_user_id)
);

CREATE INDEX idx_systems_name ON systems(name);
CREATE INDEX idx_systems_is_personal ON systems(is_personal);
CREATE INDEX idx_systems_owner_user_id ON systems(owner_user_id);
CREATE INDEX idx_systems_is_active ON systems(is_active);
```

**Sample Data:**
```sql
INSERT INTO systems (name, display_name, description, is_personal) VALUES
('system-a', 'System A', 'Production database system documentation', FALSE),
('system-b', 'System B', 'Cloud infrastructure documentation', FALSE),
('shared-docs', 'Shared Documentation', 'Company-wide documentation', FALSE);

-- Personal systems (auto-created on user signup)
INSERT INTO systems (name, display_name, is_personal, owner_user_id)
SELECT 'personal', 'Personal Documents', TRUE, id FROM users WHERE username = 'david';
```

---

### 3. User-System Assignments

```sql
CREATE TABLE user_systems (
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    system_id UUID NOT NULL REFERENCES systems(id) ON DELETE CASCADE,

    -- Permissions
    can_upload BOOLEAN DEFAULT FALSE,
    can_edit BOOLEAN DEFAULT FALSE,
    can_query BOOLEAN DEFAULT TRUE,

    -- Assignment metadata
    assigned_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    assigned_by UUID REFERENCES users(id),

    PRIMARY KEY (user_id, system_id)
);

CREATE INDEX idx_user_systems_user_id ON user_systems(user_id);
CREATE INDEX idx_user_systems_system_id ON user_systems(system_id);
CREATE INDEX idx_user_systems_can_query ON user_systems(can_query) WHERE can_query = TRUE;
```

**Sample Data:**
```sql
-- Maria (doc_manager) can upload/edit/query System A
INSERT INTO user_systems (user_id, system_id, can_upload, can_edit, can_query)
SELECT u.id, s.id, TRUE, TRUE, TRUE
FROM users u, systems s
WHERE u.username = 'maria' AND s.name = 'system-a';

-- David (system_user) can only query System A
INSERT INTO user_systems (user_id, system_id, can_query)
SELECT u.id, s.id, TRUE
FROM users u, systems s
WHERE u.username = 'david' AND s.name = 'system-a';

-- Sarah (super_user) gets read access to all non-personal systems via application logic
```

---

### 4. Documents Table

```sql
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    system_id UUID NOT NULL REFERENCES systems(id) ON DELETE CASCADE,

    -- File information
    filename VARCHAR(500) NOT NULL,
    original_filename VARCHAR(500) NOT NULL,
    file_path VARCHAR(1000) NOT NULL, -- S3 key or local path
    file_size_bytes BIGINT NOT NULL,
    file_type VARCHAR(50) NOT NULL, -- 'pdf', 'docx', 'pptx', 'xlsx', 'md', 'txt', 'jpg', 'png'
    mime_type VARCHAR(100),

    -- Document metadata
    title VARCHAR(500),
    description TEXT,

    -- Version tracking
    version INT DEFAULT 1,
    parent_document_id UUID REFERENCES documents(id), -- NULL for first version

    -- Processing status
    status VARCHAR(50) DEFAULT 'pending', -- 'pending', 'processing', 'ready', 'failed'
    processing_started_at TIMESTAMP WITH TIME ZONE,
    processing_completed_at TIMESTAMP WITH TIME ZONE,
    processing_error TEXT,

    -- Extracted metadata
    page_count INT,
    word_count INT,
    extracted_metadata JSONB, -- Author, created_date, modified_date, etc.

    -- Upload tracking
    uploaded_by UUID NOT NULL REFERENCES users(id),
    uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    -- Edit tracking
    last_edited_by UUID REFERENCES users(id),
    last_edited_at TIMESTAMP WITH TIME ZONE,

    -- Soft delete
    is_deleted BOOLEAN DEFAULT FALSE,
    deleted_at TIMESTAMP WITH TIME ZONE,
    deleted_by UUID REFERENCES users(id)
);

CREATE INDEX idx_documents_system_id ON documents(system_id);
CREATE INDEX idx_documents_uploaded_by ON documents(uploaded_by);
CREATE INDEX idx_documents_status ON documents(status);
CREATE INDEX idx_documents_file_type ON documents(file_type);
CREATE INDEX idx_documents_is_deleted ON documents(is_deleted) WHERE is_deleted = FALSE;
CREATE INDEX idx_documents_uploaded_at ON documents(uploaded_at DESC);
```

---

### 5. Document Tags

```sql
CREATE TABLE tags (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    system_id UUID REFERENCES systems(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    color VARCHAR(7), -- Hex color for UI

    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by UUID REFERENCES users(id),

    CONSTRAINT unique_tag_per_system UNIQUE (system_id, name)
);

CREATE TABLE document_tags (
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    tag_id UUID NOT NULL REFERENCES tags(id) ON DELETE CASCADE,

    added_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    added_by UUID REFERENCES users(id),

    PRIMARY KEY (document_id, tag_id)
);

CREATE INDEX idx_tags_system_id ON tags(system_id);
CREATE INDEX idx_document_tags_document_id ON document_tags(document_id);
CREATE INDEX idx_document_tags_tag_id ON document_tags(tag_id);
```

**Sample Data:**
```sql
INSERT INTO tags (system_id, name, color)
SELECT s.id, 'Installation', '#3B82F6'
FROM systems s WHERE s.name = 'system-a'
UNION ALL
SELECT s.id, 'API Documentation', '#10B981'
FROM systems s WHERE s.name = 'system-a'
UNION ALL
SELECT s.id, 'Troubleshooting', '#EF4444'
FROM systems s WHERE s.name = 'system-a';
```

---

### 6. Document Chunks (for Vector DB sync)

```sql
CREATE TABLE document_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,

    -- Chunk content
    chunk_index INT NOT NULL, -- Order within document
    content TEXT NOT NULL,
    content_hash VARCHAR(64), -- SHA-256 for deduplication

    -- Chunk metadata for vector DB
    start_char_index INT,
    end_char_index INT,
    page_number INT,
    section_title VARCHAR(500),

    -- Vector DB reference
    vector_db_id VARCHAR(255), -- ChromaDB/Pinecone ID for this chunk

    -- Embedding info
    embedding_model VARCHAR(100) DEFAULT 'text-embedding-3-small',
    embedded_at TIMESTAMP WITH TIME ZONE,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT unique_chunk_per_document UNIQUE (document_id, chunk_index)
);

CREATE INDEX idx_chunks_document_id ON document_chunks(document_id);
CREATE INDEX idx_chunks_vector_db_id ON document_chunks(vector_db_id);
CREATE INDEX idx_chunks_content_hash ON document_chunks(content_hash);
```

**Note:** Actual embeddings stored in vector database (ChromaDB), this table maintains sync and metadata.

---

## Conversation & Agent Execution Tables

### 7. Conversations (Sessions)

```sql
CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    title VARCHAR(500), -- Auto-generated from first message

    -- System filters applied to this conversation
    system_filters UUID[], -- Array of system IDs

    -- Conversation metadata
    message_count INT DEFAULT 0,
    total_tokens_used INT DEFAULT 0,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    -- Archive/delete
    is_archived BOOLEAN DEFAULT FALSE,
    archived_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_conversations_user_id ON conversations(user_id);
CREATE INDEX idx_conversations_created_at ON conversations(created_at DESC);
CREATE INDEX idx_conversations_is_archived ON conversations(is_archived) WHERE is_archived = FALSE;
```

---

### 8. Messages

```sql
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,

    -- Message details
    role VARCHAR(20) NOT NULL, -- 'user', 'assistant', 'system'
    content TEXT NOT NULL,

    -- Rich content (for agent outputs)
    rich_content JSONB, -- Charts, tables, formatted sections
    /*
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
    */

    -- Agent execution reference
    agent_execution_id UUID, -- References agent_executions table

    -- Token usage
    prompt_tokens INT,
    completion_tokens INT,
    total_tokens INT,

    -- Citations/sources
    source_documents JSONB, -- Array of {document_id, chunk_ids, relevance_score}

    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    -- Current version (after edits)
    current_version INT DEFAULT 1
);

CREATE INDEX idx_messages_conversation_id ON messages(conversation_id);
CREATE INDEX idx_messages_created_at ON messages(created_at DESC);
CREATE INDEX idx_messages_role ON messages(role);
CREATE INDEX idx_messages_agent_execution_id ON messages(agent_execution_id);
```

---

### 9. Message Edits (Version Tracking)

```sql
CREATE TABLE message_edits (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    message_id UUID NOT NULL REFERENCES messages(id) ON DELETE CASCADE,

    version_number INT NOT NULL,

    -- Edit details
    original_content TEXT NOT NULL,
    original_rich_content JSONB,
    edited_content TEXT NOT NULL,
    edited_rich_content JSONB,

    -- Who made the edit
    edited_by UUID NOT NULL REFERENCES users(id),
    edited_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    -- Edit notes
    edit_reason VARCHAR(500),
    changes_summary TEXT,

    CONSTRAINT unique_message_version UNIQUE (message_id, version_number)
);

CREATE INDEX idx_message_edits_message_id ON message_edits(message_id);
CREATE INDEX idx_message_edits_edited_by ON message_edits(edited_by);
CREATE INDEX idx_message_edits_edited_at ON message_edits(edited_at DESC);
```

---

### 10. Agent Executions (Deep Agents Tracking)

```sql
CREATE TABLE agent_executions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    message_id UUID REFERENCES messages(id), -- The assistant message this execution produced

    -- Agent configuration
    agent_type VARCHAR(100) NOT NULL, -- 'simple', 'moderate', 'complex'
    model_name VARCHAR(100) NOT NULL, -- 'claude-haiku', 'claude-sonnet-4'

    -- Deep Agents specific
    planning_enabled BOOLEAN DEFAULT FALSE,
    filesystem_enabled BOOLEAN DEFAULT FALSE,
    subagents_used JSONB, -- Array of subagent names used

    -- Execution tracking
    status VARCHAR(50) DEFAULT 'running', -- 'running', 'paused', 'completed', 'failed'
    started_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE,

    -- Human-in-the-loop
    hitl_paused_at TIMESTAMP WITH TIME ZONE,
    hitl_approved_at TIMESTAMP WITH TIME ZONE,
    hitl_approved_by UUID REFERENCES users(id),
    plan_json JSONB, -- The todo list from write_todos tool

    -- Performance metrics
    total_duration_ms INT,
    llm_calls_count INT DEFAULT 0,
    total_tokens_used INT DEFAULT 0,
    tools_called JSONB, -- Array of {tool_name, call_count, avg_duration_ms}

    -- Error tracking
    error_message TEXT,
    error_stack_trace TEXT,

    -- Execution trace (LangGraph state snapshots)
    execution_trace JSONB
    /*
    Example execution_trace:
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
    */
);

CREATE INDEX idx_agent_executions_conversation_id ON agent_executions(conversation_id);
CREATE INDEX idx_agent_executions_status ON agent_executions(status);
CREATE INDEX idx_agent_executions_started_at ON agent_executions(started_at DESC);
CREATE INDEX idx_agent_executions_agent_type ON agent_executions(agent_type);
```

---

### 11. Agent Filesystem (Deep Agents)

```sql
CREATE TABLE agent_filesystem (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_execution_id UUID NOT NULL REFERENCES agent_executions(id) ON DELETE CASCADE,

    -- File details
    file_path VARCHAR(500) NOT NULL, -- e.g., "q1_2023_data.json"
    file_type VARCHAR(50), -- 'json', 'csv', 'txt', 'md'
    content TEXT, -- For small files, store directly
    content_s3_key VARCHAR(1000), -- For large files, store in S3
    file_size_bytes BIGINT,

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by_subagent VARCHAR(100), -- Which subagent created this

    -- Purpose/description
    description TEXT,

    CONSTRAINT unique_file_per_execution UNIQUE (agent_execution_id, file_path)
);

CREATE INDEX idx_agent_filesystem_execution_id ON agent_filesystem(agent_execution_id);
CREATE INDEX idx_agent_filesystem_file_path ON agent_filesystem(file_path);
```

---

## Analytics & Compliance Tables

### 12. Q&A Analytics

```sql
CREATE TABLE qa_analytics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- References
    user_id UUID NOT NULL REFERENCES users(id),
    conversation_id UUID NOT NULL REFERENCES conversations(id),
    message_id UUID NOT NULL REFERENCES messages(id),
    agent_execution_id UUID REFERENCES agent_executions(id),

    -- Query details
    question TEXT NOT NULL,
    question_length INT,
    question_tokens INT,

    -- Systems queried
    systems_queried UUID[], -- Array of system IDs

    -- Answer details
    answer TEXT NOT NULL,
    answer_length INT,
    answer_tokens INT,

    -- Documents used
    documents_used JSONB, -- Array of {document_id, document_name, relevance_score, chunks_used}
    total_documents_used INT,
    total_chunks_used INT,

    -- Performance
    response_time_ms INT,
    retrieval_time_ms INT,
    llm_time_ms INT,

    -- Model info
    model_name VARCHAR(100),
    total_tokens_used INT,
    estimated_cost_usd DECIMAL(10, 6),

    -- User feedback
    user_rating VARCHAR(50), -- 'thumbs_up', 'thumbs_down', 'neutral'
    user_feedback_text TEXT,
    feedback_received_at TIMESTAMP WITH TIME ZONE,

    -- Quality indicators
    has_citations BOOLEAN,
    citation_count INT,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_qa_analytics_user_id ON qa_analytics(user_id);
CREATE INDEX idx_qa_analytics_conversation_id ON qa_analytics(conversation_id);
CREATE INDEX idx_qa_analytics_created_at ON qa_analytics(created_at DESC);
CREATE INDEX idx_qa_analytics_user_rating ON qa_analytics(user_rating);
CREATE INDEX idx_qa_analytics_response_time ON qa_analytics(response_time_ms);
```

---

### 13. User Feedback

```sql
CREATE TABLE user_feedback (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    message_id UUID REFERENCES messages(id),

    -- Feedback type
    feedback_type VARCHAR(50) NOT NULL, -- 'rating', 'correction', 'feature_request', 'bug_report'

    -- Rating feedback
    rating VARCHAR(50), -- 'thumbs_up', 'thumbs_down', 'neutral'

    -- Text feedback
    feedback_text TEXT,

    -- Structured feedback
    feedback_data JSONB,
    /*
    Example for corrections:
    {
        "incorrect_claim": "The revenue increased by 50%",
        "correct_information": "The revenue increased by 15%",
        "source_document_id": "uuid",
        "page_number": 12
    }
    */

    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    -- Response tracking
    addressed BOOLEAN DEFAULT FALSE,
    addressed_at TIMESTAMP WITH TIME ZONE,
    addressed_by UUID REFERENCES users(id),
    resolution_notes TEXT
);

CREATE INDEX idx_user_feedback_user_id ON user_feedback(user_id);
CREATE INDEX idx_user_feedback_message_id ON user_feedback(message_id);
CREATE INDEX idx_user_feedback_feedback_type ON user_feedback(feedback_type);
CREATE INDEX idx_user_feedback_addressed ON user_feedback(addressed) WHERE addressed = FALSE;
CREATE INDEX idx_user_feedback_created_at ON user_feedback(created_at DESC);
```

---

## Export & Sharing Tables

### 14. Exports

```sql
CREATE TABLE exports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    message_id UUID NOT NULL REFERENCES messages(id),

    -- Export details
    export_format VARCHAR(20) NOT NULL, -- 'pdf', 'markdown', 'html', 'docx'
    file_path VARCHAR(1000) NOT NULL, -- S3 key or local path
    file_size_bytes BIGINT,

    -- Export configuration
    include_charts BOOLEAN DEFAULT TRUE,
    include_citations BOOLEAN DEFAULT TRUE,
    styling_template VARCHAR(100), -- 'professional', 'minimal', 'corporate'

    -- Version exported
    message_version INT DEFAULT 1,

    -- Generation tracking
    status VARCHAR(50) DEFAULT 'pending', -- 'pending', 'generating', 'completed', 'failed'
    generated_at TIMESTAMP WITH TIME ZONE,
    generation_error TEXT,

    -- Download tracking
    download_count INT DEFAULT 0,
    last_downloaded_at TIMESTAMP WITH TIME ZONE,

    -- Expiry
    expires_at TIMESTAMP WITH TIME ZONE, -- Auto-delete after 30 days

    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_exports_user_id ON exports(user_id);
CREATE INDEX idx_exports_message_id ON exports(message_id);
CREATE INDEX idx_exports_status ON exports(status);
CREATE INDEX idx_exports_created_at ON exports(created_at DESC);
CREATE INDEX idx_exports_expires_at ON exports(expires_at) WHERE expires_at IS NOT NULL;
```

---

## Admin & Monitoring Tables

### 15. Audit Logs

```sql
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Who & What
    user_id UUID REFERENCES users(id),
    action VARCHAR(100) NOT NULL, -- 'user.login', 'document.upload', 'system.assign', etc.
    entity_type VARCHAR(50), -- 'user', 'document', 'system', 'conversation'
    entity_id UUID,

    -- Details
    old_values JSONB,
    new_values JSONB,
    changes JSONB,

    -- Context
    ip_address INET,
    user_agent TEXT,

    -- Result
    success BOOLEAN DEFAULT TRUE,
    error_message TEXT,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_action ON audit_logs(action);
CREATE INDEX idx_audit_logs_entity_type ON audit_logs(entity_type);
CREATE INDEX idx_audit_logs_created_at ON audit_logs(created_at DESC);
```

---

## Vector Database Schema (ChromaDB)

While the vector database (ChromaDB) is separate, here's the metadata structure for each embedding:

```python
# ChromaDB Collection Schema
collection_metadata = {
    "name": "document_chunks",
    "embedding_function": "text-embedding-3-small"
}

# Each embedding entry includes:
chunk_metadata = {
    # IDs for cross-referencing
    "chunk_id": "uuid from document_chunks table",
    "document_id": "uuid from documents table",
    "system_id": "uuid from systems table",

    # Permission filtering
    "system_ids": ["uuid1", "uuid2"],  # For cross-system queries
    "is_personal": False,
    "owner_user_id": None,  # Only set if is_personal=True

    # Document info
    "document_title": "System A Installation Guide",
    "document_filename": "system_a_install.pdf",
    "file_type": "pdf",

    # Chunk location
    "chunk_index": 0,
    "page_number": 12,
    "section_title": "Linux Installation",

    # Content info
    "char_count": 987,
    "word_count": 142,

    # Tags (for filtering)
    "tags": ["Installation", "Linux"],

    # Timestamps
    "indexed_at": "2024-01-15T10:30:00Z",
    "document_uploaded_at": "2024-01-15T09:00:00Z"
}
```

**Permission-Filtered Query Example:**
```python
# User David querying System A + Personal docs
accessible_system_ids = ["system-a-uuid", "david-personal-uuid"]

results = collection.query(
    query_embeddings=[query_embedding],
    n_results=10,
    where={
        "$or": [
            {"system_id": {"$in": accessible_system_ids}},
            {
                "$and": [
                    {"is_personal": True},
                    {"owner_user_id": david_user_id}
                ]
            }
        ]
    }
)
```

---

## Common Queries

### Get User's Accessible Documents

```sql
-- Get all documents user can query
SELECT DISTINCT d.*
FROM documents d
JOIN systems s ON d.system_id = s.id
LEFT JOIN user_systems us ON s.id = us.system_id
WHERE
    -- User has explicit system access
    (us.user_id = :user_id AND us.can_query = TRUE)

    -- OR it's their personal system
    OR (s.is_personal = TRUE AND s.owner_user_id = :user_id)

    -- OR user is super_user (all non-personal systems)
    OR (
        :user_role = 'super_user'
        AND s.is_personal = FALSE
    )

    -- Document must be ready and not deleted
    AND d.status = 'ready'
    AND d.is_deleted = FALSE;
```

### Get Conversation with Messages

```sql
SELECT
    c.*,
    json_agg(
        json_build_object(
            'id', m.id,
            'role', m.role,
            'content', m.content,
            'rich_content', m.rich_content,
            'created_at', m.created_at,
            'current_version', m.current_version,
            'source_documents', m.source_documents
        ) ORDER BY m.created_at ASC
    ) as messages
FROM conversations c
LEFT JOIN messages m ON c.id = m.conversation_id
WHERE c.id = :conversation_id
  AND c.user_id = :user_id
GROUP BY c.id;
```

### Analytics: Most Queried Documents

```sql
SELECT
    d.id,
    d.title,
    d.filename,
    s.display_name as system_name,
    COUNT(DISTINCT qa.id) as query_count,
    AVG(qa.response_time_ms) as avg_response_time_ms,
    COUNT(CASE WHEN qa.user_rating = 'thumbs_up' THEN 1 END) as positive_ratings,
    COUNT(CASE WHEN qa.user_rating = 'thumbs_down' THEN 1 END) as negative_ratings
FROM documents d
JOIN systems s ON d.system_id = s.id
LEFT JOIN qa_analytics qa ON qa.documents_used @> json_build_array(
    json_build_object('document_id', d.id::text)
)::jsonb
WHERE qa.created_at >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY d.id, d.title, d.filename, s.display_name
ORDER BY query_count DESC
LIMIT 20;
```

### System Usage Analytics

```sql
SELECT
    s.display_name as system_name,
    COUNT(DISTINCT c.user_id) as unique_users,
    COUNT(DISTINCT c.id) as conversations,
    COUNT(DISTINCT m.id) as messages,
    SUM(m.total_tokens) as total_tokens,
    AVG(qa.response_time_ms) as avg_response_time_ms,
    COUNT(CASE WHEN qa.user_rating = 'thumbs_up' THEN 1 END) as positive_ratings
FROM systems s
JOIN conversations c ON s.id = ANY(c.system_filters)
JOIN messages m ON c.id = m.conversation_id
LEFT JOIN qa_analytics qa ON m.id = qa.message_id
WHERE
    s.is_personal = FALSE
    AND c.created_at >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY s.id, s.display_name
ORDER BY conversations DESC;
```

---

## Migration Strategy

### Phase 1: Core Tables
1. Users
2. Systems
3. User-System Assignments
4. Documents
5. Tags & Document Tags

### Phase 2: Conversation & Messaging
6. Conversations
7. Messages
8. Message Edits

### Phase 3: Agent Execution
9. Agent Executions
10. Agent Filesystem
11. Document Chunks

### Phase 4: Analytics & Compliance
12. Q&A Analytics
13. User Feedback
14. Audit Logs

### Phase 5: Features
15. Exports

### Alembic Migration Example

```python
# migrations/versions/001_create_core_tables.py
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

def upgrade():
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('email', sa.String(255), unique=True, nullable=False),
        # ... rest of columns
    )

    # Create indexes
    op.create_index('idx_users_email', 'users', ['email'])
    # ... etc

def downgrade():
    op.drop_table('users')
```

---

## Performance Considerations

### Indexing Strategy

1. **Foreign Keys**: Always indexed for JOIN performance
2. **Filter Columns**: Status fields, booleans, dates
3. **Sort Columns**: created_at, updated_at (DESC for recent-first queries)
4. **Partial Indexes**: For common WHERE clauses (e.g., is_deleted = FALSE)

### Partitioning (Future)

For high-volume tables, consider partitioning:
- `qa_analytics`: Partition by created_at (monthly)
- `audit_logs`: Partition by created_at (monthly)
- `messages`: Partition by created_at (yearly)

### Archival Strategy

1. **Soft Delete**: Use is_deleted flag initially
2. **Archive Old Conversations**: Move conversations older than 1 year to archive table
3. **Delete Old Exports**: Auto-delete exports after 30 days
4. **Audit Log Retention**: Keep 2 years, then archive

---

## Data Integrity Rules

### Constraints

1. **System Assignment**: Users must have at least one system assignment (enforced at application level)
2. **Personal System**: Each user has exactly one personal system
3. **Document Versions**: parent_document_id must reference same system_id
4. **Message Edits**: Can only edit assistant messages, not user messages
5. **Agent Filesystem**: Files deleted when agent execution completes (configurable)

### Triggers

```sql
-- Auto-update conversation.updated_at when new message added
CREATE OR REPLACE FUNCTION update_conversation_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE conversations
    SET updated_at = CURRENT_TIMESTAMP,
        message_count = message_count + 1
    WHERE id = NEW.conversation_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_conversation
    AFTER INSERT ON messages
    FOR EACH ROW
    EXECUTE FUNCTION update_conversation_timestamp();
```

```sql
-- Auto-create personal system on user signup
CREATE OR REPLACE FUNCTION create_personal_system()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO systems (name, display_name, is_personal, owner_user_id)
    VALUES ('personal', 'Personal Documents', TRUE, NEW.id);

    -- Grant full permissions to user's personal system
    INSERT INTO user_systems (user_id, system_id, can_upload, can_edit, can_query)
    SELECT NEW.id, s.id, TRUE, TRUE, TRUE
    FROM systems s
    WHERE s.owner_user_id = NEW.id AND s.is_personal = TRUE;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_create_personal_system
    AFTER INSERT ON users
    FOR EACH ROW
    EXECUTE FUNCTION create_personal_system();
```

---

## Sample Full Data Flow

### Complete Flow: User Query to Analytics

```sql
-- 1. User David starts conversation
INSERT INTO conversations (user_id, system_filters)
VALUES ('david-uuid', ARRAY['system-a-uuid', 'david-personal-uuid']::UUID[])
RETURNING id;

-- 2. User message
INSERT INTO messages (conversation_id, role, content)
VALUES ('conversation-uuid', 'user', 'How do I install System A on Ubuntu?');

-- 3. Agent execution starts
INSERT INTO agent_executions (conversation_id, agent_type, model_name, planning_enabled)
VALUES ('conversation-uuid', 'simple', 'claude-haiku', FALSE)
RETURNING id;

-- 4. Agent retrieves from vector DB (external)
-- ChromaDB query with system_id filter

-- 5. Assistant message created
INSERT INTO messages (
    conversation_id,
    role,
    content,
    rich_content,
    agent_execution_id,
    source_documents
)
VALUES (
    'conversation-uuid',
    'assistant',
    'To install System A on Ubuntu...',
    '{"sections": [...], "citations": [...]}',
    'execution-uuid',
    '[{"document_id": "doc-uuid", "relevance_score": 0.92}]'
);

-- 6. Agent execution completes
UPDATE agent_executions
SET status = 'completed',
    completed_at = CURRENT_TIMESTAMP,
    total_duration_ms = 1234,
    llm_calls_count = 1,
    total_tokens_used = 1500
WHERE id = 'execution-uuid';

-- 7. Analytics record created
INSERT INTO qa_analytics (
    user_id,
    conversation_id,
    message_id,
    agent_execution_id,
    question,
    answer,
    systems_queried,
    documents_used,
    response_time_ms,
    model_name,
    total_tokens_used
) VALUES (...);

-- 8. User provides feedback
INSERT INTO user_feedback (
    user_id,
    message_id,
    feedback_type,
    rating
) VALUES ('david-uuid', 'message-uuid', 'rating', 'thumbs_up');

-- 9. User exports as PDF
INSERT INTO exports (
    user_id,
    message_id,
    export_format,
    file_path,
    status
) VALUES ('david-uuid', 'message-uuid', 'pdf', 's3://exports/...', 'pending');
```

---

**Last Updated**: 2025-11-15
**Status**: Complete schema design
**Next Steps**:
1. Create Alembic migrations
2. Define SQLAlchemy models
3. Create Pydantic schemas for API contracts
