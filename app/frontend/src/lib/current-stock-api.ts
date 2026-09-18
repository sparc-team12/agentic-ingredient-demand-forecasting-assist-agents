// Typed API functions for the Current Stock Setup screen (ACRI-62), built
// on the shared `apiClient` (ACRI-66) — no direct `fetch` call from any
// component.
//
// `updateCurrentStock` upserts the single snapshot row for that ingredient
// (full-replace `PUT`, keyed by `ingredient_id` not a separate stock id) —
// this is a snapshot, not a log.
import { apiClient } from "@/lib/api-client";

export interface CurrentStock {
  ingredient_id: number;
  ingredient_name: string;
  unit: string;
  perishable: boolean;
  quantity_on_hand: number | null;
  use_by_date: string | null;
  has_stock_recorded: boolean;
  use_by_date_gap: boolean;
}

export interface CurrentStockInput {
  quantity_on_hand: number;
  use_by_date: string | null;
}

export function listCurrentStock(): Promise<CurrentStock[]> {
  return apiClient.get<CurrentStock[]>("/current-stock");
}

export function updateCurrentStock(
  ingredientId: number,
  input: CurrentStockInput,
): Promise<CurrentStock> {
  return apiClient.put<CurrentStock>(`/current-stock/${ingredientId}`, input);
}
