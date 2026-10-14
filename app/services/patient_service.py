
from sqlalchemy.orm import Session

from app.safety.identity_resolution import (
    resolve_patient_identity,
)


def resolve_patient(
    session: Session,
    patient_name: str,
) -> dict:
    """Return a consistent, application-friendly identity result."""
    result = resolve_patient_identity(session, patient_name)

    if result.status == "found":
        patient = result.patient

        return {
            "status": "found",
            "patient": {
                "patient_id": patient.patient_id,
                "patient_name": patient.patient_name,
                "date_of_birth": patient.date_of_birth.isoformat(),
            },
            "candidates": [],
            "message": "Patient identified.",
        }

    if result.status == "ambiguous":
        candidates = [
            {
                "patient_id": patient.patient_id,
                "patient_name": patient.patient_name,
                "date_of_birth": patient.date_of_birth.isoformat(),
            }
            for patient in result.candidates
        ]

        return {
            "status": "ambiguous",
            "patient": None,
            "candidates": candidates,
            "message": (
                "Multiple patients match this name. "
                "Please clarify which patient you mean."
            ),
        }

    return {
        "status": "not_found",
        "patient": None,
        "candidates": [],
        "message": "No matching patient was found.",
    }
