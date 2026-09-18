// `/data-setup/sales-history-import` route (ACRI-63) — protected by
// `RequireAuth` in `App.tsx`. Fetches per-dish sales history on mount,
// owns page-level loading/empty/error state, and composes one
// `DishSalesHistorySection` per dish plus the manual add-record form.
// Reached from the Data Setup hub (ACRI-59).
import { useCallback, useEffect, useState } from "react";

import { DishSalesHistorySection } from "@/components/sales-history/dish-sales-history-section";
import { SalesHistoryRecordForm } from "@/components/sales-history/sales-history-record-form";
import { ApiError } from "@/lib/api-client";
import {
  createSalesHistoryRecord,
  listSalesHistory,
  type DishSalesHistory,
  type SalesHistoryRecordInput,
} from "@/lib/sales-history-api";

type PageState =
  | { status: "loading" }
  | { status: "error"; message: string }
  | { status: "ready"; history: DishSalesHistory[] };

export default function SalesHistoryImportRoute() {
  const [state, setState] = useState<PageState>({ status: "loading" });
  const [isAddingRecord, setIsAddingRecord] = useState(false);

  const load = useCallback(() => {
    setState({ status: "loading" });
    listSalesHistory()
      .then((history) => {
        setState({ status: "ready", history });
      })
      .catch((err: unknown) => {
        setState({
          status: "error",
          message: err instanceof ApiError ? err.detail : "Failed to load this screen.",
        });
      });
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  async function handleCreateRecord(input: SalesHistoryRecordInput) {
    await createSalesHistoryRecord(input);
    setIsAddingRecord(false);
    load();
  }

  return (
    <main className="page">
      <div className="page__header">
        <h1>Sales History Import</h1>
        <p className="page__subtitle">
          Load and review up to 12 weeks (84 days) of daily units-sold per dish. A dish with fewer
          than 84 distinct days of history is flagged.
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
          {state.history.length === 0 && (
            <p className="empty-state">
              No dishes yet. Add dishes in Menu &amp; Recipe Setup before importing sales history.
            </p>
          )}

          {state.history.map((history) => (
            <DishSalesHistorySection key={history.dish_id} history={history} />
          ))}

          {state.history.length > 0 && (
            <div className="card">
              {!isAddingRecord && (
                <button type="button" className="btn" onClick={() => setIsAddingRecord(true)}>
                  Add record
                </button>
              )}
              {isAddingRecord && (
                <SalesHistoryRecordForm
                  dishes={state.history.map((history) => ({
                    id: history.dish_id,
                    name: history.dish_name,
                  }))}
                  onSubmit={handleCreateRecord}
                  onCancel={() => setIsAddingRecord(false)}
                />
              )}
            </div>
          )}
        </>
      )}
    </main>
  );
}
