# API Documentation

API specifications for REST endpoints, WebSocket, and MCP server.

## 📑 Documents

- **[rest-api.md](rest-api.md)** - RESTful API endpoints ✅
- **[websocket-api.md](websocket-api.md)** - WebSocket events for real-time updates ✅
- **[mcp-server.md](mcp-server.md)** - MCP (Model Context Protocol) server spec *(Coming soon)*

## 🔌 API Overview

### REST API (FastAPI)
Base URL: `/api/v1`

**Endpoint Groups:**
- `/auth` - Authentication (register, login, logout, refresh)
- `/users` - User profile and management
- `/systems` - System collections and assignments
- `/documents` - Document upload, management, download
- `/tags` - Tag creation and management within systems
- `/conversations` - Conversation (session) management
- `/messages` - Send questions, receive answers, edit responses
- `/agent-executions` - Agent execution tracking and HITL approval
- `/exports` - Generate and download PDF/Markdown reports
- `/analytics` - System-wide and user-specific analytics (admin)
- `/feedback` - User feedback and ratings

### WebSocket
Connection: `/ws?token=<jwt_token>`

**Channels:**
- `user:notifications` - General user notifications
- `document:processing` - Document processing status updates
- `execution:<execution_id>` - Agent execution progress
- `export:<export_id>` - Export generation progress
- `conversation:<conversation_id>` - Conversation updates
- `system:<system_id>` - System-wide updates (admin)

### MCP Server
Exposes Ask My Docs capabilities as MCP tools for integration with other systems:
- Document querying
- Collection management
- Analytics access

## 🔐 Authentication

All endpoints require JWT authentication except:
- `POST /auth/login`
- `POST /auth/signup` (if enabled)

Headers:
```
Authorization: Bearer <jwt_token>
```

## 📝 Response Format

Success:
```json
{
  "status": "success",
  "data": { ... }
}
```

Error:
```json
{
  "status": "error",
  "message": "Error description",
  "code": "ERROR_CODE"
}
```

---

*Last updated: 2025-11-15*
