# Demo Documentation — Viscan Dental Assistant

## 1. Overview

Viscan Dental Assistant is a proof of concept for a voice-first dental assistant that supports patient report retrieval, clinical dictation structuring, and context-aware follow-up questions.

The application uses FastAPI for backend APIs, SQLite for storing synthetic patient and report records, and an LLM integration through Groq for structuring clinical dictation. Streamlit provides a lightweight user interface.

This document demonstrates the implemented workflows through API requests, observed behaviour, and validation scenarios.

> **Scope:** This is a prototype developed using synthetic data. It is not intended for clinical diagnosis or direct use in patient care.

## 2. Prerequisites

Ensure that the project dependencies are installed and the environment variables are configured.

Start the FastAPI application from the project root:

```powershell
uvicorn app.main:app --reload
```

Open the interactive API documentation:

- Swagger UI: http://127.0.0.1:8000/docs
- Health endpoint: http://127.0.0.1:8000/health

Use Swagger UI to execute the requests below and capture the actual responses returned by the running application.

## 3. Synthetic Dataset

The application uses a synthetic dataset containing five patients and ten reports.

| Patient ID | Synthetic patient | Example report |
|---|---|---|
| P001 | Priya Sharma | R001 — OPG |
| P002 | Priya Singh | R003 — OPG |
| P003 | Arjun Mehta | Synthetic dental report |
| P004 | Neha Verma | Synthetic dental report |
| P005 | Rohan Gupta | Synthetic dental report |

The dataset deliberately contains two patients with the first name **Priya**. This allows identity-resolution behaviour to be tested without relying on real patient information.

The synthetic reports include report identifiers, patient associations, report types, dates, and fictional findings.

## 4. Demonstration Scenarios

### Scenario 1: Retrieve a Patient's Report

**Objective:** Retrieve the requested report for an unambiguous patient identity.

**API:** `POST /reports/retrieve`

**Request:**

```json
{
  "patient_name": "Priya Sharma",
  "report_type": "OPG"
}
```

**Expected behaviour:**

- Resolve the patient using the supplied name.
- Retrieve the matching OPG report.
- Return the report information and its associated source record.
- Avoid selecting a report belonging to another patient with a similar name.

**Validation:** Execute the request through Swagger UI and retain the actual response. Verify that the returned patient and report identifiers match the synthetic dataset.

### Scenario 2: Handle an Ambiguous Patient Identity

**Objective:** Prevent a report from being retrieved for the wrong patient when the supplied name is insufficient.

**API:** `POST /reports/retrieve`

**Request:**

```json
{
  "patient_name": "Priya",
  "report_type": "OPG"
}
```

**Observed behaviour:**

The application identifies that more than one patient matches the name and requests clarification instead of silently selecting one.

**Why this matters:** Patient identity must be resolved before returning potentially sensitive clinical information. A matching first name alone is not sufficient to establish identity.

**Validation:** Confirm that the response indicates ambiguity or requests clarification and does not incorrectly return one patient's report as the definitive match.

### Scenario 3: Handle an Unsupported Report Type

**Objective:** Validate report-type input and reject unsupported values.

**API:** `POST /reports/retrieve`

**Request:**

```json
{
  "patient_name": "Priya Sharma",
  "report_type": "MRI"
}
```

**Observed behaviour:** The application returns HTTP `422 Unprocessable Entity` for this unsupported report type.

**Why this matters:** Input validation prevents invalid requests from being treated as valid report-retrieval operations.

### Scenario 4: Convert Clinical Dictation into a Structured Draft

**Objective:** Convert a short clinical dictation into structured fields while preserving the source wording.

**API:** `POST /dictation/draft`

**Request:**

```json
{
  "dictation": "Tooth 36 shows no caries.",
  "use_llm": true
}
```

**Observed output from a successful Groq-backed run:**

```json
{
  "processing_mode": "groq",
  "anatomical_sites": [
    "Tooth 36"
  ],
  "stated_findings": [
    "Tooth 36 shows no caries."
  ],
  "uncertain_statements": [],
  "unclassified_statements": [],
  "report_text": "Anatomical site(s): Tooth 36\nStated findings: Tooth 36 shows no caries.",
  "requires_clinician_review": true,
  "safety_notes": [
    "This is an unverified draft, not a diagnosis.",
    "Original dictation must be reviewed before clinical use.",
    "Uncertain and unclassified statements have not been confirmed.",
    "LLM output was checked against the source transcript.",
    "Clinician review is mandatory."
  ]
}
```

**Key observations:**

- The anatomical site is identified as `Tooth 36`.
- The finding preserves the negation in the original statement: `no caries`.
- No additional clinical finding is introduced in this example.
- The generated draft explicitly requires clinician review.
- The processing mode indicates whether the LLM or a fallback path was used.

**Safety consideration:** Source-text matching helps detect unsupported wording, but it does not establish that the structured interpretation is clinically correct. A clinician must review the draft before any clinical use.

### Scenario 5: Ask a Context-Aware Follow-Up Question

**Objective:** Allow a user to ask a follow-up question without repeating the patient identity when the previous conversation provides an unambiguous reference.

**API:** `POST /conversation/message`

**Demonstration sequence:**

1. Start a conversation using a consistent conversation ID.
2. Ask the assistant to retrieve Priya Singh's OPG report.
3. Confirm that the retrieved source report is R003.
4. In the same conversation, ask: `Summarize her report`.
5. Verify that the assistant uses the previously retrieved report context.

**Observed behaviour:** The application successfully handled the follow-up question in the same conversation and referenced report R003 as its source.

**Why this matters:** Context-aware follow-ups improve usability by avoiding unnecessary repetition while retaining traceability to the source report.

**Important limitation:** Conversation context is maintained in memory in the current prototype. Restarting the backend can clear this context. Persistent conversation storage and stronger authorization controls would be needed for a production implementation.

## 5. Automated Testing

The project's automated test suite was executed using:

```powershell
python -m pytest -v
```

**Observed result:** `49 passed, 0 failed`.

The tests cover the implemented workflows and validation behaviour. Relevant assignment requirements include:

- Correct report retrieval.
- Ambiguous patient identity handling.
- Prevention of unsupported clinical claims in dictation output.


## 6. Running the User Interface

To launch the Streamlit interface, open a separate terminal from the project root:

```powershell
python -m streamlit run ui/streamlit_app.py
```

Open the local URL displayed by Streamlit, normally:

http://localhost:8501

The UI can be used to demonstrate the supported workflows without manually submitting every API request.

## 7. Current Limitations

This implementation is a proof of concept. The following limitations should be considered:

- **Synthetic data only:** Patient records and findings are fictional.
- **Dictation input:** The current workflow accepts text transcripts. Live microphone capture and speech-to-text transcription should not be claimed unless separately implemented and tested.
- **Clinical validation:** Textual grounding checks cannot guarantee semantic or clinical correctness.
- **Conversation persistence:** Conversation state is in memory and may be lost when the backend restarts.
- **Authentication and authorization:** Production-grade identity verification, access controls, and audit logging require further implementation.
- **Production readiness:** The prototype has not been established as a clinically validated medical system.

## 8. Future Improvements

Potential next steps include:

1. Add a speech-to-text integration for live dictation.
2. Persist conversation state and report-access audit logs.
3. Introduce authentication and patient-level authorization.
4. Strengthen semantic validation and test negation, uncertainty, and contradictory findings.
5. Add monitoring for LLM latency, failures, and token usage.
6. Expand the test suite with adversarial inputs and additional ambiguous-identity cases.
7. Add end-to-end tests for the Streamlit interface and backend APIs.

## 9. Conclusion

The prototype demonstrates three core workflows: patient report retrieval, structured clinical dictation drafting, and context-aware follow-up questions. It also demonstrates input validation, ambiguity handling, automated testing, and explicit clinician-review requirements.


