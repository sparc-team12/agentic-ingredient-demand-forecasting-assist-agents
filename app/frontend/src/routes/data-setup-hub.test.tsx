// ACRI-59 AC1/AC2: loading/error/data states for the Data Setup hub;
// loaded vs not-loaded visibly distinguished per category; the
// all-4-loaded state; each card links to its screen.
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

import { apiClient, ApiError } from "@/lib/api-client";
import type { DataSetupStatus } from "@/lib/data-setup-api";
import DataSetupHubRoute from "@/routes/data-setup-hub";

vi.mock("@/lib/api-client", () => ({
  apiClient: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
  },
  ApiError: class ApiError extends Error {
    status: number;
    detail: string;
    constructor(status: number, detail: string) {
      super(detail);
      this.status = status;
      this.detail = detail;
    }
  },
}));

const PARTIAL_STATUS: DataSetupStatus = {
  categories: [
    {
      id: "menu-recipe",
      label: "Menu & Recipe Setup",
      path: "/data-setup/menu-recipe-setup",
      loaded: true,
    },
    {
      id: "ingredients-suppliers",
      label: "Ingredients & Suppliers Setup",
      path: "/data-setup/ingredients-suppliers",
      loaded: false,
    },
    {
      id: "current-stock",
      label: "Current Stock Setup",
      path: "/data-setup/current-stock-setup",
      loaded: false,
    },
    {
      id: "sales-history",
      label: "Sales History Import",
      path: "/data-setup/sales-history-import",
      loaded: false,
    },
  ],
  all_loaded: false,
};

const ALL_LOADED_STATUS: DataSetupStatus = {
  categories: PARTIAL_STATUS.categories.map((category) => ({ ...category, loaded: true })),
  all_loaded: true,
};

function renderHub() {
  return render(
    <MemoryRouter>
      <DataSetupHubRoute />
    </MemoryRouter>,
  );
}

describe("DataSetupHubRoute", () => {
  it("renders a loading state before the fetch resolves", () => {
    vi.mocked(apiClient.get).mockReturnValue(new Promise(() => {}));

    renderHub();

    expect(screen.getByText(/loading/i)).toBeInTheDocument();
  });

  it("renders all 4 categories with loaded/not-loaded visibly distinguished (AC1)", async () => {
    vi.mocked(apiClient.get).mockResolvedValue(PARTIAL_STATUS);

    renderHub();

    await screen.findByRole("heading", { name: "Menu & Recipe Setup" });
    expect(
      screen.getByRole("heading", { name: "Ingredients & Suppliers Setup" }),
    ).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Current Stock Setup" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Sales History Import" })).toBeInTheDocument();
    expect(screen.getAllByText("Not loaded")).toHaveLength(3);
    expect(screen.getByText("Loaded")).toBeInTheDocument();
  });

  it("does not show the all-loaded message when not every category is loaded", async () => {
    vi.mocked(apiClient.get).mockResolvedValue(PARTIAL_STATUS);

    renderHub();

    await screen.findByRole("heading", { name: "Menu & Recipe Setup" });
    expect(screen.queryByText(/all 4 data categories are loaded/i)).not.toBeInTheDocument();
  });

  it("shows the all-loaded message once every category is loaded (AC2)", async () => {
    vi.mocked(apiClient.get).mockResolvedValue(ALL_LOADED_STATUS);

    renderHub();

    expect(await screen.findByText(/all 4 data categories are loaded/i)).toBeInTheDocument();
  });

  it("links each card to its own screen", async () => {
    vi.mocked(apiClient.get).mockResolvedValue(PARTIAL_STATUS);

    renderHub();

    await screen.findByRole("heading", { name: "Menu & Recipe Setup" });
    const links = screen.getAllByRole("link");
    const hrefs = links.map((link) => link.getAttribute("href"));
    expect(hrefs).toContain("/data-setup/menu-recipe-setup");
    expect(hrefs).toContain("/data-setup/ingredients-suppliers");
    expect(hrefs).toContain("/data-setup/current-stock-setup");
    expect(hrefs).toContain("/data-setup/sales-history-import");
  });

  it("renders a visible error message if getDataSetupStatus rejects", async () => {
    vi.mocked(apiClient.get).mockRejectedValue(new ApiError(401, "Not authenticated"));

    renderHub();

    expect(await screen.findByRole("alert")).toHaveTextContent("Not authenticated");
  });
});
