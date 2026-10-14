from sqlalchemy import select

from app.database import Base, SessionLocal, engine
from app.models import Patient, Report
from app.seed_db import seed_database


def test_seed_data_and_report_relationships():
    seed_database()

    with SessionLocal() as session:
        patients = session.scalars(
            select(Patient)
        ).all()

        reports = session.scalars(
            select(Report)
        ).all()

        assert len(patients) == 5
        assert len(reports) == 10

        priya_sharma = session.get(Patient, "P001")

        assert priya_sharma is not None
        assert priya_sharma.patient_name == "Priya Sharma"
        assert len(priya_sharma.reports) == 2

        report = session.get(Report, "R001")

        assert report is not None
        assert report.patient.patient_id == "P001"
        assert report.report_type == "OPG"
        assert report.report_date.isoformat() == "2026-08-15"
        assert isinstance(report.findings, list)
