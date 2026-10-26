/** Selected account for the account detail panel (FR-ACC-05). */
import { create } from "zustand";

interface AccountDetailState {
  accountId: string | null;
  title: string;
  open: (accountId: string, title: string) => void;
  close: () => void;
}

export const useAccountDetail = create<AccountDetailState>()((set) => ({
  accountId: null,
  title: "",
  open: (accountId, title) => set({ accountId, title }),
  close: () => set({ accountId: null, title: "" }),
}));
