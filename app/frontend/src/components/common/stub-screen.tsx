// Shared placeholder-screen component (ACRI-66) reused by all 4 gated
// routes. Fetches its backend stub endpoint on mount and renders the
// returned message + a logout button. No persona-conditional rendering —
// both personas see the identical shape (AC5).
import { useEffect, useState } from "react";

import { useAuth } from "@/hooks/use-auth";
import { apiClient, ApiError } from "@/lib/api-client";
import type { ScreenMeta } from "@/lib/screens";

interface ScreenPlaceholderResponse {
  screen: string;
  message: string;
  user: { email: string; persona: string };
}

interface StubScreenProps {
  screen: ScreenMeta;
}

export function StubScreen({ screen }: StubScreenProps) {
  const { logout } = useAuth();
  const [data, setData] = useState<ScreenPlaceholderResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setData(null);
    setError(null);
    apiClient
      .get<ScreenPlaceholderResponse>(screen.backendPath)
      .then((response) => {
        if (!cancelled) setData(response);
      })
      .catch((err: unknown) => {
        if (cancelled) return;
        setError(err instanceof ApiError ? err.detail : "Failed to load this screen.");
      });
    return () => {
      cancelled = true;
    };
  }, [screen.backendPath]);

  return (
    <section className="page">
      <div className="page__header">
        <h1>{screen.label}</h1>
      </div>
      <div className="card">
        {error !== null && (
          <p role="alert" className="alert">
            {error}
          </p>
        )}
        {data !== null && (
          <>
            <p>{data.message}</p>
            <p className="hint-text">
              Logged in as {data.user.email} ({data.user.persona})
            </p>
          </>
        )}
        <button type="button" className="btn" onClick={() => void logout()}>
          Log out
        </button>
      </div>
    </section>
  );
}
