"""Tests for prediction service validation."""

import pytest

from app.services.prediction_service import (
    LocalModelPredictionService,
    validate_prediction_response,
)


def test_validate_prediction_valid():
    result = validate_prediction_response(
        {
            "failureProbability": 0.75,
            "anomalyScore": 0.6,
            "confidence": 0.85,
            "healthScore": 45,
            "likelyFailureType": "bearing_failure",
        },
        "MOTOR-204",
    )
    assert result["valid"] is True
    assert result["machineId"] == "MOTOR-204"


def test_validate_prediction_missing_field():
    with pytest.raises(ValueError, match="Missing required field"):
        validate_prediction_response({"failureProbability": 0.5}, "MOTOR-204")


def test_validate_prediction_out_of_range():
    with pytest.raises(ValueError, match="between 0 and 1"):
        validate_prediction_response(
            {
                "failureProbability": 1.5,
                "anomalyScore": 0.6,
                "confidence": 0.85,
                "healthScore": 45,
                "likelyFailureType": "bearing_failure",
            },
            "MOTOR-204",
        )


def test_local_prediction_returns_valid():
    svc = LocalModelPredictionService()
    readings = [
        {"temperature": 72, "vibration": 2.5, "pressure": 42, "powerConsumption": 14, "rotationalSpeed": 1780, "operatingLoad": 70},
        {"temperature": 73, "vibration": 2.8, "pressure": 43, "powerConsumption": 14.5, "rotationalSpeed": 1775, "operatingLoad": 72},
    ]
    result = svc.predict("MOTOR-204", readings, "motor", 1000)
    assert "failureProbability" in result
    assert 0 <= result["failureProbability"] <= 1
    assert result.get("valid", True)
