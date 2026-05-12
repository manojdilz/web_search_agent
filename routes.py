"""
API routes and endpoint handlers.
Defines FastAPI endpoints for chat streaming.
"""

import logging
from typing import Optional
from fastapi import APIRouter, Query, HTTPException, status
from fastapi.responses import StreamingResponse

from services import ChatStreamService
from models import ChatRequest

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["chat"])


def create_chat_routes(chat_service: ChatStreamService) -> APIRouter:
    """
    Create chat routes with injected service.

    Args:
        chat_service: Chat streaming service instance

    Returns:
        Configured API router
    """

    @router.get("/chat_stream/{message}")
    async def chat_stream_legacy(
        message: str,
        checkpoint_id: Optional[str] = Query(None),
    ) -> StreamingResponse:
        """
        Stream chat response (legacy path-based endpoint).

        Args:
            message: User message
            checkpoint_id: Optional checkpoint for session continuation

        Returns:
            Server-Sent Events stream

        Raises:
            HTTPException: If message is empty
        """
        if not message or not message.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Message cannot be empty"
            )

        logger.info(f"Chat stream requested: {message[:50]}...")

        return StreamingResponse(
            chat_service.stream_response(message, checkpoint_id),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no",
            }
        )

    @router.post("/chat_stream")
    async def chat_stream_post(request: ChatRequest) -> StreamingResponse:
        """
        Stream chat response (POST endpoint).

        Args:
            request: Chat request with message and optional checkpoint_id

        Returns:
            Server-Sent Events stream

        Raises:
            HTTPException: If message is empty
        """
        if not request.message or not request.message.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Message cannot be empty"
            )

        logger.info(f"Chat stream requested (POST): {request.message[:50]}...")

        return StreamingResponse(
            chat_service.stream_response(
                request.message, request.checkpoint_id),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no",
            }
        )

    @router.get("/health")
    async def health_check() -> dict:
        """
        Health check endpoint.

        Returns:
            Health status
        """
        return {"status": "ok", "service": "perplexity-2.0-backend"}

    return router
