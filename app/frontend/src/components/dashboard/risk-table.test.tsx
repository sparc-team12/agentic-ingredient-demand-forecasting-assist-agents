// ACRI-54..57: `RiskTable` renders both risk types with their type-specific
// column (order-by date for stockout, waste cost for spoilage), the
// severity badge's exact text, filters out suppressed rows, and renders
// the empty state when nothing is visible.
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { RiskTable } from "@/components/dashboard/risk-table";
import type { DashboardRiskRow } from "@/lib/dashboard-api";

const STOCKOUT_ROW: DashboardRiskRow = {
  ingredient_id: 1,
  ingredient_name: "Roma Tomatoes",
  risk_type: "stockout",
  severity: "Critical",
  order_by_date: "2026-01-02",
  waste_cost_inr: null,
  suppressed: false,
};

const SPOILAGE_ROW: DashboardRiskRow = {
  ingredient_id: 2,
  ingredient_name: "Mozzarella",
  risk_type: "spoilage",
  severity: "High",
  order_by_date: null,
  waste_cost_inr: 750,
  suppressed: false,
};

const SUPPRESSED_ROW: DashboardRiskRow = {
  ingredient_id: 3,
  ingredient_name: "Basil",
  risk_type: "spoilage",
  severity: "Low",
  order_by_date: null,
  waste_cost_inr: 50,
  suppressed: true,
};

describe("RiskTable", () => {
  it("renders a stockout row with its order-by date and severity text", () => {
    render(<RiskTable rows={[STOCKOUT_ROW]} />);

    expect(screen.getByText("Roma Tomatoes")).toBeInTheDocument();
    expect(screen.getByText("Stockout")).toBeInTheDocument();
    expect(screen.getByText("Critical")).toBeInTheDocument();
    expect(screen.getByText("2026-01-02")).toBeInTheDocument();
  });

  it("renders a spoilage row with its waste cost and severity text", () => {
    render(<RiskTable rows={[SPOILAGE_ROW]} />);

    expect(screen.getByText("Mozzarella")).toBeInTheDocument();
    expect(screen.getByText("Spoilage")).toBeInTheDocument();
    expect(screen.getByText("High")).toBeInTheDocument();
    expect(screen.getByText("₹750")).toBeInTheDocument();
  });

  it("filters out suppressed rows from the rendered table", () => {
    render(<RiskTable rows={[STOCKOUT_ROW, SUPPRESSED_ROW]} />);

    expect(screen.getByText("Roma Tomatoes")).toBeInTheDocument();
    expect(screen.queryByText("Basil")).not.toBeInTheDocument();
  });

  it("renders the empty state when there are no visible rows", () => {
    render(<RiskTable rows={[]} />);

    expect(screen.getByText(/no ingredients currently at risk/i)).toBeInTheDocument();
  });

  it("renders the empty state when every row is suppressed", () => {
    render(<RiskTable rows={[SUPPRESSED_ROW]} />);

    expect(screen.getByText(/no ingredients currently at risk/i)).toBeInTheDocument();
  });

  it("preserves the backend-provided order (interleaved severity ranking)", () => {
    render(<RiskTable rows={[SPOILAGE_ROW, STOCKOUT_ROW]} />);

    const cells = screen
      .getAllByRole("row")
      .slice(1)
      .map((row) => row.textContent);
    expect(cells[0]).toContain("Mozzarella");
    expect(cells[1]).toContain("Roma Tomatoes");
  });
});
