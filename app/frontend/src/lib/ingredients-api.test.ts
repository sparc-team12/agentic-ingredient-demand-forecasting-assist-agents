// Request shape / error-propagation behavior of the ingredients-api
// functions (ACRI-61), mirroring `api-client.test.ts`'s pattern: mock the
// shared `apiClient`, assert each function calls it with the expected
// method/path/body, and that an `ApiError` propagates unchanged.
import { describe, expect, it, vi } from "vitest";

import { ApiError, apiClient } from "@/lib/api-client";
import {
  createIngredient,
  createSupplier,
  listIngredients,
  listSuppliers,
  updateIngredient,
  updateSupplier,
} from "@/lib/ingredients-api";

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

describe("ingredients-api", () => {
  it("listSuppliers calls apiClient.get with /suppliers", async () => {
    vi.mocked(apiClient.get).mockResolvedValue([]);

    await listSuppliers();

    expect(apiClient.get).toHaveBeenCalledWith("/suppliers");
  });

  it("createSupplier calls apiClient.post with /suppliers and the payload", async () => {
    const input = { name: "Acme Produce Co", lead_time_days: 3, safety_margin_days: 2 };
    vi.mocked(apiClient.post).mockResolvedValue({ id: 1, ...input });

    await createSupplier(input);

    expect(apiClient.post).toHaveBeenCalledWith("/suppliers", input);
  });

  it("updateSupplier calls apiClient.put with /suppliers/{id} and the full payload", async () => {
    const input = { name: "Acme Produce Co", lead_time_days: 4, safety_margin_days: null };
    vi.mocked(apiClient.put).mockResolvedValue({ id: 7, ...input });

    await updateSupplier(7, input);

    expect(apiClient.put).toHaveBeenCalledWith("/suppliers/7", input);
  });

  it("listIngredients calls apiClient.get with /ingredients", async () => {
    vi.mocked(apiClient.get).mockResolvedValue([]);

    await listIngredients();

    expect(apiClient.get).toHaveBeenCalledWith("/ingredients");
  });

  it("createIngredient calls apiClient.post with /ingredients and the payload", async () => {
    const input = {
      name: "Roma Tomatoes",
      unit: "kg",
      unit_cost: 2.5,
      perishable: true,
      shelf_life_days: 7,
      supplier_id: null,
      safety_margin_days_override: null,
    };
    vi.mocked(apiClient.post).mockResolvedValue({
      id: 1,
      ...input,
      supplier: null,
      has_supplier: false,
      effective_safety_margin_days: null,
      safety_margin_source: null,
      safety_margin_gap: true,
    });

    await createIngredient(input);

    expect(apiClient.post).toHaveBeenCalledWith("/ingredients", input);
  });

  it("updateIngredient calls apiClient.put with /ingredients/{id} and the full payload", async () => {
    const input = {
      name: "Roma Tomatoes",
      unit: "kg",
      unit_cost: 3.0,
      perishable: false,
      shelf_life_days: null,
      supplier_id: null,
      safety_margin_days_override: null,
    };
    vi.mocked(apiClient.put).mockResolvedValue({
      id: 9,
      ...input,
      supplier: null,
      has_supplier: false,
      effective_safety_margin_days: null,
      safety_margin_source: null,
      safety_margin_gap: true,
    });

    await updateIngredient(9, input);

    expect(apiClient.put).toHaveBeenCalledWith("/ingredients/9", input);
  });

  it("propagates an ApiError unchanged when the underlying apiClient call rejects", async () => {
    vi.mocked(apiClient.get).mockRejectedValue(new ApiError(401, "Not authenticated"));

    await expect(listSuppliers()).rejects.toMatchObject({
      status: 401,
      detail: "Not authenticated",
    });
  });
});
