import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.conversation_service import clear_conversation_context
from app.seed_db import seed_database


client = TestClient(app)


@pytest.fixture(autouse=True)
def prepare_seed_data():
    clear_conversation_context("conversation-1")
    clear_conversation_context("conversation-2")
    seed_database()
    yield
    clear_conversation_context("conversation-1")
    clear_conversation_context("conversation-2")


def test_retrieval_sets_conversation_context():
    response = client.post(
        "/conversation/message",
        json={
            "conversation_id": "conversation-1",
            "message": "Open the latest OPG report",
            "patient_name": "Priya Sharma",
            "report_type": "OPG",
        },
    )

    assert response.status_code == 200
    body = response.json()

    assert body["status"] == "success"
    assert body["patient"]["patient_id"] == "P001"
    assert body["report"]["report_id"] == "R001"


def test_follow_up_summarizes_selected_report():
    first = client.post(
        "/conversation/message",
        json={
            "conversation_id": "conversation-1",
            "message": "Open the latest OPG report",
            "patient_name": "Priya Sharma",
            "report_type": "OPG",
        },
    )
    assert first.status_code == 200

    follow_up = client.post(
        "/conversation/message",
        json={
            "conversation_id": "conversation-1",
            "message": "Summarize her report",
        },
    )

    assert follow_up.status_code == 200
    body = follow_up.json()

    assert body["status"] == "success"
    assert body["report"]["report_id"] == "R001"
    assert body["patient"]["patient_name"] == "Priya Sharma"
    assert body["source_evidence"][0]["report_id"] == "R001"
    assert body["requires_clinician_review"] is True
    assert "OPG report dated" in body["message"]
    assert (
        "Fictional horizontal orientation of the lower right third molar"
        in body["message"]
    )
    assert "Lower right third molar" in body["message"]
    assert "{'observation':" not in body["message"]


def test_new_conversation_has_no_inherited_context():
    first = client.post(
        "/conversation/message",
        json={
            "conversation_id": "conversation-1",
            "message": "Open the latest OPG report",
            "patient_name": "Priya Sharma",
            "report_type": "OPG",
        },
    )
    assert first.status_code == 200

    follow_up = client.post(
        "/conversation/message",
        json={
            "conversation_id": "conversation-2",
            "message": "Summarize her report",
        },
    )

    assert follow_up.status_code == 200
    assert follow_up.json()["status"] == "needs_clarification"
    assert follow_up.json()["report"] is None


def test_ambiguous_patient_does_not_set_new_context():
    response = client.post(
        "/conversation/message",
        json={
            "conversation_id": "conversation-1",
            "message": "Open Priya's report",
            "patient_name": "Priya",
            "report_type": "OPG",
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "needs_clarification"
    assert response.json()["report"] is None


def test_unknown_follow_up_does_not_guess_a_report():
    response = client.post(
        "/conversation/message",
        json={
            "conversation_id": "conversation-2",
            "message": "Tell me more",
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "needs_clarification"
    assert response.json()["report"] is None


def test_invalid_conversation_request_is_rejected():
    response = client.post(
        "/conversation/message",
        json={
            "conversation_id": "",
            "message": "Summarize her report",
        },
    )

    assert response.status_code == 422
