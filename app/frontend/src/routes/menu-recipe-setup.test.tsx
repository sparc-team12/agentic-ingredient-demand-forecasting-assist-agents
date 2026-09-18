// ACRI-60 AC1/AC2: loading/empty/error/data states for the Menu & Recipe
// Setup screen; full (never summarized) recipe rendered per dish; the
// unmatched-ingredient gap flag; add-dish and add/edit-recipe-line forms
// open and submit.
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { apiClient, ApiError } from "@/lib/api-client";
import type { Dish } from "@/lib/menu-recipe-api";
import MenuRecipeSetupRoute from "@/routes/menu-recipe-setup";

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

const DISH_WITH_FLAGGED_LINE: Dish = {
  id: 1,
  name: "Margherita Pizza",
  created_at: "2026-01-01T00:00:00Z",
  recipe_lines: [
    {
      id: 1,
      dish_id: 1,
      ingredient_name: "Mozzarella",
      ingredient_id: 5,
      quantity_per_serving: 0.2,
      unit: "kg",
      ingredient_flagged: false,
    },
    {
      id: 2,
      dish_id: 1,
      ingredient_name: "Unicorn Meat",
      ingredient_id: null,
      quantity_per_serving: 0.5,
      unit: "kg",
      ingredient_flagged: true,
    },
  ],
};

function mockGet(dishes: Dish[]) {
  vi.mocked(apiClient.get).mockImplementation((path: string) => {
    if (path === "/dishes") return Promise.resolve(dishes);
    return Promise.reject(new Error(`unexpected path ${path}`));
  });
}

describe("MenuRecipeSetupRoute", () => {
  it("renders a loading state before the fetch resolves", () => {
    vi.mocked(apiClient.get).mockReturnValue(new Promise(() => {}));

    render(<MenuRecipeSetupRoute />);

    expect(screen.getByText(/loading/i)).toBeInTheDocument();
  });

  it("renders the empty-state message when there are no dishes", async () => {
    mockGet([]);

    render(<MenuRecipeSetupRoute />);

    expect(await screen.findByText(/no dishes yet/i)).toBeInTheDocument();
  });

  it("renders the dish name and its full recipe (AC1)", async () => {
    mockGet([DISH_WITH_FLAGGED_LINE]);

    render(<MenuRecipeSetupRoute />);

    await screen.findByRole("heading", { name: "Margherita Pizza" });
    expect(screen.getByText("Mozzarella")).toBeInTheDocument();
    expect(screen.getByText("Unicorn Meat")).toBeInTheDocument();
  });

  it("renders the gap flag for a recipe line with no matching ingredient (AC2)", async () => {
    mockGet([DISH_WITH_FLAGGED_LINE]);

    render(<MenuRecipeSetupRoute />);

    await screen.findByText("Unicorn Meat");
    expect(screen.getByText("Not in Ingredients master")).toBeInTheDocument();
  });

  it("renders a visible error message if listDishes rejects", async () => {
    vi.mocked(apiClient.get).mockRejectedValue(new ApiError(401, "Not authenticated"));

    render(<MenuRecipeSetupRoute />);

    expect(await screen.findByRole("alert")).toHaveTextContent("Not authenticated");
  });

  it("opens the add-dish form and submits a create request", async () => {
    mockGet([]);
    vi.mocked(apiClient.post).mockResolvedValue({ ...DISH_WITH_FLAGGED_LINE, recipe_lines: [] });

    render(<MenuRecipeSetupRoute />);

    await screen.findByText(/no dishes yet/i);
    fireEvent.click(screen.getByRole("button", { name: /add dish/i }));

    fireEvent.change(screen.getByLabelText("Name"), { target: { value: "Margherita Pizza" } });
    fireEvent.click(screen.getByRole("button", { name: /save dish/i }));

    await waitFor(() => {
      expect(apiClient.post).toHaveBeenCalledWith("/dishes", { name: "Margherita Pizza" });
    });
  });

  it("opens the add-recipe-line form for a dish and submits a create request", async () => {
    mockGet([{ ...DISH_WITH_FLAGGED_LINE, recipe_lines: [] }]);
    vi.mocked(apiClient.post).mockResolvedValue(DISH_WITH_FLAGGED_LINE.recipe_lines[0]);

    render(<MenuRecipeSetupRoute />);

    await screen.findByRole("heading", { name: "Margherita Pizza" });
    fireEvent.click(screen.getByRole("button", { name: /add recipe line/i }));

    fireEvent.change(screen.getByLabelText("Ingredient"), { target: { value: "Mozzarella" } });
    fireEvent.change(screen.getByLabelText("Quantity per serving"), { target: { value: "0.2" } });
    fireEvent.change(screen.getByLabelText("Unit"), { target: { value: "kg" } });
    fireEvent.click(screen.getByRole("button", { name: /save recipe line/i }));

    await waitFor(() => {
      expect(apiClient.post).toHaveBeenCalledWith(
        "/dishes/1/recipe-lines",
        expect.objectContaining({ ingredient_name: "Mozzarella", unit: "kg" }),
      );
    });
  });
});
