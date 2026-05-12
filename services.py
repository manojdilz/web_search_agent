"""
Service layer for chat streaming logic.
Handles the main business logic of streaming responses with tool tracking.
"""

import json
import logging
from typing import AsyncGenerator, Generator, Optional
from uuid import uuid4
from langchain.messages import HumanMessage, AIMessageChunk, ToolMessage

from utils import ToolArgumentParser, SSEEventBuilder, ContentNormalizer
from serializers import MessageSerializer, PayloadBuilder

logger = logging.getLogger(__name__)


class ToolTracker:
    """Tracks tool calls throughout the streaming session."""

    def __init__(self):
        """Initialize tool tracker."""
        self.pending_calls: dict[str, dict] = {}
        self.seen_call_ids: set[str] = set()
        self.execution_started: set[str] = set()

    def mark_seen(self, tool_id: str) -> bool:
        """
        Mark tool call as seen.

        Args:
            tool_id: Tool call ID

        Returns:
            True if this is first time seeing this ID
        """
        if tool_id in self.seen_call_ids:
            return False
        self.seen_call_ids.add(tool_id)
        return True

    def add_pending(self, tool_id: str, tool_name: str, args: dict) -> None:
        """Record pending tool call."""
        self.pending_calls[tool_id] = {
            "name": tool_name,
            "args": args,
        }

    def get_pending(self, tool_id: str) -> dict:
        """Get pending tool information."""
        return self.pending_calls.get(tool_id, {})

    def remove_pending(self, tool_id: str) -> None:
        """Remove tool from pending."""
        self.pending_calls.pop(tool_id, None)

    def mark_execution_started(self, tool_id: str) -> bool:
        """
        Mark tool execution as started.

        Returns:
            True if first time marking execution started
        """
        if tool_id in self.execution_started:
            return False
        self.execution_started.add(tool_id)
        return True


class ChatStreamService:
    """Service for streaming chat responses with tool tracking."""

    def __init__(self, graph):
        """
        Initialize chat stream service.

        Args:
            graph: Compiled LangGraph agent
        """
        self.graph = graph
        self.sse_builder = SSEEventBuilder()

    async def stream_response(
        self,
        message: str,
        checkpoint_id: Optional[str] = None,
    ) -> AsyncGenerator[str, None]:
        """
        Stream a chat response with real-time tool tracking.

        Args:
            message: User message
            checkpoint_id: Optional checkpoint ID for session continuation

        Yields:
            SSE formatted event strings
        """
        thread_id = checkpoint_id or str(uuid4())
        run_config = {"configurable": {"thread_id": thread_id}}

        tracker = ToolTracker()

        try:
            async for event in self.graph.astream(
                {"messages": [HumanMessage(content=message)]},
                config=run_config,
                stream_mode="messages"
            ):
                # Validate event format
                if not isinstance(event, tuple) or len(event) != 2:
                    continue

                msg, metadata = event

                # Handle different message types
                if isinstance(msg, ToolMessage):
                    for chunk in self._handle_tool_message(msg, tracker):
                        yield chunk
                elif isinstance(msg, AIMessageChunk):
                    for chunk in self._handle_ai_chunk(msg, tracker):
                        yield chunk
                else:
                    for chunk in self._handle_ai_message(msg, tracker):
                        yield chunk

            # Emit completion event
            yield self.sse_builder.build_event(
                "done",
                PayloadBuilder.build_done(thread_id)
            )

        except Exception as e:
            logger.error(f"Error streaming response: {e}")
            yield self.sse_builder.build_event(
                "error",
                {"message": str(e), "checkpoint_id": thread_id}
            )

    def _handle_tool_message(
        self,
        msg: ToolMessage,
        tracker: ToolTracker,
    ) -> Generator[str, None, None]:
        """
        Handle tool message (results from tool execution).

        Args:
            msg: Tool message
            tracker: Tool tracker instance

        Yields:
            SSE events
        """
        tool_call_id = getattr(msg, "tool_call_id", None)
        tool_info = tracker.get_pending(tool_call_id) if tool_call_id else {}

        # Emit executing event if we haven't already
        if tool_call_id and tracker.mark_execution_started(tool_call_id):
            yield self.sse_builder.build_event(
                "tool_executing",
                PayloadBuilder.build_tool_executing(
                    tool_call_id=tool_call_id,
                    tool_name=tool_info.get("name", ""),
                    args=tool_info.get("args", {}),
                )
            )

        # Parse and emit result
        if tool_call_id:
            tracker.remove_pending(tool_call_id)
            content = ContentNormalizer.normalize(
                getattr(msg, "content", None)
            )

            yield self.sse_builder.build_event(
                "tool_result",
                PayloadBuilder.build_tool_result(
                    tool_call_id=tool_call_id,
                    tool_name=tool_info.get("name"),
                    content=content,
                    artifact=getattr(msg, "artifact", None),
                )
            )

    def _handle_ai_chunk(
        self,
        msg: AIMessageChunk,
        tracker: ToolTracker,
    ) -> Generator[str, None, None]:
        """
        Handle AI message chunk (streaming content).

        Args:
            msg: AI message chunk
            tracker: Tool tracker instance

        Yields:
            SSE events for tool selection and chunks
        """
        # Process tool calls in chunk
        for chunk in self._process_tool_calls(msg, tracker):
            yield chunk

        # Emit chunk if it has content or tool calls
        serialized = MessageSerializer.serialize_ai_chunk(msg)
        if serialized.content or serialized.has_tool_calls:
            yield self.sse_builder.build_event(
                "assistant",
                PayloadBuilder.build_assistant_chunk(serialized)
            )

    def _handle_ai_message(
        self,
        msg,
        tracker: ToolTracker,
    ) -> Generator[str, None, None]:
        """
        Handle complete AI message.

        Args:
            msg: AI message
            tracker: Tool tracker instance

        Yields:
            SSE events
        """
        # Process tool calls in message
        for chunk in self._process_tool_calls(msg, tracker):
            yield chunk

        # Emit message if it has content
        if hasattr(msg, "content"):
            content = ContentNormalizer.normalize(
                getattr(msg, "content", None)
            )
            if content:
                yield self.sse_builder.build_event(
                    "assistant",
                    PayloadBuilder.build_assistant_message(
                        content=content,
                        message_id=getattr(msg, "id", None),
                    )
                )

    def _process_tool_calls(
        self,
        msg,
        tracker: ToolTracker,
    ) -> Generator[str, None, None]:
        """
        Extract and process tool calls from message.

        Args:
            msg: Message containing tool calls
            tracker: Tool tracker instance

        Yields:
            SSE events for tool selection
        """
        # Extract tool calls
        tool_calls = self._extract_tool_calls(msg)

        if not tool_calls:
            return

        # Build tool call dictionaries
        new_tools = []
        for tc_data in tool_calls:
            tool_id = tc_data.get("id")

            # Skip if already seen
            if not tool_id or not tracker.mark_seen(tool_id):
                continue

            tool_name = tc_data.get("name")
            args = ToolArgumentParser.parse(tc_data.get("args", {}))

            # Track pending tool
            tracker.add_pending(tool_id, tool_name, args)

            # Add to new tools list
            new_tools.append(
                PayloadBuilder.build_tool_call_dict(
                    tool_call_id=tool_id,
                    tool_name=tool_name,
                    args=args,
                )
            )

        # Emit tool selection event if we have new tools
        if new_tools:
            yield self.sse_builder.build_event(
                "tool_selected",
                PayloadBuilder.build_tool_selected_payload(new_tools)
            )

    @staticmethod
    def _extract_tool_calls(msg) -> list[dict]:
        """
        Extract tool calls from message.

        Args:
            msg: Message object

        Returns:
            List of tool call dictionaries
        """
        tool_calls = []

        if hasattr(msg, "tool_calls"):
            tc = getattr(msg, "tool_calls", None) or []
            tool_calls.extend(tc)

        if hasattr(msg, "tool_call_chunks"):
            tc_chunks = getattr(msg, "tool_call_chunks", None) or []
            tool_calls.extend(tc_chunks)

        # Normalize to dict format
        return [
            (tc if isinstance(tc, dict) else {
                "id": getattr(tc, "id", None),
                "name": getattr(tc, "name", None),
                "args": getattr(tc, "args", None),
            })
            for tc in tool_calls
        ]
