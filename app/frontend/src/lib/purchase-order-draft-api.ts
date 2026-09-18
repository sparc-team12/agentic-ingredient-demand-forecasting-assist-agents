// Typed API function for the Purchase Order Draft screen (ACRI-53 US-018),
// built on the shared `apiClient` (ACRI-66) — no direct `fetch` call from
// any component. Mirrors `routes/purchase_order_draft.py` /
// `schemas/purchase_order_draft.py::PurchaseOrderDraftOut` one-to-one.
import { apiClient } from "@/lib/api-client";

export interface PurchaseOrderDraft {
  ingredient_id: number;
  item_name: string;
  unit: string;
  supplier_name: string | null;
  supplier_gap: boolean;
  suggested_quantity: number;
  required_delivery_date: string;
}

export function getPurchaseOrderDraft(ingredientId: number): Promise<PurchaseOrderDraft> {
  return apiClient.get<PurchaseOrderDraft>(`/ingredients/${ingredientId}/purchase-order-draft`);
}
