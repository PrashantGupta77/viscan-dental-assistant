
from app.repositories.report_repository import get_report_by_id
from app.services.report_service import retrieve_patient_report


# Prototype-only memory store. Restarting the server clears this context.
# Production should use a persistent store with access controls and expiry.
_conversation_context: dict[str, dict[str, str]] = {}


def process_conversation_message(
    session,
    conversation_id: str,
    message: str,
    patient_name: str | None = None,
    report_type: str | None = None,
) -> dict:
    normalized_message = message.casefold().strip()

    # A new explicit patient name triggers report retrieval.
    if patient_name and patient_name.strip():
        result = retrieve_patient_report(
            session=session,
            patient_name=patient_name,
            report_type=report_type,
        )

        if result["status"] == "success":
            _conversation_context[conversation_id] = {
                "patient_id": result["patient"]["patient_id"],
                "report_id": result["report"]["report_id"],
            }

        return {
            "conversation_id": conversation_id,
            "status": result["status"],
            "message": result["message"],
            "patient": result["patient"],
            "report": result["report"],
            "source_evidence": result["source_evidence"],
            "requires_clinician_review": result.get(
                "requires_clinician_review", False
            ),
        }

    # Follow-up requests rely only on the current conversation's context.
    if "summary" in normalized_message or "her report" in normalized_message:
        context = _conversation_context.get(conversation_id)

        if not context:
            return {
                "conversation_id": conversation_id,
                "status": "needs_clarification",
                "message": (
                    "I don't have a report selected in this conversation. "
                    "Please provide the patient's full name and report type."
                ),
                "patient": None,
                "report": None,
                "source_evidence": [],
                "requires_clinician_review": False,
            }

        report = get_report_by_id(session, context["report_id"])

        # Fail closed if the stored report no longer exists or is not available.
        if report is None or report.status != "available":
            _conversation_context.pop(conversation_id, None)

            return {
                "conversation_id": conversation_id,
                "status": "report_not_found",
                "message": (
                    "The previously selected report is no longer available. "
                    "Please select a report again."
                ),
                "patient": None,
                "report": None,
                "source_evidence": [],
                "requires_clinician_review": False,
            }

        patient = report.patient

        # Use only source-record content; do not generate new clinical claims.

        summary = (
            f"{report.report_type} report dated "
            f"{report.report_date.isoformat()}."
        )

        if report.findings:
            finding_summaries = []

            for item in report.findings:
                if isinstance(item, dict):
                    observation = item.get("observation", "")
                    anatomical_site = item.get("anatomical_site", "")

                    finding = observation
                    if anatomical_site:
                        finding += f" (site: {anatomical_site})"

                    if finding:
                        finding_summaries.append(finding)
                else:
                    finding_summaries.append(str(item))

            if finding_summaries:
                summary += " Recorded findings: " + "; ".join(
                    finding_summaries
                )
        else:
            summary += (
                " No structured findings are recorded in the report data."
            )


        return {
            "conversation_id": conversation_id,
            "status": "success",
            "message": summary,
            "patient": {
                "patient_id": patient.patient_id,
                "patient_name": patient.patient_name,
                "date_of_birth": patient.date_of_birth.isoformat(),
            },
            "report": {
                "report_id": report.report_id,
                "report_type": report.report_type,
                "report_date": report.report_date.isoformat(),
                "report_text": report.report_text,
                "findings": report.findings,
                "status": report.status,
            },
            "source_evidence": [
                {
                    "source_type": "dental_report",
                    "patient_id": patient.patient_id,
                    "report_id": report.report_id,
                    "report_date": report.report_date.isoformat(),
                    "report_type": report.report_type,
                }
            ],
            "requires_clinician_review": True,
        }

    return {
        "conversation_id": conversation_id,
        "status": "needs_clarification",
        "message": (
            "Please specify a patient's full name to retrieve a report, "
            "or ask to summarize a report already selected in this conversation."
        ),
        "patient": None,
        "report": None,
        "source_evidence": [],
        "requires_clinician_review": False,
    }


def clear_conversation_context(conversation_id: str) -> None:
    """Clear the selected patient/report for a conversation."""
    _conversation_context.pop(conversation_id, None)
