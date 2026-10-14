
import re


UNCERTAINTY_PATTERNS = (
    r"\bpossible\b",
    r"\bpossibly\b",
    r"\bsuspected\b",
    r"\bsuspicious for\b",
    r"\bappears to\b",
    r"\bmay represent\b",
    r"\bcannot exclude\b",
    r"\bquestionable\b",
    r"\buncertain\b",
    r"\blikely\b",
)

RECOGNIZED_FINDING_TERMS = (
    "caries",
    "fracture",
    "radiolucency",
    "radiopacity",
    "bone loss",
    "impacted",
    "restoration",
    "lesion",
    "periapical",
    "root resorption",
    "periodontal",
    "no evidence of",
)


def contains_uncertainty(statement: str) -> bool:
    """Check whether the statement contains common uncertainty language."""
    return any(
        re.search(pattern, statement, flags=re.IGNORECASE)
        for pattern in UNCERTAINTY_PATTERNS
    )


def is_recognized_finding(statement: str) -> bool:
    """
    Identify statements containing supported prototype vocabulary.

    This is a simple text filter, not clinical verification.
    """
    normalized = statement.casefold()

    return any(term in normalized for term in RECOGNIZED_FINDING_TERMS)


def extract_anatomical_sites(text: str) -> list[str]:
    """Extract explicitly mentioned FDI-style tooth numbers."""
    matches = re.findall(
        r"\b(?:tooth|teeth)\s+#?(\d{2})\b",
        text,
        flags=re.IGNORECASE,
    )

    # Preserve first-occurrence order and remove duplicates.
    return list(dict.fromkeys(f"Tooth {number}" for number in matches))
