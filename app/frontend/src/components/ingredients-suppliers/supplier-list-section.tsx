// Supplier list table (ACRI-61 AC2/AC4) + "Add supplier" entry point,
// using `SupplierForm`. A supplier's own missing `safety_margin_days` is
// shown as a lighter, non-error hint (not a hard AC5 gap flag) — the hard
// gap flag applies at the ingredient level, per the plan's Q2 resolution:
// a supplier's missing default only becomes an AC5 gap for ingredients
// that rely on it and have no override of their own.
import { useState } from "react";

import { SupplierForm } from "@/components/ingredients-suppliers/supplier-form";
import type { Supplier, SupplierInput } from "@/lib/ingredients-api";

interface SupplierListSectionProps {
  suppliers: Supplier[];
  onCreate: (input: SupplierInput) => Promise<void>;
  onUpdate: (id: number, input: SupplierInput) => Promise<void>;
}

export function SupplierListSection({ suppliers, onCreate, onUpdate }: SupplierListSectionProps) {
  const [mode, setMode] = useState<"closed" | "add" | number>("closed");

  return (
    <section className="card" aria-labelledby="supplier-list-heading">
      <div className="section-heading-row">
        <h2 id="supplier-list-heading">Suppliers</h2>
      </div>

      {suppliers.length === 0 ? (
        <p className="empty-state">No suppliers yet. Add one to get started.</p>
      ) : (
        <div className="table-wrap">
          <table className="data-table">
            <thead>
              <tr>
                <th scope="col">Name</th>
                <th scope="col">Lead time (days)</th>
                <th scope="col">Safety margin (days)</th>
                <th scope="col">Actions</th>
              </tr>
            </thead>
            <tbody>
              {suppliers.map((supplier) => (
                <tr key={supplier.id}>
                  <td>{supplier.name}</td>
                  <td>{supplier.lead_time_days}</td>
                  <td>
                    {supplier.safety_margin_days ?? (
                      <span className="hint-text">Not set — used as default only when set</span>
                    )}
                  </td>
                  <td>
                    <button
                      type="button"
                      className="btn btn--small"
                      onClick={() => setMode(supplier.id)}
                    >
                      Edit
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {mode === "closed" && (
        <button type="button" className="btn" onClick={() => setMode("add")}>
          Add supplier
        </button>
      )}

      {mode === "add" && (
        <SupplierForm
          onSubmit={async (input) => {
            await onCreate(input);
            setMode("closed");
          }}
          onCancel={() => setMode("closed")}
        />
      )}

      {typeof mode === "number" &&
        (() => {
          const editing = suppliers.find((supplier) => supplier.id === mode);
          if (!editing) return null;
          return (
            <SupplierForm
              initialValue={editing}
              onSubmit={async (input) => {
                await onUpdate(editing.id, input);
                setMode("closed");
              }}
              onCancel={() => setMode("closed")}
            />
          );
        })()}
    </section>
  );
}
