import json
import uuid

from sqlalchemy.orm import Session

from app.config import settings
from app.models.db_models import InterviewQuestion, InterviewSession
from app.models.schemas import QuestionItem, ResumeProfile
from app.services.llm_client import llm_client
from app.services.rag.vector_store import vector_store
from app.services.roles import RoleInfo


def _difficulty_from_profile(profile: ResumeProfile) -> str:
    years = profile.experience_years or 0
    skill_count = len(profile.skills) + len(profile.technologies)
    if years >= 5 or skill_count >= 12:
        return "hard"
    if years >= 2 or skill_count >= 6:
        return "medium"
    return "easy"


async def build_retrieval_query(role: RoleInfo, profile: ResumeProfile) -> str:
    skills = ", ".join(profile.skills[:10]) or "general machine learning"
    tech = ", ".join(profile.technologies[:10]) or "python, scikit-learn"
    topics = ", ".join(role.topics)
    return (
        f"Role: {role.title}. Topics: {topics}. "
        f"Candidate skills: {skills}. Technologies: {tech}. "
        f"Experience years: {profile.experience_years or 'unknown'}."
    )


async def generate_questions(
    db: Session,
    session: InterviewSession,
    role: RoleInfo,
    profile: ResumeProfile,
) -> list[QuestionItem]:
    query = await build_retrieval_query(role, profile)
    retrieved = await vector_store.retrieve(query=query, role_id=role.id)
    context_blocks = [
        f"[{item['metadata'].get('source', 'unknown')} | {item['metadata'].get('topic', 'ML')}] {item['text']}"
        for item in retrieved
    ]
    context = "\n\n".join(context_blocks) or "No retrieved context available."

    difficulty_hint = _difficulty_from_profile(profile)
    prompt = f"""You are an expert technical interviewer for the role of {role.title}.

Candidate profile:
- Name: {profile.name or 'Unknown'}
- Skills: {', '.join(profile.skills) or 'none detected'}
- Technologies: {', '.join(profile.technologies) or 'none detected'}
- Experience: {profile.experience_years or 'unknown'} years
- Education: {', '.join(profile.education) or 'not specified'}

Role topics: {', '.join(role.topics)}
Target difficulty baseline: {difficulty_hint}

Retrieved knowledge base context:
{context}

Generate exactly {settings.questions_per_session} personalized interview questions.
Rules:
1. Questions must be grounded in the retrieved context and role topics.
2. Difficulty should reflect candidate experience and skills.
3. Include a mix of conceptual and practical questions.
4. At least 2 questions should reference technologies/skills from the resume.
5. Return valid JSON only.

JSON schema:
{{
  "questions": [
    {{
      "question": "string",
      "topic": "string",
      "difficulty": "easy|medium|hard",
      "rationale": "string"
    }}
  ]
}}"""

    raw = await llm_client.generate(
        prompt=prompt,
        system="You generate rigorous, fair technical interview questions. Output JSON only.",
    )
    payload = llm_client.extract_json(raw)
    questions_data = payload.get("questions", [])

    if not questions_data:
        questions_data = _fallback_questions(role, profile)

    stored: list[QuestionItem] = []
    for index, item in enumerate(questions_data[: settings.questions_per_session]):
        question = InterviewQuestion(
            id=str(uuid.uuid4()),
            session_id=session.id,
            question=item["question"],
            topic=item.get("topic", role.topics[0]),
            difficulty=item.get("difficulty", difficulty_hint),
            rationale=item.get("rationale", "Generated from role and resume context."),
            order_index=index,
        )
        db.add(question)
        stored.append(
            QuestionItem(
                id=question.id,
                question=question.question,
                topic=question.topic,
                difficulty=question.difficulty,
                rationale=question.rationale,
            )
        )

    session.status = "questions_generated"
    db.commit()
    return stored


def _fallback_questions(role: RoleInfo, profile: ResumeProfile) -> list[dict[str, str]]:
    skill = profile.skills[0] if profile.skills else "machine learning"
    return [
        {
            "question": f"Explain how {skill} applies to {role.topics[0].lower()} in production systems.",
            "topic": role.topics[0],
            "difficulty": "medium",
            "rationale": "Fallback question aligned with role topic and resume skill.",
        },
        {
            "question": f"Describe a project where you used {profile.technologies[0] if profile.technologies else 'Python'} for model development.",
            "topic": role.topics[1] if len(role.topics) > 1 else role.topics[0],
            "difficulty": "easy",
            "rationale": "Resume-informed practical question.",
        },
    ]
