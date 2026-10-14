
from pydantic import BaseModel, Field, StrictBool, field_validator


class DictationRequest(BaseModel):
    dictation: str = Field(
        min_length=1,
        max_length=5000,
        description="Clinician's dictated text.",
    )
    use_llm: StrictBool = Field(
        default=False,
        description="Use Groq for structured interpretation when enabled.",
    )

    @field_validator("dictation")
    @classmethod
    def reject_blank_dictation(cls, value: str) -> str:
        if not value.strip():
            raise ValueError(
                "Dictation must not be empty or whitespace only."
            )
        return value


class DictationDraft(BaseModel):
    status: str = "draft"
    anatomical_sites: list[str] = Field(default_factory=list)
    stated_findings: list[str] = Field(default_factory=list)
    uncertain_statements: list[str] = Field(default_factory=list)
    unclassified_statements: list[str] = Field(default_factory=list)
    report_text: str
    requires_clinician_review: bool = True
    safety_notes: list[str] = Field(default_factory=list)
    processing_mode: str = "rule_based"
