# Frontend Implementation Guide - React Example

Complete React component example for handling streaming chat with tool execution display.

## Installation Requirements

```bash
npm install react axios
```

## Component Implementation

```typescript
import React, { useState, useRef, useEffect } from 'react';
import './ChatComponent.css';

interface ToolCall {
  tool_call_id: string;
  tool_name: string;
  args: Record<string, any>;
  status: 'selected' | 'executing' | 'completed';
  result?: any;
}

interface Message {
  id: string;
  type: 'user' | 'assistant';
  content: string;
  tools?: ToolCall[];
  timestamp: Date;
}

export const ChatComponent: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [checkpointId, setCheckpointId] = useState<string | null>(null);
  const [toolStates, setToolStates] = useState<Map<string, ToolCall>>(new Map());
  const [currentAssistantMessage, setCurrentAssistantMessage] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new messages arrive
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, currentAssistantMessage, toolStates]);

  const streamChat = async (userMessage: string) => {
    // Add user message
    const userMsg: Message = {
      id: Date.now().toString(),
      type: 'user',
      content: userMessage,
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, userMsg]);

    setLoading(true);
    setCurrentAssistantMessage('');
    setToolStates(new Map());

    try {
      const params = new URLSearchParams();
      if (checkpointId) {
        params.append('checkpoint_id', checkpointId);
      }

      const url = `/chat_stream/${encodeURIComponent(userMessage)}?${params.toString()}`;
      const eventSource = new EventSource(url);

      eventSource.addEventListener('tool_selected', (e) => {
        const data = JSON.parse(e.data);
        console.log('Tools selected:', data);

        data.tools.forEach((tool: any) => {
          setToolStates((prev) => {
            const newMap = new Map(prev);
            newMap.set(tool.tool_call_id, {
              tool_call_id: tool.tool_call_id,
              tool_name: tool.tool_name,
              args: tool.args,
              status: 'selected',
            });
            return newMap;
          });
        });
      });

      eventSource.addEventListener('tool_executing', (e) => {
        const data = JSON.parse(e.data);
        console.log('Tool executing:', data.tool_name);

        setToolStates((prev) => {
          const newMap = new Map(prev);
          const existing = newMap.get(data.tool_call_id);
          if (existing) {
            newMap.set(data.tool_call_id, {
              ...existing,
              status: 'executing',
            });
          }
          return newMap;
        });
      });

      eventSource.addEventListener('tool_result', (e) => {
        const data = JSON.parse(e.data);
        console.log('Tool result:', data);

        setToolStates((prev) => {
          const newMap = new Map(prev);
          const existing = newMap.get(data.tool_call_id);
          if (existing) {
            newMap.set(data.tool_call_id, {
              ...existing,
              status: 'completed',
              result: data.content,
            });
          }
          return newMap;
        });
      });

      eventSource.addEventListener('assistant', (e) => {
        const data = JSON.parse(e.data);

        if (data.type === 'chunk') {
          // Stream chunks in real-time
          const content = data.chunk?.content || '';
          setCurrentAssistantMessage((prev) => prev + content);
        } else if (data.type === 'message') {
          // Complete message
          setCurrentAssistantMessage(data.content);
        }
      });

      eventSource.addEventListener('done', (e) => {
        const data = JSON.parse(e.data);
        console.log('Stream complete, checkpoint:', data.checkpoint_id);

        // Save checkpoint for session continuation
        setCheckpointId(data.checkpoint_id);

        // Add assistant message with tool info
        if (currentAssistantMessage) {
          const assistantMsg: Message = {
            id: Date.now().toString(),
            type: 'assistant',
            content: currentAssistantMessage,
            tools: Array.from(toolStates.values()),
            timestamp: new Date(),
          };
          setMessages((prev) => [...prev, assistantMsg]);
        }

        setLoading(false);
        eventSource.close();
      });

      eventSource.addEventListener('error', (e) => {
        console.error('Stream error:', e);
        setLoading(false);
        eventSource.close();
      });
    } catch (error) {
      console.error('Error streaming chat:', error);
      setLoading(false);
    }
  };

  const handleSendMessage = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || loading) return;

    streamChat(input);
    setInput('');
  };

  const getToolStatusIcon = (status: string) => {
    switch (status) {
      case 'selected':
        return '◆';
      case 'executing':
        return '⟳';
      case 'completed':
        return '✓';
      default:
        return '●';
    }
  };

  const getToolStatusColor = (status: string) => {
    switch (status) {
      case 'selected':
        return 'tool-selected';
      case 'executing':
        return 'tool-executing';
      case 'completed':
        return 'tool-completed';
      default:
        return '';
    }
  };

  return (
    <div className="chat-container">
      <div className="messages-container">
        {messages.map((msg) => (
          <div key={msg.id} className={`message message-${msg.type}`}>
            <div className="message-content">
              {msg.content}
            </div>

            {msg.tools && msg.tools.length > 0 && (
              <div className="tools-section">
                <div className="tools-title">Tools Used:</div>
                {msg.tools.map((tool) => (
                  <div
                    key={tool.tool_call_id}
                    className={`tool-item ${getToolStatusColor(tool.status)}`}
                  >
                    <span className="tool-icon">
                      {getToolStatusIcon(tool.status)}
                    </span>
                    <span className="tool-name">{tool.tool_name}</span>
                    <span className="tool-status">{tool.status}</span>

                    {tool.args && (
                      <div className="tool-args">
                        Query: {JSON.stringify(tool.args).substring(0, 50)}...
                      </div>
                    )}

                    {tool.result && (
                      <div className="tool-result">
                        <details>
                          <summary>Results ({Array.isArray(tool.result) ? tool.result.length : 1})</summary>
                          <pre>{JSON.stringify(tool.result, null, 2).substring(0, 300)}...</pre>
                        </details>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}

            <div className="message-time">
              {msg.timestamp.toLocaleTimeString()}
            </div>
          </div>
        ))}

        {/* Current streaming message */}
        {loading && currentAssistantMessage && (
          <div className="message message-assistant streaming">
            <div className="message-content">
              {currentAssistantMessage}
              <span className="cursor">▌</span>
            </div>
          </div>
        )}

        {/* Tool execution status */}
        {loading && toolStates.size > 0 && (
          <div className="tools-status">
            {Array.from(toolStates.values()).map((tool) => (
              <div
                key={tool.tool_call_id}
                className={`tool-status-item ${getToolStatusColor(tool.status)}`}
              >
                <span className="tool-icon">
                  {getToolStatusIcon(tool.status)}
                </span>
                <span className="tool-name">{tool.tool_name}</span>
                {tool.status === 'executing' && (
                  <span className="spinner"></span>
                )}
              </div>
            ))}
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      <form className="input-form" onSubmit={handleSendMessage}>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask me anything..."
          disabled={loading}
          className="input-field"
        />
        <button type="submit" disabled={loading} className="send-button">
          {loading ? 'Sending...' : 'Send'}
        </button>
        {checkpointId && (
          <span className="checkpoint-indicator" title={`Session: ${checkpointId}`}>
            🔗
          </span>
        )}
      </form>
    </div>
  );
};

export default ChatComponent;
```

## Styling (ChatComponent.css)

```css
.chat-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  background: #f5f5f5;
}

.message {
  margin-bottom: 16px;
  padding: 12px 16px;
  border-radius: 8px;
  max-width: 80%;
  word-wrap: break-word;
  animation: slideIn 0.3s ease-in-out;
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.message-user {
  align-self: flex-end;
  background: #667eea;
  color: white;
  margin-left: auto;
}

.message-assistant {
  align-self: flex-start;
  background: white;
  color: #333;
  border: 1px solid #e0e0e0;
}

.message-assistant.streaming {
  background: #f9f9f9;
}

.message-content {
  font-size: 14px;
  line-height: 1.5;
}

.cursor {
  animation: blink 1s infinite;
}

@keyframes blink {
  0%, 49% {
    opacity: 1;
  }
  50%, 100% {
    opacity: 0;
  }
}

.tools-section {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid #e0e0e0;
}

.tools-title {
  font-size: 12px;
  font-weight: 600;
  color: #666;
  margin-bottom: 8px;
  text-transform: uppercase;
}

.tool-item {
  background: #f9f9f9;
  border-left: 3px solid #999;
  padding: 8px 12px;
  margin-bottom: 6px;
  border-radius: 4px;
  font-size: 12px;
}

.tool-selected {
  border-left-color: #ffc107;
  background: #fffaf0;
}

.tool-executing {
  border-left-color: #2196f3;
  background: #f0f8ff;
}

.tool-completed {
  border-left-color: #4caf50;
  background: #f0f8f0;
}

.tool-icon {
  margin-right: 6px;
  font-weight: bold;
}

.tool-name {
  font-weight: 600;
  margin-right: 8px;
}

.tool-status {
  font-size: 11px;
  color: #999;
  text-transform: uppercase;
}

.tool-args {
  margin-top: 4px;
  font-size: 11px;
  color: #666;
}

.tool-result {
  margin-top: 6px;
}

.tool-result summary {
  cursor: pointer;
  color: #667eea;
  font-weight: 500;
}

.tool-result pre {
  background: white;
  padding: 8px;
  border-radius: 4px;
  font-size: 11px;
  overflow-x: auto;
  margin-top: 4px;
}

.tools-status {
  background: #f0f0f0;
  padding: 12px;
  border-radius: 8px;
  margin-bottom: 12px;
}

.tool-status-item {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  background: white;
  border-radius: 4px;
  font-size: 12px;
  margin-right: 8px;
  margin-bottom: 6px;
}

.spinner {
  display: inline-block;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.input-form {
  display: flex;
  gap: 8px;
  padding: 16px;
  background: white;
  border-top: 1px solid #e0e0e0;
}

.input-field {
  flex: 1;
  padding: 12px 16px;
  border: 1px solid #ddd;
  border-radius: 24px;
  font-size: 14px;
  outline: none;
  transition: border-color 0.3s;
}

.input-field:focus {
  border-color: #667eea;
}

.input-field:disabled {
  background: #f5f5f5;
  cursor: not-allowed;
}

.send-button {
  padding: 12px 24px;
  background: #667eea;
  color: white;
  border: none;
  border-radius: 24px;
  cursor: pointer;
  font-weight: 600;
  transition: background 0.3s;
}

.send-button:hover:not(:disabled) {
  background: #5568d3;
}

.send-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.checkpoint-indicator {
  padding: 0 12px;
  font-size: 16px;
  display: flex;
  align-items: center;
}

.message-time {
  font-size: 11px;
  color: #999;
  margin-top: 6px;
}
```

## Key Features

1. **Real-time Streaming**: Messages appear word by word as they stream
2. **Tool Visualization**: Shows tool progression (selected → executing → completed)
3. **Tool Results**: Collapsible tool results with detailed information
4. **Session Persistence**: Uses checkpoint_id to maintain conversation context
5. **Smooth Animations**: Sliding messages, blinking cursor, spinning loader
6. **Responsive Design**: Adapts to different screen sizes
7. **Error Handling**: Graceful error recovery

## Usage

```typescript
import ChatComponent from './ChatComponent';

function App() {
  return (
    <div>
      <ChatComponent />
    </div>
  );
}

export default App;
```
