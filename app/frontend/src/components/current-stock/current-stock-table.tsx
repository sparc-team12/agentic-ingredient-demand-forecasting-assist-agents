// Current stock table (ACRI-62 AC1/AC2): one row per existing ingredient
// (whether or not a snapshot has been recorded yet), an inline edit entry
// point, and the AC2 gap flag for a perishable ingredient with no
// recorded use-by date.
import { Fragment, useState } from "react";

import { GapFlag } from "@/components/ingredients-suppliers/gap-flag";
import { CurrentStockForm } from "@/components/current-stock/current-stock-form";
import type { CurrentStock, CurrentStockInput } from "@/lib/current-stock-api";

interface CurrentStockTableProps {
  stocks: CurrentStock[];
  onUpdate: (ingredientId: number, input: CurrentStockInput) => Promise<void>;
}

export function CurrentStockTable({ stocks, onUpdate }: CurrentStockTableProps) {
  const [editingIngredientId, setEditingIngredientId] = useState<number | null>(null);

  if (stocks.length === 0) {
    return <p className="empty-state">No ingredients exist yet. Add one in Ingredients Setup.</p>;
  }

  return (
    <div className="table-wrap">
      <table className="data-table">
        <thead>
          <tr>
            <th scope="col">Ingredient</th>
            <th scope="col">Quantity on hand</th>
            <th scope="col">Use-by date</th>
            <th scope="col">Actions</th>
          </tr>
        </thead>
        <tbody>
          {stocks.map((stock) => (
            <Fragment key={stock.ingredient_id}>
              <tr>
                <td>{stock.ingredient_name}</td>
                <td>
                  {stock.has_stock_recorded ? (
                    `${stock.quantity_on_hand} ${stock.unit}`
                  ) : (
                    <span className="hint-text">Not recorded yet</span>
                  )}
                </td>
                <td>
                  {stock.use_by_date_gap ? (
                    <GapFlag when={true} text="Use-by date missing" />
                  ) : (
                    (stock.use_by_date ?? "—")
                  )}
                </td>
                <td>
                  <button
                    type="button"
                    className="btn btn--small"
                    onClick={() => setEditingIngredientId(stock.ingredient_id)}
                  >
                    Edit
                  </button>
                </td>
              </tr>
              {editingIngredientId === stock.ingredient_id && (
                <tr>
                  <td colSpan={4}>
                    <CurrentStockForm
                      stock={stock}
                      onSubmit={async (input) => {
                        await onUpdate(stock.ingredient_id, input);
                        setEditingIngredientId(null);
                      }}
                      onCancel={() => setEditingIngredientId(null)}
                    />
                  </td>
                </tr>
              )}
            </Fragment>
          ))}
        </tbody>
      </table>
    </div>
  );
}
