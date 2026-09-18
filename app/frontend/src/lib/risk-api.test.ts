// Request shape / error-propagation behavior of the `RiskConfig` functions
// added to risk-api.ts for the Risk Dashboard's materiality-threshold
// control (ACRI-58 US-023), mirroring `current-stock-api.test.ts`'s
// pattern. `getIngredientRisk` already has end-to-end coverage via
// `ingredient-detail.test.tsx`.
import { describe, expect, it, vi } from "vitest";

import { ApiError, apiClient } from "@/lib/api-client";
import { getRiskConfig, updateRiskConfig } from "@/lib/risk-api";

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

describe("risk-api RiskConfig functions", () => {
  it("getRiskConfig calls apiClient.get with /risk-config", async () => {
    vi.mocked(apiClient.get).mockResolvedValue({ materiality_threshold_inr: 500 });

    const result = await getRiskConfig();

    expect(apiClient.get).toHaveBeenCalledWith("/risk-config");
    expect(result).toEqual({ materiality_threshold_inr: 500 });
  });

  it("updateRiskConfig calls apiClient.put with /risk-config and the payload", async () => {
    vi.mocked(apiClient.put).mockResolvedValue({ materiality_threshold_inr: 250 });

    const result = await updateRiskConfig(250);

    expect(apiClient.put).toHaveBeenCalledWith("/risk-config", {
      materiality_threshold_inr: 250,
    });
    expect(result).toEqual({ materiality_threshold_inr: 250 });
  });

  it("propagates an ApiError unchanged when the underlying apiClient call rejects", async () => {
    vi.mocked(apiClient.put).mockRejectedValue(new ApiError(422, "Invalid threshold"));

    await expect(updateRiskConfig(-1)).rejects.toMatchObject({
      status: 422,
      detail: "Invalid threshold",
    });
  });
});
