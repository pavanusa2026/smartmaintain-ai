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


@pytest.fixture
def auth_headers(client):
    resp = client.post("/api/auth/login", json={"email": "admin@smartmaintain.ai", "password": "demo123"})
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "healthy"


def test_login(client):
    resp = client.post("/api/auth/login", json={"email": "admin@smartmaintain.ai", "password": "demo123"})
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["role"] == "admin"


def test_login_invalid(client):
    resp = client.post("/api/auth/login", json={"email": "admin@smartmaintain.ai", "password": "wrongpass"})
    assert resp.status_code == 401


def test_list_machines(client, auth_headers):
    resp = client.get("/api/machines", headers=auth_headers)
    assert resp.status_code == 200
    machines = resp.json()
    assert len(machines) == 5
    assert any(m["machineId"] == "MOTOR-204" for m in machines)


def test_get_machine(client, auth_headers):
    resp = client.get("/api/machines/MOTOR-204", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["name"] == "Conveyor Motor 204"


def test_dashboard_stats(client, auth_headers):
    resp = client.get("/api/dashboard/stats", headers=auth_headers)
    assert resp.status_code == 200
    stats = resp.json()
    assert stats["totalMachines"] == 5


def test_submit_reading(client, auth_headers):
    resp = client.post(
        "/api/readings",
        headers=auth_headers,
        json={
            "machineId": "MOTOR-204",
            "temperature": 75.0,
            "vibration": 2.8,
            "pressure": 42.0,
            "powerConsumption": 14.5,
            "rotationalSpeed": 1780,
            "operatingLoad": 72,
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "prediction" in data
    assert "reading" in data


def test_prediction(client, auth_headers):
    resp = client.get("/api/machines/MOTOR-204/prediction", headers=auth_headers)
    assert resp.status_code == 200
    pred = resp.json()
    assert "failureProbability" in pred
    assert "healthScore" in pred


def test_list_alerts(client, auth_headers):
    resp = client.get("/api/alerts", headers=auth_headers)
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_create_work_order(client, auth_headers):
    resp = client.post(
        "/api/work-orders",
        headers=auth_headers,
        json={
            "machineId": "MOTOR-204",
            "title": "Test work order",
            "description": "Test description",
            "priority": "normal",
        },
    )
    assert resp.status_code == 200
    assert resp.json()["title"] == "Test work order"


def test_assistant_query(client, auth_headers):
    resp = client.post(
        "/api/assistant/query",
        headers=auth_headers,
        json={"question": "What should I inspect when motor vibration increases?", "machineId": "MOTOR-204"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "answer" in data
    assert len(data["sources"]) > 0


def test_unauthenticated(client):
    resp = client.get("/api/machines")
    assert resp.status_code == 401
