import json
from typing import Any, Set


def extract_readable_text(content: Any, max_chars: int = 50000) -> str:
    """
    Extract ONLY human-readable text from BlockNote/rich editor JSON content.

    Strategy:
    - Only extract from known text-bearing keys: "text", "caption", "name", "alt"
    - Skip all metadata/config (props, type, id, styles, textColor, etc.)
    - Handle nested content/children arrays properly
    - Be extremely defensive against malformed data

    Returns clean text suitable for word counting and read-time calculation.
    """
    if content is None:
        return ""

    # Handle bytes/bytearray input
    if isinstance(content, (bytes, bytearray)):
        try:
            content = content.decode("utf-8", errors="ignore")
        except Exception:
            return ""

    # Parse JSON strings
    if isinstance(content, str):
        stripped = content.strip()
        if not stripped:
            return ""

        # Try to parse as JSON if it looks like JSON
        if stripped.startswith("{") or stripped.startswith("["):
            try:
                content = json.loads(stripped)
            except (json.JSONDecodeError, ValueError):
                # Not valid JSON, return as plain text
                return stripped[:max_chars]
        else:
            # Plain text string
            return stripped[:max_chars]

    # Keys that contain actual human-readable text
    TEXT_KEYS: Set[str] = {"text", "caption", "alt", "name"}

    # Keys to recursively explore
    CONTAINER_KEYS: Set[str] = {"content", "children", "rows", "cells"}

    collected_text = []
    total_chars = 0

    def _extract(node: Any, depth: int = 0) -> None:
        """Recursively extract text from nested structure."""
        nonlocal total_chars

        # Safety: prevent infinite recursion
        if depth > 100 or total_chars >= max_chars:
            return

        # Handle None
        if node is None:
            return

        # Handle strings directly
        if isinstance(node, str):
            cleaned = node.strip()
            if cleaned:
                collected_text.append(cleaned)
                total_chars += len(cleaned)
            return

        # Handle dictionaries
        if isinstance(node, dict):
            # First, extract text from text-bearing keys ONLY
            for key in TEXT_KEYS:
                if key in node:
                    value = node[key]
                    if isinstance(value, str):
                        cleaned = value.strip()
                        if cleaned:
                            collected_text.append(cleaned)
                            total_chars += len(cleaned)
                            if total_chars >= max_chars:
                                return
                    elif isinstance(value, (list, dict)):
                        # Handle cases where text might be nested (like links)
                        _extract(value, depth + 1)

            # Then explore container keys for nested content
            for key in CONTAINER_KEYS:
                if key in node and total_chars < max_chars:
                    _extract(node[key], depth + 1)

            return

        # Handle lists and tuples
        if isinstance(node, (list, tuple)):
            for item in node:
                if total_chars >= max_chars:
                    return
                _extract(item, depth + 1)
            return

        # Handle numbers, booleans - ignore them
        if isinstance(node, (int, float, bool)):
            return

        # Last resort: try to stringify but be careful
        try:
            if hasattr(node, "__dict__"):
                # Custom object, try to extract from dict
                _extract(node.__dict__, depth + 1)
        except Exception:
            pass

    try:
        _extract(content)
    except Exception as e:
        # Log error in production, but don't crash
        print(f"Error extracting text: {e}")
        return ""

    if not collected_text:
        return ""

    # Join with spaces and clean up
    result = " ".join(collected_text)

    # Remove excessive whitespace
    result = " ".join(result.split())

    return result[:max_chars]


def calculate_read_time(text: str, wpm: int = 225) -> int:
    """
    Calculate reading time in minutes based on word count.

    Args:
        text: The text content to analyze
        wpm: Words per minute reading speed (default: 225, average adult)

    Returns:
        Estimated reading time in minutes (minimum 1 if there's any content)
    """
    if not text or not isinstance(text, str):
        return 0

    # Count words (split by whitespace)
    words = text.split()
    word_count = len(words)

    if word_count == 0:
        return 0

    # Calculate minutes, round up
    minutes = max(1, round(word_count / wpm))

    return minutes


def extract_text_from_json_content(content: Any, max_chars: int = 50000) -> str:
    """
    Wrapper function to maintain backward compatibility.
    Alias for extract_readable_text.
    """
    return extract_readable_text(content, max_chars)


# ============================================================================
# TESTING / DEBUGGING UTILITIES
# ============================================================================


def debug_extraction(content: Any) -> dict:
    """
    Debug helper to see what's being extracted and word counts.
    """
    try:
        text = extract_readable_text(content)
        words = text.split()

        return {
            "extracted_text": text[:500] + "..." if len(text) > 500 else text,
            "total_chars": len(text),
            "word_count": len(words),
            "estimated_read_time": calculate_read_time(text),
            "sample_words": words[:20] if words else [],
        }
    except Exception as e:
        return {
            "error": str(e),
            "content_type": type(content).__name__,
        }
