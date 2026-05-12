# Architecture Visualization

## System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend (React)                          │
│                    (STREAMING_EVENTS.md)                         │
└────────────────────────┬────────────────────────────────────────┘
                         │
                    HTTP/SSE
                         │
        ┌────────────────▼────────────────┐
        │      FastAPI Application        │
        │          (main.py)              │
        └────────────────┬────────────────┘
                         │
        ┌────────────────▼──────────────────────┐
        │   Configuration Layer                 │
        │  ┌──────────────────────────────────┐ │
        │  │ config.py (Settings)             │ │
        │  │ - Environment variables          │ │
        │  │ - Type validation                │ │
        │  │ - Logging setup                  │ │
        │  └──────────────────────────────────┘ │
        └────────────────┬──────────────────────┘
                         │
    ┌────────────────────┴────────────────────────┐
    │                                             │
    ▼                                             ▼
┌─────────────┐                          ┌──────────────┐
│ routes.py   │                          │ services.py  │
│ ────────    │                          │ ──────────   │
│ - GET /chat │                          │ - Stream     │
│ - POST /chat│                          │ - Tool Track │
│ - GET /heal │                          │ - Serialize  │
└─────────────┘                          └──────┬───────┘
    │                                            │
    │                                ┌───────────▼──────────┐
    │                                │                      │
    │                                ▼                      ▼
    │                          ┌────────────┐        ┌────────────┐
    │                          │ models.py  │        │  utils.py  │
    │                          │ ──────────│        │  ─────────  │
    │                          │ - State    │        │ - Normalize │
    │                          │ - Payloads │        │ - Parse Arg │
    │                          │ - Schemas  │        │ - SSE Build │
    │                          └────────────┘        └────────────┘
    │                                │
    │                                │
    └────────────┬───────────────────┘
                 │
            ┌────▼────────────────────┐
            │   agent.py              │
            │  ──────────             │
            │ ┌──────────────────┐    │
            │ │ AgentFactory     │    │
            │ │ - ToolFactory    │    │
            │ │ - LLMFactory     │    │
            │ │ - GraphBuilder   │    │
            │ └──────────────────┘    │
            │        │                │
            │        ├─► LangGraph    │
            │        │   - Model Node │
            │        │   - Tool Node  │
            │        │   - Router     │
            │        │                │
            └────┬───────────────────┘
                 │
        ┌────────┴─────────────────┐
        │                          │
        ▼                          ▼
  ┌──────────┐            ┌─────────────┐
  │   LLM    │            │  Tools      │
  │ ─────────│            │ ──────────  │
  │ Groq API │            │ Tavily      │
  │ (Remote) │            │ Search      │
  └──────────┘            └─────────────┘
```

## Module Dependency Graph

```
main.py (Entry Point)
  ├── config.py
  │   └── logging setup
  │
  ├── agent.py
  │   ├── models.py (State)
  │   └── langchain
  │
  ├── services.py
  │   ├── agent.py
  │   ├── models.py
  │   ├── utils.py
  │   └── serializers.py
  │
  ├── routes.py
  │   ├── services.py
  │   ├── models.py
  │   └── fastapi
  │
  └── FastAPI middleware
      └── CORS
```

## Data Flow Diagram

```
User Query
    ↓
[routes.py] Input Validation
    ↓
[services.py] ChatStreamService.stream_response()
    ├─► Initialize ToolTracker
    └─► Stream from LangGraph
        ↓
    [agent.py] Graph Execution
        ├─► Model Node
        │   └─► LLM (Groq)
        │       ↓ Detect tool calls
        │
        └─► Tool Node
            └─► Execute Tools (Tavily)
                ↓ Get results
    ↓
[messages] AI Response
    ├─► AIMessageChunk
    ├─► ToolMessage
    └─► Complete Messages
    ↓
[serializers.py] Serialize Message
    ├─► MessageSerializer
    └─► PayloadBuilder
    ↓
[utils.py] Normalize & Build SSE Event
    ├─► ContentNormalizer
    └─► SSEEventBuilder
    ↓
[routes.py] Stream to Frontend
    └─► StreamingResponse (SSE)
```

## Event Generation Timeline

```
                    Request Timeline
                    ════════════════════

T=0ms  ┌──────────────────────────────────┐
       │ User sends message               │
       └──────────────────────────────────┘
           │
           │ models.py: ChatRequest validation
           │ routes.py: Input check
           │
T=10ms │
       └──────────────────────────────────┐
           │ services.py: stream_response() │
           │ Start LangGraph execution      │
           └──────────────────────────────┘
           │
T=50ms │
       └──────────────────────────────────┐
           │ agent.py: Model Node          │
           │ LLM processes query           │
           └──────────────────────────────┘
           │
T=1000ms   │
           ├─► [tool_selected] Event ◄────────┐
           │                                  │
           │   serializers.py + utils.py     │
           │   Build SSE event               │
           │
T=1010ms   │
           ├─► [tool_executing] Event ◄──────┤ Real-time
           │   Status: "executing"           │ Events
           │                                  │
T=2000ms   │ (Tool executes at backend)      │
           │                                  │
T=2100ms   │
           ├─► [tool_result] Event ◄─────────┤
           │   Results from Tavily           │
           │                                  │
T=2200ms   │
           │   agent.py: Tool Node           │
           │   Process results               │
           │                                  │
T=2250ms   │
           │   agent.py: Model Node again   │
           │   Generate response             │
           │                                  │
T=2300ms   │
           ├─► [assistant] chunk ◄──────────┤
           │   "The president..."            │
           │                                  │
T=2310ms   ├─► [assistant] chunk ◄──────────┤ Streaming
           │   "of Sri Lanka"                │ Text
           │                                  │
T=2320ms   ├─► [assistant] chunk ◄──────────┤
           │   "is Anura Kumara..."          │
           │                                  │
T=2350ms   │
           ├─► [done] Event ◄────────────────┤
           │   checkpoint_id: "uuid-12345"   │
           │                                  │
T=2360ms   └──────────────────────────────────┘
               Streaming complete!
```

## Class Hierarchy

```
config.py
├── Settings (BaseSettings)
└── get_settings() → Settings

models.py
├── State (TypedDict)
├── AIMessageChunkData (BaseModel)
├── ToolCallDict (BaseModel)
├── *Payload (BaseModel)
└── ChatRequest (BaseModel)

utils.py
├── ContentNormalizer
│   └── normalize(value) → Any
├── ToolArgumentParser
│   └── parse(args) → Union[str, dict]
├── SSEEventBuilder
│   └── build_event(type, payload) → str
└── AttributeExtractor
    └── get(obj, attr, default) → Any

agent.py
├── ToolFactory
│   ├── __init__(max_results)
│   ├── tools (property)
│   └── search_tool (property)
├── LLMFactory
│   ├── __init__(settings)
│   ├── llm (property)
│   └── get_llm_with_tools(tool_factory)
├── GraphBuilder
│   ├── __init__(llm_with_tools, tool_factory)
│   ├── model_node(state) → dict
│   ├── tool_router(state) → str
│   ├── tool_node(state) → dict
│   └── build() → CompiledGraph
└── AgentFactory
    ├── __init__(settings)
    ├── create_graph_builder() → GraphBuilder
    └── get_compiled_graph() → CompiledGraph

serializers.py
├── MessageSerializer
│   └── serialize_ai_chunk(chunk) → AIMessageChunkData
└── PayloadBuilder
    ├── build_tool_executing(...) → dict
    ├── build_tool_result(...) → dict
    ├── build_tool_call_dict(...) → ToolCallDict
    ├── build_tool_selected_payload(...) → dict
    ├── build_assistant_chunk(...) → dict
    ├── build_assistant_message(...) → dict
    └── build_done(...) → dict

services.py
├── ToolTracker
│   ├── pending_calls: dict
│   ├── seen_call_ids: set
│   ├── execution_started: set
│   ├── mark_seen(tool_id) → bool
│   ├── add_pending(tool_id, name, args)
│   ├── get_pending(tool_id) → dict
│   ├── remove_pending(tool_id)
│   └── mark_execution_started(tool_id) → bool
└── ChatStreamService
    ├── __init__(graph)
    ├── stream_response(message, checkpoint_id) → AsyncGenerator
    ├── _handle_tool_message(msg, tracker)
    ├── _handle_ai_chunk(msg, tracker)
    ├── _handle_ai_message(msg, tracker)
    ├── _process_tool_calls(msg, tracker)
    └── _extract_tool_calls(msg) → list[dict]

routes.py
└── create_chat_routes(chat_service) → APIRouter
    ├── chat_stream_legacy(message, checkpoint_id)
    ├── chat_stream_post(request)
    └── health_check()

main.py
├── init_logging() → logging.Logger
├── init_config() → Settings
├── init_agent() → AgentFactory
├── init_services() → ChatStreamService
├── lifespan(app) → AsyncContextManager
├── create_app() → FastAPI
└── setup_routes(app) → FastAPI
```

## Request/Response Cycle

```
HTTP Request
    │
    ├─ GET /api/chat_stream/{message}
    │  or
    └─ POST /api/chat_stream (JSON body)
        │
        ▼
    [routes.py]
    ├─ Validate input
    ├─ Check for empty message
    │
    ├─ No: Return 400 Bad Request
    │
    ├─ Yes: Continue
    │
    ├─ Create StreamingResponse
    │
    ├─ Call chat_service.stream_response()
    │
    └─ Return SSE stream
        │
        ▼
    Streaming Response (text/event-stream)
    │
    ├─ event: tool_selected
    ├─ event: tool_executing
    ├─ event: tool_result
    ├─ event: assistant
    ├─ event: assistant (multiple chunks)
    │
    └─ event: done
```

## Error Handling Flow

```
Request Processing
    │
    ├─ Success Path ✓
    │  └─ Normal response
    │
    └─ Error Paths ✗
        │
        ├─ Input Validation Error
        │  └─ 400 Bad Request
        │
        ├─ Configuration Error
        │  └─ 500 Internal Server Error
        │  └─ Log error details
        │
        ├─ LLM Error
        │  └─ Emit error event
        │  └─ Continue gracefully
        │
        ├─ Tool Execution Error
        │  └─ Create error ToolMessage
        │  └─ Continue with other tools
        │
        └─ Streaming Error
           └─ Emit error event
           └─ Close stream
           └─ Log error details
```

---

**Diagram Legend:**
- `┌─┐` = Module/Component
- `───►` = Imports/Dependencies
- `│` = Flow direction
- `▼` = Step progression

For detailed information, see [README_ARCHITECTURE.md](README_ARCHITECTURE.md)
