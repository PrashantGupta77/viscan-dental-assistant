import pytest

from fastapi.testclient import TestClient

from app.main import app
from app.safety.clinical_validation import (
    contains_uncertainty,
    extract_anatomical_sites,
)
from app.services import dictation_service
from app.services.dictation_service import create_dictation_draft

from pydantic import ValidationError
from app.schemas.dictation_schemas import DictationRequest

client = TestClient(app)


def test_extracts_explicit_anatomical_site():
    result = create_dictation_draft(
        "Tooth 36 shows caries."
    )

    assert result["anatomical_sites"] == ["Tooth 36"]
    assert result["stated_findings"] == [
        "Tooth 36 shows caries."
    ]


def test_uncertain_finding_is_not_marked_confirmed():
    result = create_dictation_draft(
        "Possible periapical lesion near tooth 36."
    )

    assert result["uncertain_statements"] == [
        "Possible periapical lesion near tooth 36."
    ]
    assert result["stated_findings"] == []


def test_unrecognized_statement_is_preserved():
    result = create_dictation_draft(
        "Patient reports discomfort."
    )

    assert result["unclassified_statements"] == [
        "Patient reports discomfort."
    ]
    assert "Patient reports discomfort." in result["report_text"]


def test_no_findings_are_invented_for_unknown_text():
    result = create_dictation_draft(
        "Review the image carefully."
    )

    assert result["stated_findings"] == []
    assert result["uncertain_statements"] == []
    assert result["unclassified_statements"] == [
        "Review the image carefully."
    ]


def test_clinician_review_is_always_required():
    result = create_dictation_draft(
        "Tooth 36 shows caries."
    )

    assert result["status"] == "draft"
    assert result["requires_clinician_review"] is True
    assert result["safety_notes"]


def test_empty_text_service_result_is_safe():
    result = create_dictation_draft("   ")

    assert result["stated_findings"] == []
    assert result["requires_clinician_review"] is True


def test_uncertainty_detector():
    assert contains_uncertainty("Possible lesion.")
    assert contains_uncertainty("Cannot exclude a fracture.")
    assert not contains_uncertainty("Caries present.")


def test_extracts_multiple_unique_sites():
    sites = extract_anatomical_sites(
        "Tooth 36 shows caries. Tooth 11 has a restoration. "
        "Tooth 36 requires review."
    )

    assert sites == ["Tooth 36", "Tooth 11"]


def test_dictation_api_returns_structured_draft():
    response = client.post(
        "/dictation/draft",
        json={
            "dictation": (
                "Tooth 36 shows caries. "
                "Possible periapical lesion."
            )
        },
    )

    assert response.status_code == 200

    body = response.json()
    assert body["status"] == "draft"
    assert body["anatomical_sites"] == ["Tooth 36"]
    assert len(body["stated_findings"]) == 1
    assert len(body["uncertain_statements"]) == 1
    assert body["requires_clinician_review"] is True


def test_empty_dictation_is_rejected_by_api():
    response = client.post(
        "/dictation/draft",
        json={"dictation": ""},
    )

    assert response.status_code == 422


def test_groq_rejects_unsupported_finding_and_falls_back(monkeypatch):
    def fake_groq(transcript):
        return {
            "anatomical_sites": ["Tooth 36", "Tooth 37"],
            "stated_findings": [
                "Tooth 36 shows caries.",
                "Tooth 37 shows caries.",
            ],
            "uncertain_statements": [],
            "unclassified_statements": [],
        }

    monkeypatch.setattr(
        dictation_service,
        "extract_dictation_with_groq",
        fake_groq,
    )

    result = dictation_service.create_dictation_draft(
        "Tooth 36 shows caries.",
        use_llm=True,
    )

    assert result["processing_mode"] == "rule_based_fallback"
    assert "Tooth 37" not in result["report_text"]
    assert result["requires_clinician_review"] is True


def test_groq_failure_uses_rule_based_fallback(monkeypatch):
    def fake_groq(transcript):
        raise RuntimeError("Simulated API failure")

    monkeypatch.setattr(
        dictation_service,
        "extract_dictation_with_groq",
        fake_groq,
    )

    result = dictation_service.create_dictation_draft(
        "Tooth 36 shows caries.",
        use_llm=True,
    )

    assert result["processing_mode"] == "rule_based_fallback"
    assert result["requires_clinician_review"] is True
    assert any(
        "Groq interpretation failed" in note
        for note in result["safety_notes"]
    )


def test_dictation_rejects_whitespace_only_input():
    with pytest.raises(ValidationError):
        DictationRequest(
            dictation="     ",
            use_llm=False,
        )


def test_dictation_rejects_string_for_use_llm():
    with pytest.raises(ValidationError):
        DictationRequest(
            dictation="Tooth 36 shows caries.",
            use_llm="yes",
        )


def test_dictation_accepts_strict_boolean_values():
    rule_based = DictationRequest(
        dictation="Tooth 36 shows caries.",
        use_llm=False,
    )
    llm_enabled = DictationRequest(
        dictation="Tooth 36 shows caries.",
        use_llm=True,
    )

    assert rule_based.use_llm is False
    assert llm_enabled.use_llm is True
