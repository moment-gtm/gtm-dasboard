import { api } from "./client";
import type { AuthUser } from "@/state/auth";

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user: AuthUser;
}

export interface EntraPersona {
  upn: string;
  username: string;
  name: string;
  email: string;
  role: string;
  role_label: string;
  job_title: string;
  group_name: string;
  scope_type: string;
  scope_value?: string | null;
  description: string;
}

export const authApi = {
  getPersonas: (): Promise<EntraPersona[]> => {
    return api.get<EntraPersona[]>("/api/auth/entra/personas");
  },
  loginWithEntra: (upn: string, password?: string): Promise<LoginResponse> => {
    const payload: { upn: string; password?: string } = { upn: upn.trim() };
    if (password && password.trim()) {
      payload.password = password.trim();
    }
    return api.post<LoginResponse>("/api/auth/entra/login", payload);
  },
  login: (username: string, password?: string): Promise<LoginResponse> => {
    return api.post<LoginResponse>("/api/auth/login", { username, password });
  },
  me: (): Promise<AuthUser> => {
    return api.get<AuthUser>("/api/auth/me");
  },
  logout: (): Promise<{ message: string }> => {
    return api.post<{ message: string }>("/api/auth/logout", {});
  },
};
