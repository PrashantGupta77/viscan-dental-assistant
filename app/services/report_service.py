
from sqlalchemy.orm import Session

from app.repositories.report_repository import get_latest_report
from app.services.patient_service import resolve_patient


def retrieve_patient_report(
    session: Session,
    patient_name: str,
    report_type: str | None = None,
) -> dict:
    """
    Resolve the patient and retrieve the latest matching report.

    Returns explicit statuses for ambiguous identities,
    missing patients, and missing reports.
    """
    identity = resolve_patient(session, patient_name)

    if identity["status"] == "ambiguous":
        return {
            "status": "needs_clarification",
            "patient": None,
            "report": None,
            "candidates": identity["candidates"],
            "source_evidence": [],
            "message": identity["message"],
        }

    if identity["status"] == "not_found":
        return {
            "status": "patient_not_found",
            "patient": None,
            "report": None,
            "candidates": [],
            "source_evidence": [],
            "message": identity["message"],
        }

    patient = identity["patient"]

    report = get_latest_report(
        session=session,
        patient_id=patient["patient_id"],
        report_type=report_type,
    )

    if report is None:
        requested_type = (
            f" {report_type.strip().upper()}"
            if report_type and report_type.strip()
            else ""
        )

        return {
            "status": "report_not_found",
            "patient": patient,
            "report": None,
            "candidates": [],
            "source_evidence": [],
            "message": (
                f"No available{requested_type} report was found "
                f"for {patient['patient_name']}."
            ),
        }

    report_data = {
        "report_id": report.report_id,
        "report_type": report.report_type,
        "report_date": report.report_date.isoformat(),
        "report_text": report.report_text,
        "findings": report.findings,
        "status": report.status,
    }

    return {
        "status": "success",
        "patient": patient,
        "report": report_data,
        "candidates": [],
        "source_evidence": [
            {
                "source_type": "patient_record",
                "patient_id": patient["patient_id"],
            },
            {
                "source_type": "dental_report",
                "report_id": report.report_id,
                "report_date": report.report_date.isoformat(),
                "report_type": report.report_type,
            },
        ],
        "message": (
            f"Retrieved the latest matching report for "
            f"{patient['patient_name']}."
        ),
        "requires_clinician_review": True,
    }
