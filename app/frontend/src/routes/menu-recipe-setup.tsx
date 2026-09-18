// `/data-setup/menu-recipe-setup` route (ACRI-60) — protected by
// `RequireAuth` in `App.tsx`. Fetches dishes (with their full recipes) on
// mount, owns page-level loading/empty/error state, and composes one
// `DishRecipeCard` per dish. Reached from the Data Setup hub (ACRI-59).
import { useCallback, useEffect, useState } from "react";

import { DishForm } from "@/components/menu-recipe/dish-form";
import { DishRecipeCard } from "@/components/menu-recipe/dish-recipe-card";
import { ApiError } from "@/lib/api-client";
import {
  createDish,
  createRecipeLine,
  listDishes,
  updateDish,
  updateRecipeLine,
  type Dish,
  type DishInput,
  type RecipeLineInput,
} from "@/lib/menu-recipe-api";

type PageState =
  | { status: "loading" }
  | { status: "error"; message: string }
  | { status: "ready"; dishes: Dish[] };

export default function MenuRecipeSetupRoute() {
  const [state, setState] = useState<PageState>({ status: "loading" });
  const [isAddingDish, setIsAddingDish] = useState(false);

  const load = useCallback(() => {
    setState({ status: "loading" });
    listDishes()
      .then((dishes) => {
        setState({ status: "ready", dishes });
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

  async function handleCreateDish(input: DishInput) {
    await createDish(input);
    setIsAddingDish(false);
    load();
  }

  async function handleUpdateDish(id: number, input: DishInput) {
    await updateDish(id, input);
    load();
  }

  async function handleCreateRecipeLine(dishId: number, input: RecipeLineInput) {
    await createRecipeLine(dishId, input);
    load();
  }

  async function handleUpdateRecipeLine(dishId: number, lineId: number, input: RecipeLineInput) {
    await updateRecipeLine(dishId, lineId, input);
    load();
  }

  return (
    <main className="page">
      <div className="page__header">
        <h1>Menu &amp; Recipe Setup</h1>
        <p className="page__subtitle">
          Load and review each dish&apos;s full recipe (ingredient quantity per serving). A recipe
          line referencing an ingredient not yet in the Ingredients master is flagged.
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
          {state.dishes.length === 0 && (
            <p className="empty-state">No dishes yet. Add one to get started.</p>
          )}

          {state.dishes.map((dish) => (
            <DishRecipeCard
              key={dish.id}
              dish={dish}
              onUpdateDish={handleUpdateDish}
              onCreateRecipeLine={handleCreateRecipeLine}
              onUpdateRecipeLine={handleUpdateRecipeLine}
            />
          ))}

          <div className="card">
            {!isAddingDish && (
              <button type="button" className="btn" onClick={() => setIsAddingDish(true)}>
                Add dish
              </button>
            )}
            {isAddingDish && (
              <DishForm onSubmit={handleCreateDish} onCancel={() => setIsAddingDish(false)} />
            )}
          </div>
        </>
      )}
    </main>
  );
}
