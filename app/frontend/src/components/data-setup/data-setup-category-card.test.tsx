// ACRI-59 AC1: `DataSetupCategoryCard` renders the category label, a
// visibly distinguished loaded/not-loaded status, and a link to its path.
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";

import { DataSetupCategoryCard } from "@/components/data-setup/data-setup-category-card";
import type { DataSetupCategoryStatus } from "@/lib/data-setup-api";

function renderCard(category: DataSetupCategoryStatus) {
  return render(
    <MemoryRouter>
      <DataSetupCategoryCard category={category} />
    </MemoryRouter>,
  );
}

describe("DataSetupCategoryCard", () => {
  it("renders the not-loaded badge and a link to the category's screen when not loaded", () => {
    renderCard({
      id: "menu-recipe",
      label: "Menu & Recipe Setup",
      path: "/data-setup/menu-recipe-setup",
      loaded: false,
    });

    expect(screen.getByRole("heading", { name: "Menu & Recipe Setup" })).toBeInTheDocument();
    expect(screen.getByText("Not loaded")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /load data/i })).toHaveAttribute(
      "href",
      "/data-setup/menu-recipe-setup",
    );
  });

  it("renders the loaded status and a link to view/edit when loaded", () => {
    renderCard({
      id: "menu-recipe",
      label: "Menu & Recipe Setup",
      path: "/data-setup/menu-recipe-setup",
      loaded: true,
    });

    expect(screen.getByText("Loaded")).toBeInTheDocument();
    expect(screen.queryByText("Not loaded")).not.toBeInTheDocument();
    expect(screen.getByRole("link", { name: /view \/ edit/i })).toHaveAttribute(
      "href",
      "/data-setup/menu-recipe-setup",
    );
  });
});
