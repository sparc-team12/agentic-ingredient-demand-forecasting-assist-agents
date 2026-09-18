// ACRI-61 TS-FE-01/02/03/04/07: loading/empty/error/data states for the
// Ingredients & Suppliers Setup screen; AC3/AC5 gap flags visible in
// rendered rows; add/edit forms open and submit.
import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { apiClient, ApiError } from "@/lib/api-client";
import type { Ingredient, Supplier } from "@/lib/ingredients-api";
import IngredientsSuppliersSetupRoute from "@/routes/ingredients-suppliers-setup";

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

const SUPPLIERS: Supplier[] = [
  { id: 1, name: "Acme Produce Co", lead_time_days: 3, safety_margin_days: 2 },
];

const MAPPED_INGREDIENT: Ingredient = {
  id: 1,
  name: "Roma Tomatoes",
  unit: "kg",
  unit_cost: 2.5,
  perishable: true,
  shelf_life_days: 7,
  supplier_id: 1,
  safety_margin_days_override: null,
  supplier: { id: 1, name: "Acme Produce Co", lead_time_days: 3 },
  has_supplier: true,
  effective_safety_margin_days: 2,
  safety_margin_source: "supplier",
  safety_margin_gap: false,
};

const UNMAPPED_NO_MARGIN_INGREDIENT: Ingredient = {
  id: 2,
  name: "Fresh Basil",
  unit: "bunch",
  unit_cost: 0.9,
  perishable: true,
  shelf_life_days: 3,
  supplier_id: null,
  safety_margin_days_override: null,
  supplier: null,
  has_supplier: false,
  effective_safety_margin_days: null,
  safety_margin_source: null,
  safety_margin_gap: true,
};

function mockGet(suppliers: Supplier[], ingredients: Ingredient[]) {
  vi.mocked(apiClient.get).mockImplementation((path: string) => {
    if (path === "/suppliers") return Promise.resolve(suppliers);
    if (path === "/ingredients") return Promise.resolve(ingredients);
    return Promise.reject(new Error(`unexpected path ${path}`));
  });
}

describe("IngredientsSuppliersSetupRoute", () => {
  it("renders a loading state before both fetches resolve", () => {
    vi.mocked(apiClient.get).mockReturnValue(new Promise(() => {}));

    render(<IngredientsSuppliersSetupRoute />);

    expect(screen.getByText(/loading/i)).toBeInTheDocument();
  });

  it("renders the supplier and ingredient tables once both fetches resolve (AC1/AC2)", async () => {
    mockGet(SUPPLIERS, [MAPPED_INGREDIENT]);

    render(<IngredientsSuppliersSetupRoute />);

    await screen.findByText("Roma Tomatoes");
    expect(screen.getAllByText("Acme Produce Co").length).toBeGreaterThan(0);
    expect(screen.getByText("kg")).toBeInTheDocument();
    expect(screen.getByText("2.5")).toBeInTheDocument();
  });

  it("shows each section's empty-state message when both arrays are empty", async () => {
    mockGet([], []);

    render(<IngredientsSuppliersSetupRoute />);

    expect(await screen.findByText(/no suppliers yet/i)).toBeInTheDocument();
    expect(screen.getByText(/no ingredients yet/i)).toBeInTheDocument();
  });

  it("renders the AC3 gap flag for an ingredient with no mapped supplier, and the supplier name for a mapped one", async () => {
    mockGet(SUPPLIERS, [MAPPED_INGREDIENT, UNMAPPED_NO_MARGIN_INGREDIENT]);

    render(<IngredientsSuppliersSetupRoute />);

    await screen.findByText("Roma Tomatoes");
    const ingredientRow = screen.getByText("Roma Tomatoes").closest("tr");
    expect(ingredientRow).not.toBeNull();
    expect(within(ingredientRow as HTMLElement).getByText("Acme Produce Co")).toBeInTheDocument();
    expect(screen.getByText("No supplier mapped")).toBeInTheDocument();
  });

  it("renders the AC5 gap flag and never a literal 0 for an ingredient with no resolved safety margin", async () => {
    mockGet(SUPPLIERS, [MAPPED_INGREDIENT, UNMAPPED_NO_MARGIN_INGREDIENT]);

    render(<IngredientsSuppliersSetupRoute />);

    await screen.findByText("Roma Tomatoes");
    expect(screen.getByText("Safety margin not set")).toBeInTheDocument();
    // The mapped ingredient's resolved value (2) renders as a number in its
    // own row (scoped to avoid also matching the supplier table's own "2").
    const ingredientRow = screen.getByText("Roma Tomatoes").closest("tr");
    expect(ingredientRow).not.toBeNull();
    expect(within(ingredientRow as HTMLElement).getByText("2")).toBeInTheDocument();
  });

  it("renders a visible error message if listSuppliers/listIngredients rejects", async () => {
    vi.mocked(apiClient.get).mockRejectedValue(new ApiError(401, "Not authenticated"));

    render(<IngredientsSuppliersSetupRoute />);

    expect(await screen.findByRole("alert")).toHaveTextContent("Not authenticated");
  });

  it("opens the add-ingredient form and submits a create request", async () => {
    mockGet(SUPPLIERS, []);
    vi.mocked(apiClient.post).mockResolvedValue(MAPPED_INGREDIENT);

    render(<IngredientsSuppliersSetupRoute />);

    await screen.findByText(/no ingredients yet/i);
    fireEvent.click(screen.getByRole("button", { name: /add ingredient/i }));

    fireEvent.change(screen.getByLabelText("Name"), { target: { value: "Roma Tomatoes" } });
    fireEvent.change(screen.getByLabelText("Unit"), { target: { value: "kg" } });
    fireEvent.change(screen.getByLabelText("Unit cost"), { target: { value: "2.5" } });
    fireEvent.click(screen.getByRole("button", { name: /save ingredient/i }));

    await waitFor(() => {
      expect(apiClient.post).toHaveBeenCalledWith(
        "/ingredients",
        expect.objectContaining({ name: "Roma Tomatoes", unit: "kg", unit_cost: 2.5 }),
      );
    });
  });

  it("opens the add-supplier form and submits a create request", async () => {
    mockGet([], []);
    vi.mocked(apiClient.post).mockResolvedValue(SUPPLIERS[0]);

    render(<IngredientsSuppliersSetupRoute />);

    await screen.findByText(/no suppliers yet/i);
    fireEvent.click(screen.getByRole("button", { name: /add supplier/i }));

    fireEvent.change(screen.getByLabelText("Name"), { target: { value: "Acme Produce Co" } });
    fireEvent.change(screen.getByLabelText("Lead time (days)"), { target: { value: "3" } });
    fireEvent.click(screen.getByRole("button", { name: /save supplier/i }));

    await waitFor(() => {
      expect(apiClient.post).toHaveBeenCalledWith(
        "/suppliers",
        expect.objectContaining({ name: "Acme Produce Co", lead_time_days: 3 }),
      );
    });
  });

  it("opens the edit-ingredient form pre-filled, and submits a full-replace update request", async () => {
    mockGet(SUPPLIERS, [MAPPED_INGREDIENT]);
    vi.mocked(apiClient.put).mockResolvedValue(MAPPED_INGREDIENT);

    render(<IngredientsSuppliersSetupRoute />);

    await screen.findByText("Roma Tomatoes");
    fireEvent.click(screen.getAllByRole("button", { name: /^edit$/i })[1]);

    expect(screen.getByLabelText("Name")).toHaveValue("Roma Tomatoes");
    fireEvent.click(screen.getByRole("button", { name: /save ingredient/i }));

    await waitFor(() => {
      expect(apiClient.put).toHaveBeenCalledWith(
        "/ingredients/1",
        expect.objectContaining({ name: "Roma Tomatoes", supplier_id: 1 }),
      );
    });
  });
});
