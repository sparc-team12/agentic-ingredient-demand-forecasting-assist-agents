// ACRI-60: `DishForm` validation (empty name blocked with an inline
// error) and submit-payload shape, including the pre-filled edit case.
import { act, fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { DishForm } from "@/components/menu-recipe/dish-form";
import type { Dish } from "@/lib/menu-recipe-api";

describe("DishForm", () => {
  it("blocks submit with an inline error when name is empty", async () => {
    const onSubmit = vi.fn();
    render(<DishForm onSubmit={onSubmit} onCancel={vi.fn()} />);

    fireEvent.click(screen.getByRole("button", { name: /save dish/i }));

    expect(await screen.findByRole("alert")).toHaveTextContent(/name is required/i);
    expect(onSubmit).not.toHaveBeenCalled();
  });

  it("submits the trimmed name", async () => {
    const onSubmit = vi.fn().mockResolvedValue(undefined);
    render(<DishForm onSubmit={onSubmit} onCancel={vi.fn()} />);

    fireEvent.change(screen.getByLabelText("Name"), { target: { value: "  Margherita Pizza  " } });
    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: /save dish/i }));
    });

    expect(onSubmit).toHaveBeenCalledWith({ name: "Margherita Pizza" });
  });

  it("pre-fills the name from `initialValue` for an edit", () => {
    const dish: Dish = {
      id: 1,
      name: "Margherita Pizza",
      created_at: "2026-01-01T00:00:00Z",
      recipe_lines: [],
    };
    render(<DishForm initialValue={dish} onSubmit={vi.fn()} onCancel={vi.fn()} />);

    expect(screen.getByLabelText("Name")).toHaveValue("Margherita Pizza");
  });

  it("calls onCancel when the cancel button is clicked", () => {
    const onCancel = vi.fn();
    render(<DishForm onSubmit={vi.fn()} onCancel={onCancel} />);

    fireEvent.click(screen.getByRole("button", { name: /cancel/i }));

    expect(onCancel).toHaveBeenCalled();
  });
});
