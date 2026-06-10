import json
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.config import settings
from app.database.session import get_db
from app.models.db_models import InterviewQuestion, InterviewSession
from app.models.schemas import (
    AnswerResponse,
    AnswerSubmission,
    InterviewSummary,
    QuestionsResponse,
    ResumeProfile,
    RoleInfo,
    SessionCreateResponse,
)
from app.services.question_generator import generate_questions
from app.services.resume_parser import extract_text_from_file, parse_resume
from app.services.roles import get_role, list_roles
from app.services.summary_generator import generate_summary

router = APIRouter()


@router.get("/health")
async def health_check():
    from app.services.llm_client import llm_client

    ollama_available = await llm_client.is_available()
    return {
        "status": "ok",
        "ollama_available": ollama_available,
        "mock_mode": settings.use_mock_llm,
    }


@router.get("/roles", response_model=list[RoleInfo])
def get_roles():
    return list_roles()


@router.post("/sessions", response_model=SessionCreateResponse)
async def create_session(
    role_id: str = Form(...),
    resume: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    role = get_role(role_id)
    if not role:
        raise HTTPException(status_code=400, detail=f"Unknown role: {role_id}")

    content = await resume.read()
    if not content:
        raise HTTPException(status_code=400, detail="Resume file is empty")

    try:
        resume_text = extract_text_from_file(resume.filename or "resume.txt", content)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    profile = parse_resume(resume_text)

    upload_dir = Path(settings.uploads_path)
    upload_dir.mkdir(parents=True, exist_ok=True)
    upload_path = upload_dir / f"{role_id}_{resume.filename}"
    upload_path.write_bytes(content)

    session = InterviewSession(
        role_id=role_id,
        candidate_name=profile.name,
        resume_text=resume_text,
        resume_profile_json=profile.model_dump_json(),
        status="created",
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    return SessionCreateResponse(
        session_id=session.id,
        role_id=role_id,
        resume_profile=profile,
    )


@router.post("/sessions/{session_id}/questions", response_model=QuestionsResponse)
async def create_questions(session_id: str, db: Session = Depends(get_db)):
    session = db.get(InterviewSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    role = get_role(session.role_id)
    if not role:
        raise HTTPException(status_code=400, detail="Invalid role on session")

    profile = ResumeProfile.model_validate_json(session.resume_profile_json)

    if session.questions:
        questions = sorted(session.questions, key=lambda q: q.order_index)
        return QuestionsResponse(
            session_id=session.id,
            questions=[
                {
                    "id": q.id,
                    "question": q.question,
                    "topic": q.topic,
                    "difficulty": q.difficulty,
                    "rationale": q.rationale,
                }
                for q in questions
            ],
        )

    generated = await generate_questions(db, session, role, profile)
    return QuestionsResponse(session_id=session.id, questions=generated)


@router.post("/sessions/{session_id}/answers", response_model=AnswerResponse)
def submit_answer(
    session_id: str,
    payload: AnswerSubmission,
    db: Session = Depends(get_db),
):
    question = db.get(InterviewQuestion, payload.question_id)
    if not question or question.session_id != session_id:
        raise HTTPException(status_code=404, detail="Question not found for session")

    question.answer = payload.answer
    session = db.get(InterviewSession, session_id)
    if session:
        session.status = "in_progress"
    db.commit()

    return AnswerResponse(question_id=payload.question_id, stored=True)


@router.post("/sessions/{session_id}/complete", response_model=InterviewSummary)
async def complete_session(session_id: str, db: Session = Depends(get_db)):
    session = db.get(InterviewSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    role = get_role(session.role_id)
    if not role:
        raise HTTPException(status_code=400, detail="Invalid role on session")

    profile = ResumeProfile.model_validate_json(session.resume_profile_json)
    unanswered = [q for q in session.questions if not q.answer]
    if unanswered:
        raise HTTPException(
            status_code=400,
            detail=f"{len(unanswered)} question(s) still unanswered",
        )

    if session.report:
        report = session.report
        return InterviewSummary(
            session_id=session.id,
            role_id=session.role_id,
            candidate_name=profile.name,
            overall_score=report.overall_score,
            strengths=json.loads(report.strengths_json),
            weaknesses=json.loads(report.weaknesses_json),
            topic_scores=json.loads(report.topic_scores_json),
            recommendation=report.recommendation,
            detailed_insights=report.detailed_insights,
            generated_at=report.generated_at,
        )

    return await generate_summary(db, session, role, profile)


@router.get("/sessions/{session_id}/summary", response_model=InterviewSummary)
def get_summary(session_id: str, db: Session = Depends(get_db)):
    session = db.get(InterviewSession, session_id)
    if not session or not session.report:
        raise HTTPException(status_code=404, detail="Summary not found")

    profile = ResumeProfile.model_validate_json(session.resume_profile_json)
    report = session.report
    return InterviewSummary(
        session_id=session.id,
        role_id=session.role_id,
        candidate_name=profile.name,
        overall_score=report.overall_score,
        strengths=json.loads(report.strengths_json),
        weaknesses=json.loads(report.weaknesses_json),
        topic_scores=json.loads(report.topic_scores_json),
        recommendation=report.recommendation,
        detailed_insights=report.detailed_insights,
        generated_at=report.generated_at,
    )
