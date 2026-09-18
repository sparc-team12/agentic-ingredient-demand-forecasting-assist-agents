// Request shape / error-propagation behavior of the menu-recipe-api
// functions (ACRI-60), mirroring `ingredients-api.test.ts`'s pattern.
import { describe, expect, it, vi } from "vitest";

import { ApiError, apiClient } from "@/lib/api-client";
import {
  createDish,
  createRecipeLine,
  listDishes,
  updateDish,
  updateRecipeLine,
} from "@/lib/menu-recipe-api";

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

describe("menu-recipe-api", () => {
  it("listDishes calls apiClient.get with /dishes", async () => {
    vi.mocked(apiClient.get).mockResolvedValue([]);

    await listDishes();

    expect(apiClient.get).toHaveBeenCalledWith("/dishes");
  });

  it("createDish calls apiClient.post with /dishes and the payload", async () => {
    const input = { name: "Margherita Pizza" };
    vi.mocked(apiClient.post).mockResolvedValue({ id: 1, ...input, recipe_lines: [] });

    await createDish(input);

    expect(apiClient.post).toHaveBeenCalledWith("/dishes", input);
  });

  it("updateDish calls apiClient.put with /dishes/{id} and the payload", async () => {
    const input = { name: "Margherita Pizza (updated)" };
    vi.mocked(apiClient.put).mockResolvedValue({ id: 7, ...input, recipe_lines: [] });

    await updateDish(7, input);

    expect(apiClient.put).toHaveBeenCalledWith("/dishes/7", input);
  });

  it("createRecipeLine calls apiClient.post with /dishes/{dishId}/recipe-lines and the payload", async () => {
    const input = { ingredient_name: "Mozzarella", quantity_per_serving: 0.2, unit: "kg" };
    vi.mocked(apiClient.post).mockResolvedValue({
      id: 1,
      dish_id: 3,
      ...input,
      ingredient_id: null,
      ingredient_flagged: true,
    });

    await createRecipeLine(3, input);

    expect(apiClient.post).toHaveBeenCalledWith("/dishes/3/recipe-lines", input);
  });

  it("updateRecipeLine calls apiClient.put with /dishes/{dishId}/recipe-lines/{lineId} and the payload", async () => {
    const input = { ingredient_name: "Mozzarella", quantity_per_serving: 0.25, unit: "kg" };
    vi.mocked(apiClient.put).mockResolvedValue({
      id: 5,
      dish_id: 3,
      ...input,
      ingredient_id: 9,
      ingredient_flagged: false,
    });

    await updateRecipeLine(3, 5, input);

    expect(apiClient.put).toHaveBeenCalledWith("/dishes/3/recipe-lines/5", input);
  });

  it("propagates an ApiError unchanged when the underlying apiClient call rejects", async () => {
    vi.mocked(apiClient.get).mockRejectedValue(new ApiError(401, "Not authenticated"));

    await expect(listDishes()).rejects.toMatchObject({ status: 401, detail: "Not authenticated" });
  });
});
