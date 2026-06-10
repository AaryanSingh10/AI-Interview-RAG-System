"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { completeInterview, type InterviewSummary } from "@/lib/api";

export default function ResultsPage() {
  const params = useParams<{ sessionId: string }>();
  const sessionId = params.sessionId;
  const [summary, setSummary] = useState<InterviewSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const cached = sessionStorage.getItem(`summary:${sessionId}`);
    if (cached) {
      setSummary(JSON.parse(cached));
      setLoading(false);
      return;
    }

    completeInterview(sessionId)
      .then(setSummary)
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false));
  }, [sessionId]);

  if (loading) {
    return (
      <main>
        <div className="card">Loading interview summary...</div>
      </main>
    );
  }

  if (error || !summary) {
    return (
      <main>
        <div className="card error">{error || "Summary unavailable"}</div>
      </main>
    );
  }

  return (
    <main>
      <section className="hero">
        <h1>Interview Results</h1>
        <p className="muted">
          {summary.candidate_name || "Candidate"} · Role: {summary.role_id.replaceAll("_", " ")}
        </p>
      </section>

      <div className="steps">
        <span className="step">1. Upload & Role</span>
        <span className="step">2. Interview</span>
        <span className="step active">3. Results</span>
      </div>

      <div className="grid grid-2" style={{ marginBottom: "1rem" }}>
        <div className="card">
          <p className="muted">Overall Score</p>
          <div className="score-ring">{summary.overall_score.toFixed(1)}</div>
        </div>
        <div className="card">
          <p className="muted">Recommendation</p>
          <h2 style={{ margin: 0, fontSize: "1.2rem" }}>{summary.recommendation}</h2>
        </div>
      </div>

      <div className="grid grid-2" style={{ marginBottom: "1rem" }}>
        <div className="card">
          <h3>Strengths</h3>
          <ul>
            {summary.strengths.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </div>
        <div className="card">
          <h3>Areas to Improve</h3>
          <ul>
            {summary.weaknesses.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </div>
      </div>

      <div className="card" style={{ marginBottom: "1rem" }}>
        <h3>Topic Scores</h3>
        {Object.entries(summary.topic_scores).map(([topic, score]) => (
          <div className="topic-row" key={topic}>
            <span>{topic}</span>
            <strong>{score.toFixed(1)}</strong>
          </div>
        ))}
      </div>

      <div className="card">
        <h3>Detailed Insights</h3>
        <p style={{ lineHeight: 1.7 }}>{summary.detailed_insights}</p>
      </div>

      <div style={{ marginTop: "1.25rem" }}>
        <Link className="button" href="/">
          Start New Interview
        </Link>
      </div>
    </main>
  );
}
