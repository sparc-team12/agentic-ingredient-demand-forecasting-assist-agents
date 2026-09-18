// Editable purchase-order draft text block (ACRI-53 US-018 AC1/AC2/AC3).
// Pre-fills a formatted draft (supplier, item, suggested quantity, required
// delivery date) into a plain, fully editable `<textarea>` — no save/send
// button: nothing is auto-sent anywhere (AC2), and the edited text persists
// in local component state for as long as the manager stays on this screen
// (AC3; not persisted server-side, matching the story's scope).
import { useEffect, useState } from "react";

import { GapFlag } from "@/components/ingredients-suppliers/gap-flag";
import type { PurchaseOrderDraft } from "@/lib/purchase-order-draft-api";

interface PurchaseOrderDraftEditorProps {
  draft: PurchaseOrderDraft;
}

export function formatPurchaseOrderDraftText(draft: PurchaseOrderDraft): string {
  const supplierLine = draft.supplier_name ?? "No supplier on file";
  return (
    `To: ${supplierLine}\n` +
    `Item: ${draft.item_name}\n` +
    `Quantity: ${draft.suggested_quantity} ${draft.unit}\n` +
    `Required by: ${draft.required_delivery_date}`
  );
}

export function PurchaseOrderDraftEditor({ draft }: PurchaseOrderDraftEditorProps) {
  // Re-seeds only when a *new* draft object arrives (a fresh fetch for a
  // newly selected ingredient) — editing the text in place never changes
  // the `draft` reference, so in-progress edits are left untouched while
  // the manager stays on this screen (AC3).
  const [text, setText] = useState(() => formatPurchaseOrderDraftText(draft));

  useEffect(() => {
    setText(formatPurchaseOrderDraftText(draft));
  }, [draft]);

  return (
    <section className="card" aria-labelledby="purchase-order-draft-heading">
      <div className="section-heading-row">
        <h2 id="purchase-order-draft-heading">Purchase order draft</h2>
      </div>
      <GapFlag
        when={draft.supplier_gap}
        text="No supplier on file for this ingredient — the draft leaves the recipient blank"
      />
      <div className="field">
        <label htmlFor="purchase-order-draft-text">Draft (edit as needed)</label>
        <textarea
          id="purchase-order-draft-text"
          value={text}
          onChange={(event) => setText(event.target.value)}
          rows={6}
        />
      </div>
      <p className="hint-text">
        This draft is local to this screen only — nothing is sent automatically. Copy the text into
        your own email or messaging tool when you are ready to send it.
      </p>
    </section>
  );
}
