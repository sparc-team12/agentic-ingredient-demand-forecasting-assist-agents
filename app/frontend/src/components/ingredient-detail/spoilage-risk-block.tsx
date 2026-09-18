// Spoilage risk detail block (ACRI-42/43/44/64): use-by date, waste cost
// (INR), severity badge, and — when applicable — a visible
// suppressed-by-threshold note (the raw cost is still shown; suppression
// only affects whether a *caller's visible list* would include this item).
// Also links into the Chat Agent (ACRI-45) so the manager can ask why
// this ingredient is flagged, with the ingredient already in focus.
import { Link } from "react-router-dom";

import { SeverityBadge } from "@/components/ingredient-detail/severity-badge";
import type { SpoilageRisk } from "@/lib/risk-api";

interface SpoilageRiskBlockProps {
  spoilage: SpoilageRisk;
}

export function SpoilageRiskBlock({ spoilage }: SpoilageRiskBlockProps) {
  return (
    <section className="card" aria-labelledby="spoilage-risk-heading">
      <div className="section-heading-row">
        <h2 id="spoilage-risk-heading">Spoilage risk</h2>
        <SeverityBadge severity={spoilage.severity} />
      </div>
      <dl>
        <div className="field">
          <label>Use-by date</label>
          <p>{spoilage.use_by_date}</p>
        </div>
        <div className="field">
          <label>Waste cost (INR)</label>
          <p>₹{spoilage.waste_cost_inr.toLocaleString("en-IN", { maximumFractionDigits: 2 })}</p>
        </div>
      </dl>
      {spoilage.suppressed && (
        <p className="hint-text">
          Below the current materiality threshold — suppressed from summary lists, but shown here in
          full.
        </p>
      )}
      <div className="btn-row">
        <Link to={`/chat-agent?ingredientId=${spoilage.ingredient_id}`} className="btn">
          Ask why flagged
        </Link>
      </div>
    </section>
  );
}
