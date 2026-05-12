# Quick Start Guide

## 5-Minute Setup

### 1. Install Dependencies

```bash
# Create virtual environment
python -m venv venv

# Activate it
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install package in development mode
pip install -e .
```

### 2. Configure Environment

Create `.env` file in the project root:

```env
GROQ_API_KEY=your-groq-api-key-here
LLM_MODEL=meta-llama/llama-4-scout-17b-16e-instruct
LLM_PROVIDER=groq
HOST=0.0.0.0
PORT=8000
DEBUG=False
LOG_LEVEL=INFO
```

Get your API key from [console.groq.com](https://console.groq.com)

### 3. Run the Server

```bash
python main.py
```

The server will start at `http://localhost:8000`

### 4. Test the API

Open a new terminal and test streaming:

```bash
# Using curl
curl -N "http://localhost:8000/api/chat_stream/who%20is%20the%20president%20of%20sri%20lanka"

# Using Python
python -c "
import requests
import json

response = requests.get(
    'http://localhost:8000/api/chat_stream/who%20is%20the%20president%20of%20sri%20lanka',
    stream=True
)

for line in response.iter_lines():
    if line:
        print(line.decode('utf-8'))
"
```

## 📚 Understanding the Architecture

### Key Modules

| Module | Purpose |
|--------|---------|
| `main.py` | 🎬 Entry point, app initialization |
| `config.py` | ⚙️ Configuration management |
| `models.py` | 📋 Data structures & validation |
| `utils.py` | 🔧 Utility functions |
| `agent.py` | 🤖 LangGraph agent setup |
| `serializers.py` | 📦 Message serialization |
| `services.py` | 💼 Business logic |
| `routes.py` | 🛣️ API endpoints |

### What Happens When You Send a Message

1. **Request arrives** → `routes.py` validates input
2. **Service starts** → `services.py` creates `ChatStreamService`
3. **Agent runs** → `agent.py` processes with LLM
4. **Tool selection** → Model decides which tools to use
5. **Tool execution** → `agent.py` executes the tool
6. **Streaming** → Events emitted in real-time to frontend
7. **Serialization** → `serializers.py` formats responses
8. **Frontend receives** → SSE stream with tool updates

## 🧪 Testing Your Setup

### Health Check

```bash
curl http://localhost:8000/api/health
```

Expected response:
```json
{"status": "ok", "service": "perplexity-2.0-backend"}
```

### Simple Query

```bash
curl -N "http://localhost:8000/api/chat_stream/hello"
```

You should see SSE events streaming in real-time.

## 🐛 Debugging

### Enable Debug Logging

```bash
LOG_LEVEL=DEBUG python main.py
```

### Check API Documentation

Open http://localhost:8000/docs in your browser for interactive API docs.

### Stream Events in Python

```python
import requests
import json

url = 'http://localhost:8000/api/chat_stream/tell%20me%20a%20joke'
response = requests.get(url, stream=True)

for line in response.iter_lines():
    if line.startswith(b'event:'):
        print("Event:", line.decode('utf-8')[7:])
    elif line.startswith(b'data:'):
        data = json.loads(line.decode('utf-8')[6:])
        print("Data:", json.dumps(data, indent=2))
```

## 📁 Project Layout

```
perplexity-2-0-server/
├── main.py                      # Start here
├── config.py                    # Environment config
├── models.py                    # Type definitions
├── utils.py                     # Helper functions
├── agent.py                     # LLM & tools
├── serializers.py               # Message formatting
├── services.py                  # Core logic
├── routes.py                    # API endpoints
├── app_legacy.py                # Original monolithic code
├── pyproject.toml               # Dependencies
├── .env                         # Configuration (create this)
├── README.md                    # Original README
├── README_ARCHITECTURE.md       # Detailed architecture
└── QUICKSTART.md                # This file
```

## 🔄 Development Workflow

### Making Changes

1. **Edit a module** (e.g., `services.py`)
2. **Server auto-reloads** (dev mode)
3. **Test your changes** with curl or Python client
4. **Check logs** for errors

### Adding New Features

1. Add data models in `models.py`
2. Add business logic in `services.py`
3. Add routes in `routes.py`
4. Update `config.py` if new settings needed
5. Add utility functions in `utils.py` if reusable

### Best Practices

✅ Use type hints everywhere  
✅ Add docstrings to functions  
✅ Keep modules focused  
✅ Handle errors gracefully  
✅ Log important events  
✅ Write tests for new code  

## 🚀 Moving to Production

### Build Docker Image

```dockerfile
FROM python:3.13-slim

WORKDIR /app
COPY . .

RUN pip install -e .

ENV PYTHONUNBUFFERED=1

CMD ["python", "main.py"]
```

Build it:
```bash
docker build -t perplexity-backend:latest .
```

Run it:
```bash
docker run \
  -e GROQ_API_KEY=your-key \
  -e HOST=0.0.0.0 \
  -e PORT=8000 \
  -p 8000:8000 \
  perplexity-backend:latest
```

### Environment for Production

```env
# Use specific API keys, not wildcards
GROQ_API_KEY=sk-xxxxxxxxxxxx

# Restrict CORS origins
CORS_ORIGINS=["https://yourdomain.com"]

# Disable debug mode
DEBUG=False
LOG_LEVEL=INFO

# Use proper host/port
HOST=0.0.0.0
PORT=8000
```

## 📞 Getting Help

### Common Issues

**"ModuleNotFoundError: No module named 'main'"**
- Make sure you're in the project directory
- Activate virtual environment: `source venv/bin/activate`

**"GROQ_API_KEY not found"**
- Create `.env` file with your API key
- Or set it: `export GROQ_API_KEY=your-key`

**"Connection refused"**
- Server not running? Start with: `python main.py`
- Wrong port? Check with: `lsof -i :8000` (macOS/Linux)

**Events not streaming**
- Check logs for errors
- Verify `GROQ_API_KEY` is set
- Try a health check: `curl http://localhost:8000/api/health`

## 📖 Next Steps

1. Read [README_ARCHITECTURE.md](README_ARCHITECTURE.md) for detailed architecture
2. Check [STREAMING_EVENTS.md](STREAMING_EVENTS.md) for event documentation
3. Review [FRONTEND_REACT_EXAMPLE.md](FRONTEND_REACT_EXAMPLE.md) for frontend integration
4. Start building your UI!

## 🎯 What This Backend Does

- 🔍 **Search**: Uses Tavily Search tool to find information
- 🧠 **Reasoning**: Uses Groq's LLM to understand queries and generate responses
- 📡 **Streaming**: Real-time events showing tool selection, execution, and results
- 💬 **Conversations**: Maintains context across messages with checkpoint system
- 🔄 **Tool Execution**: Automatically selects and runs relevant tools

Enjoy! 🚀
