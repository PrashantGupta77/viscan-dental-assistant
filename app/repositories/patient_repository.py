
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Patient


def get_patient_by_id(
    session: Session,
    patient_id: str,
) -> Patient | None:
    """Retrieve a patient using the unique patient ID."""
    return session.get(Patient, patient_id)


def find_patients_by_exact_name(
    session: Session,
    patient_name: str,
) -> list[Patient]:
    """Find patients whose full names match exactly, ignoring case."""
    normalized_name = patient_name.strip().casefold()

    if not normalized_name:
        return []

    statement = (
        select(Patient)
        .where(Patient.patient_name.collate("NOCASE") == normalized_name)
        .order_by(Patient.patient_id)
    )

    return list(session.scalars(statement).all())


def search_patients_by_name(
    session: Session,
    name_query: str,
) -> list[Patient]:
    """Find patients whose names contain the supplied text."""
    normalized_query = name_query.strip()

    if not normalized_query:
        return []

    statement = (
        select(Patient)
        .where(
            Patient.patient_name.ilike(f"%{normalized_query}%")
        )
        .order_by(Patient.patient_name, Patient.patient_id)
        .limit(20)
    )

    return list(session.scalars(statement).all())
