# Real-Time Streaming Events Documentation

## Overview
The chat streaming API emits Server-Sent Events (SSE) that allow the frontend to display tool selection, execution, and streaming responses in real-time (similar to Perplexity).

## Event Flow

```
User sends message
    ↓
Assistant thinks and selects tools
    ↓
[tool_selected] - Frontend shows which tools are being used
    ↓
[tool_executing] - Frontend shows tool is running
    ↓
Backend executes tool
    ↓
[tool_result] - Frontend displays tool results
    ↓
Assistant streams response chunks
    ↓
[assistant] chunks - Frontend shows streaming text in real-time
    ↓
[done] - Request complete, checkpoint_id provided for session continuation
```

## Event Types

### 1. `tool_selected` - Tool Selection
**When:** Model has selected tools to use before execution
**Payload:**
```json
{
  "event": "tool_selected",
  "data": {
    "tools": [
      {
        "tool_call_id": "unique-id-123",
        "tool_name": "tavily_search",
        "args": {
          "query": "current president of Sri Lanka"
        },
        "status": "selected"
      }
    ],
    "count": 1,
    "timestamp": null
  }
}
```

**Frontend Action:**
- Show a UI indicator that a tool is selected
- Display the tool name and arguments
- Example: "🔍 Searching for: current president of Sri Lanka"

---

### 2. `tool_executing` - Tool Execution Started
**When:** Tool execution begins (this may be emitted when results arrive if execution was fast)
**Payload:**
```json
{
  "event": "tool_executing",
  "data": {
    "tool_call_id": "unique-id-123",
    "tool_name": "tavily_search",
    "status": "executing",
    "args": {
      "query": "current president of Sri Lanka"
    }
  }
}
```

**Frontend Action:**
- Show a loading spinner next to the tool
- Display "Executing..." status
- Example: "🔍 Searching for: current president of Sri Lanka (executing...)"

---

### 3. `tool_result` - Tool Execution Complete
**When:** Tool has finished execution and returned results
**Payload:**
```json
{
  "event": "tool_result",
  "data": {
    "tool_call_id": "unique-id-123",
    "tool_name": "tavily_search",
    "status": "completed",
    "content": [
      {
        "title": "Sri Lanka president",
        "url": "https://example.com",
        "snippet": "..."
      }
    ],
    "artifact": null
  }
}
```

**Frontend Action:**
- Hide loading spinner
- Display tool results (usually in a collapsible section)
- Show a small preview of what was found
- Mark tool as completed
- Example: "✓ Searched and found 4 results"

---

### 4. `assistant` - AI Response Chunks (Streaming)
**Type A - Chunk (streaming in real-time):**
```json
{
  "event": "assistant",
  "data": {
    "type": "chunk",
    "chunk": {
      "type": "AIMessageChunk",
      "id": "msg-456",
      "content": "The current president of Sri Lanka is ",
      "has_tool_calls": false,
      "tool_calls": [],
      "tool_call_chunks": []
    }
  }
}
```

**Type B - Complete Message:**
```json
{
  "event": "assistant",
  "data": {
    "type": "message",
    "content": "The current president of Sri Lanka is Anura Kumara Dissanayake.",
    "id": "msg-789"
  }
}
```

**Frontend Action:**
- Stream the content character by character or in chunks
- Append to the message being displayed
- Maintain smooth streaming animation
- Example: Show text appearing word by word in the chat

---

### 5. `done` - Request Complete
**When:** Entire response streaming is complete
**Payload:**
```json
{
  "event": "done",
  "data": {
    "checkpoint_id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "completed"
  }
}
```

**Frontend Action:**
- Stop any loading animations
- Save `checkpoint_id` for session continuation (can use it in next request to continue the same conversation)
- Enable user input again
- Example: Mark the message as fully received, ready for next message

---

## Frontend Implementation Example

```javascript
async function streamChat(message, checkpointId = null) {
  const eventSource = new EventSource(
    `/chat_stream/${encodeURIComponent(message)}${checkpointId ? `?checkpoint_id=${checkpointId}` : ''}`
  );

  let currentCheckpointId = null;

  eventSource.addEventListener('tool_selected', (e) => {
    const data = JSON.parse(e.data);
    console.log('Tools selected:', data.tools);
    // Show tool selection UI
    updateUI({ type: 'tool_selected', data });
  });

  eventSource.addEventListener('tool_executing', (e) => {
    const data = JSON.parse(e.data);
    console.log('Tool executing:', data.tool_name);
    // Show loading indicator
    updateUI({ type: 'tool_executing', data });
  });

  eventSource.addEventListener('tool_result', (e) => {
    const data = JSON.parse(e.data);
    console.log('Tool result:', data.content);
    // Display tool results
    updateUI({ type: 'tool_result', data });
  });

  eventSource.addEventListener('assistant', (e) => {
    const data = JSON.parse(e.data);
    if (data.type === 'chunk') {
      // Stream chunks in real-time
      appendToMessage(data.chunk.content);
    } else {
      // Complete message
      setMessage(data.content);
    }
  });

  eventSource.addEventListener('done', (e) => {
    const data = JSON.parse(e.data);
    currentCheckpointId = data.checkpoint_id;
    console.log('Response complete, checkpoint:', currentCheckpointId);
    // Stop loading, enable input
    updateUI({ type: 'done', data });
    eventSource.close();
  });

  eventSource.addEventListener('error', (e) => {
    console.error('Stream error:', e);
    eventSource.close();
  });
}
```

---

## Session Continuation

The `checkpoint_id` returned in the `done` event allows you to continue a conversation:

```javascript
// First message
let checkpointId = await streamChat("Who is the president of Sri Lanka?");

// Continue in same session (conversation context preserved)
await streamChat("When did they take office?", checkpointId);
```

This maintains conversation history on the backend using the in-memory checkpoint system.

---

## Key Implementation Tips

1. **Real-time Streaming**: Emit `assistant` chunks as they arrive - don't wait for completion
2. **Tool Visualization**: Show tool selection → executing → results in a clear progression
3. **User Feedback**: Provide visual feedback at each stage (spinner, checkmark, etc.)
4. **Error Handling**: Handle SSE disconnections and errors gracefully
5. **Session Persistence**: Save `checkpoint_id` to continue conversations
6. **Type Safety**: Parse JSON payloads carefully, handle missing fields

---

## UI/UX Pattern (Perplexity-style)

```
[Message Input]

┌─────────────────────────────────┐
│ Thinking...                      │
└─────────────────────────────────┘

┌─────────────────────────────────┐
│ 🔍 Searching (executing...)     │
└─────────────────────────────────┘

┌─────────────────────────────────┐
│ ✓ Searched and found 4 results   │
│                                  │
│ The current president of Sri     │
│ Lanka is Anura Kumara            │
│ Dissanayake. He took office...   │
└─────────────────────────────────┘

[Message Input ready for next]
```
