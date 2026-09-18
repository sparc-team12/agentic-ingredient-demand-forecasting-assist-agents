// Controlled add/edit form for an `Ingredient` (ACRI-61 AC1/AC2/AC3/AC4).
//
// Used for both "add" (no `initialValue`) and "edit" (`initialValue` set —
// pre-filled from the already-fetched ingredient list, per the
// full-replace `PUT` contract in `ingredients-api.ts`): name, unit, unit
// cost, a real (keyboard-operable) perishable checkbox, a shelf-life
// number input that is only enabled/required when perishable is checked, a
// real `<select>` supplier picker populated only from the already-fetched
// supplier list (cannot free-type a nonexistent supplier — AC3's gap is a
// *missing* mapping, never an invalid one), and an optional safety-margin
// override.
import { useState, type FormEvent } from "react";

import type { Ingredient, IngredientInput, Supplier } from "@/lib/ingredients-api";

interface IngredientFormProps {
  suppliers: Supplier[];
  initialValue?: Ingredient;
  onSubmit: (input: IngredientInput) => Promise<void>;
  onCancel: () => void;
}

const NO_SUPPLIER_VALUE = "";

export function IngredientForm({
  suppliers,
  initialValue,
  onSubmit,
  onCancel,
}: IngredientFormProps) {
  const [name, setName] = useState(initialValue?.name ?? "");
  const [unit, setUnit] = useState(initialValue?.unit ?? "");
  const [unitCost, setUnitCost] = useState(initialValue ? String(initialValue.unit_cost) : "");
  const [perishable, setPerishable] = useState(initialValue?.perishable ?? false);
  const [shelfLifeDays, setShelfLifeDays] = useState(
    initialValue?.shelf_life_days != null ? String(initialValue.shelf_life_days) : "",
  );
  const [supplierId, setSupplierId] = useState(
    initialValue?.supplier_id != null ? String(initialValue.supplier_id) : NO_SUPPLIER_VALUE,
  );
  const [safetyMarginOverride, setSafetyMarginOverride] = useState(
    initialValue?.safety_margin_days_override != null
      ? String(initialValue.safety_margin_days_override)
      : "",
  );
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);

    const trimmedName = name.trim();
    const trimmedUnit = unit.trim();
    if (!trimmedName || !trimmedUnit) {
      setError("Name and unit are required.");
      return;
    }
    const unitCostValue = Number(unitCost);
    if (unitCost.trim() === "" || Number.isNaN(unitCostValue) || unitCostValue < 0) {
      setError("Unit cost must be a non-negative number.");
      return;
    }
    let shelfLifeValue: number | null = null;
    if (perishable) {
      if (shelfLifeDays.trim() === "") {
        setError("Shelf life (days) is required for a perishable ingredient.");
        return;
      }
      shelfLifeValue = Number(shelfLifeDays);
      if (Number.isNaN(shelfLifeValue) || shelfLifeValue <= 0) {
        setError("Shelf life (days) must be a positive number.");
        return;
      }
    } else if (shelfLifeDays.trim() !== "") {
      shelfLifeValue = Number(shelfLifeDays);
      if (Number.isNaN(shelfLifeValue) || shelfLifeValue <= 0) {
        setError("Shelf life (days) must be a positive number, or left blank.");
        return;
      }
    }
    let safetyMarginOverrideValue: number | null = null;
    if (safetyMarginOverride.trim() !== "") {
      safetyMarginOverrideValue = Number(safetyMarginOverride);
      if (Number.isNaN(safetyMarginOverrideValue) || safetyMarginOverrideValue < 0) {
        setError("Safety margin override (days) must be a non-negative number, or left blank.");
        return;
      }
    }

    setIsSubmitting(true);
    try {
      await onSubmit({
        name: trimmedName,
        unit: trimmedUnit,
        unit_cost: unitCostValue,
        perishable,
        shelf_life_days: shelfLifeValue,
        supplier_id: supplierId === NO_SUPPLIER_VALUE ? null : Number(supplierId),
        safety_margin_days_override: safetyMarginOverrideValue,
      });
    } catch {
      setError("Something went wrong saving this ingredient. Please try again.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <form
      onSubmit={handleSubmit}
      noValidate
      aria-label={initialValue ? "Edit ingredient" : "Add ingredient"}
      className="form-card"
    >
      <div className="field">
        <label htmlFor="ingredient-name">Name</label>
        <input
          id="ingredient-name"
          name="name"
          type="text"
          value={name}
          onChange={(event) => setName(event.target.value)}
          required
        />
      </div>
      <div className="field">
        <label htmlFor="ingredient-unit">Unit</label>
        <input
          id="ingredient-unit"
          name="unit"
          type="text"
          value={unit}
          onChange={(event) => setUnit(event.target.value)}
          required
        />
      </div>
      <div className="field">
        <label htmlFor="ingredient-unit-cost">Unit cost</label>
        <input
          id="ingredient-unit-cost"
          name="unit_cost"
          type="number"
          min={0}
          step="any"
          value={unitCost}
          onChange={(event) => setUnitCost(event.target.value)}
          required
        />
      </div>
      <div className="field field--checkbox">
        <label htmlFor="ingredient-perishable">
          <input
            id="ingredient-perishable"
            name="perishable"
            type="checkbox"
            checked={perishable}
            onChange={(event) => setPerishable(event.target.checked)}
          />
          Perishable
        </label>
      </div>
      <div className="field">
        <label htmlFor="ingredient-shelf-life-days">Shelf life (days)</label>
        <input
          id="ingredient-shelf-life-days"
          name="shelf_life_days"
          type="number"
          min={1}
          value={shelfLifeDays}
          onChange={(event) => setShelfLifeDays(event.target.value)}
          disabled={!perishable}
          required={perishable}
        />
      </div>
      <div className="field">
        <label htmlFor="ingredient-supplier">Supplier</label>
        <select
          id="ingredient-supplier"
          name="supplier_id"
          value={supplierId}
          onChange={(event) => setSupplierId(event.target.value)}
        >
          <option value={NO_SUPPLIER_VALUE}>No supplier mapped</option>
          {suppliers.map((supplier) => (
            <option key={supplier.id} value={String(supplier.id)}>
              {supplier.name}
            </option>
          ))}
        </select>
      </div>
      <div className="field">
        <label htmlFor="ingredient-safety-margin-override">Safety margin override (days)</label>
        <input
          id="ingredient-safety-margin-override"
          name="safety_margin_days_override"
          type="number"
          min={0}
          value={safetyMarginOverride}
          onChange={(event) => setSafetyMarginOverride(event.target.value)}
        />
      </div>
      {error !== null && (
        <p role="alert" className="alert">
          {error}
        </p>
      )}
      <div className="btn-row">
        <button type="submit" className="btn btn--primary" disabled={isSubmitting}>
          {isSubmitting ? "Saving…" : "Save ingredient"}
        </button>
        <button type="button" className="btn" onClick={onCancel} disabled={isSubmitting}>
          Cancel
        </button>
      </div>
    </form>
  );
}
