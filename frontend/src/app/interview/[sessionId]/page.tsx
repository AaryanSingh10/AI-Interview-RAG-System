"use client";

import { useEffect, useMemo, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import {
  completeInterview,
  generateQuestions,
  submitAnswer,
  type Question,
  type ResumeProfile,
} from "@/lib/api";

export default function InterviewPage() {
  const params = useParams<{ sessionId: string }>();
  const router = useRouter();
  const sessionId = params.sessionId;

  const [questions, setQuestions] = useState<Question[]>([]);
  const [profile, setProfile] = useState<ResumeProfile | null>(null);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [answer, setAnswer] = useState("");
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  const currentQuestion = questions[currentIndex];
  const progress = useMemo(() => {
    if (!questions.length) return 0;
    return Math.round((Object.keys(answers).length / questions.length) * 100);
  }, [answers, questions.length]);

  useEffect(() => {
    const stored = sessionStorage.getItem(`session:${sessionId}`);
    if (stored) setProfile(JSON.parse(stored));

    generateQuestions(sessionId)
      .then((data) => setQuestions(data.questions))
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false));
  }, [sessionId]);

  useEffect(() => {
    if (currentQuestion) {
      setAnswer(answers[currentQuestion.id] || "");
    }
  }, [currentQuestion, answers]);

  async function saveCurrentAnswer() {
    if (!currentQuestion || !answer.trim()) {
      setError("Please provide an answer before continuing.");
      return;
    }
    setSubmitting(true);
    setError("");
    try {
      await submitAnswer(sessionId, currentQuestion.id, answer.trim());
      setAnswers((prev) => ({ ...prev, [currentQuestion.id]: answer.trim() }));
      return true;
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save answer");
      return false;
    } finally {
      setSubmitting(false);
    }
  }

  async function handleNext() {
    const saved = await saveCurrentAnswer();
    if (!saved) return;
    if (currentIndex < questions.length - 1) {
      setCurrentIndex((i) => i + 1);
    }
  }

  async function handleFinish() {
    const saved = await saveCurrentAnswer();
    if (!saved) return;

    setSubmitting(true);
    try {
      const summary = await completeInterview(sessionId);
      sessionStorage.setItem(`summary:${sessionId}`, JSON.stringify(summary));
      router.push(`/results/${sessionId}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to complete interview");
    } finally {
      setSubmitting(false);
    }
  }

  if (loading) {
    return (
      <main>
        <div className="card">Generating personalized questions from resume and knowledge base...</div>
      </main>
    );
  }

  if (!currentQuestion) {
    return (
      <main>
        <div className="card error">No questions were generated for this session.</div>
      </main>
    );
  }

  return (
    <main>
      <section className="hero">
        <h1>Interview Session</h1>
        <p className="muted">
          Question {currentIndex + 1} of {questions.length}
          {profile?.name ? ` · Candidate: ${profile.name}` : ""}
        </p>
      </section>

      <div className="steps">
        <span className="step">1. Upload & Role</span>
        <span className="step active">2. Interview</span>
        <span className="step">3. Results</span>
      </div>

      <div className="progress">
        <span style={{ width: `${progress}%` }} />
      </div>

      {profile && (
        <div className="card" style={{ marginBottom: "1rem" }}>
          <p className="muted" style={{ marginTop: 0 }}>
            Resume context used for personalization
          </p>
          <div>
            {profile.skills.slice(0, 8).map((skill) => (
              <span className="pill" key={skill}>
                {skill}
              </span>
            ))}
          </div>
        </div>
      )}

      <div className="card grid">
        <div>
          <span className="pill">{currentQuestion.topic}</span>
          <span className="pill">{currentQuestion.difficulty}</span>
        </div>
        <h2 style={{ margin: 0 }}>{currentQuestion.question}</h2>
        <p className="muted">{currentQuestion.rationale}</p>

        <div>
          <label htmlFor="answer">Your Answer</label>
          <textarea
            id="answer"
            value={answer}
            onChange={(e) => setAnswer(e.target.value)}
            placeholder="Write your response here..."
          />
        </div>

        <div style={{ display: "flex", gap: "0.75rem", flexWrap: "wrap" }}>
          {currentIndex > 0 && (
            <button
              type="button"
              className="button-secondary"
              onClick={() => setCurrentIndex((i) => i - 1)}
              disabled={submitting}
            >
              Previous
            </button>
          )}
          {currentIndex < questions.length - 1 ? (
            <button type="button" onClick={handleNext} disabled={submitting}>
              {submitting ? "Saving..." : "Save & Next"}
            </button>
          ) : (
            <button type="button" onClick={handleFinish} disabled={submitting}>
              {submitting ? "Generating summary..." : "Finish & View Results"}
            </button>
          )}
        </div>
        {error && <p className="error">{error}</p>}
      </div>
    </main>
  );
}
