// `useAuth()` — the single consumption point for `AuthContext` (ACRI-66).
import { useContext } from "react";

import { AuthContext, type AuthContextValue } from "@/lib/auth-context";

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
