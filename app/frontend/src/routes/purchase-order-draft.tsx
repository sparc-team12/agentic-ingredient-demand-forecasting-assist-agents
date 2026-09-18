// `/purchase-order-draft` route (ACRI-53 US-018) — protected by
// `RequireAuth` in `App.tsx`. Lets a kitchen manager pick a stockout-risk
// ingredient and generates an editable text draft (supplier, item,
// suggested order quantity, required delivery date) — AC1. Nothing is
// auto-sent anywhere: purely local, editable text (AC2), which persists in
// the UI for as long as the manager stays on this screen (AC3). Mirrors
// `routes/ingredient-detail.tsx`'s picker/fetch pattern.
import { useCallback, useEffect, useState } from "react";

import { IngredientPicker } from "@/components/ingredient-detail/ingredient-picker";
import { PurchaseOrderDraftEditor } from "@/components/purchase-order-draft/purchase-order-draft-editor";
import { ApiError } from "@/lib/api-client";
import { listIngredients, type Ingredient } from "@/lib/ingredients-api";
import { getPurchaseOrderDraft, type PurchaseOrderDraft } from "@/lib/purchase-order-draft-api";

type IngredientListState =
  | { status: "loading" }
  | { status: "error"; message: string }
  | { status: "ready"; ingredients: Ingredient[] };

type DraftState =
  | { status: "idle" }
  | { status: "loading" }
  | { status: "error"; message: string }
  | { status: "ready"; draft: PurchaseOrderDraft };

export default function PurchaseOrderDraftRoute() {
  const [listState, setListState] = useState<IngredientListState>({ status: "loading" });
  const [selectedIngredientId, setSelectedIngredientId] = useState<number | null>(null);
  const [draftState, setDraftState] = useState<DraftState>({ status: "idle" });

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

  const loadDraft = useCallback((ingredientId: number) => {
    setDraftState({ status: "loading" });
    getPurchaseOrderDraft(ingredientId)
      .then((draft) => {
        setDraftState({ status: "ready", draft });
      })
      .catch((err: unknown) => {
        setDraftState({
          status: "error",
          message:
            err instanceof ApiError
              ? err.detail
              : "Failed to load a purchase order draft for this ingredient.",
        });
      });
  }, []);

  function handleSelect(ingredientId: number | null) {
    setSelectedIngredientId(ingredientId);
    if (ingredientId === null) {
      setDraftState({ status: "idle" });
      return;
    }
    loadDraft(ingredientId);
  }

  return (
    <main className="page">
      <div className="page__header">
        <h1>Purchase Order Draft</h1>
        <p className="page__subtitle">
          Pick a stockout-risk ingredient to generate an editable purchase order draft.
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

      {draftState.status === "loading" && <p>Loading draft…</p>}
      {draftState.status === "error" && (
        <p role="alert" className="alert">
          {draftState.message}
        </p>
      )}
      {draftState.status === "ready" && <PurchaseOrderDraftEditor draft={draftState.draft} />}
    </main>
  );
}
