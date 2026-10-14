
from pydantic import BaseModel, Field
from typing import Literal


class ConversationRequest(BaseModel):
    conversation_id: str = Field(
        min_length=1,
        max_length=100,
        description="Identifier shared by messages in one conversation.",
    )
    message: str = Field(
        min_length=1,
        max_length=2000,
        description="User's current message.",
    )
    patient_name: str | None = Field(
        default=None,
        max_length=100,
        description="Patient name for a new report retrieval request.",
    )
    report_type: Literal["OPG", "CBCT", "Periapical"] | None = None


class ConversationResponse(BaseModel):
    conversation_id: str
    status: str
    message: str
    patient: dict | None = None
    report: dict | None = None
    source_evidence: list[dict] = Field(default_factory=list)
    requires_clinician_review: bool = False
