// Request shape / error-propagation behavior of the sales-history-api
// functions (ACRI-63), mirroring `ingredients-api.test.ts`'s pattern.
import { describe, expect, it, vi } from "vitest";

import { ApiError, apiClient } from "@/lib/api-client";
import { createSalesHistoryRecord, listSalesHistory } from "@/lib/sales-history-api";

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

describe("sales-history-api", () => {
  it("listSalesHistory calls apiClient.get with /sales-history", async () => {
    vi.mocked(apiClient.get).mockResolvedValue([]);

    await listSalesHistory();

    expect(apiClient.get).toHaveBeenCalledWith("/sales-history");
  });

  it("createSalesHistoryRecord calls apiClient.post with /sales-history and the payload", async () => {
    const input = { dish_id: 3, sale_date: "2026-01-01", units_sold: 42 };
    vi.mocked(apiClient.post).mockResolvedValue({ id: 1, ...input });

    await createSalesHistoryRecord(input);

    expect(apiClient.post).toHaveBeenCalledWith("/sales-history", input);
  });

  it("propagates an ApiError unchanged when the underlying apiClient call rejects", async () => {
    vi.mocked(apiClient.get).mockRejectedValue(new ApiError(401, "Not authenticated"));

    await expect(listSalesHistory()).rejects.toMatchObject({
      status: 401,
      detail: "Not authenticated",
    });
  });
});
