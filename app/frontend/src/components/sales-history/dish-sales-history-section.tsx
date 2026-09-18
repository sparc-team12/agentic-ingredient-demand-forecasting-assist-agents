// One dish's sales-history card (ACRI-63 AC1/AC2): the computed
// distinct-days-of-history count, the <84-days gap flag, and the full
// (never summarized) list of daily records.
import { GapFlag } from "@/components/ingredients-suppliers/gap-flag";
import { TARGET_DAYS_OF_HISTORY, type DishSalesHistory } from "@/lib/sales-history-api";

interface DishSalesHistorySectionProps {
  history: DishSalesHistory;
}

export function DishSalesHistorySection({ history }: DishSalesHistorySectionProps) {
  return (
    <section className="card" aria-labelledby={`sales-history-${history.dish_id}-heading`}>
      <div className="section-heading-row">
        <h2 id={`sales-history-${history.dish_id}-heading`}>{history.dish_name}</h2>
        <span>
          {history.distinct_days_of_history} / {TARGET_DAYS_OF_HISTORY} days
        </span>
      </div>

      {!history.has_full_history && (
        <GapFlag when={true} text={`Fewer than ${TARGET_DAYS_OF_HISTORY} days of history`} />
      )}

      {history.records.length === 0 ? (
        <p className="empty-state">No sales history recorded yet for this dish.</p>
      ) : (
        <div className="table-wrap">
          <table className="data-table">
            <thead>
              <tr>
                <th scope="col">Date</th>
                <th scope="col">Units sold</th>
              </tr>
            </thead>
            <tbody>
              {history.records.map((record) => (
                <tr key={record.id}>
                  <td>{record.sale_date}</td>
                  <td>{record.units_sold}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
