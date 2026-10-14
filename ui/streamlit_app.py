import json

import requests
import streamlit as st


API_BASE_URL = "http://127.0.0.1:8000"
REQUEST_TIMEOUT = 15

st.set_page_config(
    page_title="Viscan Dental Assistant",
    page_icon="🦷",
    layout="wide",
)

st.title("🦷 Viscan Dental Assistant")
st.caption(
    "Synthetic-data prototype for dental report retrieval, "
    "clinical dictation, and context-aware follow-up."
)


def post_to_api(endpoint: str, payload: dict):
    """Send a request to FastAPI and handle expected connection errors."""
    try:
        response = requests.post(
            f"{API_BASE_URL}{endpoint}",
            json=payload,
            timeout=REQUEST_TIMEOUT,
        )

        try:
            body = response.json()
        except ValueError:
            body = {"detail": response.text}

        return response.status_code, body

    except requests.exceptions.ConnectionError:
        st.error(
            "Cannot connect to the backend. "
            "Start FastAPI in another terminal using: "
            "uvicorn app.main:app --reload"
        )
    except requests.exceptions.Timeout:
        st.error("The backend took too long to respond.")
    except requests.exceptions.RequestException as exc:
        st.error(f"Request failed: {exc}")

    return None, None


def show_api_error(status_code, body):
    """Display API validation or server errors."""
    if status_code is not None and status_code >= 400:
        st.error(f"API returned HTTP {status_code}")
        st.json(body)
        return True

    return False


def show_source_evidence(body):
    evidence = body.get("source_evidence") or []

    if evidence:
        st.markdown("#### Source evidence")
        st.dataframe(evidence, use_container_width=True)


def show_review_notice(body):
    if body.get("requires_clinician_review"):
        st.warning(
            "Clinician review required. This output is a draft "
            "and must not be treated as a verified clinical conclusion."
        )


tab_retrieval, tab_dictation, tab_conversation = st.tabs(
    [
        "📄 Report Retrieval",
        "📝 Clinical Dictation",
        "💬 Conversation",
    ]
)


# ---------------------------------------------------------
# Tab 1: Patient report retrieval
# ---------------------------------------------------------
with tab_retrieval:
    st.subheader("Retrieve a patient's latest report")

    st.info(
        "Use a full patient name when possible. If multiple patients "
        "match, the assistant should request clarification."
    )

    with st.form("report_retrieval_form"):
        patient_name = st.text_input(
            "Patient name",
            placeholder="e.g. Priya Sharma",
        )

        report_type = st.selectbox(
            "Report type",
            ["All types", "OPG", "CBCT", "Periapical"],
        )

        retrieve_clicked = st.form_submit_button(
            "Retrieve report",
            type="primary",
        )

    if retrieve_clicked:
        if not patient_name.strip():
            st.warning("Please enter a patient name.")
        else:
            payload = {
                "patient_name": patient_name.strip(),
            }

            if report_type != "All types":
                payload["report_type"] = report_type

            status, body = post_to_api("/reports/retrieve", payload)

            if status is not None and not show_api_error(status, body):
                if body.get("status") == "success":
                    st.success("Report retrieved.")

                    patient = body.get("patient") or {}
                    report = body.get("report") or {}

                    left, right = st.columns(2)

                    with left:
                        st.markdown("#### Patient")
                        st.write(
                            f"**Name:** {patient.get('patient_name', 'N/A')}"
                        )
                        st.write(
                            f"**Patient ID:** "
                            f"{patient.get('patient_id', 'N/A')}"
                        )

                    with right:
                        st.markdown("#### Report")
                        st.write(
                            f"**Report ID:** {report.get('report_id', 'N/A')}"
                        )
                        st.write(
                            f"**Type:** {report.get('report_type', 'N/A')}"
                        )
                        st.write(
                            f"**Date:** {report.get('report_date', 'N/A')}"
                        )

                    st.markdown("#### Report text")
                    st.write(report.get("report_text", "No report text."))

                    findings = report.get("findings") or []
                    if findings:
                        st.markdown("#### Recorded findings")
                        st.json(findings)

                    show_source_evidence(body)
                    show_review_notice(body)

                else:
                    st.warning(body.get("message", "No report retrieved."))

                    candidates = body.get("candidates") or []
                    if candidates:
                        st.markdown("#### Matching patients")
                        st.dataframe(candidates, use_container_width=True)

                    # Keep the complete response visible for debugging
                    # and for statuses not yet given a dedicated UI.
                    with st.expander("API response details"):
                        st.json(body)


# ---------------------------------------------------------
# Tab 2: Clinical dictation
# ---------------------------------------------------------
with tab_dictation:
    st.subheader("Convert dictation into a structured draft")

    st.caption(
        "Transcript input is used in this prototype. "
        "Live microphone transcription is not implemented yet."
    )

    with st.form("dictation_form"):
        transcript = st.text_area(
            "Clinical dictation transcript",
            placeholder=(
                "Example: Tooth 36 shows caries. "
                "Possible periapical lesion."
            ),
            height=160,
        )


        use_llm = st.checkbox(
            "Use Groq LLM for interpretation",
            value=False,
            help=(
                "Enable Groq for clinical dictation interpretation. "
                "If unavailable or validation fails, the backend "
                "uses its rule-based fallback."
            ),
        )


        dictation_clicked = st.form_submit_button(
            "Generate draft",
            type="primary",
        )

    if dictation_clicked:
        if not transcript.strip():
            st.warning("Please enter a dictation transcript.")
        else:
            status, body = post_to_api(
                "/dictation/draft",
                {
                    "dictation": transcript.strip(),
                    "use_llm": use_llm,
                },
            )

            if status is not None and not show_api_error(status, body):
                st.success("Structured draft generated.")
            
                processing_mode = body.get(
                    "processing_mode",
                    "unknown",
                )

                if processing_mode == "groq":
                    st.info("Interpretation mode: Groq LLM")
                elif processing_mode == "rule_based_fallback":
                    st.warning(
                        "Groq interpretation was unavailable or "
                        "rejected. Rule-based fallback was used."
                    )
                elif processing_mode == "rule_based":
                    st.info("Interpretation mode: Rule-based")
    

                col1, col2 = st.columns(2)

                with col1:
                    st.markdown("#### Anatomical sites")
                    st.write(body.get("anatomical_sites") or [])

                    st.markdown("#### Stated findings")
                    st.write(body.get("stated_findings") or [])

                with col2:
                    st.markdown("#### Uncertain statements")
                    st.write(body.get("uncertain_statements") or [])

                    st.markdown("#### Unclassified statements")
                    st.write(body.get("unclassified_statements") or [])

                st.markdown("#### Readable report draft")
                st.text_area(
                    "Draft text",
                    value=body.get("report_text", ""),
                    height=130,
                    disabled=True,
                    key="dictation_draft_display",
                )

                show_review_notice(body)

                with st.expander("Complete structured JSON"):
                    st.json(body)


# ---------------------------------------------------------
# Tab 3: Context-aware conversation
# ---------------------------------------------------------
with tab_conversation:
    st.subheader("Ask follow-up questions about a report")

    st.caption(
        "First retrieve a report, then ask something like "
        "'Summarize her report'. The same conversation ID must be "
        "used for both requests."
    )

    if "conversation_id" not in st.session_state:
        st.session_state.conversation_id = "demo-001"

    conversation_id = st.text_input(
        "Conversation ID",
        key="conversation_id",
        help="Use the same ID to retain context between requests.",
    )

    with st.form("conversation_form"):
        conversation_message = st.text_input(
            "Your message",
            placeholder="e.g. Open the latest OPG report",
        )

        conversation_patient = st.text_input(
            "Patient name (for a new report request)",
            placeholder="e.g. Priya Sharma",
        )

        conversation_report_type = st.selectbox(
            "Report type (for a new report request)",
            ["OPG", "CBCT", "Periapical"],
        )

        conversation_clicked = st.form_submit_button(
            "Send message",
            type="primary",
        )

    if conversation_clicked:
        if not conversation_id.strip():
            st.warning("Please enter a conversation ID.")
        elif not conversation_message.strip():
            st.warning("Please enter a message.")
        else:
            payload = {
                "conversation_id": conversation_id.strip(),
                "message": conversation_message.strip(),
            }

            # Only pass patient details when the user explicitly enters
            # a patient name. Otherwise the backend can use prior context.
            if conversation_patient.strip():
                payload["patient_name"] = conversation_patient.strip()
                payload["report_type"] = conversation_report_type

            status, body = post_to_api(
                "/conversation/message",
                payload,
            )

            if status is not None and not show_api_error(status, body):
                if body.get("status") == "success":
                    st.success("Message processed.")
                else:
                    st.warning(body.get("message", "Clarification needed."))

                st.markdown("#### Assistant response")
                st.write(body.get("message", ""))

                patient = body.get("patient")
                report = body.get("report")

                if patient:
                    st.markdown("#### Selected patient")
                    st.json(patient)

                if report:
                    st.markdown("#### Referenced report")
                    st.json(report)

                show_source_evidence(body)
                show_review_notice(body)

                with st.expander("Complete response JSON"):
                    st.json(body)


st.divider()
st.caption(
    "Prototype only · Synthetic records · Not for real patient care. "
    "All clinical drafts require review by a qualified clinician."
)
