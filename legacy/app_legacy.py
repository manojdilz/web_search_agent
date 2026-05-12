"""
Monolithic legacy implementation (for reference).
Use main.py for the refactored production version.

This file contains the original bulky implementation before architectural improvements.
"""

from langgraph.graph import StateGraph, START, END, add_messages
from langgraph.checkpoint.memory import InMemorySaver
from langchain.chat_models import init_chat_model
from langchain.messages import HumanMessage, AIMessageChunk, ToolMessage
from langchain_tavily import TavilySearch
from fastapi import FastAPI, Query
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from uuid import uuid4
from typing import TypedDict, Annotated, Optional
from dotenv import load_dotenv
import json
import os
import asyncio

load_dotenv()


# Node names
MODEL_NODE = "model"
TOOL_NODE = "tool_node"

memory = InMemorySaver()


class State(TypedDict):
    messages: Annotated[list, add_messages]


search_tool = TavilySearch(max_results=4)
tools = [search_tool]

llm = init_chat_model(
    model="meta-llama/llama-4-scout-17b-16e-instruct",
    model_provider="groq",
    api_key=os.environ["GROQ_API_KEY"]
).bind_tools(tools)


async def model(state: State):
    result = await llm.ainvoke(state["messages"])
    return {
        "messages": [result]
    }


async def tool_router(state: State):
    last_msg = state["messages"][-1]

    if (hasattr(last_msg, "tool_calls") and len(last_msg.tool_calls) > 0):
        return TOOL_NODE
    else:
        return END


async def tool_node(state: State):
    tool_calls = state["messages"][-1].tool_calls

    tool_messages = []
    for tool_call in tool_calls:
        tool_name = tool_call["name"]
        tool_args = tool_call["args"]
        tool_id = tool_call["id"]

        if tool_name == search_tool.name:
            search_results = await search_tool.ainvoke(tool_args)
            tool_message = ToolMessage(
                content=str(search_results),
                tool_call_id=tool_id,
                name=tool_name
            )
            tool_messages.append(tool_message)

    return {"messages": tool_messages}


graph_builder = StateGraph(State)

graph_builder.add_node(MODEL_NODE, model)
graph_builder.add_node(TOOL_NODE, tool_node)

graph_builder.add_edge(START, MODEL_NODE)
graph_builder.add_conditional_edges(MODEL_NODE, tool_router)
graph_builder.add_edge(TOOL_NODE, MODEL_NODE)

graph = graph_builder.compile(checkpointer=memory)
config = {
    "configurable": {
        "thread_id": "1"
    }
}

app = FastAPI()

# Allow CORS for all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
    expose_headers=["Content-Type"]
)


def _normalise_content(value):
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, dict):
        return {k: _normalise_content(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_normalise_content(v) for v in value]
    return str(value)


def _parse_tool_args(args):
    if isinstance(args, str):
        try:
            return json.loads(args)
        except Exception:
            return args
    return args


def serialise_ai_msg_chunk(chunk):
    """
    Serialize an AI message chunk with comprehensive tool call information.
    Includes tool calls/chunks for frontend to track tool invocations.
    """
    content = _normalise_content(getattr(chunk, "content", None))
    tool_calls = _normalise_content(getattr(chunk, "tool_calls", []))
    tool_call_chunks = _normalise_content(
        getattr(chunk, "tool_call_chunks", []))

    return {
        "type": getattr(chunk, "type", "AIMessageChunk"),
        "id": getattr(chunk, "id", None),
        "content": content or "",  # Ensure content is always present
        "has_tool_calls": bool(tool_calls or tool_call_chunks),
        "tool_calls": tool_calls,
        "tool_call_chunks": tool_call_chunks,
        "chunk_position": getattr(chunk, "chunk_position", None),
        "response_metadata": _normalise_content(getattr(chunk, "response_metadata", {})),
        "additional_kwargs": _normalise_content(getattr(chunk, "additional_kwargs", {})),
    }


def _sse_event(event_type: str, payload: dict):
    return f"event: {event_type}\ndata: {json.dumps(payload, default=str)}\n\n"


async def generate_chat_response(message: str, checkpoint_id: Optional[str] = None):
    """
    Stream chat response with real-time tool execution updates.

    Events emitted:
    - tool_selected: When model selects tools to use (status: "selected")
    - tool_executing: When tool is executing (status: "executing") 
    - tool_result: When tool completes and returns results (status: "completed")
    - assistant: When streaming AI response chunks
    - done: When response is complete
    """
    thread_id = checkpoint_id or str(uuid4())
    run_config = {
        "configurable": {
            "thread_id": thread_id
        }
    }

    pending_tool_calls: dict[str, dict] = {}
    seen_tool_call_ids: set[str] = set()
    # Track which tools have started executing
    tool_execution_started: set[str] = set()

    async for event in graph.astream(
        {"messages": [HumanMessage(content=message)]},
        config=run_config,
        stream_mode="messages"
    ):
        if not isinstance(event, tuple) or len(event) != 2:
            continue

        msg, metadata = event

        # Handle tool results - emitted when tool completes execution
        if isinstance(msg, ToolMessage):
            tool_call_id = getattr(msg, "tool_call_id", None)
            tool_info = pending_tool_calls.get(
                tool_call_id, {}) if tool_call_id else {}

            # Emit tool_executing event if we haven't already for this tool
            if tool_call_id and tool_call_id not in tool_execution_started:
                tool_execution_started.add(tool_call_id)
                yield _sse_event(
                    "tool_executing",
                    {
                        "tool_call_id": tool_call_id,
                        "tool_name": tool_info.get("name"),
                        "status": "executing",
                        "args": _normalise_content(tool_info.get("args", {})),
                    },
                )

            # Parse tool result content
            content = _normalise_content(getattr(msg, "content", None))
            try:
                # Try to parse content as JSON for better structure
                if isinstance(content, str):
                    parsed_content = json.loads(content)
                else:
                    parsed_content = content
            except Exception:
                parsed_content = content

            # Emit tool_result event with completion status
            pending_tool_calls.pop(tool_call_id, None)
            yield _sse_event(
                "tool_result",
                {
                    "tool_call_id": tool_call_id,
                    "tool_name": tool_info.get("name"),
                    "status": "completed",
                    "content": parsed_content,
                    "artifact": _normalise_content(getattr(msg, "artifact", None)),
                },
            )
            continue

        # Extract tool calls from AI message
        tool_calls = []
        if hasattr(msg, "tool_calls"):
            tool_calls = getattr(msg, "tool_calls", []) or []
        if hasattr(msg, "tool_call_chunks"):
            tool_calls = tool_calls or getattr(
                msg, "tool_call_chunks", []) or []

        def _tool_call_to_dict(tool_call):
            """Convert tool call object to dictionary format."""
            if isinstance(tool_call, dict):
                return tool_call
            return {
                "id": getattr(tool_call, "id", None),
                "name": getattr(tool_call, "name", None),
                "args": getattr(tool_call, "args", None),
            }

        # Process new tool selections
        new_tool_events = []
        for tc in tool_calls:
            tc_data = _tool_call_to_dict(tc)
            tool_id = tc_data.get("id")

            # Skip if already seen or no ID
            if not tool_id or tool_id in seen_tool_call_ids:
                continue

            seen_tool_call_ids.add(tool_id)
            tool_name = tc_data.get("name")
            args = _parse_tool_args(tc_data.get("args", {}))

            # Store tool info for later use in result handling
            pending_tool_calls[tool_id] = {
                "name": tool_name,
                "args": args,
            }

            new_tool_events.append({
                "tool_call_id": tool_id,
                "tool_name": tool_name,
                "args": _normalise_content(args),
                "status": "selected",  # Explicitly mark as selected
            })

        # Emit tool_selected event with all new tools
        if new_tool_events:
            yield _sse_event(
                "tool_selected",
                {
                    "tools": new_tool_events,
                    "count": len(new_tool_events),
                    "timestamp": _normalise_content(metadata) if metadata else None,
                },
            )

        # Stream AI message chunks in real-time
        if isinstance(msg, AIMessageChunk):
            serialized = serialise_ai_msg_chunk(msg)
            # Only emit if there's actual content or tool information
            if serialized["content"] or serialized["has_tool_calls"]:
                yield _sse_event(
                    "assistant",
                    {
                        "type": "chunk",
                        "chunk": serialized,
                    },
                )
            continue

        # Handle complete AI messages
        if hasattr(msg, "content"):
            content = _normalise_content(getattr(msg, "content", None))
            if content:  # Only emit if there's content
                yield _sse_event(
                    "assistant",
                    {
                        "type": "message",
                        "content": content,
                        "id": getattr(msg, "id", None),
                    },
                )

    # Signal completion with thread ID for session continuation
    yield _sse_event("done", {
        "checkpoint_id": thread_id,
        "status": "completed"
    })


@app.get("/chat_stream/{message}")
async def chat_stream(message: str, checkpoint_id: Optional[str] = Query(None)):
    return StreamingResponse(
        generate_chat_response(message, checkpoint_id),
        media_type="text/event-stream"
    )
