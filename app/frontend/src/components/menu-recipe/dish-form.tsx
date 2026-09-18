// Controlled add/edit form for a `Dish` (ACRI-60 AC1). Used for both "add"
// (no `initialValue`) and "edit" (`initialValue` set) — mirrors
// `components/ingredients-suppliers/supplier-form.tsx`'s structure.
import { useState, type FormEvent } from "react";

import type { Dish, DishInput } from "@/lib/menu-recipe-api";

interface DishFormProps {
  initialValue?: Dish;
  onSubmit: (input: DishInput) => Promise<void>;
  onCancel: () => void;
}

export function DishForm({ initialValue, onSubmit, onCancel }: DishFormProps) {
  const [name, setName] = useState(initialValue?.name ?? "");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);

    const trimmedName = name.trim();
    if (!trimmedName) {
      setError("Name is required.");
      return;
    }

    setIsSubmitting(true);
    try {
      await onSubmit({ name: trimmedName });
    } catch {
      setError("Something went wrong saving this dish. Please try again.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <form
      onSubmit={handleSubmit}
      noValidate
      aria-label={initialValue ? "Edit dish" : "Add dish"}
      className="form-card"
    >
      <div className="field">
        <label htmlFor="dish-name">Name</label>
        <input
          id="dish-name"
          name="name"
          type="text"
          value={name}
          onChange={(event) => setName(event.target.value)}
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
          {isSubmitting ? "Saving…" : "Save dish"}
        </button>
        <button type="button" className="btn" onClick={onCancel} disabled={isSubmitting}>
          Cancel
        </button>
      </div>
    </form>
  );
}
