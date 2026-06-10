from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class RoleInfo(BaseModel):
    id: str
    title: str
    description: str
    topics: list[str]


class ResumeProfile(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    skills: list[str] = Field(default_factory=list)
    technologies: list[str] = Field(default_factory=list)
    experience_years: Optional[float] = None
    education: list[str] = Field(default_factory=list)
    summary: str = ""


class SessionCreateResponse(BaseModel):
    session_id: str
    role_id: str
    resume_profile: ResumeProfile


class QuestionItem(BaseModel):
    id: str
    question: str
    topic: str
    difficulty: str
    rationale: str


class QuestionsResponse(BaseModel):
    session_id: str
    questions: list[QuestionItem]


class AnswerSubmission(BaseModel):
    question_id: str
    answer: str


class AnswerResponse(BaseModel):
    question_id: str
    stored: bool


class InterviewSummary(BaseModel):
    session_id: str
    role_id: str
    candidate_name: Optional[str]
    overall_score: float
    strengths: list[str]
    weaknesses: list[str]
    topic_scores: dict[str, float]
    recommendation: str
    detailed_insights: str
    generated_at: datetime
