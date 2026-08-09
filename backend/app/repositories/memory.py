"""In-memory repository for local development."""

import uuid
from datetime import datetime, timezone
from typing import Generic, TypeVar

T = TypeVar("T")


class InMemoryStore:
    """Thread-safe enough for demo; single-process FastAPI."""

    def __init__(self) -> None:
        self.machines: dict[str, dict] = {}
        self.readings: dict[str, list[dict]] = {}
        self.alerts: dict[str, dict] = {}
        self.work_orders: dict[str, dict] = {}
        self.inspections: dict[str, dict] = {}
        self.feedback: dict[str, dict] = {}
        self.users: dict[str, dict] = {}

    def new_id(self, prefix: str = "") -> str:
        uid = str(uuid.uuid4())[:8].upper()
        return f"{prefix}{uid}" if prefix else uid

    def now(self) -> datetime:
        return datetime.now(timezone.utc)


_store: InMemoryStore | None = None


def get_store() -> InMemoryStore:
    global _store
    if _store is None:
        _store = InMemoryStore()
    return _store


def reset_store() -> None:
    global _store
    _store = InMemoryStore()
