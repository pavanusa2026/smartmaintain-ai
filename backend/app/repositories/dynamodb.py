"""Amazon DynamoDB repository implementations.

Table design:
- Machines: PK=machineId
- SensorReadings: PK=machineId, SK=timestamp (ISO)
- Alerts: PK=alertId, GSI1: status-severity-index (status PK, createdAt SK)
- WorkOrders: PK=workOrderId, GSI1: status-index (status PK, createdAt SK)
- Inspections: PK=inspectionId, GSI1: date-index (date PK, createdAt SK)
- AuditEvents: PK=eventId, GSI1: user-index (userId PK, timestamp SK)
"""

import logging
from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from app.core.config import get_settings
from app.repositories.base import (
    AlertRepository,
    InspectionRepository,
    MachineRepository,
    WorkOrderRepository,
)

logger = logging.getLogger(__name__)


def _get_table(table_name: str):
    import boto3
    settings = get_settings()
    dynamodb = boto3.resource("dynamodb", region_name=settings.aws_region)
    return dynamodb.Table(table_name)


def _serialize(obj: dict) -> dict:
    result = {}
    for k, v in obj.items():
        if isinstance(v, datetime):
            result[k] = v.isoformat()
        elif v is None:
            continue
        else:
            result[k] = v
    return result


class DynamoDBMachineRepository(MachineRepository):
    def __init__(self) -> None:
        settings = get_settings()
        self.table = _get_table(settings.machines_table)
        self.readings_table_name = settings.machines_table + "-readings"

    def list_machines(self, status: Optional[str] = None, search: Optional[str] = None) -> list[dict]:
        try:
            if status:
                resp = self.table.scan(FilterExpression="status = :s", ExpressionAttributeValues={":s": status})
            else:
                resp = self.table.scan()
            items = resp.get("Items", [])
            if search:
                q = search.lower()
                items = [m for m in items if q in m.get("name", "").lower() or q in m.get("machineId", "").lower()]
            return sorted(items, key=lambda m: m.get("name", ""))
        except Exception as exc:
            logger.error("DynamoDB list_machines failed: %s", exc)
            raise

    def get_machine(self, machine_id: str) -> Optional[dict]:
        try:
            resp = self.table.get_item(Key={"machineId": machine_id})
            return resp.get("Item")
        except Exception as exc:
            logger.error("DynamoDB get_machine failed: %s", exc)
            raise

    def create_machine(self, data: dict) -> dict:
        now = datetime.now(timezone.utc).isoformat()
        mid = data.get("machineId") or f"MACH-{uuid4().hex[:8].upper()}"
        record = {**data, "machineId": mid, "createdAt": now, "updatedAt": now}
        self.table.put_item(Item=_serialize(record), ConditionExpression="attribute_not_exists(machineId)")
        return record

    def update_machine(self, machine_id: str, updates: dict) -> Optional[dict]:
        existing = self.get_machine(machine_id)
        if not existing:
            return None
        updates["updatedAt"] = datetime.now(timezone.utc).isoformat()
        existing.update({k: v for k, v in updates.items() if v is not None})
        self.table.put_item(Item=_serialize(existing))
        return existing


class DynamoDBAlertRepository(AlertRepository):
    def __init__(self) -> None:
        self.table = _get_table(get_settings().alerts_table)

    def create_alert(self, data: dict) -> dict:
        aid = f"ALERT-{uuid4().hex[:8].upper()}"
        now = datetime.now(timezone.utc)
        record = {**data, "alertId": aid, "status": data.get("status", "new"), "createdAt": now.isoformat(), "updatedAt": now.isoformat()}
        self.table.put_item(Item=_serialize(record))
        return record


class DynamoDBWorkOrderRepository(WorkOrderRepository):
    def __init__(self) -> None:
        self.table = _get_table(get_settings().work_orders_table)

    def create_work_order(self, data: dict) -> dict:
        wid = f"WO-{uuid4().hex[:8].upper()}"
        now = datetime.now(timezone.utc)
        record = {**data, "workOrderId": wid, "status": data.get("status", "open"), "createdAt": now.isoformat(), "updatedAt": now.isoformat()}
        self.table.put_item(Item=_serialize(record))
        return record


class DynamoDBInspectionRepository(InspectionRepository):
    def __init__(self) -> None:
        self.table = _get_table(get_settings().inspections_table)

    def create_inspection(self, data: dict) -> dict:
        iid = f"INSP-{uuid4().hex[:8].upper()}"
        now = datetime.now(timezone.utc)
        record = {**data, "inspectionId": iid, "createdAt": now.isoformat()}
        self.table.put_item(Item=_serialize(record))
        return record
