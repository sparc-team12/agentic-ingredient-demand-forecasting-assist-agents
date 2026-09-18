// `/data-setup/ingredients-suppliers` route (ACRI-61) — protected by
// `RequireAuth` in `App.tsx`. Fetches suppliers + ingredients on mount,
// owns page-level loading/empty/error state, and composes the supplier
// list and ingredient master sections. Reached from a standalone route for
// now (the Data Setup hub, ACRI-59, is not yet built).
import { useCallback, useEffect, useState } from "react";

import { IngredientMasterSection } from "@/components/ingredients-suppliers/ingredient-master-section";
import { SupplierListSection } from "@/components/ingredients-suppliers/supplier-list-section";
import { ApiError } from "@/lib/api-client";
import {
  createIngredient,
  createSupplier,
  listIngredients,
  listSuppliers,
  updateIngredient,
  updateSupplier,
  type Ingredient,
  type IngredientInput,
  type Supplier,
  type SupplierInput,
} from "@/lib/ingredients-api";

type PageState =
  | { status: "loading" }
  | { status: "error"; message: string }
  | { status: "ready"; suppliers: Supplier[]; ingredients: Ingredient[] };

export default function IngredientsSuppliersSetupRoute() {
  const [state, setState] = useState<PageState>({ status: "loading" });

  const load = useCallback(() => {
    setState({ status: "loading" });
    Promise.all([listSuppliers(), listIngredients()])
      .then(([suppliers, ingredients]) => {
        setState({ status: "ready", suppliers, ingredients });
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

  async function handleCreateSupplier(input: SupplierInput) {
    await createSupplier(input);
    load();
  }

  async function handleUpdateSupplier(id: number, input: SupplierInput) {
    await updateSupplier(id, input);
    load();
  }

  async function handleCreateIngredient(input: IngredientInput) {
    await createIngredient(input);
    load();
  }

  async function handleUpdateIngredient(id: number, input: IngredientInput) {
    await updateIngredient(id, input);
    load();
  }

  return (
    <main className="page">
      <div className="page__header">
        <h1>Ingredients &amp; Suppliers Setup</h1>
        <p className="page__subtitle">
          Load and review ingredient, supplier, and safety-margin data used by stockout and spoilage
          risk.
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
          <SupplierListSection
            suppliers={state.suppliers}
            onCreate={handleCreateSupplier}
            onUpdate={handleUpdateSupplier}
          />
          <IngredientMasterSection
            ingredients={state.ingredients}
            suppliers={state.suppliers}
            onCreate={handleCreateIngredient}
            onUpdate={handleUpdateIngredient}
          />
        </>
      )}
    </main>
  );
}
