"""Repository layer abstracting storage backends."""

from datetime import datetime, timedelta, timezone
from typing import Optional

from app.repositories.memory import get_store


class MachineRepository:
    def list_machines(self, status: Optional[str] = None, search: Optional[str] = None) -> list[dict]:
        store = get_store()
        items = list(store.machines.values())
        if status:
            items = [m for m in items if m.get("status") == status]
        if search:
            q = search.lower()
            items = [
                m
                for m in items
                if q in m.get("name", "").lower()
                or q in m.get("machineId", "").lower()
                or q in m.get("location", "").lower()
            ]
        return sorted(items, key=lambda m: m.get("name", ""))

    def get_machine(self, machine_id: str) -> Optional[dict]:
        return get_store().machines.get(machine_id)

    def create_machine(self, data: dict) -> dict:
        store = get_store()
        mid = data.get("machineId") or store.new_id("MACH-")
        record = {**data, "machineId": mid}
        store.machines[mid] = record
        store.readings[mid] = []
        return record

    def update_machine(self, machine_id: str, updates: dict) -> Optional[dict]:
        store = get_store()
        if machine_id not in store.machines:
            return None
        store.machines[machine_id].update({k: v for k, v in updates.items() if v is not None})
        return store.machines[machine_id]

    def add_reading(self, data: dict) -> dict:
        store = get_store()
        mid = data["machineId"]
        rid = store.new_id("READ-")
        record = {**data, "readingId": rid}
        if mid not in store.readings:
            store.readings[mid] = []
        store.readings[mid].append(record)
        # Keep last 500 readings per machine
        store.readings[mid] = store.readings[mid][-500:]
        return record

    def get_readings(
        self, machine_id: str, limit: int = 100, since: Optional[datetime] = None
    ) -> list[dict]:
        readings = get_store().readings.get(machine_id, [])
        if since:
            readings = [r for r in readings if r.get("timestamp", datetime.min) >= since]
        return readings[-limit:]


class AlertRepository:
    def list_alerts(
        self,
        status: Optional[str] = None,
        severity: Optional[str] = None,
        machine_id: Optional[str] = None,
    ) -> list[dict]:
        items = list(get_store().alerts.values())
        if status:
            items = [a for a in items if a.get("status") == status]
        if severity:
            items = [a for a in items if a.get("severity") == severity]
        if machine_id:
            items = [a for a in items if a.get("machineId") == machine_id]
        return sorted(items, key=lambda a: a.get("createdAt", datetime.min), reverse=True)

    def get_alert(self, alert_id: str) -> Optional[dict]:
        return get_store().alerts.get(alert_id)

    def create_alert(self, data: dict) -> dict:
        store = get_store()
        aid = store.new_id("ALERT-")
        record = {
            **data,
            "alertId": aid,
            "status": data.get("status", "new"),
            "createdAt": data.get("createdAt", store.now()),
        }
        store.alerts[aid] = record
        return record

    def update_alert(self, alert_id: str, updates: dict) -> Optional[dict]:
        store = get_store()
        if alert_id not in store.alerts:
            return None
        store.alerts[alert_id].update({k: v for k, v in updates.items() if v is not None})
        return store.alerts[alert_id]


class WorkOrderRepository:
    def list_work_orders(
        self, status: Optional[str] = None, machine_id: Optional[str] = None
    ) -> list[dict]:
        items = list(get_store().work_orders.values())
        if status:
            items = [w for w in items if w.get("status") == status]
        if machine_id:
            items = [w for w in items if w.get("machineId") == machine_id]
        return sorted(items, key=lambda w: w.get("createdAt", datetime.min), reverse=True)

    def get_work_order(self, work_order_id: str) -> Optional[dict]:
        return get_store().work_orders.get(work_order_id)

    def create_work_order(self, data: dict) -> dict:
        store = get_store()
        wid = store.new_id("WO-")
        record = {
            **data,
            "workOrderId": wid,
            "status": data.get("status", "open"),
            "createdAt": data.get("createdAt", store.now()),
        }
        store.work_orders[wid] = record
        return record

    def update_work_order(self, work_order_id: str, updates: dict) -> Optional[dict]:
        store = get_store()
        if work_order_id not in store.work_orders:
            return None
        store.work_orders[work_order_id].update({k: v for k, v in updates.items() if v is not None})
        if updates.get("status") == "completed":
            store.work_orders[work_order_id]["completedAt"] = store.now()
        return store.work_orders[work_order_id]


class InspectionRepository:
    def list_inspections(self, limit: int = 50) -> list[dict]:
        items = list(get_store().inspections.values())
        return sorted(items, key=lambda i: i.get("createdAt", datetime.min), reverse=True)[:limit]

    def get_inspection(self, inspection_id: str) -> Optional[dict]:
        return get_store().inspections.get(inspection_id)

    def create_inspection(self, data: dict) -> dict:
        store = get_store()
        iid = store.new_id("INSP-")
        record = {**data, "inspectionId": iid, "createdAt": data.get("createdAt", store.now())}
        store.inspections[iid] = record
        return record

    def update_inspection(self, inspection_id: str, updates: dict) -> Optional[dict]:
        store = get_store()
        if inspection_id not in store.inspections:
            return None
        store.inspections[inspection_id].update({k: v for k, v in updates.items() if v is not None})
        return store.inspections[inspection_id]


class FeedbackRepository:
    def create_feedback(self, data: dict) -> dict:
        store = get_store()
        fid = store.new_id("FB-")
        record = {**data, "feedbackId": fid, "createdAt": store.now()}
        store.feedback[fid] = record
        return record


class UserRepository:
    def get_by_email(self, email: str) -> Optional[dict]:
        for user in get_store().users.values():
            if user.get("email") == email:
                return user
        return None

    def create_user(self, data: dict) -> dict:
        store = get_store()
        uid = store.new_id("USER-")
        record = {**data, "userId": uid}
        store.users[uid] = record
        return record


def get_dashboard_stats() -> dict:
    store = get_store()
    machines = list(store.machines.values())
    today = datetime.now(timezone.utc).date()
    inspections_today = [
        i
        for i in store.inspections.values()
        if i.get("createdAt") and i["createdAt"].date() == today and i.get("predictedResult") == "fail"
    ]
    open_wo = [w for w in store.work_orders.values() if w.get("status") in ("open", "in_progress")]
    active_alerts = [a for a in store.alerts.values() if a.get("status") not in ("closed",)]
    return {
        "totalMachines": len(machines),
        "healthyMachines": sum(1 for m in machines if m.get("status") == "healthy"),
        "warningMachines": sum(1 for m in machines if m.get("status") == "warning"),
        "criticalMachines": sum(1 for m in machines if m.get("status") == "critical"),
        "offlineMachines": sum(1 for m in machines if m.get("status") == "offline"),
        "openWorkOrders": len(open_wo),
        "defectsDetectedToday": len(inspections_today),
        "activeAlerts": len(active_alerts),
        "estimatedDowntimeAvoidedHours": round(len(active_alerts) * 2.5, 1),
    }
