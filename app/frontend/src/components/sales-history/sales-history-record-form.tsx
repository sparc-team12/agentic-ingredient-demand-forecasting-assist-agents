// Manual add-record form for a single day's units-sold for one dish
// (ACRI-63 AC1). A real `<select>` dish picker populated only from the
// already-fetched dish list (cannot free-type a nonexistent dish),
// mirroring `ingredient-form.tsx`'s supplier-picker pattern.
import { useState, type FormEvent } from "react";

import type { SalesHistoryRecordInput } from "@/lib/sales-history-api";

interface DishOption {
  id: number;
  name: string;
}

interface SalesHistoryRecordFormProps {
  dishes: DishOption[];
  onSubmit: (input: SalesHistoryRecordInput) => Promise<void>;
  onCancel: () => void;
}

export function SalesHistoryRecordForm({
  dishes,
  onSubmit,
  onCancel,
}: SalesHistoryRecordFormProps) {
  const [dishId, setDishId] = useState(dishes[0] ? String(dishes[0].id) : "");
  const [saleDate, setSaleDate] = useState("");
  const [unitsSold, setUnitsSold] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);

    if (dishId === "") {
      setError("Dish is required.");
      return;
    }
    if (saleDate.trim() === "") {
      setError("Date is required.");
      return;
    }
    const unitsSoldValue = Number(unitsSold);
    if (unitsSold.trim() === "" || Number.isNaN(unitsSoldValue) || unitsSoldValue < 0) {
      setError("Units sold must be a non-negative number.");
      return;
    }

    setIsSubmitting(true);
    try {
      await onSubmit({
        dish_id: Number(dishId),
        sale_date: saleDate,
        units_sold: unitsSoldValue,
      });
    } catch {
      setError("Something went wrong saving this record. Please try again.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <form
      onSubmit={handleSubmit}
      noValidate
      aria-label="Add sales history record"
      className="form-card"
    >
      <div className="field">
        <label htmlFor="sales-history-dish-id">Dish</label>
        <select
          id="sales-history-dish-id"
          name="dish_id"
          value={dishId}
          onChange={(event) => setDishId(event.target.value)}
          required
        >
          {dishes.map((dish) => (
            <option key={dish.id} value={String(dish.id)}>
              {dish.name}
            </option>
          ))}
        </select>
      </div>
      <div className="field">
        <label htmlFor="sales-history-sale-date">Date</label>
        <input
          id="sales-history-sale-date"
          name="sale_date"
          type="date"
          value={saleDate}
          onChange={(event) => setSaleDate(event.target.value)}
          required
        />
      </div>
      <div className="field">
        <label htmlFor="sales-history-units-sold">Units sold</label>
        <input
          id="sales-history-units-sold"
          name="units_sold"
          type="number"
          min={0}
          value={unitsSold}
          onChange={(event) => setUnitsSold(event.target.value)}
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
          {isSubmitting ? "Saving…" : "Save record"}
        </button>
        <button type="button" className="btn" onClick={onCancel} disabled={isSubmitting}>
          Cancel
        </button>
      </div>
    </form>
  );
}
