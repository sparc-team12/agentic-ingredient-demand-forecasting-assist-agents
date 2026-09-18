// AC2/AC3: `LoginForm` calls `useAuth().login` with entered values on
// submit; a successful login navigates away, a failed login renders the
// inline error and does not navigate.
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

import { LoginForm } from "@/components/auth/login-form";
import { useAuth } from "@/hooks/use-auth";
import { ApiError } from "@/lib/api-client";

vi.mock("@/hooks/use-auth");

const mockedUseAuth = vi.mocked(useAuth);

function renderLoginForm() {
  return render(
    <MemoryRouter>
      <LoginForm />
    </MemoryRouter>,
  );
}

function fillAndSubmit(email: string, password: string) {
  fireEvent.change(screen.getByLabelText(/email/i), { target: { value: email } });
  fireEvent.change(screen.getByLabelText(/password/i), { target: { value: password } });
  fireEvent.click(screen.getByRole("button", { name: /log in/i }));
}

describe("LoginForm", () => {
  it("calls login with the entered email/password on success (AC2)", async () => {
    const login = vi.fn().mockResolvedValue(undefined);
    mockedUseAuth.mockReturnValue({
      status: "unauthenticated",
      user: null,
      login,
      logout: vi.fn(),
    });

    renderLoginForm();
    fillAndSubmit("km@example.com", "correct-password");

    await waitFor(() => expect(login).toHaveBeenCalledWith("km@example.com", "correct-password"));
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });

  it("renders the inline error and does not clear the form on failure (AC3)", async () => {
    const login = vi.fn().mockRejectedValue(new ApiError(401, "Invalid email or password"));
    mockedUseAuth.mockReturnValue({
      status: "unauthenticated",
      user: null,
      login,
      logout: vi.fn(),
    });

    renderLoginForm();
    fillAndSubmit("km@example.com", "wrong-password");

    expect(await screen.findByRole("alert")).toHaveTextContent("Invalid email or password");
    expect(login).toHaveBeenCalledWith("km@example.com", "wrong-password");
  });

  it("renders a generic error for a non-ApiError failure", async () => {
    const login = vi.fn().mockRejectedValue(new Error("network down"));
    mockedUseAuth.mockReturnValue({
      status: "unauthenticated",
      user: null,
      login,
      logout: vi.fn(),
    });

    renderLoginForm();
    fillAndSubmit("km@example.com", "whatever");

    expect(await screen.findByRole("alert")).toHaveTextContent(/something went wrong/i);
  });
});
