// Request shape / error-propagation behavior of the dashboard-api
// functions (ACRI-54..58), mirroring `current-stock-api.test.ts`'s
// pattern.
import { describe, expect, it, vi } from "vitest";

import { ApiError, apiClient } from "@/lib/api-client";
import { getRiskSummary } from "@/lib/dashboard-api";

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

describe("dashboard-api", () => {
  it("getRiskSummary calls apiClient.get with /dashboard/risk-summary", async () => {
    const summary = { total_waste_exposure_inr: 0, rows: [], materiality_threshold_inr: 500 };
    vi.mocked(apiClient.get).mockResolvedValue(summary);

    const result = await getRiskSummary();

    expect(apiClient.get).toHaveBeenCalledWith("/dashboard/risk-summary");
    expect(result).toEqual(summary);
  });

  it("propagates an ApiError unchanged when the underlying apiClient call rejects", async () => {
    vi.mocked(apiClient.get).mockRejectedValue(new ApiError(401, "Not authenticated"));

    await expect(getRiskSummary()).rejects.toMatchObject({
      status: 401,
      detail: "Not authenticated",
    });
  });
});
