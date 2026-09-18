// Route guard (ACRI-66, AC1): redirects to `/login` when unauthenticated,
// shows a loading placeholder while the session bootstrap (`GET /auth/me`)
// is in flight, and renders its children once authenticated.
import type { ReactNode } from "react";
import { Navigate } from "react-router-dom";

import { useAuth } from "@/hooks/use-auth";

interface RequireAuthProps {
  children: ReactNode;
}

export function RequireAuth({ children }: RequireAuthProps) {
  const { status } = useAuth();

  if (status === "loading") {
    return <p>Loading…</p>;
  }

  if (status === "unauthenticated") {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
}
