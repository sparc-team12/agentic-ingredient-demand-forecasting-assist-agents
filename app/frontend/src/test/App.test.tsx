// Bootstrap smoke test, updated for ACRI-66 (routing/auth), extended for
// ACRI-61 (new gated route), and further extended for ACRI-60/62/63/59
// (Menu & Recipe Setup, Current Stock Setup, Sales History Import, and the
// Data Setup hub). Renders `App` inside a test router + `AuthProvider`
// (mocked authenticated/unauthenticated via a mocked `apiClient`) and
// asserts the auth-gating behavior (AC1) for each new route, mirroring how
// this same test was extended when ACRI-66 introduced routing.
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";

import { apiClient } from "../lib/api-client";
import App from "../App";
import { AuthProvider } from "../lib/auth-context";

vi.mock("@/lib/api-client", () => ({
  apiClient: {
    get: vi.fn().mockRejectedValue(new Error("no session in this test")),
    post: vi.fn(),
    put: vi.fn(),
  },
  ApiError: class ApiError extends Error {
    status: number;
    detail: string;
    constructor(status: number, detail: string) {
      super(detail);
      this.status = status;
      this.detail = detail;
    }
  },
}));

describe("App (bootstrap smoke test)", () => {
  afterEach(() => {
    vi.mocked(apiClient.get).mockReset();
    vi.mocked(apiClient.get).mockRejectedValue(new Error("no session in this test"));
  });

  it("redirects an unauthenticated visitor to the login screen", async () => {
    render(
      <MemoryRouter initialEntries={["/"]}>
        <AuthProvider>
          <App />
        </AuthProvider>
      </MemoryRouter>,
    );

    expect(await screen.findByRole("heading", { name: /log in/i })).toBeInTheDocument();
  });

  it("redirects an unauthenticated visitor away from the Ingredients & Suppliers Setup route", async () => {
    render(
      <MemoryRouter initialEntries={["/data-setup/ingredients-suppliers"]}>
        <AuthProvider>
          <App />
        </AuthProvider>
      </MemoryRouter>,
    );

    expect(await screen.findByRole("heading", { name: /log in/i })).toBeInTheDocument();
  });

  it("renders the Ingredients & Suppliers Setup screen for an authenticated visitor", async () => {
    vi.mocked(apiClient.get).mockImplementation((path: string) => {
      if (path === "/auth/me") {
        return Promise.resolve({
          email: "kitchen.manager@example.com",
          persona: "kitchen_manager",
        });
      }
      if (path === "/suppliers" || path === "/ingredients") {
        return Promise.resolve([]);
      }
      return Promise.reject(new Error(`unexpected path ${path}`));
    });

    render(
      <MemoryRouter initialEntries={["/data-setup/ingredients-suppliers"]}>
        <AuthProvider>
          <App />
        </AuthProvider>
      </MemoryRouter>,
    );

    expect(
      await screen.findByRole("heading", { name: /ingredients & suppliers setup/i }),
    ).toBeInTheDocument();
  });

  it("redirects an unauthenticated visitor away from the Data Setup hub route", async () => {
    render(
      <MemoryRouter initialEntries={["/data-setup"]}>
        <AuthProvider>
          <App />
        </AuthProvider>
      </MemoryRouter>,
    );

    expect(await screen.findByRole("heading", { name: /log in/i })).toBeInTheDocument();
  });

  it("renders the Data Setup hub for an authenticated visitor", async () => {
    vi.mocked(apiClient.get).mockImplementation((path: string) => {
      if (path === "/auth/me") {
        return Promise.resolve({
          email: "kitchen.manager@example.com",
          persona: "kitchen_manager",
        });
      }
      if (path === "/data-setup/status") {
        return Promise.resolve({
          categories: [
            {
              id: "menu-recipe",
              label: "Menu & Recipe Setup",
              path: "/data-setup/menu-recipe-setup",
              loaded: false,
            },
          ],
          all_loaded: false,
        });
      }
      return Promise.reject(new Error(`unexpected path ${path}`));
    });

    render(
      <MemoryRouter initialEntries={["/data-setup"]}>
        <AuthProvider>
          <App />
        </AuthProvider>
      </MemoryRouter>,
    );

    expect(await screen.findByRole("heading", { name: /data setup/i })).toBeInTheDocument();
  });

  it("renders the Menu & Recipe Setup screen for an authenticated visitor", async () => {
    vi.mocked(apiClient.get).mockImplementation((path: string) => {
      if (path === "/auth/me") {
        return Promise.resolve({
          email: "kitchen.manager@example.com",
          persona: "kitchen_manager",
        });
      }
      if (path === "/dishes") {
        return Promise.resolve([]);
      }
      return Promise.reject(new Error(`unexpected path ${path}`));
    });

    render(
      <MemoryRouter initialEntries={["/data-setup/menu-recipe-setup"]}>
        <AuthProvider>
          <App />
        </AuthProvider>
      </MemoryRouter>,
    );

    expect(
      await screen.findByRole("heading", { name: /menu & recipe setup/i }),
    ).toBeInTheDocument();
  });

  it("renders the Current Stock Setup screen for an authenticated visitor", async () => {
    vi.mocked(apiClient.get).mockImplementation((path: string) => {
      if (path === "/auth/me") {
        return Promise.resolve({
          email: "kitchen.manager@example.com",
          persona: "kitchen_manager",
        });
      }
      if (path === "/current-stock") {
        return Promise.resolve([]);
      }
      return Promise.reject(new Error(`unexpected path ${path}`));
    });

    render(
      <MemoryRouter initialEntries={["/data-setup/current-stock-setup"]}>
        <AuthProvider>
          <App />
        </AuthProvider>
      </MemoryRouter>,
    );

    expect(
      await screen.findByRole("heading", { name: /current stock setup/i }),
    ).toBeInTheDocument();
  });

  it("renders the Sales History Import screen for an authenticated visitor", async () => {
    vi.mocked(apiClient.get).mockImplementation((path: string) => {
      if (path === "/auth/me") {
        return Promise.resolve({
          email: "kitchen.manager@example.com",
          persona: "kitchen_manager",
        });
      }
      if (path === "/sales-history") {
        return Promise.resolve([]);
      }
      return Promise.reject(new Error(`unexpected path ${path}`));
    });

    render(
      <MemoryRouter initialEntries={["/data-setup/sales-history-import"]}>
        <AuthProvider>
          <App />
        </AuthProvider>
      </MemoryRouter>,
    );

    expect(
      await screen.findByRole("heading", { name: /sales history import/i }),
    ).toBeInTheDocument();
  });
});
