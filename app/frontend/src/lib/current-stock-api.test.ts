// Request shape / error-propagation behavior of the current-stock-api
// functions (ACRI-62), mirroring `ingredients-api.test.ts`'s pattern.
import { describe, expect, it, vi } from "vitest";

import { ApiError, apiClient } from "@/lib/api-client";
import { listCurrentStock, updateCurrentStock } from "@/lib/current-stock-api";

vi.mock("@/lib/api-client", () => {
  class MockApiError extends Error {
    status: number;
    detail: string;
    constructor(status: number, detail: string) {
      super(detail);
      this.status = status;
      this.detail = detail;
    }
  }
  return {
    apiClient: {
      get: vi.fn(),
      post: vi.fn(),
      put: vi.fn(),
    },
    ApiError: MockApiError,
  };
});

describe("current-stock-api", () => {
  it("listCurrentStock calls apiClient.get with /current-stock", async () => {
    vi.mocked(apiClient.get).mockResolvedValue([]);

    await listCurrentStock();

    expect(apiClient.get).toHaveBeenCalledWith("/current-stock");
  });

  it("updateCurrentStock calls apiClient.put with /current-stock/{ingredientId} and the payload", async () => {
    const input = { quantity_on_hand: 12.5, use_by_date: "2026-01-01" };
    vi.mocked(apiClient.put).mockResolvedValue({
      ingredient_id: 3,
      ingredient_name: "Roma Tomatoes",
      unit: "kg",
      perishable: true,
      ...input,
      has_stock_recorded: true,
      use_by_date_gap: false,
    });

    await updateCurrentStock(3, input);

    expect(apiClient.put).toHaveBeenCalledWith("/current-stock/3", input);
  });

  it("propagates an ApiError unchanged when the underlying apiClient call rejects", async () => {
    vi.mocked(apiClient.get).mockRejectedValue(new ApiError(401, "Not authenticated"));

    await expect(listCurrentStock()).rejects.toMatchObject({
      status: 401,
      detail: "Not authenticated",
    });
  });
});
