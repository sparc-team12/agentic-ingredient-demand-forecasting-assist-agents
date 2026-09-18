// The live-adjustable spoilage materiality threshold control (ACRI-58
// US-023, deferred from the Stockout/Spoilage track): a small inline
// number input + "Save" reading/writing `GET/PUT /risk-config`
// (`lib/risk-api.ts`). Mirrors the validation/submit pattern in
// `components/current-stock/current-stock-form.tsx` (blank/negative
// rejected inline, no new dependency).
import { useState, type FormEvent } from "react";

interface MaterialityThresholdControlProps {
  materialityThresholdInr: number;
  onSave: (materialityThresholdInr: number) => Promise<void>;
}

export function MaterialityThresholdControl({
  materialityThresholdInr,
  onSave,
}: MaterialityThresholdControlProps) {
  const [value, setValue] = useState(String(materialityThresholdInr));
  const [error, setError] = useState<string | null>(null);
  const [savedMessage, setSavedMessage] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setSavedMessage(null);

    const numericValue = Number(value);
    if (value.trim() === "" || Number.isNaN(numericValue) || numericValue < 0) {
      setError("Materiality threshold must be a non-negative number.");
      return;
    }

    setIsSaving(true);
    try {
      await onSave(numericValue);
      setSavedMessage("Saved.");
    } catch {
      setError("Something went wrong saving the threshold. Please try again.");
    } finally {
      setIsSaving(false);
    }
  }

  return (
    <section className="card" aria-labelledby="materiality-threshold-heading">
      <h2 id="materiality-threshold-heading">Materiality threshold</h2>
      <p className="hint-text">
        Warnings below this INR amount are hidden from the list below (the total above always
        includes them).
      </p>
      <form onSubmit={handleSubmit} noValidate aria-label="Materiality threshold">
        <div className="field">
          <label htmlFor="materiality-threshold-input">Materiality threshold (INR)</label>
          <input
            id="materiality-threshold-input"
            name="materiality_threshold_inr"
            type="number"
            min={0}
            step="any"
            value={value}
            onChange={(event) => setValue(event.target.value)}
          />
        </div>
        {error !== null && (
          <p role="alert" className="alert">
            {error}
          </p>
        )}
        <div className="btn-row">
          <button type="submit" className="btn btn--primary btn--small" disabled={isSaving}>
            {isSaving ? "Saving…" : "Save"}
          </button>
        </div>
        {savedMessage !== null && <p className="hint-text">{savedMessage}</p>}
      </form>
    </section>
  );
}
