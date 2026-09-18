// One dish's card: dish name + edit action, and its full (never
// summarized) recipe table with add/edit recipe-line entry points and the
// AC2 gap flag for a recipe line whose ingredient has no match in the
// Ingredient table.
import { useState } from "react";

import { GapFlag } from "@/components/ingredients-suppliers/gap-flag";
import { DishForm } from "@/components/menu-recipe/dish-form";
import { RecipeLineForm } from "@/components/menu-recipe/recipe-line-form";
import type { Dish, DishInput, RecipeLine, RecipeLineInput } from "@/lib/menu-recipe-api";

interface DishRecipeCardProps {
  dish: Dish;
  onUpdateDish: (id: number, input: DishInput) => Promise<void>;
  onCreateRecipeLine: (dishId: number, input: RecipeLineInput) => Promise<void>;
  onUpdateRecipeLine: (dishId: number, lineId: number, input: RecipeLineInput) => Promise<void>;
}

export function DishRecipeCard({
  dish,
  onUpdateDish,
  onCreateRecipeLine,
  onUpdateRecipeLine,
}: DishRecipeCardProps) {
  const [isEditingDish, setIsEditingDish] = useState(false);
  const [lineMode, setLineMode] = useState<"closed" | "add" | number>("closed");

  return (
    <section className="card" aria-labelledby={`dish-${dish.id}-heading`}>
      <div className="section-heading-row">
        <h2 id={`dish-${dish.id}-heading`}>{dish.name}</h2>
        {!isEditingDish && (
          <button type="button" className="btn btn--small" onClick={() => setIsEditingDish(true)}>
            Edit dish
          </button>
        )}
      </div>

      {isEditingDish && (
        <DishForm
          initialValue={dish}
          onSubmit={async (input) => {
            await onUpdateDish(dish.id, input);
            setIsEditingDish(false);
          }}
          onCancel={() => setIsEditingDish(false)}
        />
      )}

      {dish.recipe_lines.length === 0 ? (
        <p className="empty-state">No recipe lines yet. Add one to get started.</p>
      ) : (
        <div className="table-wrap">
          <table className="data-table">
            <thead>
              <tr>
                <th scope="col">Ingredient</th>
                <th scope="col">Quantity per serving</th>
                <th scope="col">Unit</th>
                <th scope="col">Actions</th>
              </tr>
            </thead>
            <tbody>
              {dish.recipe_lines.map((line) => (
                <tr key={line.id}>
                  <td>
                    {line.ingredient_name}{" "}
                    {line.ingredient_flagged && (
                      <GapFlag when={true} text="Not in Ingredients master" />
                    )}
                  </td>
                  <td>{line.quantity_per_serving}</td>
                  <td>{line.unit}</td>
                  <td>
                    <button
                      type="button"
                      className="btn btn--small"
                      onClick={() => setLineMode(line.id)}
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

      {lineMode === "closed" && (
        <button type="button" className="btn" onClick={() => setLineMode("add")}>
          Add recipe line
        </button>
      )}

      {lineMode === "add" && (
        <RecipeLineForm
          onSubmit={async (input) => {
            await onCreateRecipeLine(dish.id, input);
            setLineMode("closed");
          }}
          onCancel={() => setLineMode("closed")}
        />
      )}

      {typeof lineMode === "number" &&
        (() => {
          const editing = dish.recipe_lines.find((line: RecipeLine) => line.id === lineMode);
          if (!editing) return null;
          return (
            <RecipeLineForm
              initialValue={editing}
              onSubmit={async (input) => {
                await onUpdateRecipeLine(dish.id, editing.id, input);
                setLineMode("closed");
              }}
              onCancel={() => setLineMode("closed")}
            />
          );
        })()}
    </section>
  );
}
