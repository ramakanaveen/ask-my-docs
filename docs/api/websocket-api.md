# WebSocket API Specification

Real-time WebSocket events for Ask My Docs.

## Connection

### Endpoint

```
Development: ws://localhost:8000/ws
Production: wss://api.askmydocs.com/ws
```

### Authentication

Include JWT token in connection query parameter:
```
ws://localhost:8000/ws?token=<jwt_token>
```

Or in first message after connection:
```json
{
  "type": "auth",
  "token": "<jwt_token>"
}
```

### Connection Flow

```javascript
// Client-side example
const ws = new WebSocket('ws://localhost:8000/ws?token=' + jwtToken);

ws.onopen = () => {
  console.log('Connected to WebSocket');

  // Subscribe to channels
  ws.send(JSON.stringify({
    type: 'subscribe',
    channels: ['user:notifications', 'document:processing']
  }));
};

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  handleWebSocketMessage(message);
};

ws.onerror = (error) => {
  console.error('WebSocket error:', error);
};

ws.onclose = () => {
  console.log('WebSocket disconnected');
  // Implement reconnection logic
};
```

---

## Channels

Users can subscribe to multiple channels to receive relevant real-time updates.

### Available Channels

1. **`user:notifications`** - General user notifications
2. **`document:processing`** - Document processing status updates
3. **`execution:<execution_id>`** - Specific agent execution progress
4. **`export:<export_id>`** - Specific export generation progress
5. **`conversation:<conversation_id>`** - Conversation updates
6. **`system:<system_id>`** - System-wide updates (admin only)

---

## Message Types

### Client → Server Messages

#### 1. Subscribe to Channels

```json
{
  "type": "subscribe",
  "channels": [
    "user:notifications",
    "document:processing",
    "execution:abc-123"
  ]
}
```

**Server Response:**
```json
{
  "type": "subscribed",
  "channels": [
    "user:notifications",
    "document:processing",
    "execution:abc-123"
  ],
  "timestamp": "2024-01-20T11:00:00Z"
}
```

---

#### 2. Unsubscribe from Channels

```json
{
  "type": "unsubscribe",
  "channels": ["execution:abc-123"]
}
```

**Server Response:**
```json
{
  "type": "unsubscribed",
  "channels": ["execution:abc-123"],
  "timestamp": "2024-01-20T11:00:00Z"
}
```

---

#### 3. Ping (Keep-Alive)

```json
{
  "type": "ping"
}
```

**Server Response:**
```json
{
  "type": "pong",
  "timestamp": "2024-01-20T11:00:00Z"
}
```

---

### Server → Client Messages

## 1. Document Processing Events

### Document Processing Started

```json
{
  "type": "document.processing.started",
  "channel": "document:processing",
  "data": {
    "document_id": "uuid",
    "filename": "system_a_install.pdf",
    "system_id": "system-a-uuid",
    "system_name": "System A",
    "status": "processing",
    "started_at": "2024-01-20T10:00:00Z"
  },
  "timestamp": "2024-01-20T10:00:00Z"
}
```

---

### Document Processing Progress

```json
{
  "type": "document.processing.progress",
  "channel": "document:processing",
  "data": {
    "document_id": "uuid",
    "filename": "system_a_install.pdf",
    "status": "processing",
    "progress": {
      "current_step": "embedding",
      "steps_completed": 2,
      "total_steps": 4,
      "percentage": 50,
      "message": "Generating embeddings for chunks..."
    },
    "pages_processed": 23,
    "total_pages": 45
  },
  "timestamp": "2024-01-20T10:01:15Z"
}
```

**Processing Steps:**
1. `extracting` - Extracting text from document
2. `chunking` - Splitting into semantic chunks
3. `embedding` - Generating embeddings
4. `indexing` - Storing in vector database

---

### Document Processing Completed

```json
{
  "type": "document.processing.completed",
  "channel": "document:processing",
  "data": {
    "document_id": "uuid",
    "filename": "system_a_install.pdf",
    "system_id": "system-a-uuid",
    "system_name": "System A",
    "status": "ready",
    "completed_at": "2024-01-20T10:02:30Z",
    "processing_duration_ms": 150000,
    "stats": {
      "page_count": 45,
      "word_count": 12500,
      "chunk_count": 89,
      "embedding_count": 89
    },
    "auto_generated_tags": ["Installation", "Linux", "Technical"]
  },
  "timestamp": "2024-01-20T10:02:30Z"
}
```

---

### Document Processing Failed

```json
{
  "type": "document.processing.failed",
  "channel": "document:processing",
  "data": {
    "document_id": "uuid",
    "filename": "corrupted_file.pdf",
    "status": "failed",
    "error": {
      "code": "extraction_error",
      "message": "Unable to extract text from PDF. File may be corrupted.",
      "details": "PyMuPDF error: Invalid PDF structure"
    },
    "failed_at": "2024-01-20T10:00:45Z"
  },
  "timestamp": "2024-01-20T10:00:45Z"
}
```

---

## 2. Agent Execution Events

### Agent Execution Started

```json
{
  "type": "agent.execution.started",
  "channel": "execution:abc-123",
  "data": {
    "execution_id": "abc-123",
    "conversation_id": "uuid",
    "agent_type": "complex",
    "model_name": "claude-sonnet-4",
    "planning_enabled": true,
    "filesystem_enabled": true,
    "status": "running",
    "started_at": "2024-01-20T11:00:00Z"
  },
  "timestamp": "2024-01-20T11:00:00Z"
}
```

---

### Agent Planning Phase

```json
{
  "type": "agent.execution.planning",
  "channel": "execution:abc-123",
  "data": {
    "execution_id": "abc-123",
    "status": "planning",
    "message": "Creating execution plan...",
    "plan": {
      "todos": [
        {
          "content": "Extract financial data from Q1 2023 report",
          "status": "pending",
          "activeForm": "Extracting financial data from Q1 2023 report"
        },
        {
          "content": "Extract financial data from Q2 2023 report",
          "status": "pending",
          "activeForm": "Extracting financial data from Q2 2023 report"
        },
        {
          "content": "Calculate YoY growth rates",
          "status": "pending",
          "activeForm": "Calculating YoY growth rates"
        },
        {
          "content": "Generate trend visualizations",
          "status": "pending",
          "activeForm": "Generating trend visualizations"
        }
      ]
    }
  },
  "timestamp": "2024-01-20T11:00:05Z"
}
```

---

### Agent Awaiting Human Approval (HITL)

```json
{
  "type": "agent.execution.awaiting_approval",
  "channel": "execution:abc-123",
  "data": {
    "execution_id": "abc-123",
    "status": "paused",
    "message": "Agent has created a plan and is awaiting your approval",
    "plan": {
      "todos": [...]  // Same structure as planning phase
    },
    "approval_required": true,
    "paused_at": "2024-01-20T11:00:10Z",
    "approval_url": "/api/v1/agent-executions/abc-123/approve"
  },
  "timestamp": "2024-01-20T11:00:10Z"
}
```

---

### Agent Plan Approved

```json
{
  "type": "agent.execution.approved",
  "channel": "execution:abc-123",
  "data": {
    "execution_id": "abc-123",
    "status": "running",
    "message": "Plan approved. Agent resuming execution...",
    "approved_by": "david-uuid",
    "approved_at": "2024-01-20T11:00:30Z"
  },
  "timestamp": "2024-01-20T11:00:30Z"
}
```

---

### Agent Execution Progress

```json
{
  "type": "agent.execution.progress",
  "channel": "execution:abc-123",
  "data": {
    "execution_id": "abc-123",
    "status": "running",
    "current_step": {
      "step_number": 2,
      "total_steps": 4,
      "todo_index": 1,
      "todo_content": "Extract financial data from Q2 2023 report",
      "status": "in_progress",
      "message": "Spawning pdf-extraction-agent for Q2 2023..."
    },
    "completed_todos": [
      {
        "content": "Extract financial data from Q1 2023 report",
        "status": "completed",
        "completed_at": "2024-01-20T11:00:45Z"
      }
    ],
    "tools_used": [
      {
        "tool_name": "semantic_search",
        "timestamp": "2024-01-20T11:00:32Z",
        "duration_ms": 234
      },
      {
        "tool_name": "extract_pdf_tables",
        "timestamp": "2024-01-20T11:00:40Z",
        "duration_ms": 1250
      }
    ]
  },
  "timestamp": "2024-01-20T11:01:00Z"
}
```

---

### Agent Subagent Spawned

```json
{
  "type": "agent.subagent.spawned",
  "channel": "execution:abc-123",
  "data": {
    "execution_id": "abc-123",
    "subagent_name": "pdf-extraction-agent",
    "subagent_description": "Extract financial tables and data from PDF quarterly reports",
    "task": "Extract Q2 2023 financial data",
    "spawned_at": "2024-01-20T11:01:00Z"
  },
  "timestamp": "2024-01-20T11:01:00Z"
}
```

---

### Agent Subagent Completed

```json
{
  "type": "agent.subagent.completed",
  "channel": "execution:abc-123",
  "data": {
    "execution_id": "abc-123",
    "subagent_name": "pdf-extraction-agent",
    "task": "Extract Q2 2023 financial data",
    "result_summary": "Extracted 15 financial metrics from 8 pages",
    "output_files": ["q2_2023_data.json"],
    "completed_at": "2024-01-20T11:01:30Z",
    "duration_ms": 30000
  },
  "timestamp": "2024-01-20T11:01:30Z"
}
```

---

### Agent Filesystem Operation

```json
{
  "type": "agent.filesystem.operation",
  "channel": "execution:abc-123",
  "data": {
    "execution_id": "abc-123",
    "operation": "write",  // or "read", "delete"
    "file_path": "q2_2023_data.json",
    "file_size_bytes": 5420,
    "description": "Stored Q2 2023 extracted financial data",
    "timestamp": "2024-01-20T11:01:35Z"
  },
  "timestamp": "2024-01-20T11:01:35Z"
}
```

---

### Agent Execution Completed

```json
{
  "type": "agent.execution.completed",
  "channel": "execution:abc-123",
  "data": {
    "execution_id": "abc-123",
    "conversation_id": "uuid",
    "message_id": "uuid",  // The generated assistant message
    "status": "completed",
    "completed_at": "2024-01-20T11:02:45Z",
    "total_duration_ms": 165000,
    "stats": {
      "todos_completed": 4,
      "llm_calls": 12,
      "total_tokens": 45000,
      "subagents_used": 3,
      "tools_called": 15,
      "files_created": 4
    },
    "result": {
      "message_preview": "Based on analysis of Q1-Q4 2023 financial reports...",
      "has_rich_content": true,
      "citation_count": 8
    }
  },
  "timestamp": "2024-01-20T11:02:45Z"
}
```

---

### Agent Execution Failed

```json
{
  "type": "agent.execution.failed",
  "channel": "execution:abc-123",
  "data": {
    "execution_id": "abc-123",
    "status": "failed",
    "error": {
      "code": "tool_execution_error",
      "message": "Failed to extract PDF tables",
      "details": "Document is password-protected",
      "occurred_at_step": 2,
      "failed_todo": "Extract financial data from Q2 2023 report"
    },
    "failed_at": "2024-01-20T11:01:00Z"
  },
  "timestamp": "2024-01-20T11:01:00Z"
}
```

---

## 3. Export Events

### Export Generation Started

```json
{
  "type": "export.generation.started",
  "channel": "export:xyz-789",
  "data": {
    "export_id": "xyz-789",
    "message_id": "uuid",
    "export_format": "pdf",
    "status": "pending",
    "started_at": "2024-01-20T12:00:00Z"
  },
  "timestamp": "2024-01-20T12:00:00Z"
}
```

---

### Export Generation Progress

```json
{
  "type": "export.generation.progress",
  "channel": "export:xyz-789",
  "data": {
    "export_id": "xyz-789",
    "status": "generating",
    "progress": {
      "current_step": "rendering_charts",
      "steps_completed": 2,
      "total_steps": 5,
      "percentage": 40,
      "message": "Rendering charts as images..."
    }
  },
  "timestamp": "2024-01-20T12:00:20Z"
}
```

**Export Steps:**
1. `preparing` - Preparing content and metadata
2. `rendering_charts` - Converting charts to images
3. `applying_styles` - Applying professional styling
4. `generating_pdf` - Creating PDF file
5. `uploading` - Uploading to storage

---

### Export Generation Completed

```json
{
  "type": "export.generation.completed",
  "channel": "export:xyz-789",
  "data": {
    "export_id": "xyz-789",
    "message_id": "uuid",
    "export_format": "pdf",
    "status": "completed",
    "file_size_bytes": 1245000,
    "download_url": "/api/v1/exports/xyz-789/download",
    "expires_at": "2024-02-19T12:00:45Z",
    "completed_at": "2024-01-20T12:00:45Z",
    "generation_duration_ms": 45000
  },
  "timestamp": "2024-01-20T12:00:45Z"
}
```

---

### Export Generation Failed

```json
{
  "type": "export.generation.failed",
  "channel": "export:xyz-789",
  "data": {
    "export_id": "xyz-789",
    "status": "failed",
    "error": {
      "code": "chart_rendering_error",
      "message": "Failed to render chart as image",
      "details": "Headless browser timeout"
    },
    "failed_at": "2024-01-20T12:00:25Z"
  },
  "timestamp": "2024-01-20T12:00:25Z"
}
```

---

## 4. Conversation Events

### New Message in Conversation

```json
{
  "type": "conversation.message.new",
  "channel": "conversation:uuid",
  "data": {
    "conversation_id": "uuid",
    "message": {
      "id": "uuid",
      "role": "assistant",
      "content": "To install System A on Ubuntu...",
      "rich_content": {...},
      "source_documents": [...],
      "created_at": "2024-01-20T11:00:15Z"
    }
  },
  "timestamp": "2024-01-20T11:00:15Z"
}
```

---

### Message Edited

```json
{
  "type": "conversation.message.edited",
  "channel": "conversation:uuid",
  "data": {
    "conversation_id": "uuid",
    "message_id": "uuid",
    "new_version": 2,
    "edited_by": {
      "id": "uuid",
      "username": "david",
      "full_name": "David Chen"
    },
    "edited_at": "2024-01-20T12:00:00Z",
    "edit_reason": "Updated for Ubuntu 22.04 specifically"
  },
  "timestamp": "2024-01-20T12:00:00Z"
}
```

---

## 5. User Notification Events

### General Notification

```json
{
  "type": "notification",
  "channel": "user:notifications",
  "data": {
    "notification_id": "uuid",
    "title": "Document processing completed",
    "message": "Your document 'system_a_install.pdf' is ready for querying",
    "notification_type": "success",  // or "info", "warning", "error"
    "action": {
      "type": "view_document",
      "url": "/documents/uuid",
      "label": "View Document"
    },
    "created_at": "2024-01-20T10:02:30Z"
  },
  "timestamp": "2024-01-20T10:02:30Z"
}
```

---

### System Announcement (Admin Only)

```json
{
  "type": "system.announcement",
  "channel": "system:system-a-uuid",
  "data": {
    "announcement_id": "uuid",
    "title": "System A documentation updated",
    "message": "New v2.5 documentation has been uploaded",
    "severity": "info",  // or "warning", "critical"
    "affected_users": "all",  // or specific user list
    "created_at": "2024-01-20T10:00:00Z"
  },
  "timestamp": "2024-01-20T10:00:00Z"
}
```

---

## 6. Error Events

### Permission Error

```json
{
  "type": "error",
  "data": {
    "error_code": "permission_denied",
    "message": "You don't have permission to upload documents to this system",
    "details": {
      "required_permission": "can_upload",
      "system_id": "uuid",
      "system_name": "System A"
    }
  },
  "timestamp": "2024-01-20T11:00:00Z"
}
```

---

### Rate Limit Error

```json
{
  "type": "error",
  "data": {
    "error_code": "rate_limit_exceeded",
    "message": "Too many messages sent. Please wait before sending another.",
    "retry_after": 60  // seconds
  },
  "timestamp": "2024-01-20T11:00:00Z"
}
```

---

## Connection Management

### Server Disconnection Notice

```json
{
  "type": "server.disconnecting",
  "data": {
    "reason": "maintenance",
    "message": "Server is restarting for maintenance. Please reconnect in 30 seconds.",
    "reconnect_after": 30
  },
  "timestamp": "2024-01-20T11:00:00Z"
}
```

---

## Client-Side Implementation Examples

### React Hook Example

```typescript
import { useEffect, useState } from 'react';

interface WebSocketMessage {
  type: string;
  channel?: string;
  data: any;
  timestamp: string;
}

export function useWebSocket(token: string, channels: string[]) {
  const [ws, setWs] = useState<WebSocket | null>(null);
  const [messages, setMessages] = useState<WebSocketMessage[]>([]);
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    const websocket = new WebSocket(`ws://localhost:8000/ws?token=${token}`);

    websocket.onopen = () => {
      console.log('WebSocket connected');
      setConnected(true);

      // Subscribe to channels
      websocket.send(JSON.stringify({
        type: 'subscribe',
        channels: channels
      }));
    };

    websocket.onmessage = (event) => {
      const message: WebSocketMessage = JSON.parse(event.data);
      setMessages(prev => [...prev, message]);
    };

    websocket.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    websocket.onclose = () => {
      console.log('WebSocket disconnected');
      setConnected(false);

      // Implement reconnection logic
      setTimeout(() => {
        console.log('Attempting to reconnect...');
        // Reconnect logic here
      }, 3000);
    };

    setWs(websocket);

    return () => {
      websocket.close();
    };
  }, [token, channels]);

  const sendMessage = (message: any) => {
    if (ws && connected) {
      ws.send(JSON.stringify(message));
    }
  };

  return { ws, messages, connected, sendMessage };
}
```

---

### Usage in Component

```typescript
import { useWebSocket } from './hooks/useWebSocket';

function DocumentUploadPage() {
  const { messages, connected } = useWebSocket(
    jwtToken,
    ['user:notifications', 'document:processing']
  );

  useEffect(() => {
    messages.forEach(message => {
      if (message.type === 'document.processing.completed') {
        toast.success(`Document ${message.data.filename} is ready!`);
      } else if (message.type === 'document.processing.failed') {
        toast.error(`Failed to process ${message.data.filename}`);
      }
    });
  }, [messages]);

  return (
    <div>
      <div>Status: {connected ? 'Connected' : 'Disconnected'}</div>
      {/* Rest of component */}
    </div>
  );
}
```

---

### Agent Execution Progress Display

```typescript
function AgentExecutionProgress({ executionId }: { executionId: string }) {
  const { messages } = useWebSocket(
    jwtToken,
    [`execution:${executionId}`]
  );

  const [status, setStatus] = useState<string>('running');
  const [currentStep, setCurrentStep] = useState<any>(null);
  const [plan, setPlan] = useState<any>(null);

  useEffect(() => {
    messages.forEach(message => {
      switch (message.type) {
        case 'agent.execution.planning':
          setPlan(message.data.plan);
          break;

        case 'agent.execution.awaiting_approval':
          setStatus('awaiting_approval');
          setPlan(message.data.plan);
          break;

        case 'agent.execution.progress':
          setCurrentStep(message.data.current_step);
          break;

        case 'agent.execution.completed':
          setStatus('completed');
          break;

        case 'agent.execution.failed':
          setStatus('failed');
          break;
      }
    });
  }, [messages]);

  return (
    <div>
      <h3>Agent Execution Status: {status}</h3>

      {plan && (
        <div>
          <h4>Plan:</h4>
          <ul>
            {plan.todos.map((todo: any, i: number) => (
              <li key={i} className={todo.status}>
                {todo.content} - {todo.status}
              </li>
            ))}
          </ul>
        </div>
      )}

      {currentStep && (
        <div>
          <h4>Current Step:</h4>
          <p>
            {currentStep.message} ({currentStep.step_number}/{currentStep.total_steps})
          </p>
        </div>
      )}
    </div>
  );
}
```

---

## Best Practices

### 1. Reconnection Strategy

```typescript
class WebSocketManager {
  private ws: WebSocket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;

  connect(url: string, token: string) {
    this.ws = new WebSocket(`${url}?token=${token}`);

    this.ws.onclose = () => {
      if (this.reconnectAttempts < this.maxReconnectAttempts) {
        setTimeout(() => {
          this.reconnectAttempts++;
          const delay = Math.min(
            this.reconnectDelay * Math.pow(2, this.reconnectAttempts),
            30000
          );
          console.log(`Reconnecting in ${delay}ms...`);
          this.connect(url, token);
        }, this.reconnectDelay);
      }
    };

    this.ws.onopen = () => {
      this.reconnectAttempts = 0;
    };
  }
}
```

---

### 2. Message Buffering

```typescript
class WebSocketWithBuffer {
  private messageQueue: any[] = [];
  private ws: WebSocket | null = null;

  send(message: any) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    } else {
      // Buffer messages while disconnected
      this.messageQueue.push(message);
    }
  }

  onOpen() {
    // Send buffered messages
    while (this.messageQueue.length > 0) {
      const message = this.messageQueue.shift();
      this.ws?.send(JSON.stringify(message));
    }
  }
}
```

---

### 3. Channel Management

```typescript
class ChannelManager {
  private subscribedChannels = new Set<string>();

  subscribe(ws: WebSocket, channel: string) {
    if (!this.subscribedChannels.has(channel)) {
      ws.send(JSON.stringify({
        type: 'subscribe',
        channels: [channel]
      }));
      this.subscribedChannels.add(channel);
    }
  }

  unsubscribe(ws: WebSocket, channel: string) {
    if (this.subscribedChannels.has(channel)) {
      ws.send(JSON.stringify({
        type: 'unsubscribe',
        channels: [channel]
      }));
      this.subscribedChannels.delete(channel);
    }
  }
}
```

---

## Security Considerations

1. **Authentication**: Always validate JWT token on connection
2. **Channel Authorization**: Ensure user has permission for subscribed channels
3. **Rate Limiting**: Limit messages per second per connection
4. **Message Size**: Limit maximum message size (e.g., 1MB)
5. **Timeout**: Close idle connections after 5 minutes of inactivity
6. **TLS/SSL**: Use WSS (WebSocket Secure) in production

---

**Last Updated**: 2025-11-15
**WebSocket Protocol Version**: v1
**Status**: Complete specification
