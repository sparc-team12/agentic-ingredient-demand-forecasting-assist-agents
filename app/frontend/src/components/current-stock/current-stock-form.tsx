// Controlled edit form for one ingredient's `CurrentStock` snapshot
// (ACRI-62 AC2) — upserts quantity-on-hand and use-by-date. Always opened
// pre-filled from the already-fetched row (or blank when
// `has_stock_recorded` is false), mirroring the full-replace `PUT`
// contract in `current-stock-api.ts`.
import { useState, type FormEvent } from "react";

import type { CurrentStock, CurrentStockInput } from "@/lib/current-stock-api";

interface CurrentStockFormProps {
  stock: CurrentStock;
  onSubmit: (input: CurrentStockInput) => Promise<void>;
  onCancel: () => void;
}

export function CurrentStockForm({ stock, onSubmit, onCancel }: CurrentStockFormProps) {
  const [quantityOnHand, setQuantityOnHand] = useState(
    stock.quantity_on_hand != null ? String(stock.quantity_on_hand) : "",
  );
  const [useByDate, setUseByDate] = useState(stock.use_by_date ?? "");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);

    const quantityValue = Number(quantityOnHand);
    if (quantityOnHand.trim() === "" || Number.isNaN(quantityValue) || quantityValue < 0) {
      setError("Quantity on hand must be a non-negative number.");
      return;
    }

    setIsSubmitting(true);
    try {
      await onSubmit({
        quantity_on_hand: quantityValue,
        use_by_date: useByDate.trim() === "" ? null : useByDate,
      });
    } catch {
      setError("Something went wrong saving this stock snapshot. Please try again.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <form
      onSubmit={handleSubmit}
      noValidate
      aria-label={`Edit current stock for ${stock.ingredient_name}`}
      className="form-card"
    >
      <div className="field">
        <label htmlFor={`current-stock-quantity-${stock.ingredient_id}`}>
          Quantity on hand ({stock.unit})
        </label>
        <input
          id={`current-stock-quantity-${stock.ingredient_id}`}
          name="quantity_on_hand"
          type="number"
          min={0}
          step="any"
          value={quantityOnHand}
          onChange={(event) => setQuantityOnHand(event.target.value)}
          required
        />
      </div>
      <div className="field">
        <label htmlFor={`current-stock-use-by-date-${stock.ingredient_id}`}>Use-by date</label>
        <input
          id={`current-stock-use-by-date-${stock.ingredient_id}`}
          name="use_by_date"
          type="date"
          value={useByDate}
          onChange={(event) => setUseByDate(event.target.value)}
        />
      </div>
      {error !== null && (
        <p role="alert" className="alert">
          {error}
        </p>
      )}
      <div className="btn-row">
        <button type="submit" className="btn btn--primary" disabled={isSubmitting}>
          {isSubmitting ? "Saving…" : "Save stock"}
        </button>
        <button type="button" className="btn" onClick={onCancel} disabled={isSubmitting}>
          Cancel
        </button>
      </div>
    </form>
  );
}
