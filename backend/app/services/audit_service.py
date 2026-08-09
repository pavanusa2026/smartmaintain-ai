"""Audit event logging for important user actions."""

import logging
from typing import Any, Optional

from app.repositories.memory import get_store

logger = logging.getLogger(__name__)


class AuditService:
    def log(
        self,
        user_id: str,
        action: str,
        resource_type: str,
        resource_id: str,
        metadata: Optional[dict[str, Any]] = None,
    ) -> dict:
        store = get_store()
        event_id = store.new_id("AUDIT-")
        event = {
            "eventId": event_id,
            "userId": user_id,
            "action": action,
            "resourceType": resource_type,
            "resourceId": resource_id,
            "timestamp": store.now(),
            "metadata": metadata or {},
        }
        if not hasattr(store, "audit_events"):
            store.audit_events = {}
        store.audit_events[event_id] = event
        logger.info("AUDIT %s %s %s/%s by %s", action, resource_type, resource_id, user_id)
        return event

    def list_events(self, limit: int = 50) -> list[dict]:
        store = get_store()
        events = getattr(store, "audit_events", {})
        return sorted(events.values(), key=lambda e: e.get("timestamp"), reverse=True)[:limit]
