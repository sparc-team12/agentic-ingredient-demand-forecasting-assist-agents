// ACRI-58 US-023: `MateralityThresholdControl` pre-fills the current
// threshold, validates (blank/negative blocked inline), calls `onSave`
// with the parsed numeric value on submit, and surfaces a save error.
import { act, fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { MaterialityThresholdControl } from "@/components/dashboard/materiality-threshold-control";

describe("MaterialityThresholdControl", () => {
  it("pre-fills the input from the current threshold", () => {
    render(<MaterialityThresholdControl materialityThresholdInr={500} onSave={vi.fn()} />);

    expect(screen.getByRole("spinbutton", { name: /materiality threshold/i })).toHaveValue(500);
  });

  it("blocks submit with an inline error when the value is negative", async () => {
    const onSave = vi.fn();
    render(<MaterialityThresholdControl materialityThresholdInr={500} onSave={onSave} />);

    fireEvent.change(screen.getByRole("spinbutton", { name: /materiality threshold/i }), {
      target: { value: "-5" },
    });
    fireEvent.click(screen.getByRole("button", { name: /save/i }));

    expect(await screen.findByRole("alert")).toHaveTextContent(/non-negative/i);
    expect(onSave).not.toHaveBeenCalled();
  });

  it("calls onSave with the parsed numeric value and shows a saved confirmation", async () => {
    const onSave = vi.fn().mockResolvedValue(undefined);
    render(<MaterialityThresholdControl materialityThresholdInr={500} onSave={onSave} />);

    fireEvent.change(screen.getByRole("spinbutton", { name: /materiality threshold/i }), {
      target: { value: "250" },
    });
    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: /save/i }));
    });

    expect(onSave).toHaveBeenCalledWith(250);
    expect(await screen.findByText(/saved/i)).toBeInTheDocument();
  });

  it("shows an error message when onSave rejects", async () => {
    const onSave = vi.fn().mockRejectedValue(new Error("boom"));
    render(<MaterialityThresholdControl materialityThresholdInr={500} onSave={onSave} />);

    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: /save/i }));
    });

    expect(await screen.findByRole("alert")).toHaveTextContent(/something went wrong/i);
  });

  it("renders the suppression note", () => {
    render(<MaterialityThresholdControl materialityThresholdInr={500} onSave={vi.fn()} />);

    expect(screen.getByText(/hidden from the list below/i)).toBeInTheDocument();
  });
});
