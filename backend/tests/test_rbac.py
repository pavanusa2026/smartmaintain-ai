"""Tests for role-based access control."""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.repositories.memory import reset_store
from app.services.seed_service import seed_database


@pytest.fixture
def client():
    reset_store()
    seed_database()
    with TestClient(app) as c:
        yield c


def _token(client, email):
    resp = client.post("/api/auth/login", json={"email": email, "password": "demo123"})
    assert resp.status_code == 200
    return resp.json()["access_token"]


def test_operator_can_view_machines(client):
    headers = {"Authorization": f"Bearer {_token(client, 'operator@smartmaintain.ai')}"}
    assert client.get("/api/machines", headers=headers).status_code == 200


def test_operator_cannot_create_machine(client):
    headers = {"Authorization": f"Bearer {_token(client, 'operator@smartmaintain.ai')}"}
    resp = client.post(
        "/api/machines",
        headers=headers,
        json={"name": "Test", "type": "motor", "location": "Line A"},
    )
    assert resp.status_code == 403


def test_supervisor_can_create_machine(client):
    headers = {"Authorization": f"Bearer {_token(client, 'supervisor@smartmaintain.ai')}"}
    resp = client.post(
        "/api/machines",
        headers=headers,
        json={"name": "New Motor", "type": "motor", "location": "Line B"},
    )
    assert resp.status_code == 200


def test_operator_cannot_acknowledge_alert(client):
    headers = {"Authorization": f"Bearer {_token(client, 'operator@smartmaintain.ai')}"}
    alerts = client.get("/api/alerts", headers=headers).json()
    if alerts:
        resp = client.post(f"/api/alerts/{alerts[0]['alertId']}/acknowledge", headers=headers)
        assert resp.status_code == 403


def test_technician_can_acknowledge_alert(client):
    headers = {"Authorization": f"Bearer {_token(client, 'tech@smartmaintain.ai')}"}
    alerts = client.get("/api/alerts", headers=headers).json()
    if alerts:
        resp = client.post(f"/api/alerts/{alerts[0]['alertId']}/acknowledge", headers=headers)
        assert resp.status_code == 200


def test_operator_cannot_view_reports(client):
    headers = {"Authorization": f"Bearer {_token(client, 'operator@smartmaintain.ai')}"}
    assert client.get("/api/reports/summary", headers=headers).status_code == 403


def test_supervisor_can_view_reports(client):
    headers = {"Authorization": f"Bearer {_token(client, 'supervisor@smartmaintain.ai')}"}
    assert client.get("/api/reports/summary", headers=headers).status_code == 200


def test_unauthenticated_rejected(client):
    assert client.get("/api/machines").status_code == 401


def test_validation_error_format(client):
    headers = {"Authorization": f"Bearer {_token(client, 'admin@smartmaintain.ai')}"}
    resp = client.post(
        "/api/readings",
        headers=headers,
        json={
            "machineId": "MOTOR-204",
            "temperature": 99999,
            "vibration": 2.0,
            "pressure": 40,
            "powerConsumption": 12,
            "rotationalSpeed": 1750,
            "operatingLoad": 70,
        },
    )
    assert resp.status_code == 422
    assert "error" in resp.json()
