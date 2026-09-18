// `/ingredient-detail` route (ACRI-38..44, ACRI-64) — protected by
// `RequireAuth` in `App.tsx`. Fetches the ingredient list, lets the user
// pick one (no navigation-from-dashboard yet — that lands with the
// Dashboard track), then shows its stockout/spoilage risk: both blocks
// stacked when both are flagged (dual-flag stacking rule), either one
// alone when only one is flagged, and a plain "neither" message otherwise.
import { useCallback, useEffect, useState } from "react";

import { IngredientPicker } from "@/components/ingredient-detail/ingredient-picker";
import { SpoilageRiskBlock } from "@/components/ingredient-detail/spoilage-risk-block";
import { StockoutRiskBlock } from "@/components/ingredient-detail/stockout-risk-block";
import { ApiError } from "@/lib/api-client";
import { listIngredients, type Ingredient } from "@/lib/ingredients-api";
import { getIngredientRisk, type IngredientRisk } from "@/lib/risk-api";

type IngredientListState =
  | { status: "loading" }
  | { status: "error"; message: string }
  | { status: "ready"; ingredients: Ingredient[] };

type RiskState =
  | { status: "idle" }
  | { status: "loading" }
  | { status: "error"; message: string }
  | { status: "ready"; risk: IngredientRisk };

export default function IngredientDetailRoute() {
  const [listState, setListState] = useState<IngredientListState>({ status: "loading" });
  const [selectedIngredientId, setSelectedIngredientId] = useState<number | null>(null);
  const [riskState, setRiskState] = useState<RiskState>({ status: "idle" });

  useEffect(() => {
    setListState({ status: "loading" });
    listIngredients()
      .then((ingredients) => {
        setListState({ status: "ready", ingredients });
      })
      .catch((err: unknown) => {
        setListState({
          status: "error",
          message: err instanceof ApiError ? err.detail : "Failed to load this screen.",
        });
      });
  }, []);

  const loadRisk = useCallback((ingredientId: number) => {
    setRiskState({ status: "loading" });
    getIngredientRisk(ingredientId)
      .then((risk) => {
        setRiskState({ status: "ready", risk });
      })
      .catch((err: unknown) => {
        setRiskState({
          status: "error",
          message:
            err instanceof ApiError ? err.detail : "Failed to load risk for this ingredient.",
        });
      });
  }, []);

  function handleSelect(ingredientId: number | null) {
    setSelectedIngredientId(ingredientId);
    if (ingredientId === null) {
      setRiskState({ status: "idle" });
      return;
    }
    loadRisk(ingredientId);
  }

  return (
    <main className="page">
      <div className="page__header">
        <h1>Ingredient Detail</h1>
        <p className="page__subtitle">
          Pick an ingredient to see its current stockout and spoilage risk.
        </p>
      </div>

      {listState.status === "loading" && <p>Loading…</p>}
      {listState.status === "error" && (
        <p role="alert" className="alert">
          {listState.message}
        </p>
      )}
      {listState.status === "ready" && (
        <section className="card">
          {listState.ingredients.length === 0 ? (
            <p className="empty-state">No ingredients exist yet. Add one in Ingredients Setup.</p>
          ) : (
            <IngredientPicker
              ingredients={listState.ingredients}
              selectedIngredientId={selectedIngredientId}
              onSelect={handleSelect}
            />
          )}
        </section>
      )}

      {riskState.status === "loading" && <p>Loading risk…</p>}
      {riskState.status === "error" && (
        <p role="alert" className="alert">
          {riskState.message}
        </p>
      )}
      {riskState.status === "ready" && (
        <>
          {riskState.risk.stockout !== null && (
            <StockoutRiskBlock stockout={riskState.risk.stockout} />
          )}
          {riskState.risk.spoilage !== null && (
            <SpoilageRiskBlock spoilage={riskState.risk.spoilage} />
          )}
          {riskState.risk.stockout === null && riskState.risk.spoilage === null && (
            <section className="card">
              <p>This ingredient has no stockout or spoilage risk right now.</p>
            </section>
          )}
        </>
      )}
    </main>
  );
}
