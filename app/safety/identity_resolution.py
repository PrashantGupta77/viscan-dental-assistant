
from dataclasses import dataclass
from typing import Literal

from sqlalchemy.orm import Session

from app.models import Patient
from app.repositories.patient_repository import (
    find_patients_by_exact_name,
    search_patients_by_name,
)


IdentityStatus = Literal["found", "ambiguous", "not_found"]


@dataclass
class IdentityResolution:
    status: IdentityStatus
    patient: Patient | None
    candidates: list[Patient]


def resolve_patient_identity(
    session: Session,
    patient_name: str,
) -> IdentityResolution:
    """Resolve a patient name without guessing between similar identities."""
    normalized_name = " ".join(patient_name.split())

    if not normalized_name:
        return IdentityResolution(
            status="not_found",
            patient=None,
            candidates=[],
        )

    # Prefer an exact full-name match.
    exact_matches = find_patients_by_exact_name(
        session,
        normalized_name,
    )

    if len(exact_matches) == 1:
        return IdentityResolution(
            status="found",
            patient=exact_matches[0],
            candidates=exact_matches,
        )

    if len(exact_matches) > 1:
        return IdentityResolution(
            status="ambiguous",
            patient=None,
            candidates=exact_matches,
        )

    # If no exact match exists, check partial-name matches.
    partial_matches = search_patients_by_name(
        session,
        normalized_name,
    )

    if not partial_matches:
        return IdentityResolution(
            status="not_found",
            patient=None,
            candidates=[],
        )

    if len(partial_matches) == 1:
        return IdentityResolution(
            status="found",
            patient=partial_matches[0],
            candidates=partial_matches,
        )

    return IdentityResolution(
        status="ambiguous",
        patient=None,
        candidates=partial_matches,
    )
