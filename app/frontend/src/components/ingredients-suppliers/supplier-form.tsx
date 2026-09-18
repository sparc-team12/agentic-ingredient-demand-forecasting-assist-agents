// Controlled add/edit form for a `Supplier` (ACRI-61 AC2/AC4).
//
// Used for both "add" (no `initialValue`) and "edit" (`initialValue` set —
// pre-filled from the already-fetched supplier list, per the full-replace
// `PUT` contract in `ingredients-api.ts`): name, lead time (number input,
// non-negative), and an optional safety-margin-in-days number input.
import { useState, type FormEvent } from "react";

import type { Supplier, SupplierInput } from "@/lib/ingredients-api";

interface SupplierFormProps {
  initialValue?: Supplier;
  onSubmit: (input: SupplierInput) => Promise<void>;
  onCancel: () => void;
}

export function SupplierForm({ initialValue, onSubmit, onCancel }: SupplierFormProps) {
  const [name, setName] = useState(initialValue?.name ?? "");
  const [leadTimeDays, setLeadTimeDays] = useState(
    initialValue ? String(initialValue.lead_time_days) : "",
  );
  const [safetyMarginDays, setSafetyMarginDays] = useState(
    initialValue?.safety_margin_days != null ? String(initialValue.safety_margin_days) : "",
  );
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
    const leadTimeValue = Number(leadTimeDays);
    if (leadTimeDays.trim() === "" || Number.isNaN(leadTimeValue) || leadTimeValue < 0) {
      setError("Lead time (days) must be a non-negative number.");
      return;
    }
    let safetyMarginValue: number | null = null;
    if (safetyMarginDays.trim() !== "") {
      safetyMarginValue = Number(safetyMarginDays);
      if (Number.isNaN(safetyMarginValue) || safetyMarginValue < 0) {
        setError("Safety margin (days) must be a non-negative number, or left blank.");
        return;
      }
    }

    setIsSubmitting(true);
    try {
      await onSubmit({
        name: trimmedName,
        lead_time_days: leadTimeValue,
        safety_margin_days: safetyMarginValue,
      });
    } catch {
      setError("Something went wrong saving this supplier. Please try again.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <form
      onSubmit={handleSubmit}
      noValidate
      aria-label={initialValue ? "Edit supplier" : "Add supplier"}
      className="form-card"
    >
      <div className="field">
        <label htmlFor="supplier-name">Name</label>
        <input
          id="supplier-name"
          name="name"
          type="text"
          value={name}
          onChange={(event) => setName(event.target.value)}
          required
        />
      </div>
      <div className="field">
        <label htmlFor="supplier-lead-time-days">Lead time (days)</label>
        <input
          id="supplier-lead-time-days"
          name="lead_time_days"
          type="number"
          min={0}
          value={leadTimeDays}
          onChange={(event) => setLeadTimeDays(event.target.value)}
          required
        />
      </div>
      <div className="field">
        <label htmlFor="supplier-safety-margin-days">Safety margin (days)</label>
        <input
          id="supplier-safety-margin-days"
          name="safety_margin_days"
          type="number"
          min={0}
          value={safetyMarginDays}
          onChange={(event) => setSafetyMarginDays(event.target.value)}
        />
      </div>
      {error !== null && (
        <p role="alert" className="alert">
          {error}
        </p>
      )}
      <div className="btn-row">
        <button type="submit" className="btn btn--primary" disabled={isSubmitting}>
          {isSubmitting ? "Saving…" : "Save supplier"}
        </button>
        <button type="button" className="btn" onClick={onCancel} disabled={isSubmitting}>
          Cancel
        </button>
      </div>
    </form>
  );
}
