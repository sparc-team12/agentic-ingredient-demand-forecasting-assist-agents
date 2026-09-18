// Request shape / error-propagation behavior of `getPurchaseOrderDraft`
// (ACRI-53 US-018), mirroring `risk-api.test.ts`'s pattern.
import { describe, expect, it, vi } from "vitest";

import { ApiError, apiClient } from "@/lib/api-client";
import { getPurchaseOrderDraft } from "@/lib/purchase-order-draft-api";

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

describe("purchase-order-draft-api", () => {
  it("getPurchaseOrderDraft calls apiClient.get with /ingredients/{id}/purchase-order-draft", async () => {
    const draft = {
      ingredient_id: 1,
      item_name: "Roma Tomatoes",
      unit: "kg",
      supplier_name: "Acme Produce Co",
      supplier_gap: false,
      suggested_quantity: 42,
      required_delivery_date: "2026-01-02",
    };
    vi.mocked(apiClient.get).mockResolvedValue(draft);

    const result = await getPurchaseOrderDraft(1);

    expect(apiClient.get).toHaveBeenCalledWith("/ingredients/1/purchase-order-draft");
    expect(result).toEqual(draft);
  });

  it("propagates an ApiError unchanged when the underlying apiClient call rejects", async () => {
    vi.mocked(apiClient.get).mockRejectedValue(
      new ApiError(404, "This ingredient is not currently flagged for stockout risk")
    );

    await expect(getPurchaseOrderDraft(1)).rejects.toMatchObject({
      status: 404,
      detail: "This ingredient is not currently flagged for stockout risk",
    });
  });
});
