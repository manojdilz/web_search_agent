# Perplexity 2.0 Backend - Production Architecture

A production-grade, modular backend for AI-powered search and response streaming with real-time tool execution tracking.

## 📁 Project Structure

```
server/
├── main.py                  # Application entry point & lifecycle management
├── config.py               # Configuration management (env vars, settings)
├── models.py               # Data models & Pydantic schemas
├── utils.py                # Utility functions (normalization, parsing)
├── agent.py                # LangGraph agent setup & execution
├── serializers.py          # Message serialization & payload builders
├── services.py             # Business logic & streaming service
├── routes.py               # API endpoints & handlers
├── pyproject.toml          # Project metadata & dependencies
└── README.md               # This file
```

## 🏗️ Architecture Principles

### 1. **Clean Separation of Concerns**
- **config.py**: All environment configuration and settings
- **models.py**: Type definitions and data structures
- **utils.py**: Reusable utility functions
- **agent.py**: LLM and tool setup logic
- **serializers.py**: Message serialization and formatting
- **services.py**: Core business logic
- **routes.py**: HTTP endpoints
- **main.py**: Application initialization and wiring

### 2. **Factory Pattern**
- `ToolFactory`: Creates and manages tools
- `LLMFactory`: Lazy-initializes LLM with proper error handling
- `AgentFactory`: Orchestrates agent creation
- `create_chat_routes()`: Creates router with dependency injection

### 3. **Dependency Injection**
- Services receive dependencies through constructors
- Loose coupling between modules
- Easy testing and mocking

### 4. **Type Safety**
- 100% type hints throughout
- Pydantic models for validation
- Clear function signatures

### 5. **Error Handling**
- Structured exception handling in all services
- Logging at each layer
- Graceful degradation

## 🚀 Running the Application

### Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e .
```

### Configuration

Create `.env` file:

```env
# LLM Configuration
LLM_MODEL=meta-llama/llama-4-scout-17b-16e-instruct
LLM_PROVIDER=groq
GROQ_API_KEY=your-api-key-here

# Server Configuration
HOST=0.0.0.0
PORT=8000
DEBUG=False
LOG_LEVEL=INFO

# CORS Configuration (as comma-separated string)
CORS_ORIGINS=["*"]
CORS_METHODS=["*"]
CORS_HEADERS=["*"]
```

### Start Development Server

```bash
# Using uvicorn directly
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Or using Python
python main.py
```

## 📝 Module Documentation

### `config.py`
Centralized configuration management using Pydantic Settings.

**Key Classes:**
- `Settings`: Application configuration schema
- `get_settings()`: Factory function for settings singleton
- `setup_logging()`: Logging initialization

**Usage:**
```python
from config import get_settings

settings = get_settings()
print(settings.llm_model)
```

### `models.py`
TypedDict and Pydantic models for type safety.

**Key Structures:**
- `State`: Graph state definition
- `AIMessageChunkData`: Serialized chunk structure
- `*Payload`: Event payload models
- `ChatRequest`: Request validation

### `utils.py`
Reusable utility classes for common operations.

**Key Classes:**
- `ContentNormalizer`: Recursively normalize objects for JSON
- `ToolArgumentParser`: Parse and validate tool arguments
- `SSEEventBuilder`: Build properly formatted SSE events
- `AttributeExtractor`: Safely extract attributes

### `agent.py`
LangGraph agent configuration and execution.

**Key Classes:**
- `ToolFactory`: Tool initialization and management
- `LLMFactory`: LLM initialization with lazy loading
- `GraphBuilder`: Constructs and manages the agent graph
- `AgentFactory`: Orchestrates all agent components

**Features:**
- Lazy initialization for performance
- Comprehensive error handling
- Tool execution with error recovery

### `serializers.py`
Message serialization and event payload building.

**Key Classes:**
- `MessageSerializer`: Converts messages to transferable format
- `PayloadBuilder`: Constructs all event payload types

**Benefits:**
- Centralized serialization logic
- Consistent payload structure
- Type-safe payload building

### `services.py`
Business logic and streaming service.

**Key Classes:**
- `ToolTracker`: Tracks tool calls throughout session
- `ChatStreamService`: Main streaming orchestration

**Features:**
- Real-time tool tracking (selected → executing → completed)
- Intelligent event emission
- Async streaming with proper cleanup

### `routes.py`
FastAPI endpoints with proper validation.

**Endpoints:**
- `GET /api/chat_stream/{message}`: Legacy path-based streaming
- `POST /api/chat_stream`: POST-based streaming with JSON body
- `GET /api/health`: Health check

**Features:**
- Input validation
- Proper error responses
- SSE headers for streaming

### `main.py`
Application initialization and lifecycle management.

**Features:**
- Lifespan context manager for startup/shutdown
- Middleware configuration (CORS)
- Dependency injection setup
- Development server runner

## 🔄 Request Flow

```
Request comes in
    ↓
[routes.py] Validates input
    ↓
[services.py] StreamingService.stream_response()
    ↓
[agent.py] Graph executes with streaming
    ↓
[serializers.py] Messages are serialized
    ↓
[utils.py] Content normalized, SSE events built
    ↓
Events streamed to frontend
    ↓
[models.py] Responses validated by Pydantic
```

## 📊 Event Streaming Flow

```
┌─────────────────────────────┐
│ User Message                │
└──────────────┬──────────────┘
               ↓
        [tool_selected]
    "Tools: [tavily_search]"
               ↓
        [tool_executing]
      "Status: executing..."
               ↓
       [Backend executes]
               ↓
         [tool_result]
      "Results: [...]"
               ↓
       [assistant chunks]
    "The president of... is..."
               ↓
           [done]
      "checkpoint_id: uuid"
```

## 🧪 Testing

### Unit Testing Pattern

```python
# Test utilities
from utils import ContentNormalizer

def test_normalize_content():
    result = ContentNormalizer.normalize({"key": [1, 2, 3]})
    assert result == {"key": [1, 2, 3]}

# Test services
from services import ToolTracker

def test_tool_tracker():
    tracker = ToolTracker()
    assert tracker.mark_seen("id-1") == True
    assert tracker.mark_seen("id-1") == False
```

### Integration Testing Pattern

```python
# Mock the graph
async def test_stream_response(mocker):
    mock_graph = mocker.AsyncMock()
    service = ChatStreamService(mock_graph)
    
    # Test streaming
    result = []
    async for event in service.stream_response("test"):
        result.append(event)
    
    assert len(result) > 0
```

## 🔐 Best Practices Implemented

### 1. **Configuration Management**
✅ Environment-based configuration  
✅ No hardcoded secrets  
✅ Type-safe settings  

### 2. **Error Handling**
✅ Try-catch in critical sections  
✅ Structured logging  
✅ Graceful error responses  

### 3. **Code Organization**
✅ Single responsibility principle  
✅ Clear module boundaries  
✅ Factory patterns for object creation  

### 4. **Type Safety**
✅ Full type hints  
✅ Pydantic validation  
✅ Runtime type checking  

### 5. **Async/Await**
✅ Async/await throughout  
✅ Non-blocking operations  
✅ Proper context management  

### 6. **Logging**
✅ Structured logging  
✅ Appropriate log levels  
✅ Context information  

### 7. **Documentation**
✅ Module docstrings  
✅ Function docstrings  
✅ Type hints as documentation  

## 🚦 API Endpoints

### 1. Stream Chat (GET - Legacy)

```
GET /api/chat_stream/who%20is%20the%20president
Query params:
  - checkpoint_id (optional): Session ID for continuation
  
Response: Server-Sent Events stream
```

### 2. Stream Chat (POST - Recommended)

```
POST /api/chat_stream
Content-Type: application/json

{
  "message": "who is the president",
  "checkpoint_id": "optional-session-id"
}

Response: Server-Sent Events stream
```

### 3. Health Check

```
GET /api/health

Response:
{
  "status": "ok",
  "service": "perplexity-2.0-backend"
}
```

## 🔍 Monitoring & Debugging

### Logging

Enable debug logging:
```
LOG_LEVEL=DEBUG uvicorn main:app --reload
```

### Performance Profiling

```python
import cProfile
import pstats

profiler = cProfile.Profile()
profiler.enable()
# ... run code ...
profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative').print_stats(10)
```

### Event Tracing

All events are logged with timestamps and relevant context for debugging.

## 📚 Additional Resources

- **FastAPI Docs**: http://localhost:8000/docs
- **OpenAPI Schema**: http://localhost:8000/openapi.json
- **LangGraph Documentation**: https://langchain-ai.github.io/langgraph/
- **Pydantic Documentation**: https://docs.pydantic.dev/

## 📈 Scalability Considerations

### Current Limitations
- In-memory checkpoint storage (single instance only)
- No request queuing or rate limiting

### Future Improvements
- PostgreSQL checkpointer for distributed deployments
- Redis cache for tool results
- Rate limiting and request queuing
- Horizontal scaling with load balancing
- Telemetry and metrics collection

## 📝 Contributing

1. Follow the existing code structure
2. Add type hints to all functions
3. Update docstrings
4. Write tests for new features
5. Maintain separation of concerns

## 🔄 Deployment

### Docker

```dockerfile
FROM python:3.13-slim

WORKDIR /app
COPY . .
RUN pip install -e .

CMD ["python", "main.py"]
```

### Environment Variables (Production)

```env
LLM_MODEL=meta-llama/llama-4-scout-17b-16e-instruct
LLM_PROVIDER=groq
GROQ_API_KEY=${GROQ_API_KEY}
HOST=0.0.0.0
PORT=8000
DEBUG=False
LOG_LEVEL=INFO
CORS_ORIGINS=["https://yourdomain.com"]
```

## 📄 License

MIT
