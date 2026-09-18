// Typed API functions for the Sales History Import screen (ACRI-63), built
// on the shared `apiClient` (ACRI-66) — no direct `fetch` call from any
// component. Manual add-record only — no update/delete, matching the
// backend contract.
import { apiClient } from "@/lib/api-client";

export interface SalesHistoryRecord {
  id: number;
  dish_id: number;
  sale_date: string;
  units_sold: number;
}

export interface SalesHistoryRecordInput {
  dish_id: number;
  sale_date: string;
  units_sold: number;
}

export interface DishSalesHistory {
  dish_id: number;
  dish_name: string;
  distinct_days_of_history: number;
  has_full_history: boolean;
  records: SalesHistoryRecord[];
}

export const TARGET_DAYS_OF_HISTORY = 84;

export function listSalesHistory(): Promise<DishSalesHistory[]> {
  return apiClient.get<DishSalesHistory[]>("/sales-history");
}

export function createSalesHistoryRecord(
  input: SalesHistoryRecordInput,
): Promise<SalesHistoryRecord> {
  return apiClient.post<SalesHistoryRecord>("/sales-history", input);
}
