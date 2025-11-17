# Use Case Technical Design - End to End

This document analyzes each use case and designs the complete technical flow from user action to system response.

---

## Use Case 1: System Documentation Q&A

### User Story
**Document Manager** uploads System A manuals → **End User** asks questions scoped to System A across multiple sessions

### Technical Flow

#### Part 1: Document Manager Upload (One-time Setup)

**User Actions:**
1. Maria (Doc Manager) logs in
2. Navigates to Document Manager dashboard
3. Clicks "Upload Documents"
4. Selects 3 PDFs: Installation Manual, API Docs, Troubleshooting Guide
5. Creates/selects tag: "System A", "Documentation", "Technical"
6. Sets permissions: Engineering team + Support team
7. Clicks "Upload & Process"

**Frontend (React):**
```typescript
// Component: DocumentUploadModal
1. User drags files or clicks to select
2. Shows file preview with metadata form
3. Tag selector (multi-select with autocomplete)
4. Permission selector (users/groups dropdown)
5. Validates files (size, type)
6. Uploads files with FormData
7. Shows upload progress bar
8. Polls for processing status
9. Shows success notification when ready
```

**API Calls:**
```http
POST /api/v1/documents/upload
Content-Type: multipart/form-data

{
  files: [File, File, File],
  tags: ["System A", "Documentation", "Technical"],
  permissions: {
    groups: ["engineering", "support"],
    users: []
  },
  visibility: "shared"
}

Response:
{
  "status": "success",
  "data": {
    "upload_id": "upload-123",
    "documents": [
      {"id": "doc-1", "title": "System A Install.pdf", "status": "processing"},
      {"id": "doc-2", "title": "System A API.pdf", "status": "processing"},
      {"id": "doc-3", "title": "Troubleshooting.pdf", "status": "processing"}
    ]
  }
}
```

**Backend Processing (FastAPI + Celery):**
```python
# API Endpoint
@router.post("/documents/upload")
async def upload_documents(
    files: List[UploadFile],
    tags: List[str],
    permissions: PermissionSchema,
    current_user: User = Depends(get_current_user)
):
    # 1. Validate user has doc_manager role
    if current_user.role not in ["admin", "doc_manager"]:
        raise HTTPException(403, "Insufficient permissions")

    # 2. Save files to S3/local storage
    document_ids = []
    for file in files:
        # Save to S3
        file_path = await storage.save_file(file)

        # Create document record
        doc = Document(
            title=file.filename,
            file_path=file_path,
            file_type=get_file_type(file),
            uploaded_by=current_user.id,
            status="processing",
            visibility="shared"
        )
        db.add(doc)
        db.flush()

        # Create tag associations
        for tag_name in tags:
            tag = get_or_create_tag(tag_name)
            db.add(DocumentTag(document_id=doc.id, tag_id=tag.id))

        # Create permissions
        for group_id in permissions.groups:
            db.add(Permission(
                resource_type="document",
                resource_id=doc.id,
                group_id=group_id,
                access_level="read"
            ))

        document_ids.append(doc.id)

    db.commit()

    # 3. Queue background processing jobs
    for doc_id in document_ids:
        process_document_task.delay(doc_id)

    return {"upload_id": upload_id, "documents": documents}
```

**Background Processing (Celery Task):**
```python
@celery_app.task
def process_document_task(document_id: str):
    """Process document: extract text, generate embeddings, index."""

    doc = db.query(Document).get(document_id)

    try:
        # 1. Extract text based on file type
        if doc.file_type == "pdf":
            extractor = PDFExtractor()
        elif doc.file_type == "pptx":
            extractor = PPTXExtractor()
        # ... other extractors

        extracted_content = extractor.extract(doc.file_path)

        # 2. Chunk the content
        chunker = SemanticChunker(chunk_size=1000, overlap=200)
        chunks = chunker.chunk(extracted_content)

        # 3. Generate embeddings
        embedding_model = get_embedding_model()

        for i, chunk in enumerate(chunks):
            # Create chunk record
            db_chunk = DocumentChunk(
                document_id=doc.id,
                chunk_index=i,
                content=chunk.text,
                page_number=chunk.page_number,
                section_title=chunk.section
            )
            db.add(db_chunk)
            db.flush()

            # Generate embedding
            embedding = embedding_model.embed(chunk.text)

            # Store in vector DB with metadata for filtering
            vector_db.add(
                id=db_chunk.id,
                embedding=embedding,
                metadata={
                    "document_id": doc.id,
                    "chunk_index": i,
                    "tags": [tag.name for tag in doc.tags],
                    "permissions": get_permission_ids(doc),
                    "title": doc.title,
                    "file_type": doc.file_type
                }
            )

        # 4. Update document status
        doc.status = "ready"
        doc.page_count = len(chunks)
        db.commit()

        # 5. Send WebSocket notification
        await notify_user(doc.uploaded_by, {
            "type": "document_ready",
            "document_id": doc.id,
            "title": doc.title
        })

    except Exception as e:
        doc.status = "failed"
        doc.error_message = str(e)
        db.commit()
        raise
```

**Database Changes:**
```sql
-- Documents table
INSERT INTO documents (id, title, file_path, file_type, uploaded_by, status, visibility)
VALUES ('doc-1', 'System A Install.pdf', 's3://...', 'pdf', 'user-maria', 'ready', 'shared');

-- Tags
INSERT INTO tags (id, name) VALUES ('tag-1', 'System A');
INSERT INTO document_tags (document_id, tag_id) VALUES ('doc-1', 'tag-1');

-- Permissions
INSERT INTO permissions (resource_type, resource_id, group_id, access_level)
VALUES ('document', 'doc-1', 'group-engineering', 'read');

-- Chunks (many)
INSERT INTO document_chunks (id, document_id, chunk_index, content, page_number)
VALUES ('chunk-1', 'doc-1', 0, 'To install System A on Linux...', 5);
```

**Vector DB (ChromaDB/Pinecone):**
```python
# Store embeddings with metadata for filtering
collection.add(
    ids=["chunk-1", "chunk-2", ...],
    embeddings=[embedding_1, embedding_2, ...],
    metadatas=[
        {
            "document_id": "doc-1",
            "tags": ["System A", "Documentation"],
            "permissions": ["group-engineering", "group-support"],
            "title": "System A Install.pdf"
        },
        ...
    ]
)
```

---

#### Part 2: End User Query (Session 1 - Week 1)

**User Actions:**
1. David (Engineer) logs in
2. Sees available collections: "System A", "System B", etc.
3. Selects "System A" collection
4. Types: "How do I install System A on Linux?"
5. Hits Enter

**Frontend (React):**
```typescript
// Component: ChatInterface
1. User selects collection from dropdown
2. Types question in input field
3. On submit:
   - Disable input
   - Show loading indicator
   - Send message via WebSocket or POST
   - Stream agent response in real-time
   - Render rich content (markdown, tables, code blocks)
   - Show source citations as clickable links
```

**API Call:**
```http
POST /api/v1/messages
{
  "conversation_id": "conv-123",  // or null for new conversation
  "content": "How do I install System A on Linux?",
  "tags_filter": ["System A"],
  "context": {}
}

Response (streamed via WebSocket):
{
  "message_id": "msg-456",
  "conversation_id": "conv-123",
  "status": "thinking",
  "agent_step": "Planning retrieval strategy..."
}

{
  "status": "retrieving",
  "agent_step": "Searching System A documentation..."
}

{
  "status": "analyzing",
  "agent_step": "Analyzing installation instructions..."
}

{
  "status": "complete",
  "content": "To install System A on Linux:\n\n1. **Prerequisites**\n...",
  "is_rich_content": true,
  "render_format": "markdown",
  "sources": [
    {"document_id": "doc-1", "title": "System A Install.pdf", "page": 5, "chunk_id": "chunk-1"}
  ]
}
```

**Backend (Agent Workflow):**
```python
@router.post("/messages")
async def create_message(
    message_request: MessageCreate,
    current_user: User = Depends(get_current_user),
    websocket: WebSocket = Depends(get_websocket)
):
    # 1. Create message record
    message = Message(
        conversation_id=message_request.conversation_id or create_conversation(),
        role="user",
        content=message_request.content,
    )
    db.add(message)
    db.commit()

    # 2. Get user's accessible document IDs (permission filtering)
    accessible_docs = get_user_accessible_documents(
        current_user,
        tags=message_request.tags_filter
    )

    # 3. Initialize agent with user context
    agent = DocumentQAAgent(
        user_id=current_user.id,
        accessible_documents=accessible_docs,
        tags_filter=message_request.tags_filter,
        websocket=websocket  # for streaming updates
    )

    # 4. Run agent workflow
    response = await agent.run(message.content)

    # 5. Save assistant message
    assistant_message = Message(
        conversation_id=message.conversation_id,
        role="assistant",
        content=response.content,
        is_rich_content=response.has_formatting,
        render_format="markdown",
        metadata={
            "documents_used": response.document_ids,
            "agent_steps": response.steps,
            "sources": response.sources
        }
    )
    db.add(assistant_message)

    # 6. Log to analytics
    qa_log = QAAnalytics(
        user_id=current_user.id,
        conversation_id=message.conversation_id,
        message_id=assistant_message.id,
        question=message.content,
        answer=response.content,
        documents_used=response.document_ids,
        tags_used=message_request.tags_filter,
        response_time_ms=response.time_ms,
        token_count=response.tokens
    )
    db.add(qa_log)

    db.commit()

    return assistant_message
```

**Agent Workflow (Deep Agents):**
```python
from deepagents import create_deep_agent

# Create agent with Deep Agents framework
def create_document_qa_agent(
    user_id: str,
    accessible_documents: List[str],
    system_filter: List[str],
    websocket: WebSocket,
    complexity: str = "simple"
) -> Agent:
    """Create appropriate agent based on query complexity."""

    if complexity == "simple":
        # Fast agent for simple lookups
        return create_deep_agent(
            tools=[semantic_search_tool],
            system_prompt="""You answer questions from documentation concisely.

Search the documents, find the answer, cite your sources.""",
            model="anthropic:claude-haiku",
            planning=False
        )

    elif complexity == "moderate":
        # Planning agent for multi-step queries
        return create_deep_agent(
            tools=[semantic_search_tool, extract_data_tool],
            system_prompt="""You are a documentation expert.

When answering complex questions:
1. Create a plan using write_todos
2. Search relevant documents
3. Extract key information
4. Synthesize clear answer with citations""",
            model="anthropic:claude-sonnet",
            planning=True,
            interrupt_on=["write_todos"]  # Human approval
        )

    else:  # complex
        # Full deep agent with specialized capabilities
        return create_deep_agent(
            tools=[
                semantic_search_tool,
                extract_tables_tool,
                compare_documents_tool,
                write_file,
                read_file
            ],
            system_prompt="""You are an expert analyst helping users understand documentation.

For complex analysis:
1. Plan your approach (write_todos)
2. Extract relevant sections from multiple documents
3. Store intermediate results in filesystem if needed
4. Compare and synthesize information
5. Present findings with clear citations""",
            model="anthropic:claude-sonnet-4",
            planning=True,
            interrupt_on=["write_todos"],
            filesystem=True
        )


# Tools for the agent
class DocumentSearchTool:
    """Tool for searching documents with permission filtering."""

    def __init__(self, user_id: str, accessible_documents: List[str]):
        self.user_id = user_id
        self.accessible_documents = accessible_documents

    async def search(self, query: str) -> List[Dict]:
        """Search vector DB for relevant chunks."""

        # Generate embedding
        query_embedding = embedding_model.embed(query)

        # Search with permission filter
        results = vector_db.query(
            query_embedding=query_embedding,
            filter={
                "document_id": {"$in": self.accessible_documents}
            },
            n_results=10
        )

        return [
            {
                "content": r.content,
                "document": r.metadata["title"],
                "page": r.metadata.get("page_number"),
                "source": f"{r.metadata['title']}, p.{r.metadata.get('page_number')}"
            }
            for r in results
        ]
```

**Database Changes:**
```sql
-- New conversation
INSERT INTO conversations (id, user_id, created_at, title)
VALUES ('conv-123', 'user-david', NOW(), 'System A Installation');

-- User message
INSERT INTO messages (id, conversation_id, role, content, created_at)
VALUES ('msg-455', 'conv-123', 'user', 'How do I install System A on Linux?', NOW());

-- Assistant message
INSERT INTO messages (id, conversation_id, role, content, is_rich_content, render_format, metadata)
VALUES ('msg-456', 'conv-123', 'assistant', 'To install System A on Linux...', true, 'markdown',
        '{"documents_used": ["doc-1"], "sources": [...]}');

-- Analytics
INSERT INTO qa_analytics (user_id, conversation_id, message_id, question, answer,
                          documents_used, tags_used, response_time_ms)
VALUES ('user-david', 'conv-123', 'msg-456', 'How do...', 'To install...',
        '["doc-1"]', '["System A"]', 1234);
```

---

#### Part 3: Follow-up Query (Session 2 - Week 3)

**User Actions:**
1. David logs in again (3 weeks later)
2. Sees conversation history
3. Can either continue existing conversation or start new one
4. Starts new conversation, asks: "I'm getting error code E-401, how do I fix it?"

**Key Difference:**
- Documents are already processed (no re-upload needed)
- User session is new but can access same documents
- Agent retrieves from same vector DB
- Analytics logged separately

**Frontend:**
```typescript
// Shows conversation history on sidebar
<ConversationList>
  <Conversation id="conv-123" title="System A Installation" date="3 weeks ago" />
  <Button>+ New Conversation</Button>
</ConversationList>

// User starts new conversation
// Same flow as Session 1, but new conversation_id
```

---

---

## Updated Permission Model (After Feedback)

### **System-Centric Permission Architecture**

#### **User Roles:**

| Role | Upload/Edit Docs | Query Assigned Systems | Query All Systems | Create Systems |
|------|------------------|------------------------|-------------------|----------------|
| **Document Admin** | ✅ Yes (assigned systems) | ✅ Yes | ❌ No | ❌ No |
| **System User** | ❌ No | ✅ Yes | ❌ No | ❌ No |
| **Super User** | ❌ No | ✅ Yes (read-only) | ✅ Yes (read-only) | ❌ No |
| **Admin** | ✅ Yes (all systems) | ✅ Yes | ✅ Yes | ✅ Yes |

#### **Personal Documents System:**

Every user gets a **"Personal" system** automatically created on signup:

```python
# On user signup
@router.post("/auth/signup")
async def signup(user_data: UserCreate):
    # Create user
    user = User(
        email=user_data.email,
        password_hash=hash_password(user_data.password),
        role="system_user",  # default role
        created_at=datetime.now()
    )
    db.add(user)
    db.flush()

    # Auto-create personal system for this user
    personal_system = System(
        name=f"Personal - {user.name}",
        description=f"Personal documents for {user.name}",
        created_by=user.id,
        is_active=True,
        is_personal=True,  # NEW FLAG
        owner_user_id=user.id  # NEW: Links to user
    )
    db.add(personal_system)
    db.flush()

    # Assign user to their personal system with full permissions
    user_system = UserSystem(
        user_id=user.id,
        system_id=personal_system.id,
        can_upload=True,   # Can upload to personal
        can_edit=True,     # Can edit personal docs
        can_query=True     # Can query personal docs
    )
    db.add(user_system)
    db.commit()

    return {"user": user, "personal_system": personal_system}
```

#### **Cross-System Querying:**

Users can query across **Personal + Assigned Systems**:

```python
# Updated permission helper
def get_user_accessible_systems(user: User, include_personal: bool = True) -> List[str]:
    """Get all systems a user can query."""

    if user.role == "super_user":
        # Super users: All systems (excluding personal systems of other users)
        systems = db.query(System.id).filter(
            System.is_active == True,
            or_(
                System.is_personal == False,
                System.owner_user_id == user.id  # Include own personal
            )
        ).all()
        return [s.id for s in systems]

    elif user.role in ["document_admin", "system_user"]:
        # Get assigned systems (includes their personal system)
        systems = (
            db.query(System.id)
            .join(UserSystem)
            .filter(
                UserSystem.user_id == user.id,
                UserSystem.can_query == True,
                System.is_active == True
            )
            .all()
        )
        return [s.id for s in systems]

    elif user.role == "admin":
        # Admins: Everything
        if include_personal:
            return [s.id for s in db.query(System.id).filter(System.is_active == True).all()]
        else:
            # Exclude personal systems
            return [s.id for s in db.query(System.id).filter(
                System.is_active == True,
                System.is_personal == False
            ).all()]

    return []
```

#### **Multi-System Query Example:**

```python
# Frontend: User selects which systems to query
<SystemSelector multiple>
  <Option value="personal">My Personal Documents (5 docs)</Option>
  <Option value="system-a">System A (20 docs) ✅ Can Upload</Option>
  <Option value="system-b">System B (15 docs)</Option>
</SystemSelector>

# User selects: ["personal", "system-a"]
# Asks: "How do I configure authentication?"

# Backend: Query across both systems
POST /api/v1/messages
{
  "content": "How do I configure authentication?",
  "system_filters": ["personal", "system-a"]  # Query both!
}

# Agent retrieves from:
# - Personal documents (maybe user's notes on auth)
# - System A documents (official auth documentation)
# - Combines results in answer with proper attribution
```

#### **Updated Database Schema:**

```sql
-- Systems table with personal flag
CREATE TABLE systems (
    id UUID PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    description TEXT,
    created_at TIMESTAMP,
    created_by UUID REFERENCES users(id),
    is_active BOOLEAN DEFAULT TRUE,
    is_personal BOOLEAN DEFAULT FALSE,  -- NEW: Flag for personal systems
    owner_user_id UUID REFERENCES users(id),  -- NEW: Owner if personal
    CHECK (is_personal = FALSE OR owner_user_id IS NOT NULL)  -- Personal must have owner
);

-- User-system assignments (unchanged)
CREATE TABLE user_systems (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    system_id UUID REFERENCES systems(id),
    can_upload BOOLEAN DEFAULT FALSE,
    can_edit BOOLEAN DEFAULT FALSE,
    can_query BOOLEAN DEFAULT TRUE,
    assigned_at TIMESTAMP,
    assigned_by UUID REFERENCES users(id),
    UNIQUE(user_id, system_id)
);

-- Documents (unchanged)
CREATE TABLE documents (
    id UUID PRIMARY KEY,
    title VARCHAR(500),
    file_path VARCHAR(1000),
    file_type VARCHAR(50),
    system_id UUID REFERENCES systems(id) NOT NULL,  -- Belongs to system (personal or shared)
    uploaded_by UUID REFERENCES users(id),
    uploaded_at TIMESTAMP,
    status VARCHAR(50),
    version INT DEFAULT 1,
    metadata JSONB
);
```

#### **Admin Capabilities:**

```python
# Admins can do everything
if current_user.role == "admin":
    # Create new systems
    POST /api/v1/systems
    {
        "name": "System C",
        "description": "New product line documentation"
    }

    # Assign users to systems
    POST /api/v1/systems/{system_id}/assign-users
    {
        "user_ids": ["user-1", "user-2"],
        "permissions": {
            "can_upload": true,
            "can_edit": true,
            "can_query": true
        }
    }

    # Upload/edit/query all systems (except personal systems of other users)
    # Delete systems
    # Manage all users
```

---

## Use Case 2: Instant Personal Document Upload & Query

### User Story
**End User** uploads a contract directly in chat → Immediately asks questions → All interactions logged for compliance

### Technical Flow

#### Part 1: In-Chat Document Upload

**User Actions:**
1. Bob (System User) is in a conversation
2. Sees "📎 Attach File" button in chat input
3. Clicks and selects "vendor_contract_2024.pdf"
4. File uploads with progress indicator
5. System processes in background
6. Bob immediately types: "What are the payment terms?"
7. Hits Enter (even before processing completes)

**Frontend (React):**
```typescript
// Component: ChatInput with file upload
export const ChatInput: React.FC = () => {
  const [message, setMessage] = useState('');
  const [uploadingFiles, setUploadingFiles] = useState<File[]>([]);
  const [processingDocs, setProcessingDocs] = useState<Document[]>([]);

  const handleFileUpload = async (files: FileList) => {
    setUploadingFiles(Array.from(files));

    // Upload to personal system
    const formData = new FormData();
    Array.from(files).forEach(file => formData.append('files', file));

    const response = await fetch('/api/v1/documents/upload-personal', {
      method: 'POST',
      body: formData,
      headers: { 'Authorization': `Bearer ${token}` }
    });

    const data = await response.json();

    // Show processing status
    setProcessingDocs(data.documents);
    setUploadingFiles([]);

    // Listen for processing completion via WebSocket
    websocket.on('document_ready', (doc) => {
      setProcessingDocs(prev => prev.filter(d => d.id !== doc.id));
      showNotification(`${doc.title} is ready for querying!`);
    });
  };

  const handleSendMessage = async () => {
    // User can send message even if docs still processing
    const response = await fetch('/api/v1/messages', {
      method: 'POST',
      body: JSON.stringify({
        content: message,
        system_filters: ['personal'],  // Query personal system
        pending_documents: processingDocs.map(d => d.id)  // Include processing docs
      })
    });
  };

  return (
    <div className="chat-input">
      {processingDocs.length > 0 && (
        <div className="processing-indicator">
          Processing {processingDocs.length} document(s)...
          <Spinner />
        </div>
      )}

      <FileDropzone onDrop={handleFileUpload} />

      <textarea
        value={message}
        onChange={(e) => setMessage(e.target.value)}
        placeholder="Type a message or attach a file..."
      />

      <button onClick={handleSendMessage}>Send</button>
    </div>
  );
};
```

**API Call:**
```http
POST /api/v1/documents/upload-personal
Content-Type: multipart/form-data
Authorization: Bearer {token}

{
  files: [File],
  auto_tag: true  // Auto-tag with document type, date, etc.
}

Response:
{
  "status": "success",
  "documents": [
    {
      "id": "doc-personal-1",
      "title": "vendor_contract_2024.pdf",
      "system_id": "system-personal-bob",
      "status": "processing",
      "uploaded_at": "2024-11-15T10:30:00Z"
    }
  ]
}
```

**Backend Processing:**
```python
@router.post("/documents/upload-personal")
async def upload_personal_documents(
    files: List[UploadFile],
    auto_tag: bool = True,
    current_user: User = Depends(get_current_user)
):
    """Upload documents to user's personal system."""

    # Get user's personal system
    personal_system = (
        db.query(System)
        .filter(
            System.is_personal == True,
            System.owner_user_id == current_user.id
        )
        .first()
    )

    if not personal_system:
        raise HTTPException(404, "Personal system not found")

    documents = []
    for file in files:
        # Save to S3
        file_path = await storage.save_file(file, prefix=f"personal/{current_user.id}/")

        # Create document
        doc = Document(
            title=file.filename,
            file_path=file_path,
            file_type=get_file_type(file),
            system_id=personal_system.id,  # Personal system
            uploaded_by=current_user.id,
            status="processing",
            uploaded_at=datetime.now()
        )
        db.add(doc)
        db.flush()

        # Auto-tag if enabled
        if auto_tag:
            tags = auto_generate_tags(file.filename, file.file_type)
            # e.g., ["Contract", "2024", "Legal"]
            for tag_name in tags:
                tag = get_or_create_tag(tag_name, personal_system.id)
                db.add(DocumentTag(document_id=doc.id, tag_id=tag.id))

        # Track version
        version = DocumentVersion(
            document_id=doc.id,
            version=1,
            uploaded_by=current_user.id,
            uploaded_at=datetime.now(),
            change_type="created",
            file_path=file_path
        )
        db.add(version)

        documents.append(doc)

    db.commit()

    # Queue processing (same as shared docs)
    for doc in documents:
        process_document_task.delay(doc.id)

    return {"documents": documents}


def auto_generate_tags(filename: str, file_type: str) -> List[str]:
    """Generate tags based on filename and type."""
    tags = []

    # Add file type tag
    tags.append(file_type.upper())  # "PDF", "DOCX"

    # Extract year if in filename
    year_match = re.search(r'20\d{2}', filename)
    if year_match:
        tags.append(year_match.group())

    # Detect common document types
    filename_lower = filename.lower()
    if 'contract' in filename_lower:
        tags.append('Contract')
    elif 'invoice' in filename_lower:
        tags.append('Invoice')
    elif 'report' in filename_lower:
        tags.append('Report')
    # ... more rules

    return tags
```

#### Part 2: Query Before Processing Completes (Smart Handling)

**User Action:**
- Bob asks "What are payment terms?" while doc is still processing

**Backend Handling:**
```python
@router.post("/messages")
async def create_message(
    message_request: MessageCreate,
    current_user: User = Depends(get_current_user),
    websocket: WebSocket = Depends(get_websocket)
):
    # Get accessible documents
    accessible_docs = get_user_accessible_documents(
        current_user,
        systems=message_request.system_filters
    )

    # Check if any pending documents
    pending_docs = [
        d for d in accessible_docs
        if d.status == "processing" and d.id in message_request.pending_documents
    ]

    if pending_docs:
        # Option A: Wait for processing to complete
        await websocket.send_json({
            "type": "waiting",
            "message": f"Waiting for {len(pending_docs)} document(s) to finish processing..."
        })

        # Poll until ready (with timeout)
        max_wait = 60  # seconds
        start_time = time.time()

        while pending_docs and (time.time() - start_time) < max_wait:
            await asyncio.sleep(2)
            # Refresh document status
            for doc in pending_docs:
                db.refresh(doc)
            pending_docs = [d for d in pending_docs if d.status == "processing"]

        if pending_docs:
            # Timeout - answer without these docs
            await websocket.send_json({
                "type": "partial_answer",
                "message": f"Processing taking longer than expected. Answering based on available documents..."
            })

    # Proceed with agent workflow
    ready_docs = [d for d in accessible_docs if d.status == "ready"]

    agent = DocumentQAAgent(
        user_id=current_user.id,
        accessible_documents=[d.id for d in ready_docs],
        systems_filter=message_request.system_filters,
        websocket=websocket
    )

    response = await agent.run(message_request.content)

    # Save message and log analytics (same as before)
    # ...
```

#### Part 3: Analytics & Compliance Logging

**Every interaction is logged:**

```python
# After agent responds
qa_log = QAAnalytics(
    user_id=current_user.id,
    conversation_id=conversation.id,
    message_id=assistant_message.id,
    question=message_request.content,
    answer=response.content,
    documents_used=response.document_ids,
    tags_used=message_request.system_filters,
    response_time_ms=response.time_ms,
    token_count=response.tokens,
    created_at=datetime.now()
)
db.add(qa_log)

# Log agent execution details
agent_log = AgentExecutionLog(
    message_id=assistant_message.id,
    user_id=current_user.id,
    execution_plan=response.plan,  # JSON of agent's planned steps
    executed_steps=response.executed_steps,  # What agent actually did
    tools_used=response.tools,  # Which tools were invoked
    documents_retrieved=response.retrieved_docs,  # Which chunks
    success=True,
    execution_time_ms=response.time_ms,
    llm_calls_count=response.llm_calls,
    created_at=datetime.now()
)
db.add(agent_log)

# User feedback (captured later when user rates)
# User clicks thumbs up/down
@router.post("/feedback")
async def submit_feedback(
    message_id: str,
    feedback_type: str,  # "helpful", "not_helpful", "incorrect"
    comment: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    feedback = UserFeedback(
        user_id=current_user.id,
        message_id=message_id,
        feedback_type=feedback_type,
        comment=comment,
        created_at=datetime.now()
    )
    db.add(feedback)

    # Update qa_analytics
    qa_log = db.query(QAAnalytics).filter(
        QAAnalytics.message_id == message_id
    ).first()

    if qa_log:
        qa_log.user_feedback = feedback_type
        qa_log.feedback_text = comment

    db.commit()
    return {"status": "success"}
```

**Database Changes:**
```sql
-- Personal document
INSERT INTO documents (id, title, file_path, system_id, uploaded_by, status)
VALUES ('doc-personal-1', 'vendor_contract_2024.pdf', 's3://personal/bob/...',
        'system-personal-bob', 'user-bob', 'ready');

-- Auto-generated tags
INSERT INTO tags (id, name, system_id) VALUES ('tag-contract', 'Contract', 'system-personal-bob');
INSERT INTO tags (id, name, system_id) VALUES ('tag-2024', '2024', 'system-personal-bob');
INSERT INTO document_tags VALUES ('doc-personal-1', 'tag-contract');
INSERT INTO document_tags VALUES ('doc-personal-1', 'tag-2024');

-- Q&A Analytics
INSERT INTO qa_analytics (user_id, message_id, question, answer, documents_used,
                          tags_used, response_time_ms, user_feedback)
VALUES ('user-bob', 'msg-789', 'What are the payment terms?',
        'The payment terms are Net 30...', '["doc-personal-1"]',
        '["personal"]', 1500, 'helpful');

-- Agent execution log
INSERT INTO agent_execution_logs (message_id, user_id, execution_plan, tools_used,
                                  documents_retrieved, success, execution_time_ms)
VALUES ('msg-789', 'user-bob',
        '{"steps": ["retrieve", "analyze", "synthesize"]}',
        '["semantic_search", "llm_analyze"]',
        '{"doc-personal-1": ["chunk-1", "chunk-5"]}',
        true, 1500);

-- User feedback
INSERT INTO user_feedback (user_id, message_id, feedback_type, comment)
VALUES ('user-bob', 'msg-789', 'helpful', 'Exactly what I needed!');
```

---

## Use Case 3: Rich Export & Editing

### User Story
**CFO** queries quarterly reports → Gets professional analysis with charts → Edits in UI → Exports as PDF

### Technical Flow

#### Part 1: Generate Rich Output

**Agent Response Generation with Rich Content:**

```python
class DocumentQAAgent:
    """Enhanced agent with rich output generation."""

    async def synthesize_answer(self, state: AgentState):
        """Generate rich, professional output."""

        # Call LLM with structured output prompt
        prompt = f"""You are a professional financial analyst. Generate a comprehensive analysis.

Context: {state.context}
Question: {state.question}

Output Format:
1. Executive Summary (2-3 sentences)
2. Key Findings (bullet points with data)
3. Data Tables (if applicable)
4. Chart Specifications (JSON format for frontend rendering)
5. Detailed Analysis
6. Recommendations
7. Source Citations

For charts, provide JSON specs like:
{{
  "type": "line",
  "title": "Revenue Trend Q1 2023 - Q4 2024",
  "data": {{
    "labels": ["Q1 2023", "Q2 2023", ...],
    "datasets": [{{
      "label": "Revenue ($M)",
      "data": [45.2, 48.1, ...]
    }}]
  }},
  "options": {{
    "yAxisLabel": "Revenue ($ Millions)",
    "showLegend": true
  }}
}}

Use markdown formatting with headers, bold, tables, etc.
"""

        llm_response = await llm.ainvoke(prompt)

        # Parse response to extract charts, tables, etc.
        parsed_response = parse_rich_content(llm_response)

        return AgentResponse(
            content=parsed_response.markdown,
            has_formatting=True,
            render_format="markdown",
            charts=parsed_response.charts,  # List of chart specs
            tables=parsed_response.tables,  # Structured table data
            sources=state.sources,
            # ... other fields
        )


def parse_rich_content(llm_response: str) -> RichContent:
    """Parse LLM response to extract structured content."""

    # Extract chart JSON blocks
    chart_pattern = r'```chart\n(.*?)\n```'
    charts = []
    for match in re.finditer(chart_pattern, llm_response, re.DOTALL):
        try:
            chart_spec = json.loads(match.group(1))
            charts.append(chart_spec)
            # Replace in markdown with placeholder
            llm_response = llm_response.replace(
                match.group(0),
                f'[CHART:{len(charts)-1}]'
            )
        except json.JSONDecodeError:
            pass

    # Extract tables
    table_pattern = r'\|(.+)\|'
    # ... parse markdown tables

    return RichContent(
        markdown=llm_response,
        charts=charts,
        tables=tables
    )
```

**Save Message with Rich Content:**

```python
assistant_message = Message(
    conversation_id=conversation.id,
    role="assistant",
    content=response.content,  # Markdown with placeholders
    is_rich_content=True,
    render_format="markdown",
    metadata={
        "documents_used": response.document_ids,
        "sources": response.sources,
        "charts": response.charts,  # Chart specifications
        "tables": response.tables,  # Table data
        "agent_steps": response.steps
    }
)
db.add(assistant_message)
db.commit()
```

#### Part 2: Frontend Rich Rendering

**Frontend (React):**
```typescript
// Component: RichMessageDisplay
interface MessageData {
  content: string;  // Markdown with [CHART:0] placeholders
  metadata: {
    charts?: ChartSpec[];
    tables?: TableData[];
    sources?: Source[];
  };
}

export const RichMessageDisplay: React.FC<{ message: MessageData }> = ({ message }) => {
  // Replace chart placeholders with actual charts
  const renderContent = () => {
    let content = message.content;

    // Replace [CHART:0], [CHART:1], etc. with actual chart components
    message.metadata.charts?.forEach((chart, index) => {
      const placeholder = `[CHART:${index}]`;
      content = content.replace(
        placeholder,
        `<ChartPlaceholder id="${index}" />`
      );
    });

    return content;
  };

  return (
    <div className="rich-message">
      {/* Render markdown with custom components */}
      <ReactMarkdown
        components={{
          // Custom renderers
          h1: ({ children }) => (
            <h1 className="text-3xl font-bold mb-4">{children}</h1>
          ),
          table: ({ children }) => (
            <table className="border-collapse w-full my-4">
              {children}
            </table>
          ),
          code: CodeBlock,  // Syntax highlighting
          // Custom component for chart placeholders
          ChartPlaceholder: ({ id }) => (
            <ChartRenderer spec={message.metadata.charts[id]} />
          )
        }}
      >
        {renderContent()}
      </ReactMarkdown>

      {/* Source citations */}
      <SourceCitations sources={message.metadata.sources} />

      {/* Action buttons */}
      <div className="message-actions">
        <button onClick={() => setEditMode(true)}>
          ✏️ Edit
        </button>
        <button onClick={() => handleExport('pdf')}>
          📄 Export PDF
        </button>
        <button onClick={() => handleExport('markdown')}>
          📝 Export Markdown
        </button>
      </div>
    </div>
  );
};

// Chart renderer using Recharts
const ChartRenderer: React.FC<{ spec: ChartSpec }> = ({ spec }) => {
  if (spec.type === 'line') {
    return (
      <LineChart width={600} height={300} data={spec.data}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="label" />
        <YAxis label={{ value: spec.options.yAxisLabel, angle: -90 }} />
        <Tooltip />
        {spec.options.showLegend && <Legend />}
        {spec.data.datasets.map((dataset, i) => (
          <Line
            key={i}
            type="monotone"
            dataKey="data"
            data={dataset.data}
            name={dataset.label}
            stroke={CHART_COLORS[i]}
          />
        ))}
      </LineChart>
    );
  }
  // ... other chart types
};
```

#### Part 3: In-UI Editing

**Edit Mode:**

```typescript
// Component: MessageEditor
export const MessageEditor: React.FC<{ message: MessageData, onSave }> = ({ message, onSave }) => {
  const [content, setContent] = useState(message.content);
  const [editReason, setEditReason] = useState('');

  const handleSave = async () => {
    const response = await fetch(`/api/v1/messages/${message.id}/edit`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        edited_content: content,
        edit_reason: editReason
      })
    });

    const data = await response.json();
    onSave(data.message);
  };

  return (
    <div className="message-editor">
      {/* Rich text editor (TipTap) */}
      <TipTapEditor
        content={content}
        onChange={setContent}
        extensions={[
          StarterKit,
          Table,
          Image,
          CodeBlock,
          Markdown  // Support markdown
        ]}
      />

      {/* Edit reason */}
      <textarea
        placeholder="Why are you editing? (optional)"
        value={editReason}
        onChange={(e) => setEditReason(e.target.value)}
      />

      {/* Actions */}
      <button onClick={handleSave}>Save Changes</button>
      <button onClick={() => setEditMode(false)}>Cancel</button>
    </div>
  );
};
```

**Backend Edit Endpoint:**

```python
@router.post("/messages/{message_id}/edit")
async def edit_message(
    message_id: str,
    edit_data: MessageEditRequest,
    current_user: User = Depends(get_current_user)
):
    """Edit an AI-generated message."""

    message = db.query(Message).get(message_id)

    # Check permission (user must own the conversation)
    if message.conversation.user_id != current_user.id:
        raise HTTPException(403, "Not your message")

    # Get current version number
    latest_edit = (
        db.query(MessageEdit)
        .filter(MessageEdit.message_id == message_id)
        .order_by(MessageEdit.version_number.desc())
        .first()
    )
    new_version = (latest_edit.version_number + 1) if latest_edit else 1

    # Save edit
    edit = MessageEdit(
        message_id=message_id,
        edited_by=current_user.id,
        original_content=message.content,
        edited_content=edit_data.edited_content,
        edit_reason=edit_data.edit_reason,
        edited_at=datetime.now(),
        version_number=new_version
    )
    db.add(edit)

    # Update message
    message.content = edit_data.edited_content
    message.metadata['edited'] = True
    message.metadata['edit_count'] = new_version

    db.commit()

    return {"message": message, "edit": edit}
```

**Database Changes:**
```sql
-- Message edit tracking
INSERT INTO message_edits (id, message_id, edited_by, original_content,
                           edited_content, edit_reason, version_number)
VALUES ('edit-1', 'msg-456', 'user-cfo',
        'Original AI-generated content...',
        'CFO edited content...',
        'Added context about market conditions',
        1);

-- Update message
UPDATE messages
SET content = 'CFO edited content...',
    metadata = jsonb_set(metadata, '{edited}', 'true')
WHERE id = 'msg-456';
```

#### Part 4: Export as PDF/Markdown

**Export Endpoint:**

```python
@router.post("/messages/{message_id}/export")
async def export_message(
    message_id: str,
    format: str,  # "pdf" or "markdown"
    current_user: User = Depends(get_current_user)
):
    """Export message as PDF or Markdown."""

    message = db.query(Message).get(message_id)

    if format == "pdf":
        # Generate PDF
        pdf_path = await generate_pdf_report(message, current_user)

    elif format == "markdown":
        # Generate Markdown file
        md_content = generate_markdown_export(message)
        md_path = await storage.save_file_content(
            md_content,
            f"exports/{current_user.id}/{message_id}.md"
        )
        pdf_path = md_path

    # Track export
    export = Export(
        message_id=message_id,
        user_id=current_user.id,
        export_format=format,
        file_path=pdf_path,
        was_edited=message.metadata.get('edited', False),
        exported_at=datetime.now(),
        download_count=0
    )
    db.add(export)
    db.commit()

    # Return download link
    download_url = storage.get_presigned_url(pdf_path, expires_in=3600)

    return {
        "export_id": export.id,
        "download_url": download_url,
        "format": format
    }


async def generate_pdf_report(message: Message, user: User) -> str:
    """Generate professional PDF from message."""

    # Create HTML from markdown
    html_content = markdown_to_html(message.content)

    # Render charts as images
    charts_html = []
    for i, chart_spec in enumerate(message.metadata.get('charts', [])):
        # Use headless browser to render chart
        chart_image = await render_chart_to_image(chart_spec)
        charts_html.append(f'<img src="{chart_image}" />')

    # Replace chart placeholders
    for i, chart_html in enumerate(charts_html):
        html_content = html_content.replace(f'[CHART:{i}]', chart_html)

    # Apply professional styling
    full_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            @page {{ margin: 1in; }}
            body {{
                font-family: 'Helvetica', 'Arial', sans-serif;
                font-size: 11pt;
                line-height: 1.6;
                color: #333;
            }}
            h1 {{ font-size: 24pt; margin-bottom: 12pt; }}
            h2 {{ font-size: 18pt; margin-top: 24pt; margin-bottom: 8pt; }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin: 12pt 0;
            }}
            th, td {{
                border: 1px solid #ddd;
                padding: 8pt;
                text-align: left;
            }}
            .footer {{
                margin-top: 48pt;
                font-size: 9pt;
                color: #666;
                border-top: 1px solid #ddd;
                padding-top: 12pt;
            }}
        </style>
    </head>
    <body>
        {html_content}
        <div class="footer">
            Generated by Ask My Docs | User: {user.name} | Date: {datetime.now().strftime('%Y-%m-%d')}
            {' | Edited by User' if message.metadata.get('edited') else ' | AI Generated'}
        </div>
    </body>
    </html>
    """

    # Convert HTML to PDF using WeasyPrint
    pdf_bytes = HTML(string=full_html).write_pdf()

    # Save to S3
    pdf_path = f"exports/{user.id}/{message.id}.pdf"
    await storage.save_bytes(pdf_bytes, pdf_path)

    return pdf_path
```

**Database Changes:**
```sql
-- Export tracking
INSERT INTO exports (id, message_id, user_id, export_format, file_path,
                     was_edited, exported_at, download_count)
VALUES ('export-1', 'msg-456', 'user-cfo', 'pdf',
        's3://exports/cfo/msg-456.pdf', true, NOW(), 0);
```

---

## Summary of All 3 Use Cases

### **Use Case 1: System Documentation Q&A**
✅ Document Manager uploads → Users query by system → Persistent across sessions → Full analytics

### **Use Case 2: Instant Personal Upload**
✅ Upload in chat → Auto-tag → Query immediately (even while processing) → All logged for compliance

### **Use Case 3: Rich Export & Editing**
✅ Agent generates professional output with charts → User edits in rich text editor → Export as PDF/Markdown → Version tracking

---

## Discussion Questions for You:

Before I continue with the database schema design, let me get your feedback:

2. **Permission Filtering**: I designed two layers:
   - Database query filters accessible documents
   - Vector DB metadata filters during search

   Is this the right approach, or should we filter differently?

3. **Agent Framework**: I showed LangGraph for orchestration. Does this match your vision, or prefer simpler approach?

4. **Chunking Strategy**: I proposed semantic chunking with 1000 chars + 200 overlap. Good default?

### Data Flow Questions:
5. **Conversation Management**: Should users always see history and choose to continue or start new?

6. **Analytics Logging**: I'm logging every Q&A. Should we also log failed queries, partial responses?

7. **Background Processing**: Documents process async via Celery. Should we notify user when done, or just show status on dashboard?

### What Would You Like Me to Adjust?

Please review the above design for Use Case 1 and let me know:
- ✅ What looks good?
- ⚠️ What needs changes?
- ❓ What needs more detail?

Then I'll continue with Use Case 2 (Instant Personal Upload) and Use Case 3 (Rich Export & Editing) with your feedback incorporated!