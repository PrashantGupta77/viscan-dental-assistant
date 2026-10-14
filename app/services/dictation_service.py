
import re

from app.safety.clinical_validation import (
    contains_uncertainty,
    extract_anatomical_sites,
    is_recognized_finding,
)

from app.services.llm_service import extract_dictation_with_groq



def _validate_groq_output(transcript: str, extracted: dict) -> None:
    """Reject malformed or unsupported LLM output."""

    expected_keys = {
        "anatomical_sites",
        "stated_findings",
        "uncertain_statements",
        "unclassified_statements",
    }

    if not isinstance(extracted, dict) or set(extracted) != expected_keys:
        raise ValueError("Invalid Groq output structure.")

    def normalize(text: str) -> str:
        text = text.casefold()
        text = re.sub(r"[^\w\s]", "", text)
        return re.sub(r"\s+", " ", text).strip()

    normalized_transcript = normalize(transcript)

    for key in expected_keys:
        items = extracted[key]

        if not isinstance(items, list):
            raise ValueError(f"Invalid list returned for {key}.")

        for item in items:
            if not isinstance(item, str) or not item.strip():
                raise ValueError(f"Invalid item returned for {key}.")

            normalized_item = normalize(item)

            if normalized_item not in normalized_transcript:
                raise ValueError(
                    f"Unsupported Groq output rejected: {item}"
                )


def _create_rule_based_dictation_draft(dictation: str) -> dict:
    """Create a conservative structured draft from dictated text."""
    original_text = dictation.strip()

    if not original_text:
        return {
            "status": "draft",
            "anatomical_sites": [],
            "stated_findings": [],
            "uncertain_statements": [],
            "unclassified_statements": [],
            "report_text": "",
            "requires_clinician_review": True,
            "safety_notes": [
                "No dictation was provided.",
                "Clinician review is required.",
            ],
        }

    # Split on sentence-ending punctuation; retain each sentence's text.
    statements = [
        item.strip()
        for item in re.split(r"(?<=[.!?])\s+", original_text)
        if item.strip()
    ]

    anatomical_sites = extract_anatomical_sites(original_text)
    stated_findings = []
    uncertain_statements = []
    unclassified_statements = []

    for statement in statements:
        if contains_uncertainty(statement):
            uncertain_statements.append(statement)
        elif is_recognized_finding(statement):
            stated_findings.append(statement)
        else:
            unclassified_statements.append(statement)

    report_lines = []

    if anatomical_sites:
        report_lines.append(
            "Anatomical site(s): " + ", ".join(anatomical_sites)
        )

    if stated_findings:
        report_lines.append(
            "Stated findings: " + " ".join(stated_findings)
        )

    if uncertain_statements:
        report_lines.append(
            "Uncertain statements: " + " ".join(uncertain_statements)
        )

    if unclassified_statements:
        report_lines.append(
            "Unclassified dictation: " + " ".join(unclassified_statements)
        )

    if not report_lines:
        report_lines.append(
            "No supported structured statements were extracted."
        )

    return {
        "status": "draft",
        "anatomical_sites": anatomical_sites,
        "stated_findings": stated_findings,
        "uncertain_statements": uncertain_statements,
        "unclassified_statements": unclassified_statements,
        "report_text": "\n".join(report_lines),
        "requires_clinician_review": True,
        "safety_notes": [
            "This is an unverified draft, not a diagnosis.",
            "Original dictation must be reviewed before clinical use.",
            "Uncertain and unclassified statements have not been confirmed.",
            "No missing clinical findings have been inferred.",
        ],
    }



def create_dictation_draft(
    dictation: str,
    use_llm: bool = False,
) -> dict:
    """
    Create a structured draft using Groq when requested.
    Otherwise, use the existing deterministic parser.
    """
    if not use_llm:
        result = _create_rule_based_dictation_draft(dictation)
        result["processing_mode"] = "rule_based"
        return result

    try:
        extracted = extract_dictation_with_groq(dictation)

        # Validate the LLM output before using it.
        _validate_groq_output(dictation, extracted)

        # Start from the established response structure.
        result = _create_rule_based_dictation_draft(dictation)

        result["anatomical_sites"] = extracted["anatomical_sites"]
        result["stated_findings"] = extracted["stated_findings"]
        result["uncertain_statements"] = extracted["uncertain_statements"]
        result["unclassified_statements"] = extracted["unclassified_statements"]

        # Construct the readable draft from the extracted fields.
        report_lines = []

        if result["anatomical_sites"]:
            report_lines.append(
                "Anatomical site(s): "
                + ", ".join(result["anatomical_sites"])
            )

        if result["stated_findings"]:
            report_lines.append(
                "Stated findings: "
                + " ".join(result["stated_findings"])
            )

        if result["uncertain_statements"]:
            report_lines.append(
                "Uncertain statements: "
                + " ".join(result["uncertain_statements"])
            )

        if result["unclassified_statements"]:
            report_lines.append(
                "Unclassified dictation: "
                + " ".join(result["unclassified_statements"])
            )

        result["report_text"] = "\n".join(report_lines) or (
            "No supported structured statements were extracted."
        )
        result["processing_mode"] = "groq"
        result["requires_clinician_review"] = True

        result["safety_notes"] = [
            "This is an unverified draft, not a diagnosis.",
            "Original dictation must be reviewed before clinical use.",
            "Uncertain and unclassified statements have not been confirmed.",
            "LLM output was checked against the source transcript.",
            "Clinician review is mandatory.",
        ]

        return result

    except Exception:
        # Fail safely to the established local parser.
        result = _create_rule_based_dictation_draft(dictation)
        result["processing_mode"] = "rule_based_fallback"
        result["requires_clinician_review"] = True
        result["safety_notes"].append(
            "Groq interpretation failed or did not pass validation. "
            "The rule-based parser was used instead."
        )
        return result
