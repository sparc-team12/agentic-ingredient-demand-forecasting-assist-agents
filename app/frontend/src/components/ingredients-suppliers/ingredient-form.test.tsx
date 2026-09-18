// ACRI-61 TS-FE-05: `IngredientForm` validation (perishable requires shelf
// life; supplier `<select>` only offers existing suppliers, never a
// free-text value) and submit-payload shape.
import { act, fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { IngredientForm } from "@/components/ingredients-suppliers/ingredient-form";
import type { Ingredient, Supplier } from "@/lib/ingredients-api";

const SUPPLIERS: Supplier[] = [
  { id: 1, name: "Acme Produce Co", lead_time_days: 3, safety_margin_days: 2 },
  { id: 2, name: "Metro Wholesale Foods", lead_time_days: 5, safety_margin_days: null },
];

describe("IngredientForm", () => {
  it("blocks submit when perishable is checked but shelf life is left blank", async () => {
    const onSubmit = vi.fn();
    render(<IngredientForm suppliers={SUPPLIERS} onSubmit={onSubmit} onCancel={vi.fn()} />);

    fireEvent.change(screen.getByLabelText("Name"), { target: { value: "Roma Tomatoes" } });
    fireEvent.change(screen.getByLabelText("Unit"), { target: { value: "kg" } });
    fireEvent.change(screen.getByLabelText("Unit cost"), { target: { value: "2.5" } });
    fireEvent.click(screen.getByLabelText("Perishable"));
    fireEvent.click(screen.getByRole("button", { name: /save ingredient/i }));

    expect(await screen.findByRole("alert")).toHaveTextContent(/shelf life .* required/i);
    expect(onSubmit).not.toHaveBeenCalled();
  });

  it("disables the shelf-life field until perishable is checked", () => {
    render(<IngredientForm suppliers={SUPPLIERS} onSubmit={vi.fn()} onCancel={vi.fn()} />);

    expect(screen.getByLabelText("Shelf life (days)")).toBeDisabled();

    fireEvent.click(screen.getByLabelText("Perishable"));

    expect(screen.getByLabelText("Shelf life (days)")).toBeEnabled();
  });

  it("the supplier picker only lists suppliers passed in, never a free-text value", () => {
    render(<IngredientForm suppliers={SUPPLIERS} onSubmit={vi.fn()} onCancel={vi.fn()} />);

    const select = screen.getByLabelText("Supplier") as HTMLSelectElement;
    const optionLabels = Array.from(select.options).map((option) => option.textContent);

    expect(optionLabels).toEqual([
      "No supplier mapped",
      "Acme Produce Co",
      "Metro Wholesale Foods",
    ]);
    expect(select.tagName).toBe("SELECT");
  });

  it("submits a create payload with supplier_id null when no supplier is picked", async () => {
    const onSubmit = vi.fn().mockResolvedValue(undefined);
    render(<IngredientForm suppliers={SUPPLIERS} onSubmit={onSubmit} onCancel={vi.fn()} />);

    fireEvent.change(screen.getByLabelText("Name"), { target: { value: "Fresh Basil" } });
    fireEvent.change(screen.getByLabelText("Unit"), { target: { value: "bunch" } });
    fireEvent.change(screen.getByLabelText("Unit cost"), { target: { value: "0.9" } });
    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: /save ingredient/i }));
    });

    expect(onSubmit).toHaveBeenCalledWith({
      name: "Fresh Basil",
      unit: "bunch",
      unit_cost: 0.9,
      perishable: false,
      shelf_life_days: null,
      supplier_id: null,
      safety_margin_days_override: null,
    });
  });

  it("submits the full payload including the picked supplier and a safety margin override", async () => {
    const onSubmit = vi.fn().mockResolvedValue(undefined);
    render(<IngredientForm suppliers={SUPPLIERS} onSubmit={onSubmit} onCancel={vi.fn()} />);

    fireEvent.change(screen.getByLabelText("Name"), { target: { value: "Roma Tomatoes" } });
    fireEvent.change(screen.getByLabelText("Unit"), { target: { value: "kg" } });
    fireEvent.change(screen.getByLabelText("Unit cost"), { target: { value: "2.5" } });
    fireEvent.click(screen.getByLabelText("Perishable"));
    fireEvent.change(screen.getByLabelText("Shelf life (days)"), { target: { value: "7" } });
    fireEvent.change(screen.getByLabelText("Supplier"), { target: { value: "1" } });
    fireEvent.change(screen.getByLabelText("Safety margin override (days)"), {
      target: { value: "4" },
    });
    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: /save ingredient/i }));
    });

    expect(onSubmit).toHaveBeenCalledWith({
      name: "Roma Tomatoes",
      unit: "kg",
      unit_cost: 2.5,
      perishable: true,
      shelf_life_days: 7,
      supplier_id: 1,
      safety_margin_days_override: 4,
    });
  });

  it("pre-fills every field from `initialValue` for an edit, matching full-replace PUT semantics", () => {
    const ingredient: Ingredient = {
      id: 10,
      name: "Roma Tomatoes",
      unit: "kg",
      unit_cost: 2.5,
      perishable: true,
      shelf_life_days: 7,
      supplier_id: 1,
      safety_margin_days_override: 4,
      supplier: { id: 1, name: "Acme Produce Co", lead_time_days: 3 },
      has_supplier: true,
      effective_safety_margin_days: 4,
      safety_margin_source: "ingredient",
      safety_margin_gap: false,
    };
    render(
      <IngredientForm
        suppliers={SUPPLIERS}
        initialValue={ingredient}
        onSubmit={vi.fn()}
        onCancel={vi.fn()}
      />,
    );

    expect(screen.getByLabelText("Name")).toHaveValue("Roma Tomatoes");
    expect(screen.getByLabelText("Perishable")).toBeChecked();
    expect(screen.getByLabelText("Shelf life (days)")).toHaveValue(7);
    expect(screen.getByLabelText("Supplier")).toHaveValue("1");
    expect(screen.getByLabelText("Safety margin override (days)")).toHaveValue(4);
  });
});
