// The Risk Dashboard's single severity-ordered list of every at-risk
// ingredient (ACRI-54 US-019, ACRI-55 US-020, ACRI-56 US-021, ACRI-57
// US-022): stockout and spoilage rows interleaved, in the order the
// backend already computed (`services/dashboard_service.py`'s ranking
// rule — this component does not re-sort). Suppressed spoilage rows
// (ACRI-58 US-023 / ACRI-44 US-009's "hidden from the list below" rule)
// are filtered out of what's rendered here, even though the backend
// still returns them (tagged) for traceability. Reuses `.data-table`
// (current-stock/ingredients-suppliers precedent) and the shared
// `SeverityBadge` (color + exact text together, never color alone).
import { SeverityBadge } from "@/components/ingredient-detail/severity-badge";
import type { DashboardRiskRow } from "@/lib/dashboard-api";

interface RiskTableProps {
  rows: DashboardRiskRow[];
}

const RISK_TYPE_LABEL: Record<DashboardRiskRow["risk_type"], string> = {
  stockout: "Stockout",
  spoilage: "Spoilage",
};

export function RiskTable({ rows }: RiskTableProps) {
  const visibleRows = rows.filter((row) => !row.suppressed);

  if (visibleRows.length === 0) {
    return <p className="empty-state">No ingredients currently at risk.</p>;
  }

  return (
    <div className="table-wrap">
      <table className="data-table">
        <thead>
          <tr>
            <th scope="col">Ingredient</th>
            <th scope="col">Risk type</th>
            <th scope="col">Severity</th>
            <th scope="col">Order-by date / Waste cost</th>
          </tr>
        </thead>
        <tbody>
          {visibleRows.map((row) => (
            <tr key={`${row.risk_type}-${row.ingredient_id}`}>
              <td>{row.ingredient_name}</td>
              <td>{RISK_TYPE_LABEL[row.risk_type]}</td>
              <td>
                <SeverityBadge severity={row.severity} />
              </td>
              <td>
                {row.risk_type === "stockout"
                  ? row.order_by_date
                  : `₹${(row.waste_cost_inr ?? 0).toLocaleString("en-IN", { maximumFractionDigits: 2 })}`}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
