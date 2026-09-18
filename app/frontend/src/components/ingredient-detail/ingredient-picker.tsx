// A plain `<select>` ingredient picker for the Ingredient Detail screen.
// There's no navigation-from-dashboard yet (that lands with the Dashboard
// track), so this is the only way to choose which ingredient's risk to
// view.
import type { Ingredient } from "@/lib/ingredients-api";

interface IngredientPickerProps {
  ingredients: Ingredient[];
  selectedIngredientId: number | null;
  onSelect: (ingredientId: number | null) => void;
}

const NO_SELECTION_VALUE = "";

export function IngredientPicker({
  ingredients,
  selectedIngredientId,
  onSelect,
}: IngredientPickerProps) {
  return (
    <div className="field">
      <label htmlFor="ingredient-detail-picker">Ingredient</label>
      <select
        id="ingredient-detail-picker"
        value={selectedIngredientId != null ? String(selectedIngredientId) : NO_SELECTION_VALUE}
        onChange={(event) => {
          const value = event.target.value;
          onSelect(value === NO_SELECTION_VALUE ? null : Number(value));
        }}
      >
        <option value={NO_SELECTION_VALUE}>Select an ingredient…</option>
        {ingredients.map((ingredient) => (
          <option key={ingredient.id} value={String(ingredient.id)}>
            {ingredient.name}
          </option>
        ))}
      </select>
    </div>
  );
}
