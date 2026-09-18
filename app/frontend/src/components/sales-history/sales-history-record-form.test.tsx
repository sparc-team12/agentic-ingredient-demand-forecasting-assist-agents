// ACRI-63 AC1: `SalesHistoryRecordForm` validation (missing date/negative
// units blocked with an inline error), the dish `<select>` populated only
// from the passed dish list, and submit-payload shape.
import { act, fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { SalesHistoryRecordForm } from "@/components/sales-history/sales-history-record-form";

const DISHES = [
  { id: 1, name: "Margherita Pizza" },
  { id: 2, name: "Caesar Salad" },
];

describe("SalesHistoryRecordForm", () => {
  it("blocks submit with an inline error when date is missing", async () => {
    const onSubmit = vi.fn();
    render(<SalesHistoryRecordForm dishes={DISHES} onSubmit={onSubmit} onCancel={vi.fn()} />);

    fireEvent.change(screen.getByLabelText("Units sold"), { target: { value: "10" } });
    fireEvent.click(screen.getByRole("button", { name: /save record/i }));

    expect(await screen.findByRole("alert")).toHaveTextContent(/date is required/i);
    expect(onSubmit).not.toHaveBeenCalled();
  });

  it("blocks submit with an inline error when units sold is negative", async () => {
    const onSubmit = vi.fn();
    render(<SalesHistoryRecordForm dishes={DISHES} onSubmit={onSubmit} onCancel={vi.fn()} />);

    fireEvent.change(screen.getByLabelText("Date"), { target: { value: "2026-01-01" } });
    fireEvent.change(screen.getByLabelText("Units sold"), { target: { value: "-1" } });
    fireEvent.click(screen.getByRole("button", { name: /save record/i }));

    expect(await screen.findByRole("alert")).toHaveTextContent(/non-negative/i);
    expect(onSubmit).not.toHaveBeenCalled();
  });

  it("populates the dish select only from the passed dish list", () => {
    render(<SalesHistoryRecordForm dishes={DISHES} onSubmit={vi.fn()} onCancel={vi.fn()} />);

    expect(screen.getByRole("option", { name: "Margherita Pizza" })).toBeInTheDocument();
    expect(screen.getByRole("option", { name: "Caesar Salad" })).toBeInTheDocument();
  });

  it("submits the create payload with the selected dish, date, and units sold", async () => {
    const onSubmit = vi.fn().mockResolvedValue(undefined);
    render(<SalesHistoryRecordForm dishes={DISHES} onSubmit={onSubmit} onCancel={vi.fn()} />);

    fireEvent.change(screen.getByLabelText("Dish"), { target: { value: "2" } });
    fireEvent.change(screen.getByLabelText("Date"), { target: { value: "2026-01-01" } });
    fireEvent.change(screen.getByLabelText("Units sold"), { target: { value: "10" } });
    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: /save record/i }));
    });

    expect(onSubmit).toHaveBeenCalledWith({ dish_id: 2, sale_date: "2026-01-01", units_sold: 10 });
  });

  it("calls onCancel when the cancel button is clicked", () => {
    const onCancel = vi.fn();
    render(<SalesHistoryRecordForm dishes={DISHES} onSubmit={vi.fn()} onCancel={onCancel} />);

    fireEvent.click(screen.getByRole("button", { name: /cancel/i }));

    expect(onCancel).toHaveBeenCalled();
  });
});
