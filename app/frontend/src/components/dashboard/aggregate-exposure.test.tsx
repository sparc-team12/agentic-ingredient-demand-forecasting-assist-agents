// ACRI-58 US-023: `AggregateExposure` renders the INR-formatted total,
// including a ₹0 total (the empty-dashboard case).
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { AggregateExposure } from "@/components/dashboard/aggregate-exposure";

describe("AggregateExposure", () => {
  it("renders the formatted INR total", () => {
    render(<AggregateExposure totalWasteExposureInr={7550} />);

    expect(screen.getByText("₹7,550")).toBeInTheDocument();
  });

  it("renders a ₹0 total for the empty-dashboard case", () => {
    render(<AggregateExposure totalWasteExposureInr={0} />);

    expect(screen.getByText("₹0")).toBeInTheDocument();
  });
});
