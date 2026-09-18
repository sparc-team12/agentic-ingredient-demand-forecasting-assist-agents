// Thin fetch wrapper for the FastAPI backend (ACRI-66).
//
// Always sends `credentials: 'include'` so the httpOnly session cookie set
// by `POST /auth/login` is sent on every subsequent request (session
// bootstrap, protected screen fetches, logout). Base URL comes from
// `import.meta.env.VITE_API_URL` (Vite env, not `process.env`).

const BASE_URL = import.meta.env.VITE_API_URL;

export class ApiError extends Error {
  readonly status: number;
  readonly detail: string;

  constructor(status: number, detail: string) {
    super(detail);
    this.name = "ApiError";
    this.status = status;
    this.detail = detail;
  }
}

async function request<TResponse>(path: string, init?: RequestInit): Promise<TResponse> {
  const response = await fetch(`${BASE_URL}${path}`, {
    ...init,
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
  });

  if (!response.ok) {
    let detail = response.statusText || "Request failed";
    try {
      const body = (await response.json()) as { detail?: unknown };
      // FastAPI's 422 validation-error responses send `detail` as an array
      // of {loc, msg, type} objects, not a string — normalize to a
      // readable string so callers (and React) never receive a raw
      // object/array here.
      if (typeof body?.detail === "string") {
        detail = body.detail;
      } else if (Array.isArray(body?.detail)) {
        detail = body.detail
          .map((item) => (item && typeof item === "object" && "msg" in item ? String((item as { msg: unknown }).msg) : String(item)))
          .join("; ");
      } else if (body?.detail != null) {
        detail = String(body.detail);
      }
    } catch {
      // Response body wasn't JSON (or was empty) — fall back to statusText.
    }
    throw new ApiError(response.status, detail);
  }

  if (response.status === 204) {
    return undefined as TResponse;
  }

  return (await response.json()) as TResponse;
}

export const apiClient = {
  get: <TResponse>(path: string) => request<TResponse>(path, { method: "GET" }),
  post: <TResponse>(path: string, body?: unknown) =>
    request<TResponse>(path, {
      method: "POST",
      body: body === undefined ? undefined : JSON.stringify(body),
    }),
  // Additive (ACRI-61) — `get`/`post` call sites and behavior are
  // unaffected. Used by the Ingredients & Suppliers Setup screen's edit
  // flows, which are full-replace (the client always sends the complete,
  // pre-filled current object; see `ingredients-api.ts`).
  put: <TResponse>(path: string, body?: unknown) =>
    request<TResponse>(path, {
      method: "PUT",
      body: body === undefined ? undefined : JSON.stringify(body),
    }),
};
