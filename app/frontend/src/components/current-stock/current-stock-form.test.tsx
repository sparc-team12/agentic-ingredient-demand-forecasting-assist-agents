// ACRI-62 AC2: `CurrentStockForm` validation (blank/negative quantity
// blocked with an inline error) and submit-payload shape (upsert), pre-
// filled from the passed `stock` row.
import { act, fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { CurrentStockForm } from "@/components/current-stock/current-stock-form";
import type { CurrentStock } from "@/lib/current-stock-api";

const NOT_RECORDED_STOCK: CurrentStock = {
  ingredient_id: 1,
  ingredient_name: "Roma Tomatoes",
  unit: "kg",
  perishable: false,
  quantity_on_hand: null,
  use_by_date: null,
  has_stock_recorded: false,
  use_by_date_gap: false,
};

const RECORDED_STOCK: CurrentStock = {
  ...NOT_RECORDED_STOCK,
  quantity_on_hand: 12.5,
  use_by_date: "2026-01-01",
  has_stock_recorded: true,
};

describe("CurrentStockForm", () => {
  it("blocks submit with an inline error when quantity is blank", async () => {
    const onSubmit = vi.fn();
    render(<CurrentStockForm stock={NOT_RECORDED_STOCK} onSubmit={onSubmit} onCancel={vi.fn()} />);

    fireEvent.click(screen.getByRole("button", { name: /save stock/i }));

    expect(await screen.findByRole("alert")).toHaveTextContent(/non-negative/i);
    expect(onSubmit).not.toHaveBeenCalled();
  });

  it("submits quantity and a null use-by date when left blank", async () => {
    const onSubmit = vi.fn().mockResolvedValue(undefined);
    render(<CurrentStockForm stock={NOT_RECORDED_STOCK} onSubmit={onSubmit} onCancel={vi.fn()} />);

    fireEvent.change(screen.getByLabelText(/quantity on hand/i), { target: { value: "8" } });
    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: /save stock/i }));
    });

    expect(onSubmit).toHaveBeenCalledWith({ quantity_on_hand: 8, use_by_date: null });
  });

  it("pre-fills quantity and use-by date from an already-recorded snapshot", () => {
    render(<CurrentStockForm stock={RECORDED_STOCK} onSubmit={vi.fn()} onCancel={vi.fn()} />);

    expect(screen.getByLabelText(/quantity on hand/i)).toHaveValue(12.5);
    expect(screen.getByLabelText(/use-by date/i)).toHaveValue("2026-01-01");
  });

  it("calls onCancel when the cancel button is clicked", () => {
    const onCancel = vi.fn();
    render(<CurrentStockForm stock={NOT_RECORDED_STOCK} onSubmit={vi.fn()} onCancel={onCancel} />);

    fireEvent.click(screen.getByRole("button", { name: /cancel/i }));

    expect(onCancel).toHaveBeenCalled();
  });
});
