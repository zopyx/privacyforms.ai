# Multi-Chat API Design

## Overview
RESTful API for managing multiple concurrent chat conversations with LLM models. Supports both synchronous and streaming (WebSocket) response modes.

## Base URL
```
/api/v1
```

## Data Models

### Chat
```json
{
  "id": "uuid",
  "model_key": "string",
  "title": "string | null",
  "system_prompt": "string | null",
  "created_at": "ISO8601",
  "updated_at": "ISO8601",
  "message_count": 0
}
```

### Message
```json
{
  "id": "uuid",
  "chat_id": "uuid",
  "role": "user | assistant | system",
  "content": "string",
  "created_at": "ISO8601",
  "metadata": {
    "tokens_used": 0,
    "model": "string",
    "finish_reason": "string | null"
  }
}
```

---

## Endpoints

### 1. Create Chat
Create a new chat conversation.

**POST** `/chats`

#### Request Body
```json
{
  "model_key": "moonshot/kimi-k2.5",
  "title": "My Coding Assistant",
  "system_prompt": "You are a helpful coding assistant."
}
```

#### Response (201 Created)
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "model_key": "moonshot/kimi-k2.5",
  "title": "My Coding Assistant",
  "system_prompt": "You are a helpful coding assistant.",
  "created_at": "2026-03-07T18:30:00Z",
  "updated_at": "2026-03-07T18:30:00Z",
  "message_count": 0
}
```

---

### 2. List Chats
Get all chats with pagination.

**GET** `/chats?page=1&limit=20`

#### Query Parameters
- `page` (int, default: 1)
- `limit` (int, default: 20, max: 100)
- `model_key` (string, optional) - Filter by model

#### Response (200 OK)
```json
{
  "items": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "model_key": "moonshot/kimi-k2.5",
      "title": "My Coding Assistant",
      "system_prompt": "You are a helpful coding assistant.",
      "created_at": "2026-03-07T18:30:00Z",
      "updated_at": "2026-03-07T19:00:00Z",
      "message_count": 12
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 1,
    "has_next": false
  }
}
```

---

### 3. Get Chat
Get chat details by ID.

**GET** `/chats/{chat_id}`

#### Response (200 OK)
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "model_key": "moonshot/kimi-k2.5",
  "title": "My Coding Assistant",
  "system_prompt": "You are a helpful coding assistant.",
  "created_at": "2026-03-07T18:30:00Z",
  "updated_at": "2026-03-07T19:00:00Z",
  "message_count": 12
}
```

#### Errors
- `404 Not Found` - Chat does not exist

---

### 4. Update Chat
Update chat metadata (title, system prompt).

**PATCH** `/chats/{chat_id}`

#### Request Body
```json
{
  "title": "Updated Title",
  "system_prompt": "New system prompt"
}
```

#### Response (200 OK)
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "model_key": "moonshot/kimi-k2.5",
  "title": "Updated Title",
  "system_prompt": "New system prompt",
  "created_at": "2026-03-07T18:30:00Z",
  "updated_at": "2026-03-07T19:05:00Z",
  "message_count": 12
}
```

---

### 5. Delete Chat
Delete a chat and all its messages.

**DELETE** `/chats/{chat_id}`

#### Response (204 No Content)

---

### 6. Send Message (Sync)
Send a message and get complete response.

**POST** `/chats/{chat_id}/messages`

#### Request Body
```json
{
  "content": "How do I implement a binary search in Python?",
  "stream": false
}
```

#### Response (201 Created)
```json
{
  "message": {
    "id": "660e8400-e29b-41d4-a716-446655440001",
    "chat_id": "550e8400-e29b-41d4-a716-446655440000",
    "role": "user",
    "content": "How do I implement a binary search in Python?",
    "created_at": "2026-03-07T19:10:00Z",
    "metadata": null
  },
  "response": {
    "id": "660e8400-e29b-41d4-a716-446655440002",
    "chat_id": "550e8400-e29b-41d4-a716-446655440000",
    "role": "assistant",
    "content": "Here's how to implement binary search in Python...",
    "created_at": "2026-03-07T19:10:05Z",
    "metadata": {
      "tokens_used": 150,
      "model": "moonshot/kimi-k2.5",
      "finish_reason": "stop"
    }
  }
}
```

---

### 7. Send Message (Streaming via SSE)
Stream response using Server-Sent Events.

**POST** `/chats/{chat_id}/messages`

#### Request Body
```json
{
  "content": "How do I implement a binary search in Python?",
  "stream": true
}
```

#### Response (200 OK)
Content-Type: `text/event-stream`

```
event: message_start
data: {"message_id": "660e8400-e29b-41d4-a716-446655440001", "role": "user"}

event: content_start
data: {"response_id": "660e8400-e29b-41d4-a716-446655440002"}

event: content_delta
data: {"content": "Here's"}

event: content_delta
data: {"content": " how"}

event: content_delta
data: {"content": " to"}

event: content_done
data: {"finish_reason": "stop", "tokens_used": 150}

event: done
data: {}
```

---

### 8. List Messages
Get chat message history with pagination.

**GET** `/chats/{chat_id}/messages?page=1&limit=50`

#### Query Parameters
- `page` (int, default: 1)
- `limit` (int, default: 50, max: 200)
- `role` (string, optional) - Filter by role (user/assistant/system)

#### Response (200 OK)
```json
{
  "items": [
    {
      "id": "660e8400-e29b-41d4-a716-446655440000",
      "chat_id": "550e8400-e29b-41d4-a716-446655440000",
      "role": "system",
      "content": "You are a helpful coding assistant.",
      "created_at": "2026-03-07T18:30:00Z",
      "metadata": null
    },
    {
      "id": "660e8400-e29b-41d4-a716-446655440001",
      "chat_id": "550e8400-e29b-41d4-a716-446655440000",
      "role": "user",
      "content": "How do I implement a binary search in Python?",
      "created_at": "2026-03-07T19:10:00Z",
      "metadata": null
    },
    {
      "id": "660e8400-e29b-41d4-a716-446655440002",
      "chat_id": "550e8400-e29b-41d4-a716-446655440000",
      "role": "assistant",
      "content": "Here's how to implement binary search in Python...",
      "created_at": "2026-03-07T19:10:05Z",
      "metadata": {
        "tokens_used": 150,
        "model": "moonshot/kimi-k2.5",
        "finish_reason": "stop"
      }
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 50,
    "total": 3,
    "has_next": false
  }
}
```

---

### 9. Get Message
Get a specific message by ID.

**GET** `/chats/{chat_id}/messages/{message_id}`

#### Response (200 OK)
```json
{
  "id": "660e8400-e29b-41d4-a716-446655440002",
  "chat_id": "550e8400-e29b-41d4-a716-446655440000",
  "role": "assistant",
  "content": "Here's how to implement binary search in Python...",
  "created_at": "2026-03-07T19:10:05Z",
  "metadata": {
    "tokens_used": 150,
    "model": "moonshot/kimi-k2.5",
    "finish_reason": "stop"
  }
}
```

---

### 10. Regenerate Response
Regenerate the last assistant response (useful for "retry" functionality).

**POST** `/chats/{chat_id}/regenerate`

#### Request Body
```json
{
  "stream": false
}
```

#### Response (200 OK)
Same as Send Message response.

---

## WebSocket API (Alternative Streaming)

For clients needing bidirectional communication or lower latency.

### Connection
```
WS /ws/chats/{chat_id}
```

### Client → Server Messages

#### Send Message
```json
{
  "type": "message",
  "id": "client-msg-id-123",
  "content": "How do I implement a binary search?",
  "stream": true
}
```

#### Abort Generation
```json
{
  "type": "abort",
  "response_id": "660e8400-e29b-41d4-a716-446655440002"
}
```

### Server → Client Messages

#### Acknowledgment
```json
{
  "type": "ack",
  "client_id": "client-msg-id-123",
  "message_id": "660e8400-e29b-41d4-a716-446655440001"
}
```

#### Content Delta (Streaming)
```json
{
  "type": "content_delta",
  "response_id": "660e8400-e29b-41d4-a716-446655440002",
  "content": "Here's"
}
```

#### Generation Complete
```json
{
  "type": "done",
  "response_id": "660e8400-e29b-41d4-a716-446655440002",
  "metadata": {
    "tokens_used": 150,
    "model": "moonshot/kimi-k2.5",
    "finish_reason": "stop"
  }
}
```

#### Error
```json
{
  "type": "error",
  "client_id": "client-msg-id-123",
  "error": {
    "code": "MODEL_ERROR",
    "message": "Model failed to generate response"
  }
}
```

---

## Error Responses

All errors follow this format:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable description",
    "details": {}
  }
}
```

### Common Error Codes

| Status | Code | Description |
|--------|------|-------------|
| 400 | `INVALID_REQUEST` | Malformed request body |
| 400 | `VALIDATION_ERROR` | Validation failed (missing fields, etc) |
| 404 | `CHAT_NOT_FOUND` | Chat ID does not exist |
| 404 | `MESSAGE_NOT_FOUND` | Message ID does not exist |
| 409 | `CHAT_LOCKED` | Chat is being modified by another request |
| 422 | `MODEL_ERROR` | LLM model failed to generate response |
| 429 | `RATE_LIMITED` | Too many requests |
| 500 | `INTERNAL_ERROR` | Unexpected server error |

---

## Rate Limiting

API uses token bucket rate limiting:
- 100 requests per minute per API key
- 1000 messages per hour per API key

Rate limit headers included in all responses:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1709836800
```

---

## Authentication

API uses Bearer token authentication:
```
Authorization: Bearer <api_key>
```

---

## Future Extensions

1. **Chat Templates** - Pre-defined system prompts
2. **Chat Sharing** - Public/private sharing links
3. **Chat Export** - Export to Markdown, JSON, PDF
4. **Chat Forking** - Branch conversations at any point
5. **Multi-model Compare** - Send same message to multiple models
6. **File Attachments** - Upload files for context
