// ACRI-53 US-018: the Purchase Order Draft screen renders an ingredient
// picker, shows the generated draft text after a stockout-flagged
// ingredient is selected, and surfaces a clear message for a non-flagged
// ingredient (404). Mirrors `ingredient-detail.test.tsx`'s mocking pattern.
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { apiClient, ApiError } from "@/lib/api-client";
import type { Ingredient } from "@/lib/ingredients-api";
import type { PurchaseOrderDraft } from "@/lib/purchase-order-draft-api";
import PurchaseOrderDraftRoute from "@/routes/purchase-order-draft";

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
  supplier_id: 7,
  safety_margin_days_override: null,
  supplier: { id: 7, name: "Acme Produce Co", lead_time_days: 5 },
  has_supplier: true,
  effective_safety_margin_days: 2,
  safety_margin_source: "supplier",
  safety_margin_gap: false,
};

const DRAFT: PurchaseOrderDraft = {
  ingredient_id: 1,
  item_name: "Roma Tomatoes",
  unit: "kg",
  supplier_name: "Acme Produce Co",
  supplier_gap: false,
  suggested_quantity: 42,
  required_delivery_date: "2026-01-02",
};

async function renderAndSelectIngredient() {
  render(<PurchaseOrderDraftRoute />);
  await screen.findByRole("combobox", { name: /ingredient/i });
  fireEvent.change(screen.getByRole("combobox", { name: /ingredient/i }), {
    target: { value: "1" },
  });
}

describe("PurchaseOrderDraftRoute", () => {
  it("renders the ingredient picker once the ingredient list resolves", async () => {
    vi.mocked(apiClient.get).mockImplementation((path: string) => {
      if (path === "/ingredients") return Promise.resolve([INGREDIENT]);
      return Promise.reject(new Error(`unexpected path ${path}`));
    });

    render(<PurchaseOrderDraftRoute />);

    expect(await screen.findByRole("combobox", { name: /ingredient/i })).toBeInTheDocument();
    expect(screen.getByText("Roma Tomatoes")).toBeInTheDocument();
  });

  it("shows the generated draft text after a stockout-flagged ingredient is selected", async () => {
    vi.mocked(apiClient.get).mockImplementation((path: string) => {
      if (path === "/ingredients") return Promise.resolve([INGREDIENT]);
      if (path === "/ingredients/1/purchase-order-draft") return Promise.resolve(DRAFT);
      return Promise.reject(new Error(`unexpected path ${path}`));
    });

    await renderAndSelectIngredient();

    const textarea = (await screen.findByRole("textbox", { name: /draft/i })) as HTMLTextAreaElement;
    expect(textarea.value).toContain("To: Acme Produce Co");
    expect(textarea.value).toContain("Item: Roma Tomatoes");
    expect(textarea.value).toContain("Quantity: 42 kg");
    expect(textarea.value).toContain("Required by: 2026-01-02");
  });

  it("the draft textarea is editable", async () => {
    vi.mocked(apiClient.get).mockImplementation((path: string) => {
      if (path === "/ingredients") return Promise.resolve([INGREDIENT]);
      if (path === "/ingredients/1/purchase-order-draft") return Promise.resolve(DRAFT);
      return Promise.reject(new Error(`unexpected path ${path}`));
    });

    await renderAndSelectIngredient();

    const textarea = (await screen.findByRole("textbox", { name: /draft/i })) as HTMLTextAreaElement;
    fireEvent.change(textarea, { target: { value: "My edited draft" } });

    expect(textarea.value).toBe("My edited draft");
  });

  it("shows a clear message when the ingredient is not stockout-flagged (404)", async () => {
    vi.mocked(apiClient.get).mockImplementation((path: string) => {
      if (path === "/ingredients") return Promise.resolve([INGREDIENT]);
      if (path === "/ingredients/1/purchase-order-draft") {
        return Promise.reject(
          new ApiError(404, "This ingredient is not currently flagged for stockout risk")
        );
      }
      return Promise.reject(new Error(`unexpected path ${path}`));
    });

    await renderAndSelectIngredient();

    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveTextContent(/not currently flagged/i);
    });
    expect(screen.queryByRole("textbox", { name: /draft/i })).not.toBeInTheDocument();
  });
});
