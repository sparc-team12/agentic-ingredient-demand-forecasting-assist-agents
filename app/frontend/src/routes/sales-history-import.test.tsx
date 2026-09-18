// ACRI-63 AC1/AC2: loading/empty/error/data states for the Sales History
// Import screen; full (never summarized) daily records per dish; the
// <84-days gap flag; add-record form opens and submits.
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { apiClient, ApiError } from "@/lib/api-client";
import type { DishSalesHistory } from "@/lib/sales-history-api";
import SalesHistoryImportRoute from "@/routes/sales-history-import";

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

const SHORT_HISTORY: DishSalesHistory = {
  dish_id: 1,
  dish_name: "Margherita Pizza",
  distinct_days_of_history: 1,
  has_full_history: false,
  records: [{ id: 1, dish_id: 1, sale_date: "2026-01-01", units_sold: 42 }],
};

function mockGet(history: DishSalesHistory[]) {
  vi.mocked(apiClient.get).mockImplementation((path: string) => {
    if (path === "/sales-history") return Promise.resolve(history);
    return Promise.reject(new Error(`unexpected path ${path}`));
  });
}

describe("SalesHistoryImportRoute", () => {
  it("renders a loading state before the fetch resolves", () => {
    vi.mocked(apiClient.get).mockReturnValue(new Promise(() => {}));

    render(<SalesHistoryImportRoute />);

    expect(screen.getByText(/loading/i)).toBeInTheDocument();
  });

  it("renders the empty-state message when there are no dishes", async () => {
    mockGet([]);

    render(<SalesHistoryImportRoute />);

    expect(await screen.findByText(/no dishes yet/i)).toBeInTheDocument();
  });

  it("renders the dish name, its full daily records, and the <84-days flag (AC1/AC2)", async () => {
    mockGet([SHORT_HISTORY]);

    render(<SalesHistoryImportRoute />);

    await screen.findByRole("heading", { name: "Margherita Pizza" });
    expect(screen.getByText("2026-01-01")).toBeInTheDocument();
    expect(screen.getByText(/fewer than 84 days of history/i)).toBeInTheDocument();
  });

  it("renders a visible error message if listSalesHistory rejects", async () => {
    vi.mocked(apiClient.get).mockRejectedValue(new ApiError(401, "Not authenticated"));

    render(<SalesHistoryImportRoute />);

    expect(await screen.findByRole("alert")).toHaveTextContent("Not authenticated");
  });

  it("opens the add-record form and submits a create request", async () => {
    mockGet([SHORT_HISTORY]);
    vi.mocked(apiClient.post).mockResolvedValue(SHORT_HISTORY.records[0]);

    render(<SalesHistoryImportRoute />);

    await screen.findByRole("heading", { name: "Margherita Pizza" });
    fireEvent.click(screen.getByRole("button", { name: /add record/i }));

    fireEvent.change(screen.getByLabelText("Date"), { target: { value: "2026-01-02" } });
    fireEvent.change(screen.getByLabelText("Units sold"), { target: { value: "10" } });
    fireEvent.click(screen.getByRole("button", { name: /save record/i }));

    await waitFor(() => {
      expect(apiClient.post).toHaveBeenCalledWith(
        "/sales-history",
        expect.objectContaining({ dish_id: 1, sale_date: "2026-01-02", units_sold: 10 }),
      );
    });
  });
});
