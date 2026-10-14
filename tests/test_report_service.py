import pytest

from app.database import SessionLocal
from app.seed_db import seed_database
from app.services.report_service import retrieve_patient_report


@pytest.fixture(autouse=True)
def prepare_seed_data():
    seed_database()


def test_retrieves_latest_opg_for_exact_patient():
    with SessionLocal() as session:
        result = retrieve_patient_report(
            session,
            patient_name="Priya Sharma",
            report_type="OPG",
        )

        assert result["status"] == "success"
        assert result["patient"]["patient_id"] == "P001"
        assert result["report"]["report_id"] == "R001"
        assert result["report"]["report_type"] == "OPG"


def test_ambiguous_patient_requires_clarification():
    with SessionLocal() as session:
        result = retrieve_patient_report(
            session,
            patient_name="Priya",
            report_type="OPG",
        )

        assert result["status"] == "needs_clarification"
        assert result["report"] is None
        assert len(result["candidates"]) == 2


def test_unknown_patient_returns_not_found():
    with SessionLocal() as session:
        result = retrieve_patient_report(
            session,
            patient_name="Aman Unknown",
        )

        assert result["status"] == "patient_not_found"
        assert result["report"] is None


def test_missing_report_type_does_not_substitute_another_type():
    with SessionLocal() as session:
        result = retrieve_patient_report(
            session,
            patient_name="Priya Sharma",
            report_type="Periapical",
        )

        assert result["status"] == "report_not_found"
        assert result["report"] is None
        assert result["patient"]["patient_id"] == "P001"


def test_latest_report_without_type_filter():
    with SessionLocal() as session:
        result = retrieve_patient_report(
            session,
            patient_name="Priya Sharma",
        )

        assert result["status"] == "success"
        assert result["report"]["report_id"] == "R002"
        assert result["report"]["report_type"] == "CBCT"


def test_successful_response_includes_source_evidence():
    with SessionLocal() as session:
        result = retrieve_patient_report(
            session,
            patient_name="Arjun Mehta",
            report_type="OPG",
        )

        assert result["status"] == "success"
        assert result["source_evidence"][0]["patient_id"] == "P003"
        assert result["source_evidence"][1]["report_id"] == "R005"
        assert result["requires_clinician_review"] is True


def test_report_type_matching_is_case_insensitive():
    with SessionLocal() as session:
        result = retrieve_patient_report(
            session,
            patient_name="Priya Sharma",
            report_type="opg",
        )

        assert result["status"] == "success"
        assert result["report"]["report_id"] == "R001"
