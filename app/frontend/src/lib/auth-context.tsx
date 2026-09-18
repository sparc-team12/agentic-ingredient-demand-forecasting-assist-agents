// AuthProvider + AuthContext (ACRI-66).
//
// Owns client-side session state as React Context — no dedicated
// state-management library is introduced (Assumption A8: `tech-stack.md`
// leaves state management `[TBD]`; Context is the zero-new-dependency
// option appropriate to this story's narrow scope). Bootstraps session
// state via `GET /auth/me` on mount (the browser sends the httpOnly cookie
// automatically, if present).
import { createContext, useCallback, useEffect, useState, type ReactNode } from "react";

import { apiClient } from "@/lib/api-client";

export type AuthStatus = "loading" | "authenticated" | "unauthenticated";

export interface AuthUser {
  email: string;
  persona: string;
}

export interface AuthContextValue {
  status: AuthStatus;
  user: AuthUser | null;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
}

export const AuthContext = createContext<AuthContextValue | undefined>(undefined);

interface AuthProviderProps {
  children: ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [status, setStatus] = useState<AuthStatus>("loading");
  const [user, setUser] = useState<AuthUser | null>(null);

  useEffect(() => {
    let cancelled = false;
    apiClient
      .get<AuthUser>("/auth/me")
      .then((me) => {
        if (cancelled) return;
        setUser(me);
        setStatus("authenticated");
      })
      .catch(() => {
        if (cancelled) return;
        setUser(null);
        setStatus("unauthenticated");
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    // Let ApiError propagate to the caller (LoginForm) so it can render the
    // inline error (AC3) without navigating.
    const me = await apiClient.post<AuthUser>("/auth/login", { email, password });
    setUser(me);
    setStatus("authenticated");
  }, []);

  const logout = useCallback(async () => {
    try {
      await apiClient.post("/auth/logout");
    } finally {
      setUser(null);
      setStatus("unauthenticated");
    }
  }, []);

  return (
    <AuthContext.Provider value={{ status, user, login, logout }}>{children}</AuthContext.Provider>
  );
}
