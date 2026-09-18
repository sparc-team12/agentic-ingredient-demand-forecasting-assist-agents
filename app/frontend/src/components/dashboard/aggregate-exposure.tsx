// The Risk Dashboard's single aggregate total-waste-exposure figure
// (ACRI-58 US-023): INR, summing *every* spoilage-risk ingredient's waste
// cost, including ones suppressed by the materiality threshold from the
// visible list below (the sum itself is never filtered — see
// `services/dashboard_service.py`). Rendered large and prominent, at the
// top of the dashboard, per the AC.
interface AggregateExposureProps {
  totalWasteExposureInr: number;
}

export function AggregateExposure({ totalWasteExposureInr }: AggregateExposureProps) {
  return (
    <section className="card" aria-labelledby="aggregate-exposure-heading">
      <h2 id="aggregate-exposure-heading" className="page__subtitle">
        Total waste exposure (INR)
      </h2>
      <p className="aggregate-exposure__value">
        ₹{totalWasteExposureInr.toLocaleString("en-IN", { maximumFractionDigits: 2 })}
      </p>
    </section>
  );
}
