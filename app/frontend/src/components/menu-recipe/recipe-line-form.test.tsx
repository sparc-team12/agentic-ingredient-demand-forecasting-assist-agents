// ACRI-60 AC1/AC2: `RecipeLineForm` validation (empty ingredient/unit,
// non-positive quantity blocked with an inline error) and submit-payload
// shape — the ingredient field always accepts free text, even a name with
// no match in the Ingredient table (AC2).
import { act, fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { RecipeLineForm } from "@/components/menu-recipe/recipe-line-form";
import type { RecipeLine } from "@/lib/menu-recipe-api";

describe("RecipeLineForm", () => {
  it("blocks submit with an inline error when ingredient is empty", async () => {
    const onSubmit = vi.fn();
    render(<RecipeLineForm onSubmit={onSubmit} onCancel={vi.fn()} />);

    fireEvent.change(screen.getByLabelText("Quantity per serving"), { target: { value: "0.2" } });
    fireEvent.change(screen.getByLabelText("Unit"), { target: { value: "kg" } });
    fireEvent.click(screen.getByRole("button", { name: /save recipe line/i }));

    expect(await screen.findByRole("alert")).toHaveTextContent(/ingredient and unit are required/i);
    expect(onSubmit).not.toHaveBeenCalled();
  });

  it("blocks submit with an inline error when quantity is not positive", async () => {
    const onSubmit = vi.fn();
    render(<RecipeLineForm onSubmit={onSubmit} onCancel={vi.fn()} />);

    fireEvent.change(screen.getByLabelText("Ingredient"), { target: { value: "Mozzarella" } });
    fireEvent.change(screen.getByLabelText("Quantity per serving"), { target: { value: "0" } });
    fireEvent.change(screen.getByLabelText("Unit"), { target: { value: "kg" } });
    fireEvent.click(screen.getByRole("button", { name: /save recipe line/i }));

    expect(await screen.findByRole("alert")).toHaveTextContent(/positive number/i);
    expect(onSubmit).not.toHaveBeenCalled();
  });

  it("submits an unmatched ingredient name without rejecting it (AC2)", async () => {
    const onSubmit = vi.fn().mockResolvedValue(undefined);
    render(<RecipeLineForm onSubmit={onSubmit} onCancel={vi.fn()} />);

    fireEvent.change(screen.getByLabelText("Ingredient"), { target: { value: "Unicorn Meat" } });
    fireEvent.change(screen.getByLabelText("Quantity per serving"), { target: { value: "0.5" } });
    fireEvent.change(screen.getByLabelText("Unit"), { target: { value: "kg" } });
    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: /save recipe line/i }));
    });

    expect(onSubmit).toHaveBeenCalledWith({
      ingredient_name: "Unicorn Meat",
      quantity_per_serving: 0.5,
      unit: "kg",
    });
  });

  it("pre-fills every field from `initialValue` for an edit", () => {
    const line: RecipeLine = {
      id: 1,
      dish_id: 1,
      ingredient_name: "Mozzarella",
      ingredient_id: 5,
      quantity_per_serving: 0.2,
      unit: "kg",
      ingredient_flagged: false,
    };
    render(<RecipeLineForm initialValue={line} onSubmit={vi.fn()} onCancel={vi.fn()} />);

    expect(screen.getByLabelText("Ingredient")).toHaveValue("Mozzarella");
    expect(screen.getByLabelText("Quantity per serving")).toHaveValue(0.2);
    expect(screen.getByLabelText("Unit")).toHaveValue("kg");
  });

  it("calls onCancel when the cancel button is clicked", () => {
    const onCancel = vi.fn();
    render(<RecipeLineForm onSubmit={vi.fn()} onCancel={onCancel} />);

    fireEvent.click(screen.getByRole("button", { name: /cancel/i }));

    expect(onCancel).toHaveBeenCalled();
  });
});
