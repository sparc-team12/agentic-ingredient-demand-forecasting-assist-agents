// Ingredient master table (ACRI-61 AC1/AC2/AC3/AC4/AC5) + "Add ingredient"
// entry point, using `IngredientForm` and `GapFlag`. Renders `unit`,
// `unit_cost`, a real (disabled, read-only) checkbox for `perishable`,
// `shelf_life_days` ("—" when not perishable), the mapped supplier's name
// (or the AC3 gap flag when `has_supplier` is false), and the resolved
// `effective_safety_margin_days` (or the AC5 gap flag when
// `safety_margin_gap` is true — never rendered as `0`).
import { useState } from "react";

import { GapFlag } from "@/components/ingredients-suppliers/gap-flag";
import { IngredientForm } from "@/components/ingredients-suppliers/ingredient-form";
import type { Ingredient, IngredientInput, Supplier } from "@/lib/ingredients-api";

interface IngredientMasterSectionProps {
  ingredients: Ingredient[];
  suppliers: Supplier[];
  onCreate: (input: IngredientInput) => Promise<void>;
  onUpdate: (id: number, input: IngredientInput) => Promise<void>;
}

export function IngredientMasterSection({
  ingredients,
  suppliers,
  onCreate,
  onUpdate,
}: IngredientMasterSectionProps) {
  const [mode, setMode] = useState<"closed" | "add" | number>("closed");

  return (
    <section className="card" aria-labelledby="ingredient-master-heading">
      <div className="section-heading-row">
        <h2 id="ingredient-master-heading">Ingredients</h2>
      </div>

      {ingredients.length === 0 ? (
        <p className="empty-state">No ingredients yet. Add one to get started.</p>
      ) : (
        <div className="table-wrap">
          <table className="data-table">
            <thead>
              <tr>
                <th scope="col">Name</th>
                <th scope="col">Unit</th>
                <th scope="col">Unit cost</th>
                <th scope="col">Perishable</th>
                <th scope="col">Shelf life (days)</th>
                <th scope="col">Supplier</th>
                <th scope="col">Safety margin (days)</th>
                <th scope="col">Actions</th>
              </tr>
            </thead>
            <tbody>
              {ingredients.map((ingredient) => (
                <tr key={ingredient.id}>
                  <td>{ingredient.name}</td>
                  <td>{ingredient.unit}</td>
                  <td>{ingredient.unit_cost}</td>
                  <td>
                    <input
                      type="checkbox"
                      checked={ingredient.perishable}
                      disabled
                      aria-label={`${ingredient.name} is perishable`}
                      readOnly
                    />
                  </td>
                  <td>{ingredient.perishable ? (ingredient.shelf_life_days ?? "—") : "—"}</td>
                  <td>
                    {ingredient.has_supplier && ingredient.supplier ? (
                      ingredient.supplier.name
                    ) : (
                      <GapFlag when={true} text="No supplier mapped" />
                    )}
                  </td>
                  <td>
                    {ingredient.safety_margin_gap ? (
                      <GapFlag when={true} text="Safety margin not set" />
                    ) : (
                      ingredient.effective_safety_margin_days
                    )}
                  </td>
                  <td>
                    <button
                      type="button"
                      className="btn btn--small"
                      onClick={() => setMode(ingredient.id)}
                    >
                      Edit
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {mode === "closed" && (
        <button type="button" className="btn" onClick={() => setMode("add")}>
          Add ingredient
        </button>
      )}

      {mode === "add" && (
        <IngredientForm
          suppliers={suppliers}
          onSubmit={async (input) => {
            await onCreate(input);
            setMode("closed");
          }}
          onCancel={() => setMode("closed")}
        />
      )}

      {typeof mode === "number" &&
        (() => {
          const editing = ingredients.find((ingredient) => ingredient.id === mode);
          if (!editing) return null;
          return (
            <IngredientForm
              suppliers={suppliers}
              initialValue={editing}
              onSubmit={async (input) => {
                await onUpdate(editing.id, input);
                setMode("closed");
              }}
              onCancel={() => setMode("closed")}
            />
          );
        })()}
    </section>
  );
}
