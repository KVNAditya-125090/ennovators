"""
Cloud Run - photos sent for AI grading.
A photo arrives inside the request, as base64 or a data URL (the browser shrinks it first), and is graded and forgotten:
nothing is stored. The real type is read from the first bytes, never from what the caller says, and each person gets a
small number of gradings an hour, because every grading is a paid Gemini call.
"""

import base64
import binascii
import time
from collections import defaultdict, deque
from typing import Deque, Dict, Tuple

MAX_BYTES = 4 * 1024 * 1024
PER_HOUR = 20
_recent: Dict[str, Deque[float]] = defaultdict(deque)

def _mime(head: bytes) -> str:
    if head.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if head.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if head[:4] == b"RIFF" and head[8:12] == b"WEBP":
        return "image/webp"
    return ""

def decode_photo(value: str) -> Tuple[bytes, str]:
    """The photo's bytes and real type. Raises ValueError for anything that is not a JPEG, PNG or WebP picture within the size limit."""
    text = (value or "").strip()
    if text.startswith("data:"):
        text = text.partition(",")[2]
    try:
        raw = base64.b64decode(text, validate=True)
    except (binascii.Error, ValueError):
        raise ValueError("The photo could not be read. Send a JPEG, PNG or WebP picture.")
    if not raw or len(raw) > MAX_BYTES:
        raise ValueError("The photo is empty or larger than 4 MB.")
    mime = _mime(raw[:12])
    if not mime:
        raise ValueError("The photo must be a JPEG, PNG or WebP picture.")
    return raw, mime

def take_turn(who: str) -> None:
    """Counts one grading for this person. Raises ValueError after PER_HOUR in an hour."""
    now = time.time()
    turns = _recent[who or "anonymous"]
    while turns and now - turns[0] > 3600:
        turns.popleft()
    if len(turns) >= PER_HOUR:
        raise ValueError(f"You have graded {PER_HOUR} photos this hour. Please try again later.")
    turns.append(now)
