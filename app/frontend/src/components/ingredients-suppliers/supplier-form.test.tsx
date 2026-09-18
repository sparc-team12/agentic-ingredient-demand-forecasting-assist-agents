// ACRI-61 TS-FE-06: `SupplierForm` validation (empty name / negative lead
// time blocked with an inline error) and submit-payload shape, including
// the full-replace edit case pre-filled from `initialValue`.
import { act, fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { SupplierForm } from "@/components/ingredients-suppliers/supplier-form";
import type { Supplier } from "@/lib/ingredients-api";

describe("SupplierForm", () => {
  it("blocks submit with an inline error when name is empty", async () => {
    const onSubmit = vi.fn();
    render(<SupplierForm onSubmit={onSubmit} onCancel={vi.fn()} />);

    fireEvent.change(screen.getByLabelText("Lead time (days)"), { target: { value: "3" } });
    fireEvent.click(screen.getByRole("button", { name: /save supplier/i }));

    expect(await screen.findByRole("alert")).toHaveTextContent(/name is required/i);
    expect(onSubmit).not.toHaveBeenCalled();
  });

  it("blocks submit with an inline error when lead time is negative", async () => {
    const onSubmit = vi.fn();
    render(<SupplierForm onSubmit={onSubmit} onCancel={vi.fn()} />);

    fireEvent.change(screen.getByLabelText("Name"), { target: { value: "Acme Produce Co" } });
    fireEvent.change(screen.getByLabelText("Lead time (days)"), { target: { value: "-1" } });
    fireEvent.click(screen.getByRole("button", { name: /save supplier/i }));

    expect(await screen.findByRole("alert")).toHaveTextContent(/non-negative/i);
    expect(onSubmit).not.toHaveBeenCalled();
  });

  it("submits the create payload with a null safety margin when left blank", async () => {
    const onSubmit = vi.fn().mockResolvedValue(undefined);
    render(<SupplierForm onSubmit={onSubmit} onCancel={vi.fn()} />);

    fireEvent.change(screen.getByLabelText("Name"), { target: { value: "Acme Produce Co" } });
    fireEvent.change(screen.getByLabelText("Lead time (days)"), { target: { value: "3" } });
    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: /save supplier/i }));
    });

    expect(onSubmit).toHaveBeenCalledWith({
      name: "Acme Produce Co",
      lead_time_days: 3,
      safety_margin_days: null,
    });
  });

  it("submits the full payload including a set safety margin", async () => {
    const onSubmit = vi.fn().mockResolvedValue(undefined);
    render(<SupplierForm onSubmit={onSubmit} onCancel={vi.fn()} />);

    fireEvent.change(screen.getByLabelText("Name"), { target: { value: "Acme Produce Co" } });
    fireEvent.change(screen.getByLabelText("Lead time (days)"), { target: { value: "3" } });
    fireEvent.change(screen.getByLabelText("Safety margin (days)"), { target: { value: "2" } });
    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: /save supplier/i }));
    });

    expect(onSubmit).toHaveBeenCalledWith({
      name: "Acme Produce Co",
      lead_time_days: 3,
      safety_margin_days: 2,
    });
  });

  it("pre-fills every field from `initialValue` for an edit, matching full-replace PUT semantics", () => {
    const supplier: Supplier = {
      id: 1,
      name: "Acme Produce Co",
      lead_time_days: 3,
      safety_margin_days: 2,
    };
    render(<SupplierForm initialValue={supplier} onSubmit={vi.fn()} onCancel={vi.fn()} />);

    expect(screen.getByLabelText("Name")).toHaveValue("Acme Produce Co");
    expect(screen.getByLabelText("Lead time (days)")).toHaveValue(3);
    expect(screen.getByLabelText("Safety margin (days)")).toHaveValue(2);
  });

  it("calls onCancel when the cancel button is clicked", () => {
    const onCancel = vi.fn();
    render(<SupplierForm onSubmit={vi.fn()} onCancel={onCancel} />);

    fireEvent.click(screen.getByRole("button", { name: /cancel/i }));

    expect(onCancel).toHaveBeenCalled();
  });
});
