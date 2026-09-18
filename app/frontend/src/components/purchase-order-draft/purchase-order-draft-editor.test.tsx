// ACRI-53 US-018: the draft textarea is pre-filled with the formatted
// draft text (AC1), is fully editable with no save/send button (AC2), and
// keeps the manager's edits when the same draft is still shown (AC3).
import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import {
  formatPurchaseOrderDraftText,
  PurchaseOrderDraftEditor,
} from "@/components/purchase-order-draft/purchase-order-draft-editor";
import type { PurchaseOrderDraft } from "@/lib/purchase-order-draft-api";

const DRAFT: PurchaseOrderDraft = {
  ingredient_id: 1,
  item_name: "Roma Tomatoes",
  unit: "kg",
  supplier_name: "Acme Produce Co",
  supplier_gap: false,
  suggested_quantity: 42,
  required_delivery_date: "2026-01-02",
};

describe("PurchaseOrderDraftEditor", () => {
  it("pre-fills the textarea with the formatted draft (supplier, item, quantity, delivery date) — AC1", () => {
    render(<PurchaseOrderDraftEditor draft={DRAFT} />);

    const textarea = screen.getByRole("textbox", { name: /draft/i }) as HTMLTextAreaElement;
    expect(textarea.value).toContain("To: Acme Produce Co");
    expect(textarea.value).toContain("Item: Roma Tomatoes");
    expect(textarea.value).toContain("Quantity: 42 kg");
    expect(textarea.value).toContain("Required by: 2026-01-02");
  });

  it("lets the manager edit the draft text, with no save/send button present — AC2", () => {
    render(<PurchaseOrderDraftEditor draft={DRAFT} />);

    const textarea = screen.getByRole("textbox", { name: /draft/i }) as HTMLTextAreaElement;
    fireEvent.change(textarea, { target: { value: "Edited draft text" } });

    expect(textarea.value).toBe("Edited draft text");
    expect(screen.queryByRole("button", { name: /send/i })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /save/i })).not.toBeInTheDocument();
  });

  it("keeps the manager's edits across a re-render of the same draft object — AC3", () => {
    const { rerender } = render(<PurchaseOrderDraftEditor draft={DRAFT} />);

    const textarea = screen.getByRole("textbox", { name: /draft/i }) as HTMLTextAreaElement;
    fireEvent.change(textarea, { target: { value: "Still editing this" } });

    rerender(<PurchaseOrderDraftEditor draft={DRAFT} />);

    expect((screen.getByRole("textbox", { name: /draft/i }) as HTMLTextAreaElement).value).toBe(
      "Still editing this"
    );
  });

  it("renders the supplier-gap flag when the ingredient has no supplier on file", () => {
    render(<PurchaseOrderDraftEditor draft={{ ...DRAFT, supplier_name: null, supplier_gap: true }} />);

    expect(screen.getByRole("alert")).toHaveTextContent(/no supplier on file/i);
  });
});

describe("formatPurchaseOrderDraftText", () => {
  it("falls back to a visible placeholder when supplier_name is null", () => {
    const text = formatPurchaseOrderDraftText({ ...DRAFT, supplier_name: null });
    expect(text).toContain("To: No supplier on file");
  });
});
