"""Local ML prediction service using scikit-learn."""

import logging
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from functools import lru_cache
from typing import TYPE_CHECKING, Any

from app.core.config import get_settings

if TYPE_CHECKING:
    import numpy as np

logger = logging.getLogger(__name__)

# Baseline normal ranges per machine type
BASELINES = {
    "motor": {"temp": 72, "vib": 2.5, "pressure": 42, "power": 14, "speed": 1780, "load": 70},
    "pump": {"temp": 65, "vib": 2.0, "pressure": 55, "power": 11, "speed": 1450, "load": 60},
    "conveyor": {"temp": 58, "vib": 1.8, "pressure": 38, "power": 8, "speed": 120, "load": 55},
    "cnc": {"temp": 55, "vib": 1.2, "pressure": 90, "power": 22, "speed": 8000, "load": 80},
    "compressor": {"temp": 78, "vib": 3.0, "pressure": 120, "power": 35, "speed": 3000, "load": 75},
    "oven": {"temp": 180, "vib": 0.5, "pressure": 30, "power": 45, "speed": 0, "load": 90},
    "packaging": {"temp": 50, "vib": 1.5, "pressure": 35, "power": 10, "speed": 200, "load": 65},
    "other": {"temp": 65, "vib": 2.0, "pressure": 40, "power": 12, "speed": 1500, "load": 65},
}

FAILURE_TYPES = {
    "motor": "bearing_failure",
    "pump": "seal_leak",
    "conveyor": "belt_misalignment",
    "cnc": "spindle_wear",
    "compressor": "valve_failure",
    "oven": "heating_element_degradation",
    "packaging": "sensor_malfunction",
    "other": "general_wear",
}


def _numpy():
    import numpy as np

    return np


def _extract_features(readings: list[dict], machine_type: str = "motor") -> "np.ndarray":
    np = _numpy()
    if not readings:
        baseline = BASELINES.get(machine_type, BASELINES["other"])
        return np.array(
            [
                baseline["temp"],
                baseline["vib"],
                baseline["pressure"],
                baseline["power"],
                baseline["speed"],
                baseline["load"],
                0,
                0,
                0,
            ]
        )

    temps = [r.get("temperature", 0) for r in readings]
    vibs = [r.get("vibration", 0) for r in readings]
    powers = [r.get("powerConsumption", 0) for r in readings]
    speeds = [r.get("rotationalSpeed", 0) for r in readings]

    latest = readings[-1]
    temp_slope = (temps[-1] - temps[0]) / max(len(temps), 1) if len(temps) > 1 else 0
    vib_max = max(vibs)
    vib_std = float(np.std(vibs)) if len(vibs) > 1 else 0
    speed_reduction = 0.0
    if speeds[0] > 0:
        speed_reduction = max(0, (speeds[0] - speeds[-1]) / speeds[0] * 100)

    return np.array(
        [
            latest.get("temperature", 0),
            latest.get("vibration", 0),
            latest.get("pressure", 0),
            latest.get("powerConsumption", 0),
            latest.get("rotationalSpeed", 0),
            latest.get("operatingLoad", 0),
            temp_slope,
            vib_max,
            speed_reduction,
        ]
    )


class PredictionService(ABC):
    @abstractmethod
    def predict(
        self, machine_id: str, readings: list[dict], machine_type: str = "motor", operating_hours: float = 0
    ) -> dict:
        pass


class LocalModelPredictionService(PredictionService):
    """Uses statistical models trained on synthetic data at startup."""

    def __init__(self) -> None:
        from sklearn.ensemble import IsolationForest, RandomForestClassifier

        self.settings = get_settings()
        self._np = _numpy()
        self._anomaly_model = IsolationForest(contamination=0.1, random_state=42)
        self._failure_model = RandomForestClassifier(n_estimators=50, random_state=42)
        self._train_synthetic_models()

    def _train_synthetic_models(self) -> None:
        np = self._np
        rng = np.random.default_rng(42)
        n = 500
        X_normal = rng.normal(0, 0.3, (n, 9))
        X_anomaly = rng.normal(0, 0.3, (50, 9))
        X_anomaly[:, 0] += 1.5  # high temp
        X_anomaly[:, 1] += 2.0  # high vibration
        X_anomaly[:, 8] += 15   # speed reduction
        X_train = np.vstack([X_normal, X_anomaly])
        self._anomaly_model.fit(X_train)

        X_fail = np.vstack([X_normal[:400], X_anomaly])
        y_fail = np.array([0] * 400 + [1] * 50)
        self._failure_model.fit(X_fail, y_fail)
        logger.info("Local ML models initialized (synthetic training data)")

    def predict(
        self, machine_id: str, readings: list[dict], machine_type: str = "motor", operating_hours: float = 0
    ) -> dict:
        np = self._np
        features = _extract_features(readings, machine_type)
        baseline = BASELINES.get(machine_type, BASELINES["other"])

        # Normalize features relative to baseline
        norm = np.array(
            [
                (features[0] - baseline["temp"]) / max(baseline["temp"], 1),
                (features[1] - baseline["vib"]) / max(baseline["vib"], 1),
                (features[2] - baseline["pressure"]) / max(baseline["pressure"], 1),
                (features[3] - baseline["power"]) / max(baseline["power"], 1),
                (features[4] - baseline["speed"]) / max(baseline["speed"], 1) if baseline["speed"] else 0,
                (features[5] - baseline["load"]) / max(baseline["load"], 1),
                features[6] / 5.0,
                features[7] / max(baseline["vib"] * 2, 1),
                features[8] / 100.0,
            ]
        )

        anomaly_raw = self._anomaly_model.decision_function([norm])[0]
        anomaly_score = float(max(0, min(1, 0.5 - anomaly_raw)))

        fail_proba = self._failure_model.predict_proba([norm])[0]
        failure_probability = float(fail_proba[1]) if len(fail_proba) > 1 else float(fail_proba[0])

        # Adjust based on recent trend
        if len(readings) >= 5:
            recent_vib = [r.get("vibration", 0) for r in readings[-5:]]
            vib_trend = recent_vib[-1] - recent_vib[0]
            if vib_trend > 0.3:
                failure_probability = min(0.99, failure_probability + vib_trend * 0.15)
                anomaly_score = min(0.99, anomaly_score + vib_trend * 0.1)

        health_score = max(0, min(100, 100 - failure_probability * 80 - anomaly_score * 20))
        likely_failure = FAILURE_TYPES.get(machine_type, "general_wear")

        # Remaining useful life estimate
        degradation_rate = failure_probability * 0.5 + anomaly_score * 0.3
        rul_hours = max(24, (1 - degradation_rate) * 500) if degradation_rate < 0.95 else 12

        primary_concern = "Normal operation"
        recommended = "Continue routine monitoring."
        if failure_probability > 0.7:
            primary_concern = likely_failure.replace("_", " ").title()
            recommended = f"Inspect {primary_concern.lower()} within 24 hours."
        elif failure_probability > 0.4:
            primary_concern = "Developing wear pattern"
            recommended = "Schedule preventive inspection within 7 days."

        return {
            "machineId": machine_id,
            "failureProbability": round(failure_probability, 3),
            "predictionWindowDays": 7,
            "likelyFailureType": likely_failure,
            "confidence": round(min(0.99, 0.75 + anomaly_score * 0.2), 3),
            "healthScore": round(health_score, 1),
            "anomalyScore": round(anomaly_score, 3),
            "remainingUsefulLifeHours": round(rul_hours, 1),
            "modelVersion": self.settings.model_version,
            "primaryConcern": primary_concern,
            "recommendedAction": recommended,
            "predictionTimestamp": datetime.now(timezone.utc).isoformat(),
            "valid": True,
        }


REQUIRED_PREDICTION_FIELDS = {
    "failureProbability", "anomalyScore", "confidence", "healthScore", "likelyFailureType",
}


def validate_prediction_response(result: dict, machine_id: str) -> dict:
    """Validate SageMaker response; mark invalid predictions."""
    if not isinstance(result, dict):
        raise ValueError("Prediction response must be a JSON object")
    for field in REQUIRED_PREDICTION_FIELDS:
        if field not in result:
            raise ValueError(f"Missing required field: {field}")
    fp = float(result["failureProbability"])
    conf = float(result["confidence"])
    if not (0 <= fp <= 1) or not (0 <= conf <= 1):
        raise ValueError("Probability and confidence must be between 0 and 1")
    result["machineId"] = machine_id
    result["valid"] = conf >= 0.3
    result.setdefault("modelVersion", get_settings().model_version)
    result.setdefault("predictionTimestamp", datetime.now(timezone.utc).isoformat())
    return result


class SageMakerPredictionService(PredictionService):
    """AWS SageMaker endpoint adapter with timeout, retries, and validation."""

    def __init__(self) -> None:
        self.settings = get_settings()
        from botocore.config import Config
        import boto3

        config = Config(
            connect_timeout=self.settings.ai_timeout_seconds,
            read_timeout=self.settings.ai_timeout_seconds,
            retries={"max_attempts": self.settings.ai_max_retries},
        )
        self.client = boto3.client(
            "sagemaker-runtime", region_name=self.settings.aws_region, config=config
        )
        self._fallback = LocalModelPredictionService()

    def predict(
        self, machine_id: str, readings: list[dict], machine_type: str = "motor", operating_hours: float = 0
    ) -> dict:
        import json

        features = _extract_features(readings, machine_type)
        payload = json.dumps(
            {
                "machineId": machine_id,
                "machineType": machine_type,
                "features": features.tolist(),
                "operatingHours": operating_hours,
            }
        )
        try:
            response = self.client.invoke_endpoint(
                EndpointName=self.settings.sagemaker_endpoint,
                ContentType="application/json",
                Body=payload,
            )
            result = json.loads(response["Body"].read())
            return validate_prediction_response(result, machine_id)
        except Exception as exc:
            logger.error("SageMaker invocation failed, using local fallback: %s", exc)
            fallback = self._fallback.predict(machine_id, readings, machine_type, operating_hours)
            fallback["modelVersion"] = f"{self.settings.model_version}-fallback"
            return fallback


@lru_cache
def get_prediction_service() -> PredictionService:
    settings = get_settings()
    if settings.use_local_model or not settings.sagemaker_endpoint:
        return LocalModelPredictionService()
    return SageMakerPredictionService()
