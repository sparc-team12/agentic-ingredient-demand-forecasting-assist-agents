// Stockout risk detail block (ACRI-38..41): stockout date, order-by date,
// suggested order quantity, severity badge, and — when applicable — a
// visible safety-margin-gap flag (never silently treated as "no gap").
import { GapFlag } from "@/components/ingredients-suppliers/gap-flag";
import { SeverityBadge } from "@/components/ingredient-detail/severity-badge";
import type { StockoutRisk } from "@/lib/risk-api";

interface StockoutRiskBlockProps {
  stockout: StockoutRisk;
}

export function StockoutRiskBlock({ stockout }: StockoutRiskBlockProps) {
  return (
    <section className="card" aria-labelledby="stockout-risk-heading">
      <div className="section-heading-row">
        <h2 id="stockout-risk-heading">Stockout risk</h2>
        <SeverityBadge severity={stockout.severity} />
      </div>
      <dl>
        <div className="field">
          <label>Stockout date</label>
          <p>{stockout.stockout_date}</p>
        </div>
        <div className="field">
          <label>Order-by date</label>
          <p>{stockout.order_by_date}</p>
        </div>
        <div className="field">
          <label>Suggested order quantity</label>
          <p>{stockout.suggested_order_quantity}</p>
        </div>
      </dl>
      <GapFlag
        when={stockout.safety_margin_gap}
        text="Safety margin not set — order-by date treats it as 0 days"
      />
      <GapFlag
        when={stockout.lead_time_gap}
        text="No supplier lead time on file — order-by date treats it as 0 days"
      />
    </section>
  );
}
