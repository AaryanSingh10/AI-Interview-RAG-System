const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

export type Role = {
  id: string;
  title: string;
  description: string;
  topics: string[];
};

export type ResumeProfile = {
  name?: string | null;
  email?: string | null;
  skills: string[];
  technologies: string[];
  experience_years?: number | null;
  education: string[];
  summary: string;
};

export type Question = {
  id: string;
  question: string;
  topic: string;
  difficulty: string;
  rationale: string;
};

export type InterviewSummary = {
  session_id: string;
  role_id: string;
  candidate_name?: string | null;
  overall_score: number;
  strengths: string[];
  weaknesses: string[];
  topic_scores: Record<string, number>;
  recommendation: string;
  detailed_insights: string;
  generated_at: string;
};

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, options);
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || `Request failed: ${response.status}`);
  }
  return response.json();
}

export async function fetchRoles(): Promise<Role[]> {
  return request<Role[]>("/roles");
}

export async function createSession(roleId: string, resume: File) {
  const form = new FormData();
  form.append("role_id", roleId);
  form.append("resume", resume);
  return request<{ session_id: string; role_id: string; resume_profile: ResumeProfile }>(
    "/sessions",
    { method: "POST", body: form }
  );
}

export async function generateQuestions(sessionId: string) {
  return request<{ session_id: string; questions: Question[] }>(
    `/sessions/${sessionId}/questions`,
    { method: "POST" }
  );
}

export async function submitAnswer(sessionId: string, questionId: string, answer: string) {
  return request<{ question_id: string; stored: boolean }>(
    `/sessions/${sessionId}/answers`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question_id: questionId, answer }),
    }
  );
}

export async function completeInterview(sessionId: string): Promise<InterviewSummary> {
  return request<InterviewSummary>(`/sessions/${sessionId}/complete`, { method: "POST" });
}
