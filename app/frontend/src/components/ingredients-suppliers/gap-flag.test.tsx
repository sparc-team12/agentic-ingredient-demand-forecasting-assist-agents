// ACRI-61: `GapFlag` renders its text when `when` is true, and renders
// nothing when `when` is false.
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { GapFlag } from "@/components/ingredients-suppliers/gap-flag";

describe("GapFlag", () => {
  it("renders the flag text when `when` is true", () => {
    render(<GapFlag when={true} text="No supplier mapped" />);

    expect(screen.getByText("No supplier mapped")).toBeInTheDocument();
  });

  it("renders nothing when `when` is false", () => {
    const { container } = render(<GapFlag when={false} text="No supplier mapped" />);

    expect(container).toBeEmptyDOMElement();
  });

  it("uses an accessible, non-color-only alert role so it isn't missed by a screen reader", () => {
    render(<GapFlag when={true} text="Safety margin not set" />);

    expect(screen.getByRole("alert")).toHaveTextContent("Safety margin not set");
  });
});
