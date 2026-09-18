// `/data-setup` route (ACRI-59) — protected by `RequireAuth` in
// `App.tsx`. Fetches the 4-category loaded/not-loaded status on mount and
// renders one `DataSetupCategoryCard` per category, each linking to its
// own screen. The top-nav "Data Setup" link points here (see
// `components/common/app-shell.tsx`); the 3 new screens (ACRI-60/62/63)
// are reached from this hub, not from the top nav.
import { useCallback, useEffect, useState } from "react";

import { DataSetupCategoryCard } from "@/components/data-setup/data-setup-category-card";
import { ApiError } from "@/lib/api-client";
import { getDataSetupStatus, type DataSetupStatus } from "@/lib/data-setup-api";

type PageState =
  | { status: "loading" }
  | { status: "error"; message: string }
  | { status: "ready"; data: DataSetupStatus };

export default function DataSetupHubRoute() {
  const [state, setState] = useState<PageState>({ status: "loading" });

  const load = useCallback(() => {
    setState({ status: "loading" });
    getDataSetupStatus()
      .then((data) => {
        setState({ status: "ready", data });
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

  return (
    <main className="page">
      <div className="page__header">
        <h1>Data Setup</h1>
        <p className="page__subtitle">
          Load and review the 4 categories of data used by stockout and spoilage risk. A category
          with no data loaded yet is flagged.
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
          {state.data.all_loaded && (
            <p role="status" className="hint-text">
              All 4 data categories are loaded.
            </p>
          )}
          {state.data.categories.map((category) => (
            <DataSetupCategoryCard key={category.id} category={category} />
          ))}
        </>
      )}
    </main>
  );
}
