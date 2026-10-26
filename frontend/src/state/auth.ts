import { create } from "zustand";
import { createJSONStorage, persist } from "zustand/middleware";
import { useRoleStore } from "./role";

export interface AuthUser {
  username: string;
  upn: string;
  name: string;
  email: string;
  role: string;
  role_label: string;
  job_title?: string;
  group_name?: string;
  scope_type?: string;
  scope_value?: string | null;
  description?: string;
}

interface AuthState {
  token: string | null;
  user: AuthUser | null;
  setAuth: (token: string, user: AuthUser) => void;
  clearAuth: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      token: null,
      user: null,
      setAuth: (token, user) => {
        useRoleStore.getState().setRole(user.role);
        set({ token, user });
      },
      clearAuth: () => set({ token: null, user: null }),
    }),
    {
      name: "gtm-auth",
      storage: createJSONStorage(() => localStorage),
    },
  ),
);

export function currentAuthToken(): string | null {
  return useAuthStore.getState().token;
}

export function currentAuthUser(): AuthUser | null {
  return useAuthStore.getState().user;
}
