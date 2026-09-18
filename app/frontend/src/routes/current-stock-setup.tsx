// `/data-setup/current-stock-setup` route (ACRI-62) — protected by
// `RequireAuth` in `App.tsx`. Fetches the one-row-per-ingredient snapshot
// list on mount, owns page-level loading/empty/error state. This is a
// snapshot, not a live feed — the list only refreshes on load/edit.
// Reached from the Data Setup hub (ACRI-59).
import { useCallback, useEffect, useState } from "react";

import { CurrentStockTable } from "@/components/current-stock/current-stock-table";
import { ApiError } from "@/lib/api-client";
import {
  listCurrentStock,
  updateCurrentStock,
  type CurrentStock,
  type CurrentStockInput,
} from "@/lib/current-stock-api";

type PageState =
  | { status: "loading" }
  | { status: "error"; message: string }
  | { status: "ready"; stocks: CurrentStock[] };

export default function CurrentStockSetupRoute() {
  const [state, setState] = useState<PageState>({ status: "loading" });

  const load = useCallback(() => {
    setState({ status: "loading" });
    listCurrentStock()
      .then((stocks) => {
        setState({ status: "ready", stocks });
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

  async function handleUpdate(ingredientId: number, input: CurrentStockInput) {
    await updateCurrentStock(ingredientId, input);
    load();
  }

  return (
    <main className="page">
      <div className="page__header">
        <h1>Current Stock Setup</h1>
        <p className="page__subtitle">
          Record a point-in-time quantity-on-hand and use-by date per ingredient. This is a
          snapshot, not a live feed — a perishable ingredient with no use-by date is flagged.
        </p>
      </div>

      {state.status === "loading" && <p>Loading…</p>}
      {state.status === "error" && (
        <p role="alert" className="alert">
          {state.message}
        </p>
      )}
      {state.status === "ready" && (
        <section className="card" aria-labelledby="current-stock-heading">
          <div className="section-heading-row">
            <h2 id="current-stock-heading">Ingredients</h2>
          </div>
          <CurrentStockTable stocks={state.stocks} onUpdate={handleUpdate} />
        </section>
      )}
    </main>
  );
}
