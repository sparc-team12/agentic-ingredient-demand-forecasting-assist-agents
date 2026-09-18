// ACRI-62 AC1/AC2: loading/empty/error/data states for the Current Stock
// Setup screen; one row per existing ingredient; the perishable/no-use-by-
// date gap flag; edit form opens pre-filled and submits an upsert.
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { apiClient, ApiError } from "@/lib/api-client";
import type { CurrentStock } from "@/lib/current-stock-api";
import CurrentStockSetupRoute from "@/routes/current-stock-setup";

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

const RECORDED_STOCK: CurrentStock = {
  ingredient_id: 1,
  ingredient_name: "Roma Tomatoes",
  unit: "kg",
  perishable: false,
  quantity_on_hand: 12.5,
  use_by_date: null,
  has_stock_recorded: true,
  use_by_date_gap: false,
};

const FLAGGED_STOCK: CurrentStock = {
  ingredient_id: 2,
  ingredient_name: "Fresh Basil",
  unit: "bunch",
  perishable: true,
  quantity_on_hand: 3,
  use_by_date: null,
  has_stock_recorded: true,
  use_by_date_gap: true,
};

function mockGet(stocks: CurrentStock[]) {
  vi.mocked(apiClient.get).mockImplementation((path: string) => {
    if (path === "/current-stock") return Promise.resolve(stocks);
    return Promise.reject(new Error(`unexpected path ${path}`));
  });
}

describe("CurrentStockSetupRoute", () => {
  it("renders a loading state before the fetch resolves", () => {
    vi.mocked(apiClient.get).mockReturnValue(new Promise(() => {}));

    render(<CurrentStockSetupRoute />);

    expect(screen.getByText(/loading/i)).toBeInTheDocument();
  });

  it("renders the empty-state message when there are no ingredients", async () => {
    mockGet([]);

    render(<CurrentStockSetupRoute />);

    expect(await screen.findByText(/no ingredients exist yet/i)).toBeInTheDocument();
  });

  it("renders one row per ingredient with its quantity (AC1)", async () => {
    mockGet([RECORDED_STOCK]);

    render(<CurrentStockSetupRoute />);

    await screen.findByText("Roma Tomatoes");
    expect(screen.getByText("12.5 kg")).toBeInTheDocument();
  });

  it("renders the gap flag for a perishable ingredient with no use-by date (AC2)", async () => {
    mockGet([RECORDED_STOCK, FLAGGED_STOCK]);

    render(<CurrentStockSetupRoute />);

    await screen.findByText("Fresh Basil");
    expect(screen.getByText("Use-by date missing")).toBeInTheDocument();
  });

  it("renders a visible error message if listCurrentStock rejects", async () => {
    vi.mocked(apiClient.get).mockRejectedValue(new ApiError(401, "Not authenticated"));

    render(<CurrentStockSetupRoute />);

    expect(await screen.findByRole("alert")).toHaveTextContent("Not authenticated");
  });

  it("opens the edit form pre-filled and submits an upsert request", async () => {
    mockGet([RECORDED_STOCK]);
    vi.mocked(apiClient.put).mockResolvedValue(RECORDED_STOCK);

    render(<CurrentStockSetupRoute />);

    await screen.findByText("Roma Tomatoes");
    fireEvent.click(screen.getByRole("button", { name: /edit/i }));

    expect(screen.getByLabelText(/quantity on hand/i)).toHaveValue(12.5);
    fireEvent.click(screen.getByRole("button", { name: /save stock/i }));

    await waitFor(() => {
      expect(apiClient.put).toHaveBeenCalledWith(
        "/current-stock/1",
        expect.objectContaining({ quantity_on_hand: 12.5 }),
      );
    });
  });
});
