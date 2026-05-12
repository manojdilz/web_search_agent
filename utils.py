"""
Utility functions for content normalization, parsing, and serialization.
Provides reusable helper functions across the application.
"""

import json
import logging
from typing import Any, Union

logger = logging.getLogger(__name__)


class ContentNormalizer:
    """Handles normalization of various content types to JSON-serializable formats."""

    @staticmethod
    def normalize(value: Any) -> Any:
        """
        Recursively normalize content for JSON serialization.

        Args:
            value: Any content to normalize

        Returns:
            JSON-serializable normalized value
        """
        if value is None or isinstance(value, (str, int, float, bool)):
            return value

        if isinstance(value, dict):
            return {k: ContentNormalizer.normalize(v) for k, v in value.items()}

        if isinstance(value, (list, tuple)):
            return [ContentNormalizer.normalize(v) for v in value]

        # Fallback: convert to string
        return str(value)


class ToolArgumentParser:
    """Handles parsing and validation of tool arguments."""

    @staticmethod
    def parse(args: Union[str, dict]) -> Union[str, dict]:
        """
        Parse tool arguments, attempting JSON parsing if string.

        Args:
            args: Tool arguments (string or dict)

        Returns:
            Parsed arguments
        """
        if isinstance(args, str):
            try:
                return json.loads(args)
            except (json.JSONDecodeError, ValueError) as e:
                logger.debug(f"Failed to parse tool args as JSON: {e}")
                return args

        return args


class SSEEventBuilder:
    """Builds Server-Sent Events with proper formatting."""

    @staticmethod
    def build_event(event_type: str, payload: dict) -> str:
        """
        Build an SSE formatted event.

        Args:
            event_type: Type of event
            payload: Event payload as dictionary

        Returns:
            Formatted SSE event string
        """
        return f"event: {event_type}\ndata: {json.dumps(payload, default=str)}\n\n"


class AttributeExtractor:
    """Safely extracts attributes from objects with default values."""

    @staticmethod
    def get(obj: Any, attr: str, default: Any = None) -> Any:
        """
        Safely get attribute from object.

        Args:
            obj: Object to extract from
            attr: Attribute name
            default: Default value if attribute doesn't exist

        Returns:
            Attribute value or default
        """
        try:
            return getattr(obj, attr, default)
        except Exception as e:
            logger.debug(f"Error extracting attribute {attr}: {e}")
            return default
