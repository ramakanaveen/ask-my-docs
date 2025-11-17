# Database Documentation

Database schema, migrations, and data models for Ask My Docs.

## 📑 Documents

- **[schema.md](schema.md)** - Complete database schema with all tables ✅
- **[migrations.md](migrations.md)** - Migration strategy and versioning *(Coming soon)*
- **[data-models.md](data-models.md)** - SQLAlchemy/Pydantic models *(Coming soon)*

## 🗄️ Database Overview

### Primary Database: PostgreSQL
- User accounts and authentication
- Document metadata and tags
- Permissions and access control
- Sessions and conversations
- Q&A analytics and audit logs
- Message edits and version history

### Vector Database: ChromaDB/Pinecone
- Document embeddings
- Semantic search
- Metadata filtering by tags and permissions

### Object Storage: S3/Cloud Storage
- Original document files
- Generated reports (PDF, Markdown)
- Chart images and visualizations

## 🎯 Key Tables

### Core Tables
- `users` - User accounts and roles (admin, doc_manager, system_user, super_user)
- `systems` - System collections (with personal system support)
- `user_systems` - User-system assignments with granular permissions
- `documents` - Document metadata with version tracking
- `tags` - Optional tags within systems
- `document_tags` - Many-to-many relationship
- `document_chunks` - Chunked content synced with vector DB

### Conversation & Messaging
- `conversations` - Chat sessions with system filters
- `messages` - Questions and answers with rich content
- `message_edits` - Full version history with edit tracking

### Deep Agents Execution
- `agent_executions` - Agent execution tracking with HITL support
- `agent_filesystem` - Deep Agents filesystem for intermediate results

### Analytics & Compliance
- `qa_analytics` - Comprehensive Q&A metrics and performance
- `user_feedback` - User ratings and corrections
- `audit_logs` - Full audit trail for compliance

### Export & Features
- `exports` - Generated PDFs/Markdown with professional formatting

---

*Last updated: 2025-11-15*
