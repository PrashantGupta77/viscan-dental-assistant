
from fastapi import Depends, FastAPI
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.schemas.report_schemas import (
    ReportRetrievalRequest,
    ReportRetrievalResponse,
)
from app.services.report_service import retrieve_patient_report

from app.schemas.dictation_schemas import (
    DictationDraft,
    DictationRequest,
)
from app.services.dictation_service import create_dictation_draft

from app.schemas.conversation_schemas import (
    ConversationRequest,
    ConversationResponse,
)
from app.services.conversation_service import process_conversation_message

app = FastAPI(
    title="Viscan Dental Assistant",
    description=(
        "Synthetic-data prototype for dental report retrieval "
        "and clinical dictation drafting."
    ),
    version="0.2.0",
)


def get_db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "viscan-dental-assistant",
    }


@app.post(
    "/reports/retrieve",
    response_model=ReportRetrievalResponse,
)
def retrieve_report(
    request: ReportRetrievalRequest,
    session: Session = Depends(get_db),
):
    return retrieve_patient_report(
        session=session,
        patient_name=request.patient_name,
        report_type=request.report_type,
    )


@app.post(
    "/dictation/draft",
    response_model=DictationDraft,
)
def create_dictation(
    request: DictationRequest,
):
    return create_dictation_draft(
        dictation=request.dictation,
        use_llm=request.use_llm,
    )



@app.post(
    "/conversation/message",
    response_model=ConversationResponse,
)
def conversation_message(
    request: ConversationRequest,
    session: Session = Depends(get_db),
):
    return process_conversation_message(
        session=session,
        conversation_id=request.conversation_id,
        message=request.message,
        patient_name=request.patient_name,
        report_type=request.report_type,
    )
