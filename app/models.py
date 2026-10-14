
from datetime import date

from sqlalchemy import (
    CheckConstraint,
    Date,
    ForeignKey,
    Index,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.database import Base


class Patient(Base):
    __tablename__ = "patients"

    patient_id: Mapped[str] = mapped_column(
        String(20),
        primary_key=True,
    )
    patient_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )
    date_of_birth: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    reports: Mapped[list["Report"]] = relationship(
        back_populates="patient",
        cascade="all, delete-orphan",
    )


class Report(Base):
    __tablename__ = "reports"

    report_id: Mapped[str] = mapped_column(
        String(20),
        primary_key=True,
    )
    patient_id: Mapped[str] = mapped_column(
        ForeignKey("patients.patient_id"),
        nullable=False,
        index=True,
    )
    report_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )
    report_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )
    report_text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    findings: Mapped[list] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="available",
    )

    patient: Mapped[Patient] = relationship(
        back_populates="reports",
    )

    __table_args__ = (
        CheckConstraint(
            "report_type IN ('OPG', 'CBCT', 'Periapical')",
            name="ck_report_type",
        ),
        CheckConstraint(
            "status IN ('available', 'draft')",
            name="ck_report_status",
        ),
        Index(
            "ix_report_patient_type_date",
            "patient_id",
            "report_type",
            "report_date",
        ),
    )
