"""
Message serialization and event payload builders.
Converts internal message objects to frontend-ready formats.
"""

import json
import logging
from typing import Any, Optional
from langchain.messages import AIMessageChunk

from models import (
    AIMessageChunkData,
    ToolCallDict,
    ToolExecutingPayload,
    ToolResultPayload,
)
from utils import ContentNormalizer, AttributeExtractor

logger = logging.getLogger(__name__)


class MessageSerializer:
    """Handles serialization of various message types."""

    @staticmethod
    def serialize_ai_chunk(chunk: AIMessageChunk) -> AIMessageChunkData:
        """
        Serialize an AI message chunk for streaming.

        Args:
            chunk: AI message chunk to serialize

        Returns:
            Serialized chunk data
        """
        content = ContentNormalizer.normalize(
            AttributeExtractor.get(chunk, "content")
        )
        tool_calls = ContentNormalizer.normalize(
            AttributeExtractor.get(chunk, "tool_calls", [])
        )
        tool_call_chunks = ContentNormalizer.normalize(
            AttributeExtractor.get(chunk, "tool_call_chunks", [])
        )

        return AIMessageChunkData(
            type=AttributeExtractor.get(chunk, "type", "AIMessageChunk"),
            id=AttributeExtractor.get(chunk, "id"),
            content=content or "",
            has_tool_calls=bool(tool_calls or tool_call_chunks),
            tool_calls=tool_calls,
            tool_call_chunks=tool_call_chunks,
            chunk_position=AttributeExtractor.get(chunk, "chunk_position"),
            response_metadata=ContentNormalizer.normalize(
                AttributeExtractor.get(chunk, "response_metadata", {})
            ),
            additional_kwargs=ContentNormalizer.normalize(
                AttributeExtractor.get(chunk, "additional_kwargs", {})
            ),
        )


class PayloadBuilder:
    """Builds event payloads for SSE streaming."""

    @staticmethod
    def build_tool_executing(
        tool_call_id: str,
        tool_name: str,
        args: dict[str, Any],
    ) -> dict:
        """Build tool_executing event payload."""
        payload = ToolExecutingPayload(
            tool_call_id=tool_call_id,
            tool_name=tool_name,
            args=ContentNormalizer.normalize(args),
        )
        return payload.model_dump()

    @staticmethod
    def build_tool_result(
        tool_call_id: str,
        tool_name: Optional[str],
        content: Any,
        artifact: Optional[Any] = None,
    ) -> dict:
        """Build tool_result event payload."""
        # Try to parse content as JSON if it's a string
        try:
            parsed_content = (
                json.loads(content)
                if isinstance(content, str)
                else content
            )
        except (json.JSONDecodeError, ValueError):
            parsed_content = content

        payload = ToolResultPayload(
            tool_call_id=tool_call_id,
            tool_name=tool_name,
            content=parsed_content,
            artifact=ContentNormalizer.normalize(artifact),
        )
        return payload.model_dump()

    @staticmethod
    def build_tool_call_dict(
        tool_call_id: str,
        tool_name: str,
        args: dict[str, Any],
    ) -> ToolCallDict:
        """Build a tool call data structure."""
        return ToolCallDict(
            tool_call_id=tool_call_id,
            tool_name=tool_name,
            args=ContentNormalizer.normalize(args),
            status="selected",
        )

    @staticmethod
    def build_tool_selected_payload(
        tools: list[ToolCallDict],
        metadata: Optional[dict] = None,
    ) -> dict:
        """Build tool_selected event payload."""
        return {
            "tools": [t.model_dump() for t in tools],
            "count": len(tools),
            "timestamp": ContentNormalizer.normalize(metadata) if metadata else None,
        }

    @staticmethod
    def build_assistant_chunk(chunk_data: AIMessageChunkData) -> dict:
        """Build assistant chunk payload."""
        return {
            "type": "chunk",
            "chunk": chunk_data.model_dump(),
        }

    @staticmethod
    def build_assistant_message(
        content: str,
        message_id: Optional[str] = None,
    ) -> dict:
        """Build complete assistant message payload."""
        return {
            "type": "message",
            "content": content,
            "id": message_id,
        }

    @staticmethod
    def build_done(checkpoint_id: str) -> dict:
        """Build completion event payload."""
        return {
            "checkpoint_id": checkpoint_id,
            "status": "completed",
        }
