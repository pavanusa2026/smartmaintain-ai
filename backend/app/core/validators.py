"""Reusable validation utilities for Pydantic models and services."""

import html
import math
import re
import uuid
from datetime import date, datetime, timezone
from pathlib import PurePath

MACHINE_ID_PATTERN = re.compile(r"^[A-Z0-9][A-Z0-9\-_]{2,31}$", re.IGNORECASE)
EMAIL_PATTERN = re.compile(r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$")
SCRIPT_PATTERN = re.compile(r"<script|javascript:|on\w+\s*=", re.IGNORECASE)
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/jpg"}

# Magic byte signatures for image validation
_IMAGE_SIGNATURES: list[tuple[bytes, str, str]] = [
    (b"\xff\xd8\xff", "image/jpeg", ".jpg"),
    (b"\x89PNG\r\n\x1a\n", "image/png", ".png"),
    (b"RIFF", "image/webp", ".webp"),  # WebP starts with RIFF....WEBP
]

_SAFE_FILENAME = re.compile(r"[^a-zA-Z0-9._-]+")


def strip_and_validate_text(value: str, field_name: str, min_len: int = 1, max_len: int = 500) -> str:
    cleaned = value.strip()
    if len(cleaned) < min_len:
        raise ValueError(f"{field_name} must be at least {min_len} characters")
    if len(cleaned) > max_len:
        raise ValueError(f"{field_name} must not exceed {max_len} characters")
    if SCRIPT_PATTERN.search(cleaned):
        raise ValueError(f"{field_name} contains disallowed content")
    return html.escape(cleaned)


def validate_email(value: str) -> str:
    cleaned = value.strip().lower()
    if not EMAIL_PATTERN.match(cleaned):
        raise ValueError("Invalid email address format")
    return cleaned


def validate_machine_id(value: str) -> str:
    cleaned = value.strip().upper()
    if not MACHINE_ID_PATTERN.match(cleaned):
        raise ValueError("Machine ID must be 3-32 alphanumeric characters (hyphens/underscores allowed)")
    return cleaned


def validate_probability(value: float, field_name: str = "probability") -> float:
    if math.isnan(value) or math.isinf(value):
        raise ValueError(f"{field_name} must be a valid number")
    if value < 0 or value > 1:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return value


def validate_sensor_value(value: float, field_name: str, min_val: float, max_val: float) -> float:
    if math.isnan(value) or math.isinf(value):
        raise ValueError(f"{field_name} must be a valid number")
    if value < min_val or value > max_val:
        raise ValueError(f"{field_name} must be between {min_val} and {max_val}")
    return value


def validate_due_date(value: str, allow_past: bool = False) -> str:
    try:
        parsed = date.fromisoformat(value.strip())
    except ValueError as exc:
        raise ValueError("Due date must be in YYYY-MM-DD format") from exc
    if not allow_past and parsed < date.today():
        raise ValueError("Due date cannot be in the past")
    return value


def sanitize_filename(filename: str | None) -> str:
    """Return a safe server-side filename; ignores client path components."""
    if not filename:
        return f"{uuid.uuid4().hex}.jpg"
    # Strip directory components and null bytes
    base = PurePath(filename.replace("\x00", "")).name
    cleaned = _SAFE_FILENAME.sub("_", base).strip("._")
    if not cleaned or cleaned in {".", ".."}:
        return f"{uuid.uuid4().hex}.jpg"
    return cleaned[:128]


def detect_image_type(contents: bytes) -> tuple[str, str] | None:
    """Detect image MIME type and extension from magic bytes."""
    if len(contents) < 12:
        return None
    if contents[:3] == b"\xff\xd8\xff":
        return "image/jpeg", ".jpg"
    if contents[:8] == b"\x89PNG\r\n\x1a\n":
        return "image/png", ".png"
    if contents[:4] == b"RIFF" and contents[8:12] == b"WEBP":
        return "image/webp", ".webp"
    return None


def validate_image_upload(content_type: str | None, size_bytes: int, max_size_mb: int = 10) -> None:
    if size_bytes <= 0:
        raise ValueError("File is empty")
    if size_bytes > max_size_mb * 1024 * 1024:
        raise ValueError(f"File too large (max {max_size_mb}MB)")


def validate_image_content(contents: bytes, content_type: str | None, max_size_mb: int = 10) -> str:
    """Validate upload size, declared type, and magic bytes. Returns safe extension."""
    validate_image_upload(content_type, len(contents), max_size_mb)
    detected = detect_image_type(contents)
    if not detected:
        raise ValueError("File must be a valid JPEG, PNG, or WebP image")
    mime, ext = detected
    if content_type and content_type not in ALLOWED_IMAGE_TYPES:
        raise ValueError("File must be JPEG, PNG, or WebP")
    return ext


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
