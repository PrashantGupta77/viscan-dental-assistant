
import json
import os
import re

from dotenv import load_dotenv
from groq import Groq


load_dotenv()


def _normalize_text(value: str) -> str:
    """Normalize text for conservative source-grounding checks."""
    value = value.casefold()
    value = re.sub(r"\s+", " ", value)
    value = re.sub(r"[^\w\s]", "", value)
    return value.strip()


def extract_dictation_with_groq(transcript: str) -> dict:
    """
    Ask Groq to classify only statements explicitly present
    in the supplied transcript.

    Raises an exception if the provider call or response fails.
    The caller is responsible for safe fallback behavior.
    """
    api_key = os.getenv("GROQ_API_KEY")
    model = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")

    if not api_key:
        raise RuntimeError("GROQ_API_KEY is not configured.")

    client = Groq(api_key=api_key)

    system_prompt = """
You are a conservative clinical-dictation extraction assistant.

Extract information from the supplied transcript. Do not diagnose,
infer missing observations, add recommendations, or invent findings.

Return one JSON object with exactly these keys:
- anatomical_sites: array of strings
- stated_findings: array of strings
- uncertain_statements: array of strings
- unclassified_statements: array of strings

Rules:
1. Preserve each complete original sentence verbatim in the
   appropriate statement array. Do not return sentence fragments.
2. Extract anatomical sites separately, but retain the site
   in the original statement when it appears there.
3. Put statements expressing uncertainty, suspicion, or possibility
   in uncertain_statements.
4. Put explicit observations without uncertainty in stated_findings.
5. Put other transcript statements in unclassified_statements.
6. Preserve negation. For example, "no caries" must never become
   "caries present".
7. Do not convert a possible finding into a confirmed finding.
8. Do not add text that is absent from the transcript.
9. Do not treat an example or instruction as a clinical observation.
10. Return valid JSON only, with no Markdown fences.
"""

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": (
                    "Extract the following transcript without adding "
                    "clinical information:\n\n"
                    f"<transcript>\n{transcript}\n</transcript>"
                ),
            },
        ],
        response_format={"type": "json_object"},
        temperature=0,
        max_tokens=1200,
    )

    content = response.choices[0].message.content

    if not content:
        raise ValueError("Groq returned an empty response.")

    result = json.loads(content)

    expected_keys = {
        "anatomical_sites",
        "stated_findings",
        "uncertain_statements",
        "unclassified_statements",
    }

    if not isinstance(result, dict) or set(result.keys()) != expected_keys:
        raise ValueError("Groq returned an unexpected JSON structure.")

    for key in expected_keys:
        if not isinstance(result[key], list):
            raise ValueError(f"{key} must be a JSON array.")

        if not all(
            isinstance(item, str) and item.strip()
            for item in result[key]
        ):
            raise ValueError(f"{key} must contain non-empty strings.")

    # Every extracted statement/site must be grounded in the input.
    # If Groq paraphrases or invents content, reject the response.
    normalized_transcript = _normalize_text(transcript)

    for key in expected_keys:
        for item in result[key]:
            normalized_item = _normalize_text(item)

            if normalized_item not in normalized_transcript:
                raise ValueError(
                    f"Ungrounded LLM output rejected in {key}: {item}"
                )


    # Preserve complete source sentences when the LLM returns
    # only a fragment, such as "shows no caries".
    statement_keys = [
        "stated_findings",
        "uncertain_statements",
        "unclassified_statements",
    ]

    source_sentences = [
        sentence.strip()
        for sentence in re.split(r"(?<=[.!?])\s+", transcript.strip())
        if sentence.strip()
    ]

    for key in statement_keys:
        preserved_statements = []

        for item in result[key]:
            normalized_item = _normalize_text(item)

            matching_sentences = [
                sentence
                for sentence in source_sentences
                if normalized_item in _normalize_text(sentence)
            ]

            # If the fragment belongs to exactly one source sentence,
            # preserve that complete sentence verbatim.
            if len(matching_sentences) == 1:
                preserved_statements.append(matching_sentences[0])
            else:
                preserved_statements.append(item)

        result[key] = preserved_statements


    # Avoid duplicate classifications across the three statement lists.
    statement_lists = [
        result["stated_findings"],
        result["uncertain_statements"],
        result["unclassified_statements"],
    ]
    seen = set()

    for statements in statement_lists:
        for statement in statements:
            normalized_statement = _normalize_text(statement)

            if normalized_statement in seen:
                raise ValueError(
                    "The LLM classified a statement more than once."
                )

            seen.add(normalized_statement)

    return result
