// Controlled add/edit form for a `RecipeLine` (ACRI-60 AC1/AC2). The
// ingredient is a free-text field (not a `<select>` bound to the
// ingredient master list) — AC2's flag applies to an ingredient name with
// no match in the `Ingredient` table, so an unmatched name must remain
// enterable, unlike the supplier picker in `ingredient-form.tsx`.
import { useState, type FormEvent } from "react";

import type { RecipeLine, RecipeLineInput } from "@/lib/menu-recipe-api";

interface RecipeLineFormProps {
  initialValue?: RecipeLine;
  onSubmit: (input: RecipeLineInput) => Promise<void>;
  onCancel: () => void;
}

export function RecipeLineForm({ initialValue, onSubmit, onCancel }: RecipeLineFormProps) {
  const [ingredientName, setIngredientName] = useState(initialValue?.ingredient_name ?? "");
  const [quantityPerServing, setQuantityPerServing] = useState(
    initialValue ? String(initialValue.quantity_per_serving) : "",
  );
  const [unit, setUnit] = useState(initialValue?.unit ?? "");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);

    const trimmedIngredientName = ingredientName.trim();
    const trimmedUnit = unit.trim();
    if (!trimmedIngredientName || !trimmedUnit) {
      setError("Ingredient and unit are required.");
      return;
    }
    const quantityValue = Number(quantityPerServing);
    if (quantityPerServing.trim() === "" || Number.isNaN(quantityValue) || quantityValue <= 0) {
      setError("Quantity per serving must be a positive number.");
      return;
    }

    setIsSubmitting(true);
    try {
      await onSubmit({
        ingredient_name: trimmedIngredientName,
        quantity_per_serving: quantityValue,
        unit: trimmedUnit,
      });
    } catch {
      setError("Something went wrong saving this recipe line. Please try again.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <form
      onSubmit={handleSubmit}
      noValidate
      aria-label={initialValue ? "Edit recipe line" : "Add recipe line"}
      className="form-card"
    >
      <div className="field">
        <label htmlFor="recipe-line-ingredient-name">Ingredient</label>
        <input
          id="recipe-line-ingredient-name"
          name="ingredient_name"
          type="text"
          value={ingredientName}
          onChange={(event) => setIngredientName(event.target.value)}
          required
        />
      </div>
      <div className="field">
        <label htmlFor="recipe-line-quantity-per-serving">Quantity per serving</label>
        <input
          id="recipe-line-quantity-per-serving"
          name="quantity_per_serving"
          type="number"
          min={0}
          step="any"
          value={quantityPerServing}
          onChange={(event) => setQuantityPerServing(event.target.value)}
          required
        />
      </div>
      <div className="field">
        <label htmlFor="recipe-line-unit">Unit</label>
        <input
          id="recipe-line-unit"
          name="unit"
          type="text"
          value={unit}
          onChange={(event) => setUnit(event.target.value)}
          required
        />
      </div>
      {error !== null && (
        <p role="alert" className="alert">
          {error}
        </p>
      )}
      <div className="btn-row">
        <button type="submit" className="btn btn--primary" disabled={isSubmitting}>
          {isSubmitting ? "Saving…" : "Save recipe line"}
        </button>
        <button type="button" className="btn" onClick={onCancel} disabled={isSubmitting}>
          Cancel
        </button>
      </div>
    </form>
  );
}
