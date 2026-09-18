// Request/error-handling behavior of the shared fetch wrapper (ACRI-66).
import { afterEach, describe, expect, it, vi } from "vitest";

import { apiClient, ApiError } from "@/lib/api-client";

function mockResponse(options: {
  status: number;
  statusText?: string;
  json?: () => Promise<unknown>;
}): Response {
  const { status, statusText = "", json } = options;
  return {
    ok: status >= 200 && status < 300,
    status,
    statusText,
    json: json ?? (async () => ({})),
  } as Response;
}

describe("apiClient", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("sends credentials: 'include' and a JSON content-type header on GET", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValue(mockResponse({ status: 200, json: async () => ({ status: "ok" }) }));
    vi.stubGlobal("fetch", fetchMock);

    const result = await apiClient.get<{ status: string }>("/health");

    expect(result).toEqual({ status: "ok" });
    const [url, init] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(url).toContain("/health");
    expect(init.credentials).toBe("include");
    expect(init.method).toBe("GET");
    expect((init.headers as Record<string, string>)["Content-Type"]).toBe("application/json");
  });

  it("JSON-stringifies the request body on POST", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValue(mockResponse({ status: 200, json: async () => ({ email: "a@b.com" }) }));
    vi.stubGlobal("fetch", fetchMock);

    await apiClient.post("/auth/login", { email: "a@b.com", password: "secret" });

    const [, init] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(init.method).toBe("POST");
    expect(init.body).toBe(JSON.stringify({ email: "a@b.com", password: "secret" }));
  });

  it("throws an ApiError carrying the backend's detail message on a non-2xx response", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      mockResponse({
        status: 401,
        json: async () => ({ detail: "Invalid email or password" }),
      }),
    );
    vi.stubGlobal("fetch", fetchMock);

    await expect(
      apiClient.post("/auth/login", { email: "a@b.com", password: "wrong" }),
    ).rejects.toMatchObject({ status: 401, detail: "Invalid email or password" });
  });

  it("falls back to statusText when a non-2xx response body isn't JSON", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      mockResponse({
        status: 500,
        statusText: "Internal Server Error",
        json: async () => {
          throw new SyntaxError("not json");
        },
      }),
    );
    vi.stubGlobal("fetch", fetchMock);

    const error = await apiClient.get("/broken").catch((e: unknown) => e);
    expect(error).toBeInstanceOf(ApiError);
    expect((error as ApiError).detail).toBe("Internal Server Error");
  });
});
