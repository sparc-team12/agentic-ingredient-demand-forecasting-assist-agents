// Controlled email/password login form (ACRI-66, AC2/AC3).
//
// No wireframe/spec exists for this screen (requirements-validation.json's
// own warning — the approved Design Document predates auth); this authors
// minimal, functional copy/layout only (implementation-plan.md Q2).
import { useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";

import { useAuth } from "@/hooks/use-auth";
import { ApiError } from "@/lib/api-client";

export function LoginForm() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setIsSubmitting(true);
    try {
      await login(email, password);
      navigate("/risk-dashboard", { replace: true });
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Something went wrong. Please try again.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} noValidate aria-label="Log in">
      <div className="field">
        <label htmlFor="email">Email</label>
        <input
          id="email"
          name="email"
          type="email"
          autoComplete="username"
          value={email}
          onChange={(event) => setEmail(event.target.value)}
          required
        />
      </div>
      <div className="field">
        <label htmlFor="password">Password</label>
        <input
          id="password"
          name="password"
          type="password"
          autoComplete="current-password"
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          required
        />
      </div>
      {error !== null && (
        <p role="alert" className="alert">
          {error}
        </p>
      )}
      <button type="submit" className="btn btn--primary btn--block" disabled={isSubmitting}>
        {isSubmitting ? "Logging in…" : "Log in"}
      </button>
    </form>
  );
}
