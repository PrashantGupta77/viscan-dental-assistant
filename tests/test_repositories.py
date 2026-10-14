import pytest

from app.database import SessionLocal
from app.repositories.patient_repository import (
    find_patients_by_exact_name,
    get_patient_by_id,
    search_patients_by_name,
)
from app.repositories.report_repository import (
    get_latest_report,
    get_patient_reports,
    get_report_by_id,
)
from app.seed_db import seed_database


@pytest.fixture(autouse=True)
def prepare_seed_data():
    seed_database()


def test_exact_patient_name_match():
    with SessionLocal() as session:
        patients = find_patients_by_exact_name(
            session, "Priya Sharma"
        )

        assert len(patients) == 1
        assert patients[0].patient_id == "P001"


def test_partial_name_returns_both_priyas():
    with SessionLocal() as session:
        patients = search_patients_by_name(session, "Priya")

        assert len(patients) == 2
        assert {p.patient_id for p in patients} == {
            "P001", "P002"
        }


def test_get_patient_by_id():
    with SessionLocal() as session:
        patient = get_patient_by_id(session, "P003")

        assert patient is not None
        assert patient.patient_name == "Arjun Mehta"


def test_latest_opg_report():
    with SessionLocal() as session:
        report = get_latest_report(
            session,
            patient_id="P002",
            report_type="OPG",
        )

        assert report is not None
        assert report.report_id == "R003"
        assert report.report_date.isoformat() == "2026-09-20"


def test_latest_report_without_type_filter():
    with SessionLocal() as session:
        report = get_latest_report(
            session,
            patient_id="P001",
        )

        assert report is not None
        assert report.report_id == "R002"
        assert report.report_type == "CBCT"


def test_missing_report_type_returns_none():
    with SessionLocal() as session:
        report = get_latest_report(
            session,
            patient_id="P001",
            report_type="Periapical",
        )

        assert report is None


def test_get_patient_reports():
    with SessionLocal() as session:
        reports = get_patient_reports(
            session,
            patient_id="P001",
        )

        assert len(reports) == 2
        assert reports[0].report_id == "R002"
        assert reports[1].report_id == "R001"


def test_get_report_by_id():
    with SessionLocal() as session:
        report = get_report_by_id(session, "R001")

        assert report is not None
        assert report.patient_id == "P001"


def test_unknown_patient_returns_empty_list():
    with SessionLocal() as session:
        patients = find_patients_by_exact_name(
            session, "Unknown Person"
        )

        assert patients == []
