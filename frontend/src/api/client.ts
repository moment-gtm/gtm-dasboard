/** Typed fetch wrapper: base URL, mock-role auth header, error normalisation. */
import { filtersToParams, type Filters } from "@/state/filters";
import { currentAuthToken } from "@/state/auth";
import { currentRole } from "@/state/role";
import { ApiError } from "@/api/errors";
import { mockDownloadUrl, mockRequest } from "@/mocks/api";

export { ApiError } from "@/api/errors";

const BASE = (import.meta.env.VITE_API_BASE_URL as string | undefined) ?? "";
const USE_MOCK_DATA = import.meta.env.VITE_DATA_MODE !== "api";

type Query = Record<string, string | number | undefined | null>;

export function buildUrl(path: string, filters?: Filters, extra: Query = {}): string {
  const params = filters ? filtersToParams(filters) : new URLSearchParams();
  for (const [k, v] of Object.entries(extra)) {
    if (v !== undefined && v !== null && v !== "") params.set(k, String(v));
  }
  const qs = params.toString();
  return `${BASE}${path}${qs ? `?${qs}` : ""}`;
}

async function request<T>(url: string, init: RequestInit = {}): Promise<T> {
  const token = currentAuthToken();
  if (USE_MOCK_DATA) {
    return mockRequest<T>({
      url,
      method: init.method ?? "GET",
      body: init.body,
      headers: {
        ...init.headers,
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        "X-Mock-Role": currentRole(),
      },
    });
  }

  let res: Response;
  const authHeaders: Record<string, string> = {};
  if (token) {
    authHeaders["Authorization"] = `Bearer ${token}`;
  }
  try {
    res = await fetch(url, {
      ...init,
      headers: {
        Accept: "application/json",
        "X-Mock-Role": currentRole(),
        ...authHeaders,
        ...(init.body ? { "Content-Type": "application/json" } : {}),
        ...init.headers,
      },
    });
  } catch {
    throw new ApiError(
      0,
      "The dashboard API could not be reached. Check that the backend is running.",
    );
  }
  if (!res.ok) {
    let detail = res.statusText || "Request failed";
    try {
      const body = (await res.json()) as { detail?: unknown };
      if (typeof body.detail === "string") detail = body.detail;
    } catch {
      /* non-JSON body */
    }
    throw new ApiError(res.status, detail);
  }
  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

export const api = {
  get<T>(path: string, filters?: Filters, extra?: Query): Promise<T> {
    return request<T>(buildUrl(path, filters, extra));
  },
  post<T>(path: string, body: unknown): Promise<T> {
    return request<T>(`${BASE}${path}`, { method: "POST", body: JSON.stringify(body) });
  },
  put<T>(path: string, body: unknown): Promise<T> {
    return request<T>(`${BASE}${path}`, { method: "PUT", body: JSON.stringify(body) });
  },
  /** URL for a file download opened via <a href> (role travels as a query param). */
  downloadUrl(path: string, filters?: Filters, extra: Query = {}): string {
    if (USE_MOCK_DATA) {
      return mockDownloadUrl(path, extra);
    }
    return buildUrl(path, filters, { ...extra, role: currentRole() });
  },
};
