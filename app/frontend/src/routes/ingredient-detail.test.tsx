// ACRI-38..44/ACRI-64: the Ingredient Detail screen renders the stockout
// block, the spoilage block, both stacked (dual-flag rule), the
// neither-flagged state, and the severity badge's exact text alongside its
// color.
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

import { apiClient, ApiError } from "@/lib/api-client";
import type { Ingredient } from "@/lib/ingredients-api";
import type { IngredientRisk } from "@/lib/risk-api";
import IngredientDetailRoute from "@/routes/ingredient-detail";

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

const INGREDIENT: Ingredient = {
  id: 1,
  name: "Roma Tomatoes",
  unit: "kg",
  unit_cost: 2.5,
  perishable: true,
  shelf_life_days: 5,
  supplier_id: null,
  safety_margin_days_override: null,
  supplier: null,
  has_supplier: false,
  effective_safety_margin_days: null,
  safety_margin_source: null,
  safety_margin_gap: true,
};

const STOCKOUT_ONLY: IngredientRisk = {
  stockout: {
    ingredient_id: 1,
    ingredient_name: "Roma Tomatoes",
    stockout_date: "2026-01-04",
    order_by_date: "2026-01-02",
    suggested_order_quantity: 42,
    severity: "Critical",
    safety_margin_gap: true,
    lead_time_gap: false,
    trace: {},
  },
  spoilage: null,
};

const SPOILAGE_ONLY: IngredientRisk = {
  stockout: null,
  spoilage: {
    ingredient_id: 1,
    ingredient_name: "Roma Tomatoes",
    use_by_date: "2026-01-05",
    waste_cost_inr: 250,
    severity: "Low",
    suppressed: true,
    trace: {},
  },
};

const BOTH_FLAGGED: IngredientRisk = {
  stockout: { ...STOCKOUT_ONLY.stockout!, severity: "High" },
  spoilage: { ...SPOILAGE_ONLY.spoilage!, severity: "Critical", suppressed: false },
};

const NEITHER_FLAGGED: IngredientRisk = { stockout: null, spoilage: null };

function mockApi(risk: IngredientRisk) {
  vi.mocked(apiClient.get).mockImplementation((path: string) => {
    if (path === "/ingredients") return Promise.resolve([INGREDIENT]);
    if (path === "/ingredients/1/risk") return Promise.resolve(risk);
    return Promise.reject(new Error(`unexpected path ${path}`));
  });
}

function renderRoute() {
  return render(
    <MemoryRouter>
      <IngredientDetailRoute />
    </MemoryRouter>,
  );
}

async function renderAndSelectIngredient() {
  renderRoute();
  await screen.findByRole("combobox", { name: /ingredient/i });
  fireEvent.change(screen.getByRole("combobox", { name: /ingredient/i }), {
    target: { value: "1" },
  });
}

describe("IngredientDetailRoute", () => {
  it("renders a loading state before the ingredient list resolves", () => {
    vi.mocked(apiClient.get).mockReturnValue(new Promise(() => {}));

    renderRoute();

    expect(screen.getByText(/loading/i)).toBeInTheDocument();
  });

  it("renders a visible error message if the ingredient list fetch rejects", async () => {
    vi.mocked(apiClient.get).mockRejectedValue(new ApiError(401, "Not authenticated"));

    renderRoute();

    expect(await screen.findByRole("alert")).toHaveTextContent("Not authenticated");
  });

  it("renders the stockout block with its severity badge text when only stockout is flagged", async () => {
    mockApi(STOCKOUT_ONLY);

    await renderAndSelectIngredient();

    expect(await screen.findByRole("heading", { name: /stockout risk/i })).toBeInTheDocument();
    expect(screen.getByText("2026-01-04")).toBeInTheDocument();
    expect(screen.getByText("2026-01-02")).toBeInTheDocument();
    expect(screen.getByText("42")).toBeInTheDocument();
    expect(screen.getByText("Critical")).toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: /spoilage risk/i })).not.toBeInTheDocument();
  });

  it("renders the safety-margin-gap flag when applicable", async () => {
    mockApi(STOCKOUT_ONLY);

    await renderAndSelectIngredient();

    await screen.findByRole("heading", { name: /stockout risk/i });
    expect(screen.getByText(/safety margin not set/i)).toBeInTheDocument();
  });

  it("renders the spoilage block with its severity badge text when only spoilage is flagged", async () => {
    mockApi(SPOILAGE_ONLY);

    await renderAndSelectIngredient();

    expect(await screen.findByRole("heading", { name: /spoilage risk/i })).toBeInTheDocument();
    expect(screen.getByText("2026-01-05")).toBeInTheDocument();
    expect(screen.getByText("₹250")).toBeInTheDocument();
    expect(screen.getByText("Low")).toBeInTheDocument();
    expect(screen.getByText(/suppressed from summary lists/i)).toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: /stockout risk/i })).not.toBeInTheDocument();
  });

  it("renders both blocks stacked when both stockout and spoilage are flagged (dual-flag rule)", async () => {
    mockApi(BOTH_FLAGGED);

    await renderAndSelectIngredient();

    expect(await screen.findByRole("heading", { name: /stockout risk/i })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /spoilage risk/i })).toBeInTheDocument();
    expect(screen.getByText("High")).toBeInTheDocument();
    expect(screen.getByText("Critical")).toBeInTheDocument();
  });

  it("plainly says there is no risk when neither is flagged", async () => {
    mockApi(NEITHER_FLAGGED);

    await renderAndSelectIngredient();

    await waitFor(() => {
      expect(screen.getByText(/no stockout or spoilage risk right now/i)).toBeInTheDocument();
    });
    expect(screen.queryByRole("heading", { name: /stockout risk/i })).not.toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: /spoilage risk/i })).not.toBeInTheDocument();
  });
});
