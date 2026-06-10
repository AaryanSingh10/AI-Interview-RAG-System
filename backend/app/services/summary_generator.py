import json
from datetime import datetime

from sqlalchemy.orm import Session

from app.models.db_models import InterviewQuestion, InterviewReport, InterviewSession
from app.models.schemas import InterviewSummary, ResumeProfile
from app.services.llm_client import llm_client
from app.services.roles import RoleInfo


async def generate_summary(
    db: Session,
    session: InterviewSession,
    role: RoleInfo,
    profile: ResumeProfile,
) -> InterviewSummary:
    questions: list[InterviewQuestion] = sorted(
        session.questions, key=lambda q: q.order_index
    )

    qa_blocks = []
    for question in questions:
        qa_blocks.append(
            f"Q ({question.topic}, {question.difficulty}): {question.question}\n"
            f"A: {question.answer or '[no answer]'}"
        )
    qa_text = "\n\n".join(qa_blocks)

    prompt = f"""Evaluate this technical interview for the {role.title} role.

Candidate profile:
- Skills: {', '.join(profile.skills)}
- Technologies: {', '.join(profile.technologies)}
- Experience: {profile.experience_years or 'unknown'} years

Interview Q&A:
{qa_text}

Return JSON only:
{{
  "overall_score": 0-100,
  "strengths": ["..."],
  "weaknesses": ["..."],
  "topic_scores": {{"topic": score}},
  "recommendation": "hire|proceed|reject with rationale",
  "detailed_insights": "paragraph"
}}"""

    raw = await llm_client.generate(
        prompt=prompt,
        system="You are a senior hiring manager evaluating ML interview performance. Output JSON only.",
    )
    payload = llm_client.extract_json(raw)

    report = InterviewReport(
        session_id=session.id,
        overall_score=float(payload.get("overall_score", 0)),
        strengths_json=json.dumps(payload.get("strengths", [])),
        weaknesses_json=json.dumps(payload.get("weaknesses", [])),
        topic_scores_json=json.dumps(payload.get("topic_scores", {})),
        recommendation=str(payload.get("recommendation", "Review required")),
        detailed_insights=str(
            payload.get("detailed_insights", "No detailed insights generated.")
        ),
        generated_at=datetime.utcnow(),
    )

    existing = session.report
    if existing:
        db.delete(existing)

    db.add(report)
    session.status = "completed"
    db.commit()
    db.refresh(report)

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
