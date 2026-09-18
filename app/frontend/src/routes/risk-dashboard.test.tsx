// ACRI-54..58: the Risk Dashboard route loads and renders the aggregate
// total, the materiality-threshold control (which calls the PUT endpoint
// and reloads), the severity-ordered table, and the empty-dashboard state.
import { act, fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { apiClient, ApiError } from "@/lib/api-client";
import type { DashboardRiskSummary } from "@/lib/dashboard-api";
import RiskDashboardRoute from "@/routes/risk-dashboard";

vi.mock("@/lib/api-client", () => ({
  apiClient: {
    get: vi.fn(),
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

const SUMMARY_WITH_ROWS: DashboardRiskSummary = {
  total_waste_exposure_inr: 7550,
  rows: [
    {
      ingredient_id: 1,
      ingredient_name: "Roma Tomatoes",
      risk_type: "stockout",
      severity: "Critical",
      order_by_date: "2026-01-02",
      waste_cost_inr: null,
      suppressed: false,
    },
    {
      ingredient_id: 2,
      ingredient_name: "Basil",
      risk_type: "spoilage",
      severity: "Low",
      order_by_date: null,
      waste_cost_inr: 50,
      suppressed: true,
    },
  ],
  materiality_threshold_inr: 500,
};

const EMPTY_SUMMARY: DashboardRiskSummary = {
  total_waste_exposure_inr: 0,
  rows: [],
  materiality_threshold_inr: 500,
};

describe("RiskDashboardRoute", () => {
  it("renders a loading state before the summary resolves", () => {
    vi.mocked(apiClient.get).mockReturnValue(new Promise(() => {}));

    render(<RiskDashboardRoute />);

    expect(screen.getByText(/loading/i)).toBeInTheDocument();
  });

  it("renders a visible error message if the summary fetch rejects", async () => {
    vi.mocked(apiClient.get).mockRejectedValue(new ApiError(401, "Not authenticated"));

    render(<RiskDashboardRoute />);

    expect(await screen.findByRole("alert")).toHaveTextContent("Not authenticated");
  });

  it("renders the total, threshold control, and table rows", async () => {
    vi.mocked(apiClient.get).mockResolvedValue(SUMMARY_WITH_ROWS);

    render(<RiskDashboardRoute />);

    expect(await screen.findByText("₹7,550")).toBeInTheDocument();
    expect(screen.getByRole("spinbutton", { name: /materiality threshold/i })).toHaveValue(500);
    expect(screen.getByText("Roma Tomatoes")).toBeInTheDocument();
    // Suppressed row is hidden from the visible table.
    expect(screen.queryByText("Basil")).not.toBeInTheDocument();
  });

  it("renders the empty state with a ₹0 total when there are no at-risk ingredients", async () => {
    vi.mocked(apiClient.get).mockResolvedValue(EMPTY_SUMMARY);

    render(<RiskDashboardRoute />);

    expect(await screen.findByText("₹0")).toBeInTheDocument();
    expect(screen.getByText(/no ingredients currently at risk/i)).toBeInTheDocument();
  });

  it("saves the materiality threshold via PUT and reloads the summary", async () => {
    vi.mocked(apiClient.get).mockResolvedValue(SUMMARY_WITH_ROWS);
    vi.mocked(apiClient.put).mockResolvedValue({ materiality_threshold_inr: 250 });

    render(<RiskDashboardRoute />);
    await screen.findByText("₹7,550");
    const getCallsBeforeSave = vi.mocked(apiClient.get).mock.calls.length;

    fireEvent.change(screen.getByRole("spinbutton", { name: /materiality threshold/i }), {
      target: { value: "250" },
    });
    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: /save/i }));
    });

    expect(apiClient.put).toHaveBeenCalledWith("/risk-config", {
      materiality_threshold_inr: 250,
    });
    // Reloads (exactly 1 additional GET) after saving.
    expect(vi.mocked(apiClient.get).mock.calls.length).toBe(getCallsBeforeSave + 1);
  });
});
