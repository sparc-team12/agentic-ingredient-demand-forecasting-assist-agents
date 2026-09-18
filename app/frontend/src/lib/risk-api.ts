// Typed API functions for the Ingredient Detail screen's Stockout/Spoilage
// Risk HTTP contract (ACRI-38..44, ACRI-64), built on the shared
// `apiClient` (ACRI-66) — no direct `fetch` call from any component.
//
// `RiskConfig`/`getRiskConfig`/`updateRiskConfig` (ACRI-44 US-009) live here
// rather than in a separate file because they mirror the backend's
// `routes/risk.py::risk_config_router`, which shares this same module —
// the materiality-threshold *UI control* itself is a Risk Dashboard
// concern (ACRI-58 US-023, deferred from the Stockout/Spoilage track) and
// lives in `components/dashboard/materiality-threshold-control.tsx`.
import { apiClient } from "@/lib/api-client";

export type RiskSeverity = "Critical" | "High" | "Low";

export interface StockoutRisk {
  ingredient_id: number;
  ingredient_name: string;
  stockout_date: string;
  order_by_date: string;
  suggested_order_quantity: number;
  severity: RiskSeverity;
  safety_margin_gap: boolean;
  lead_time_gap: boolean;
  trace: Record<string, unknown>;
}

export interface SpoilageRisk {
  ingredient_id: number;
  ingredient_name: string;
  use_by_date: string;
  waste_cost_inr: number;
  severity: RiskSeverity;
  suppressed: boolean;
  trace: Record<string, unknown>;
}

export interface IngredientRisk {
  stockout: StockoutRisk | null;
  spoilage: SpoilageRisk | null;
}

export function getIngredientRisk(ingredientId: number): Promise<IngredientRisk> {
  return apiClient.get<IngredientRisk>(`/ingredients/${ingredientId}/risk`);
}

export interface RiskConfig {
  materiality_threshold_inr: number;
}

export function getRiskConfig(): Promise<RiskConfig> {
  return apiClient.get<RiskConfig>("/risk-config");
}

export function updateRiskConfig(materialityThresholdInr: number): Promise<RiskConfig> {
  return apiClient.put<RiskConfig>("/risk-config", {
    materiality_threshold_inr: materialityThresholdInr,
  });
}
