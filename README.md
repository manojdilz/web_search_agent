# Perplexity 2.0 Server

A production-ready FastAPI server for AI-powered chat applications with real-time streaming and tool-augmented responses using LangGraph.

## 🚀 Features

- **Real-time Streaming**: Server-Sent Events (SSE) for live chat responses
- **Tool Integration**: Built-in support for web search and custom tools
- **Modular Architecture**: Clean separation of concerns with 8 focused modules
- **Production Ready**: Comprehensive error handling, logging, and configuration
- **Docker Support**: Containerized deployment with Docker Compose
- **CORS Enabled**: Ready for frontend integration
- **Type Safety**: Full Pydantic validation and type hints

## 📦 Quick Start

### Prerequisites
- Python 3.8+
- Groq API key ([get one here](https://console.groq.com))

### Installation

1. **Clone and setup**:
   ```bash
   git clone <your-repo-url>
   cd server
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   pip install -e .
   ```

2. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your GROQ_API_KEY
   ```

3. **Run the server**:
   ```bash
   python main.py
   ```

4. **Test the API**:
   ```bash
   curl -N "http://localhost:8000/api/chat_stream/hello%20world"
   ```

## 📚 Architecture

This project follows a modular architecture designed for maintainability and scalability:

- **`main.py`**: Application entry point and FastAPI setup
- **`config.py`**: Configuration management with Pydantic settings
- **`models.py`**: Data models and validation schemas
- **`routes.py`**: API endpoint definitions
- **`services.py`**: Business logic and streaming services
- **`agent.py`**: LangGraph agent configuration and tool setup
- **`serializers.py`**: Message serialization for streaming responses
- **`utils.py`**: Shared utility functions

For detailed architecture documentation, see [`docs/README_ARCHITECTURE.md`](docs/README_ARCHITECTURE.md).

## 🔧 API Endpoints

### Chat Streaming
```
GET /api/chat_stream/{message}
```
Streams AI responses with real-time tool execution updates.

**Parameters:**
- `message` (path): The user message to process
- `checkpoint_id` (query, optional): Session ID for conversation continuity

**Response:** Server-Sent Events stream with events:
- `tool_selected`: Tools chosen by the AI
- `tool_executing`: Tool execution in progress
- `tool_result`: Tool completion results
- `assistant`: AI response chunks
- `done`: Stream completion

### Health Check
```
GET /api/health
```
Returns server health status.

## ⚙️ Configuration

Configure the application using environment variables in `.env`:

```env
# Required
GROQ_API_KEY=your-groq-api-key-here

# Optional
LLM_MODEL=meta-llama/llama-4-scout-17b-16e-instruct
LLM_PROVIDER=groq
HOST=0.0.0.0
PORT=8000
DEBUG=False
LOG_LEVEL=INFO
```

## 🐳 Deployment

### Docker
```bash
docker build -t perplexity-server .
docker run -p 8000:8000 --env-file .env perplexity-server
```

### Docker Compose
```bash
docker-compose up -d
```

For production deployment checklist, see [`docs/DEPLOYMENT_CHECKLIST.md`](docs/DEPLOYMENT_CHECKLIST.md).

## 🧪 Development

### Running Tests
```bash
python -m pytest
```

### Code Quality
```bash
# Format code
black .

# Lint code
flake8 .

# Type checking
mypy .
```

## 📖 Documentation

- **[Quick Start Guide](docs/QUICKSTART.md)**: 5-minute setup
- **[Architecture Guide](docs/README_ARCHITECTURE.md)**: Detailed system design
- **[Refactoring Summary](docs/REFACTORING_SUMMARY.md)**: Migration from monolithic to modular
- **[Streaming Events](docs/STREAMING_EVENTS.md)**: Event protocol documentation
- **[Frontend Integration](docs/FRONTEND_REACT_EXAMPLE.md)**: React client example
- **[Deployment Checklist](docs/DEPLOYMENT_CHECKLIST.md)**: Production deployment guide

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## 📄 License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [FastAPI](https://fastapi.tiangolo.com/)
- Powered by [LangChain](https://www.langchain.com/) and [LangGraph](https://langchain-ai.github.io/langgraph/)
- LLM provided by [Groq](https://groq.com/)
- Search tools via [Tavily](https://tavily.com/)