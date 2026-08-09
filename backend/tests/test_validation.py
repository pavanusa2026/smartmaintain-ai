"""Tests for input validation."""

import pytest
from pydantic import ValidationError

from app.schemas.domain import (
    AssistantQuery,
    LoginRequest,
    MachineCreate,
    SensorReadingCreate,
    WorkOrderCreate,
)


def test_login_valid():
    req = LoginRequest(email="user@example.com", password="demo123")
    assert req.email == "user@example.com"


def test_login_invalid_email():
    with pytest.raises(ValidationError):
        LoginRequest(email="not-an-email", password="demo123")


def test_login_short_password():
    with pytest.raises(ValidationError):
        LoginRequest(email="user@example.com", password="123")


def test_machine_create_valid():
    m = MachineCreate(name="Motor 1", type="motor", location="Line A")
    assert m.name == "Motor 1"


def test_machine_create_empty_name():
    with pytest.raises(ValidationError):
        MachineCreate(name="  ", type="motor", location="Line A")


def test_machine_create_invalid_id():
    with pytest.raises(ValidationError):
        MachineCreate(name="Motor", type="motor", location="Line A", machineId="bad id!")


def test_sensor_reading_out_of_range():
    with pytest.raises(ValidationError):
        SensorReadingCreate(
            machineId="MOTOR-204",
            temperature=9999,
            vibration=2.0,
            pressure=40,
            powerConsumption=12,
            rotationalSpeed=1750,
            operatingLoad=70,
        )


def test_sensor_reading_nan_rejected():
    with pytest.raises(ValidationError):
        SensorReadingCreate(
            machineId="MOTOR-204",
            temperature=float("nan"),
            vibration=2.0,
            pressure=40,
            powerConsumption=12,
            rotationalSpeed=1750,
            operatingLoad=70,
        )


def test_work_order_past_due_date():
    with pytest.raises(ValidationError):
        WorkOrderCreate(
            machineId="MOTOR-204",
            title="Test WO",
            dueDate="2020-01-01",
        )


def test_assistant_question_too_short():
    with pytest.raises(ValidationError):
        AssistantQuery(question="hi")


def test_assistant_script_injection():
    with pytest.raises(ValidationError):
        AssistantQuery(question="<script>alert('x')</script> what is bearing wear")


def test_assistant_valid_question():
    q = AssistantQuery(question="What should I inspect when vibration increases?")
    assert len(q.question) >= 5
