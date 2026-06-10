"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { createSession, fetchRoles, type Role } from "@/lib/api";

export default function HomePage() {
  const router = useRouter();
  const [roles, setRoles] = useState<Role[]>([]);
  const [roleId, setRoleId] = useState("");
  const [resume, setResume] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    fetchRoles()
      .then((data) => {
        setRoles(data);
        if (data.length) setRoleId(data[0].id);
      })
      .catch((err: Error) => setError(err.message));
  }, []);

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    if (!resume || !roleId) {
      setError("Please select a role and upload a resume.");
      return;
    }

    setLoading(true);
    setError("");
    try {
      const session = await createSession(roleId, resume);
      sessionStorage.setItem(
        `session:${session.session_id}`,
        JSON.stringify(session.resume_profile)
      );
      router.push(`/interview/${session.session_id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create session");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main>
      <section className="hero">
        <h1>AI Candidate Screening</h1>
        <p>
          Upload your resume, choose a target role, and receive personalized interview
          questions powered by RAG over ML knowledge bases.
        </p>
      </section>

      <div className="steps">
        <span className="step active">1. Upload & Role</span>
        <span className="step">2. Interview</span>
        <span className="step">3. Results</span>
      </div>

      <form className="card grid" onSubmit={handleSubmit}>
        <div>
          <label htmlFor="role">Target Role</label>
          <select
            id="role"
            value={roleId}
            onChange={(e) => setRoleId(e.target.value)}
            disabled={!roles.length}
          >
            {roles.map((role) => (
              <option key={role.id} value={role.id}>
                {role.title}
              </option>
            ))}
          </select>
          {roles.find((r) => r.id === roleId) && (
            <p className="muted" style={{ marginTop: "0.5rem" }}>
              {roles.find((r) => r.id === roleId)?.description}
            </p>
          )}
        </div>

        <div>
          <label htmlFor="resume">Resume (PDF or TXT)</label>
          <input
            id="resume"
            type="file"
            accept=".pdf,.txt,.md"
            onChange={(e) => setResume(e.target.files?.[0] ?? null)}
          />
          <p className="muted" style={{ marginTop: "0.5rem" }}>
            Try the sample resume in <code>knowledge_base/sample_resumes/</code>
          </p>
        </div>

        <button type="submit" disabled={loading}>
          {loading ? "Starting session..." : "Start Interview"}
        </button>
        {error && <p className="error">{error}</p>}
      </form>
    </main>
  );
}
