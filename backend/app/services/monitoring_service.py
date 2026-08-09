"""Process sensor readings, run predictions, and create alerts."""

import logging
from datetime import datetime, timezone

from app.core.config import get_settings
from app.repositories.base import AlertRepository, MachineRepository
from app.services.bedrock_service import BedrockService, NotificationService
from app.services.prediction_service import get_prediction_service

logger = logging.getLogger(__name__)


def _determine_status(failure_prob: float, anomaly_score: float) -> str:
    if failure_prob >= 0.85 or anomaly_score >= 0.85:
        return "critical"
    if failure_prob >= 0.5 or anomaly_score >= 0.65:
        return "warning"
    return "healthy"


def _determine_severity(failure_prob: float, anomaly_score: float) -> str:
    if failure_prob >= 0.85:
        return "critical"
    if failure_prob >= 0.7:
        return "high"
    if failure_prob >= 0.5 or anomaly_score >= 0.65:
        return "medium"
    return "low"


def _alert_type_from_prediction(prediction: dict) -> str:
    concern = prediction.get("primaryConcern", "").lower()
    if "vibration" in concern or "bearing" in concern:
        return "vibration"
    if "temperature" in concern or "heat" in concern:
        return "temperature"
    if prediction.get("anomalyScore", 0) > 0.65:
        return "anomaly"
    return "failure_risk"


async def process_sensor_reading(reading_data: dict) -> dict:
    """Ingest a reading, update machine state, run ML, optionally create alert."""
    settings = get_settings()
    machine_repo = MachineRepository()
    alert_repo = AlertRepository()
    prediction_svc = get_prediction_service()
    bedrock_svc = BedrockService()
    notify_svc = NotificationService()

    mid = reading_data["machineId"]
    machine = machine_repo.get_machine(mid)
    if not machine:
        raise ValueError(f"Machine {mid} not found")

    if "timestamp" not in reading_data or reading_data["timestamp"] is None:
        reading_data["timestamp"] = datetime.now(timezone.utc)

    reading = machine_repo.add_reading(reading_data)
    readings = machine_repo.get_readings(mid, limit=20)

    prediction = prediction_svc.predict(
        mid,
        readings,
        machine_type=machine.get("type", "motor"),
        operating_hours=machine.get("operatingHours", 0),
    )

    reading["anomalyScore"] = prediction["anomalyScore"]

    status = _determine_status(prediction["failureProbability"], prediction["anomalyScore"])
    machine_repo.update_machine(
        mid,
        {
            "status": status,
            "healthScore": prediction["healthScore"],
            "failureProbability": prediction["failureProbability"],
            "lastReadingAt": reading_data["timestamp"],
        },
    )

    alert_created = None
    fp = prediction["failureProbability"]
    anomaly = prediction["anomalyScore"]
    prediction_valid = prediction.get("valid", True)

    if prediction_valid and (fp >= settings.failure_threshold or anomaly >= settings.anomaly_threshold):
        severity = _determine_severity(fp, anomaly)
        explanation = bedrock_svc.generate_alert_explanation(
            machine.get("name", mid),
            machine.get("type", "motor"),
            prediction,
            readings[-10:],
        )
        alert_type = _alert_type_from_prediction(prediction)
        title = f"{severity.title()} risk detected on {machine.get('name', mid)}"

        existing = [
            a
            for a in alert_repo.list_alerts(machine_id=mid)
            if a.get("status") not in ("closed",) and a.get("alertType") == alert_type
        ]
        if not existing:
            alert_created = alert_repo.create_alert(
                {
                    "machineId": mid,
                    "severity": severity,
                    "alertType": alert_type,
                    "title": title,
                    "explanation": explanation,
                    "recommendedAction": prediction.get("recommendedAction", ""),
                    "confidence": prediction.get("confidence", 0),
                }
            )
            notify_svc.send_alert_notification(alert_created, machine.get("name", mid))

    return {
        "reading": reading,
        "prediction": prediction,
        "alert": alert_created,
        "machineStatus": status,
    }
