import pytest
from fastapi.testclient import TestClient

from app.database import SessionLocal
from app.main import app, get_db
from app.seed_db import seed_database


@pytest.fixture()
def client():
    seed_database()

    def override_get_db():
        session = SessionLocal()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


def test_health_endpoint(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_retrieve_latest_opg(client):
    response = client.post(
        "/reports/retrieve",
        json={
            "patient_name": "Priya Sharma",
            "report_type": "OPG",
        },
    )

    assert response.status_code == 200
    body = response.json()

    assert body["status"] == "success"
    assert body["report"]["report_id"] == "R001"
    assert body["requires_clinician_review"] is True


def test_ambiguous_patient(client):
    response = client.post(
        "/reports/retrieve",
        json={"patient_name": "Priya", "report_type": "OPG"},
    )

    assert response.status_code == 200
    body = response.json()

    assert body["status"] == "needs_clarification"
    assert len(body["candidates"]) == 2
    assert body["report"] is None


def test_missing_report(client):
    response = client.post(
        "/reports/retrieve",
        json={
            "patient_name": "Priya Sharma",
            "report_type": "Periapical",
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "report_not_found"


def test_invalid_report_type(client):
    response = client.post(
        "/reports/retrieve",
        json={
            "patient_name": "Priya Sharma",
            "report_type": "MRI",
        },
    )

    assert response.status_code == 422


def test_empty_patient_name_is_rejected(client):
    response = client.post(
        "/reports/retrieve",
        json={"patient_name": ""},
    )

    assert response.status_code == 422
