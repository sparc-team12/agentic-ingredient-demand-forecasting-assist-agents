// AC1: `RequireAuth` redirects to `/login` when unauthenticated, shows a
// loading placeholder while bootstrap is in flight, and renders children
// once authenticated.
import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

import { RequireAuth } from "@/components/auth/require-auth";
import { useAuth } from "@/hooks/use-auth";

vi.mock("@/hooks/use-auth");

const mockedUseAuth = vi.mocked(useAuth);

function renderWithRouter(initialPath: string) {
  return render(
    <MemoryRouter initialEntries={[initialPath]}>
      <Routes>
        <Route path="/login" element={<p>Login screen</p>} />
        <Route
          path="/protected"
          element={
            <RequireAuth>
              <p>Protected content</p>
            </RequireAuth>
          }
        />
      </Routes>
    </MemoryRouter>,
  );
}

describe("RequireAuth", () => {
  it("shows a loading state while the session bootstrap is in flight", () => {
    mockedUseAuth.mockReturnValue({
      status: "loading",
      user: null,
      login: vi.fn(),
      logout: vi.fn(),
    });

    renderWithRouter("/protected");

    expect(screen.queryByText("Protected content")).not.toBeInTheDocument();
    expect(screen.queryByText("Login screen")).not.toBeInTheDocument();
  });

  it("redirects to /login when unauthenticated (AC1)", () => {
    mockedUseAuth.mockReturnValue({
      status: "unauthenticated",
      user: null,
      login: vi.fn(),
      logout: vi.fn(),
    });

    renderWithRouter("/protected");

    expect(screen.getByText("Login screen")).toBeInTheDocument();
    expect(screen.queryByText("Protected content")).not.toBeInTheDocument();
  });

  it("renders children when authenticated", () => {
    mockedUseAuth.mockReturnValue({
      status: "authenticated",
      user: { email: "km@example.com", persona: "kitchen_manager" },
      login: vi.fn(),
      logout: vi.fn(),
    });

    renderWithRouter("/protected");

    expect(screen.getByText("Protected content")).toBeInTheDocument();
  });
});
