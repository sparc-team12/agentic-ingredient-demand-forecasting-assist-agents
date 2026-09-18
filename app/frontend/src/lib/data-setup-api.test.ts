// Request shape / error-propagation behavior of the data-setup-api
// function (ACRI-59), mirroring `ingredients-api.test.ts`'s pattern.
import { describe, expect, it, vi } from "vitest";

import { ApiError, apiClient } from "@/lib/api-client";
import { getDataSetupStatus } from "@/lib/data-setup-api";

vi.mock("@/lib/api-client", () => {
  class MockApiError extends Error {
    status: number;
    detail: string;
    constructor(status: number, detail: string) {
      super(detail);
      this.status = status;
      this.detail = detail;
    }
  }
  return {
    apiClient: {
      get: vi.fn(),
      post: vi.fn(),
      put: vi.fn(),
    },
    ApiError: MockApiError,
  };
});

describe("data-setup-api", () => {
  it("getDataSetupStatus calls apiClient.get with /data-setup/status", async () => {
    vi.mocked(apiClient.get).mockResolvedValue({ categories: [], all_loaded: false });

    await getDataSetupStatus();

    expect(apiClient.get).toHaveBeenCalledWith("/data-setup/status");
  });

  it("propagates an ApiError unchanged when the underlying apiClient call rejects", async () => {
    vi.mocked(apiClient.get).mockRejectedValue(new ApiError(401, "Not authenticated"));

    await expect(getDataSetupStatus()).rejects.toMatchObject({
      status: 401,
      detail: "Not authenticated",
    });
  });
});
