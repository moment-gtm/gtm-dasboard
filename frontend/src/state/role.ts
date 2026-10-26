/** Mock Entra ID persona (NFR-04/05 stand-in). The role scopes every API call via RLS. */
import { create } from "zustand";
import { createJSONStorage, persist } from "zustand/middleware";

interface RoleState {
  role: string;
  setRole: (role: string) => void;
}

export const useRoleStore = create<RoleState>()(
  persist(
    (set) => ({
      role: "gtm_lead",
      setRole: (role) => set({ role }),
    }),
    { name: "gtm-role", storage: createJSONStorage(() => sessionStorage) },
  ),
);

export function useRole(): string {
  return useRoleStore((s) => s.role);
}

/** Non-hook accessor for the API client. */
export function currentRole(): string {
  return useRoleStore.getState().role;
}
