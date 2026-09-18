// `/risk-dashboard` route (ACRI-54 US-019, ACRI-55 US-020, ACRI-56 US-021,
// ACRI-57 US-022, ACRI-58 US-023) — protected by `RequireAuth` in
// `App.tsx`. The main landing screen: the aggregate total-waste-exposure
// figure, the materiality-threshold control, and the single
// severity-ordered list of every at-risk ingredient (stockout + spoilage
// interleaved). Replaces the former `StubScreen` stub.
import { useCallback, useEffect, useState } from "react";

import { AggregateExposure } from "@/components/dashboard/aggregate-exposure";
import { MaterialityThresholdControl } from "@/components/dashboard/materiality-threshold-control";
import { RiskTable } from "@/components/dashboard/risk-table";
import { ApiError } from "@/lib/api-client";
import { getRiskSummary, type DashboardRiskSummary } from "@/lib/dashboard-api";
import { updateRiskConfig } from "@/lib/risk-api";

type SummaryState =
  | { status: "loading" }
  | { status: "error"; message: string }
  | { status: "ready"; summary: DashboardRiskSummary };

export default function RiskDashboardRoute() {
  const [state, setState] = useState<SummaryState>({ status: "loading" });

  const loadSummary = useCallback(() => {
    setState({ status: "loading" });
    getRiskSummary()
      .then((summary) => {
        setState({ status: "ready", summary });
      })
      .catch((err: unknown) => {
        setState({
          status: "error",
          message: err instanceof ApiError ? err.detail : "Failed to load the risk dashboard.",
        });
      });
  }, []);

  useEffect(() => {
    loadSummary();
  }, [loadSummary]);

  async function handleSaveThreshold(materialityThresholdInr: number) {
    await updateRiskConfig(materialityThresholdInr);
    loadSummary();
  }

  return (
    <main className="page">
      <div className="page__header">
        <h1>Risk Dashboard</h1>
        <p className="page__subtitle">
          Every at-risk ingredient — stockout and spoilage combined — ranked by severity.
        </p>
      </div>

      {state.status === "loading" && <p>Loading…</p>}
      {state.status === "error" && (
        <p role="alert" className="alert">
          {state.message}
        </p>
      )}
      {state.status === "ready" && (
        <>
          <AggregateExposure totalWasteExposureInr={state.summary.total_waste_exposure_inr} />
          <MaterialityThresholdControl
            materialityThresholdInr={state.summary.materiality_threshold_inr}
            onSave={handleSaveThreshold}
          />
          <section className="card">
            <h2>At-risk ingredients</h2>
            <RiskTable rows={state.summary.rows} />
          </section>
        </>
      )}
    </main>
  );
}
