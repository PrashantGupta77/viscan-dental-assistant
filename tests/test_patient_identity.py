import pytest

from app.database import SessionLocal
from app.seed_db import seed_database
from app.safety.identity_resolution import resolve_patient_identity
from app.services.patient_service import resolve_patient


@pytest.fixture(autouse=True)
def prepare_seed_data():
    seed_database()


def test_exact_full_name_resolves_correct_patient():
    with SessionLocal() as session:
        result = resolve_patient_identity(session, "Priya Sharma")

        assert result.status == "found"
        assert result.patient is not None
        assert result.patient.patient_id == "P001"


def test_first_name_with_two_matches_is_ambiguous():
    with SessionLocal() as session:
        result = resolve_patient_identity(session, "Priya")

        assert result.status == "ambiguous"
        assert result.patient is None
        assert len(result.candidates) == 2


def test_unknown_patient_is_not_found():
    with SessionLocal() as session:
        result = resolve_patient_identity(
            session,
            "Aman Unknown",
        )

        assert result.status == "not_found"
        assert result.patient is None
        assert result.candidates == []


def test_whitespace_is_normalized():
    with SessionLocal() as session:
        result = resolve_patient_identity(
            session,
            "  Priya   Sharma  ",
        )

        assert result.status == "found"
        assert result.patient.patient_id == "P001"


def test_patient_service_returns_clarification_candidates():
    with SessionLocal() as session:
        result = resolve_patient(session, "Priya")

        assert result["status"] == "ambiguous"
        assert result["patient"] is None
        assert len(result["candidates"]) == 2
        assert "clarify" in result["message"].lower()
