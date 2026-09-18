// Typed API functions for the Risk Dashboard screen (ACRI-54 US-019,
// ACRI-55 US-020, ACRI-56 US-021, ACRI-57 US-022, ACRI-58 US-023), built on
// the shared `apiClient` (ACRI-66) — no direct `fetch` call from any
// component. Mirrors `services/dashboard_service.py` /
// `schemas/dashboard.py` one-to-one.
import { apiClient } from "@/lib/api-client";
import type { RiskSeverity } from "@/lib/risk-api";

export type DashboardRiskType = "stockout" | "spoilage";

export interface DashboardRiskRow {
  ingredient_id: number;
  ingredient_name: string;
  risk_type: DashboardRiskType;
  severity: RiskSeverity;
  order_by_date: string | null;
  waste_cost_inr: number | null;
  suppressed: boolean;
}

export interface DashboardRiskSummary {
  total_waste_exposure_inr: number;
  rows: DashboardRiskRow[];
  materiality_threshold_inr: number;
}

export function getRiskSummary(): Promise<DashboardRiskSummary> {
  return apiClient.get<DashboardRiskSummary>("/dashboard/risk-summary");
}
