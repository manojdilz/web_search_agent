"""
Data models and schemas for the application.
Defines TypedDict structures and Pydantic models for type safety.
"""

from typing import TypedDict, Annotated, Any, Optional, Union
from langgraph.graph import add_messages
from pydantic import BaseModel, Field


class State(TypedDict):
    """Graph state definition for LangGraph agent."""
    messages: Annotated[list, add_messages]


# Event Payloads
class ToolCallDict(BaseModel):
    """Tool call data structure."""
    tool_call_id: str
    tool_name: str
    args: dict[str, Any]
    status: str = "selected"


class ToolSelectedPayload(BaseModel):
    """Payload for tool_selected event."""
    tools: list[ToolCallDict]
    count: int
    timestamp: Optional[dict] = None


class ToolExecutingPayload(BaseModel):
    """Payload for tool_executing event."""
    tool_call_id: str
    tool_name: str
    status: str = "executing"
    args: dict[str, Any]


class ToolResultPayload(BaseModel):
    """Payload for tool_result event."""
    tool_call_id: str
    tool_name: Optional[str]
    status: str = "completed"
    content: Any
    artifact: Optional[Any] = None


class AIMessageChunkData(BaseModel):
    """Serialized AI message chunk data."""
    type: str
    id: Optional[str]
    content: str
    has_tool_calls: bool
    tool_calls: list[Any]
    tool_call_chunks: list[Any]
    chunk_position: Optional[Union[int, str]]
    response_metadata: dict[str, Any]
    additional_kwargs: dict[str, Any]


class AssistantChunkPayload(BaseModel):
    """Payload for streaming assistant chunks."""
    type: str = "chunk"
    chunk: AIMessageChunkData


class AssistantMessagePayload(BaseModel):
    """Payload for complete assistant message."""
    type: str = "message"
    content: str
    id: Optional[str]


class DonePayload(BaseModel):
    """Payload for completion event."""
    checkpoint_id: str
    status: str = "completed"


class ChatRequest(BaseModel):
    """Request model for chat endpoint."""
    message: str = Field(..., description="User message")
    checkpoint_id: Optional[str] = Field(
        None, description="Session checkpoint for conversation continuation")
