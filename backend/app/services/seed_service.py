"""Seed demo data for local development."""

import logging
from datetime import datetime, timedelta, timezone

from app.core.config import Settings, get_settings
from app.core.security import hash_password
from app.repositories.base import (
    AlertRepository,
    MachineRepository,
    UserRepository,
    WorkOrderRepository,
)
from app.repositories.memory import get_store, reset_store

logger = logging.getLogger(__name__)


def _store_is_empty() -> bool:
    store = get_store()
    return not store.users and not store.machines


def seed_database(settings: Settings | None = None) -> None:
    """Seed demo data only when enabled and the in-memory store is empty."""
    settings = settings or get_settings()

    if not settings.seed_demo_data:
        logger.info("Demo seeding disabled (SEED_DEMO_DATA=false)")
        return

    if settings.storage_backend != "memory":
        logger.warning("Demo seeding skipped: only supported with in-memory storage")
        return

    if not _store_is_empty():
        logger.info("Demo data already present; skipping seed")
        return

    logger.info("Seeding demo data")
    reset_store()
    store = get_store()
    machine_repo = MachineRepository()
    alert_repo = AlertRepository()
    wo_repo = WorkOrderRepository()
    user_repo = UserRepository()

    # Demo users (password: demo123) — local development only
    demo_password = hash_password("demo123")
    users = [
        {"email": "admin@smartmaintain.ai", "password": demo_password, "role": "admin", "name": "System Admin"},
        {"email": "supervisor@smartmaintain.ai", "password": demo_password, "role": "supervisor", "name": "Jane Supervisor"},
        {"email": "tech@smartmaintain.ai", "password": demo_password, "role": "technician", "name": "Mike Technician"},
        {"email": "operator@smartmaintain.ai", "password": demo_password, "role": "operator", "name": "Alex Operator"},
        {"email": "inspector@smartmaintain.ai", "password": demo_password, "role": "inspector", "name": "Sarah Inspector"},
    ]
    for u in users:
        user_repo.create_user(u)

    now = datetime.now(timezone.utc)
    machines = [
        {
            "machineId": "MOTOR-204",
            "name": "Conveyor Motor 204",
            "type": "motor",
            "location": "Line A - Building 2",
            "manufacturer": "Siemens",
            "modelNumber": "1LA7134-4AA60",
            "installationDate": "2022-03-15",
            "status": "healthy",
            "healthScore": 92.0,
            "failureProbability": 0.08,
            "lastReadingAt": now,
            "lastMaintenanceDate": "2026-06-01",
            "operatingHours": 12400,
            "productionLine": "Line A",
        },
        {
            "machineId": "PUMP-107",
            "name": "Cooling Pump 7",
            "type": "pump",
            "location": "Line B - Cooling Station",
            "manufacturer": "Grundfos",
            "modelNumber": "CR 32-4",
            "installationDate": "2021-08-20",
            "status": "healthy",
            "healthScore": 88.0,
            "failureProbability": 0.12,
            "lastReadingAt": now,
            "lastMaintenanceDate": "2026-05-15",
            "operatingHours": 15600,
            "productionLine": "Line B",
        },
        {
            "machineId": "CONV-301",
            "name": "Packaging Conveyor 3",
            "type": "conveyor",
            "location": "Line C - Packaging",
            "manufacturer": "Dorner",
            "modelNumber": "2200 Series",
            "installationDate": "2023-01-10",
            "status": "warning",
            "healthScore": 68.0,
            "failureProbability": 0.45,
            "lastReadingAt": now,
            "lastMaintenanceDate": "2026-04-01",
            "operatingHours": 8200,
            "productionLine": "Line C",
        },
        {
            "machineId": "CNC-512",
            "name": "CNC Mill 512",
            "type": "cnc",
            "location": "Line D - Machining",
            "manufacturer": "Haas",
            "modelNumber": "VF-2SS",
            "installationDate": "2020-11-05",
            "status": "healthy",
            "healthScore": 85.0,
            "failureProbability": 0.15,
            "lastReadingAt": now,
            "lastMaintenanceDate": "2026-07-01",
            "operatingHours": 22000,
            "productionLine": "Line D",
        },
        {
            "machineId": "COMP-089",
            "name": "Air Compressor 89",
            "type": "compressor",
            "location": "Utility Room",
            "manufacturer": "Atlas Copco",
            "modelNumber": "GA 37",
            "installationDate": "2019-06-12",
            "status": "healthy",
            "healthScore": 78.0,
            "failureProbability": 0.22,
            "lastReadingAt": now,
            "lastMaintenanceDate": "2026-03-20",
            "operatingHours": 31000,
            "productionLine": "Utility",
        },
    ]
    for m in machines:
        machine_repo.create_machine(m)

    for m in machines:
        mid = m["machineId"]
        base_temp = 68 + hash(mid) % 10
        base_vib = 1.5 + (hash(mid) % 5) / 10
        for i in range(60):
            ts = now - timedelta(minutes=(60 - i) * 5)
            machine_repo.add_reading(
                {
                    "machineId": mid,
                    "timestamp": ts,
                    "temperature": base_temp + (i % 3) * 0.5,
                    "vibration": base_vib + (i % 4) * 0.1,
                    "pressure": 40 + (hash(mid + str(i)) % 10),
                    "powerConsumption": 12 + (hash(mid) % 5),
                    "rotationalSpeed": 1750 + (hash(mid) % 50),
                    "operatingLoad": 65 + (hash(mid + str(i)) % 20),
                    "anomalyScore": 0.1 + (hash(mid + str(i)) % 20) / 100,
                }
            )

    alert_repo.create_alert(
        {
            "machineId": "CONV-301",
            "severity": "medium",
            "alertType": "vibration",
            "title": "Elevated vibration on Packaging Conveyor 3",
            "explanation": "Vibration levels are 15% above baseline. Monitor bearing condition.",
            "recommendedAction": "Schedule bearing inspection within 48 hours.",
            "confidence": 0.72,
            "status": "acknowledged",
            "acknowledgedBy": "Jane Supervisor",
        }
    )

    wo_repo.create_work_order(
        {
            "machineId": "CONV-301",
            "title": "Inspect conveyor bearings",
            "description": "Check bearing housing, lubrication, and alignment on Packaging Conveyor 3.",
            "priority": "normal",
            "assignedTo": "Mike Technician",
            "dueDate": (now + timedelta(days=3)).strftime("%Y-%m-%d"),
            "status": "in_progress",
        }
    )

    _ = store
