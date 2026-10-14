
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Report


def get_report_by_id(
    session: Session,
    report_id: str,
) -> Report | None:
    """Retrieve a report using its unique report ID."""
    return session.get(Report, report_id)


def get_patient_reports(
    session: Session,
    patient_id: str,
    report_type: str | None = None,
) -> list[Report]:
    """Retrieve a patient's reports, optionally filtered by type."""
    statement = select(Report).where(
        Report.patient_id == patient_id
    )

    if report_type:
        normalized_type = report_type.strip().casefold()

        statement = statement.where(
            Report.report_type.ilike(normalized_type)
        )

    statement = statement.order_by(
        Report.report_date.desc(),
        Report.report_id.asc(),
    )

    return list(session.scalars(statement).all())


def get_latest_report(
    session: Session,
    patient_id: str,
    report_type: str | None = None,
) -> Report | None:
    """Retrieve the most recent report matching the filters."""
    statement = select(Report).where(
        Report.patient_id == patient_id,
        Report.status == "available",
    )

    if report_type:
        normalized_type = report_type.strip().casefold()

        statement = statement.where(
            Report.report_type.ilike(normalized_type)
        )

    statement = (
        statement
        .order_by(
            Report.report_date.desc(),
            Report.report_id.asc(),
        )
        .limit(1)
    )

    return session.scalars(statement).first()
