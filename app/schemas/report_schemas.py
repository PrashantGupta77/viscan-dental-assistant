
from typing import Literal

from pydantic import BaseModel, Field


ReportType = Literal["OPG", "CBCT", "Periapical"]


class ReportRetrievalRequest(BaseModel):
    patient_name: str = Field(
        min_length=1,
        max_length=100,
        description="Patient's name as spoken or typed by the user.",
    )
    report_type: ReportType | None = Field(
        default=None,
        description="Optional report type filter.",
    )


class PatientSummary(BaseModel):
    patient_id: str
    patient_name: str
    date_of_birth: str


class ReportSummary(BaseModel):
    report_id: str
    report_type: str
    report_date: str
    report_text: str
    findings: list
    status: str


class PatientCandidate(BaseModel):
    patient_id: str
    patient_name: str
    date_of_birth: str


class SourceEvidence(BaseModel):
    source_type: str
    patient_id: str | None = None
    report_id: str | None = None
    report_date: str | None = None
    report_type: str | None = None


class ReportRetrievalResponse(BaseModel):
    status: str
    patient: PatientSummary | None = None
    report: ReportSummary | None = None
    candidates: list[PatientCandidate] = Field(default_factory=list)
    source_evidence: list[SourceEvidence] = Field(default_factory=list)
    message: str
    requires_clinician_review: bool = False
