/** Typed fetch wrapper: base URL, mock-role auth header, error normalisation. */
import { filtersToParams, type Filters } from "@/state/filters";
import { currentAuthToken } from "@/state/auth";
import { currentRole } from "@/state/role";

const BASE = (import.meta.env.VITE_API_BASE_URL as string | undefined) ?? "";

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

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
  let res: Response;
  const token = currentAuthToken();
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
  downloadUrl(path: string, filters: Filters, extra: Query = {}): string {
    return buildUrl(path, filters, { ...extra, role: currentRole() });
  },
};
