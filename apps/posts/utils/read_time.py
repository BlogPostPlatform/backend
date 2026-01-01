import json
from typing import Any, Iterator


def extract_text_from_json_content(content: Any, max_chars: int = 10000) -> str:
    """
    Safely extract human-readable text from a JSON-like content blob produced by rich editors.
    - Accepts dict, list, str, bytes, or JSON string.
    - Recursively walks nested structures, collecting values from keys like "text", "caption".
    - Falls back to plain string conversion when needed.
    - Limits output to `max_chars` to avoid huge payloads.
    """
    if content is None:
        return ""
    if isinstance(content, (bytes, bytearray)):
        try:
            content = content.decode("utf-8")
        except Exception:
            content = str(content)
    if isinstance(content, str):
        stripped = content.strip()
        if (stripped.startswith("{") and stripped.endswith("}")) or (
            stripped.startswith("[") and stripped.endswith("]")
        ):
            try:
                content = json.loads(content)
            except Exception:
                return stripped[:max_chars]
        else:
            return stripped[:max_chars]

    text_fragments = []

    def _iter_text(node: Any) -> Iterator[str]:
        if node is None:
            return
        if isinstance(node, str):
            yield node
            return
        if isinstance(node, dict):
            for key in ("text", "caption", "name", "alt", "title", "label"):
                v = node.get(key)
                if isinstance(v, str) and v.strip():
                    yield v.strip()
            if "content" in node and not any(
                isinstance(node.get(k), str) for k in ("text", "caption", "name")
            ):
                yield from _iter_text(node["content"])
            if "rows" in node:
                yield from _iter_text(node["rows"])
            for v in node.values():
                yield from _iter_text(v)
            return
        if isinstance(node, (list, tuple)):
            for el in node:
                yield from _iter_text(el)
            return
        try:
            s = str(node)
            if s and s != repr(node):
                yield s
        except Exception:
            return

    for piece in _iter_text(content):
        if piece is None:
            continue
        piece = piece.strip()
        if piece:
            text_fragments.append(piece)
            if sum(len(p) for p in text_fragments) >= max_chars:
                break

    if not text_fragments:
        try:
            fallback = json.dumps(content, default=str)
        except Exception:
            fallback = str(content)
        return fallback[:max_chars]
    result = " ".join(text_fragments)
    return result[:max_chars]


def calculate_read_time(text: str, wpm: int = 225) -> int:
    if not text:
        return 0
    words = len(text.split())
    minutes = max(1, int(words / wpm))
    return minutes
