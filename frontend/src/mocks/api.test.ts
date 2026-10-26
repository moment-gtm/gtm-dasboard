import { afterEach, describe, expect, it, vi } from "vitest";
import { api } from "@/api/client";
import { ApiError } from "@/api/errors";
import { useAuthStore, type AuthUser } from "@/state/auth";
import { useRoleStore } from "@/state/role";

describe("frontend synthetic API", () => {
  afterEach(() => {
    sessionStorage.clear();
    localStorage.clear();
    useAuthStore.getState().clearAuth();
    useRoleStore.getState().setRole("gtm_lead");
    vi.restoreAllMocks();
  });

  it("serves dashboard metrics without making a network request", async () => {
    const fetch = vi.spyOn(globalThis, "fetch");
    const result = await api.get<{ metric_id: string }>("/api/executive/runway");

    expect(result.metric_id).toBe("EXE-07");
    expect(fetch).not.toHaveBeenCalled();
  });

  it("authenticates a synthetic persona and keeps the session in this browser", async () => {
    const login = await api.post<{ access_token: string; user: AuthUser }>(
      "/api/auth/entra/login",
      { upn: "jordan.avery@moment.example", password: "Moment#2026$Jordan!GTM" },
    );
    useAuthStore.getState().setAuth(login.access_token, login.user);

    await expect(api.get<{ upn: string }>("/api/auth/me")).resolves.toMatchObject({
      upn: "jordan.avery@moment.example",
    });
  });

  it("authenticates the shared synthetic demo account as the GTM lead persona", async () => {
    const login = await api.post<{ access_token: string; user: AuthUser }>(
      "/api/auth/entra/login",
      { upn: "gtm-user", password: "gtm-tower" },
    );

    expect(login.user).toMatchObject({
      username: "jordan.avery",
      upn: "jordan.avery@moment.example",
      role: "gtm_lead",
    });
  });

  it("rejects invalid credentials and unknown fixture routes explicitly", async () => {
    await expect(
      api.post("/api/auth/entra/login", {
        upn: "jordan.avery@moment.example",
        password: "incorrect",
      }),
    ).rejects.toMatchObject({ status: 401 });
    await expect(api.get("/api/unknown")).rejects.toBeInstanceOf(ApiError);
  });

  it("filters and paginates the bundled opportunity register", async () => {
    const firstPage = await api.get<{
      total_count: number;
      rows: { name: string }[];
    }>("/api/opportunities", undefined, { page: 1, page_size: 5 });
    const search = await api.get<{ total_count: number; rows: { name: string }[] }>(
      "/api/opportunities",
      undefined,
      { search: firstPage.rows[0].name, page: 1, page_size: 5 },
    );

    expect(firstPage.total_count).toBeGreaterThan(50);
    expect(firstPage.rows).toHaveLength(5);
    expect(search.rows.every((row) => row.name.includes(firstPage.rows[0].name))).toBe(true);
  });
});
