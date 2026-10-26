/** Global filters (FR-GEN-02/03) — persisted for the browser session, shared by every module. */
import { create } from "zustand";
import { createJSONStorage, persist } from "zustand/middleware";

export type PeriodKind = "fytd" | "quarter" | "qtd" | "custom";

export const MULTI_KEYS = [
  "vertical",
  "practice",
  "platform",
  "account",
  "client_partner",
  "deal_source",
  "geography",
] as const;
export type MultiKey = (typeof MULTI_KEYS)[number];

export interface Filters {
  period: PeriodKind;
  quarter: string | null;
  start: string | null;
  end: string | null;
  vertical: string[];
  practice: string[];
  platform: string[];
  account: string[];
  client_partner: string[];
  deal_source: string[];
  geography: string[];
}

export const DEFAULT_FILTERS: Filters = {
  period: "fytd",
  quarter: null,
  start: null,
  end: null,
  vertical: [],
  practice: [],
  platform: [],
  account: [],
  client_partner: [],
  deal_source: [],
  geography: [],
};

interface FilterState extends Filters {
  setPeriod: (
    period: PeriodKind,
    extra?: Partial<Pick<Filters, "quarter" | "start" | "end">>,
  ) => void;
  setMulti: (key: MultiKey, values: string[]) => void;
  clearAll: () => void;
}

export const useFilterStore = create<FilterState>()(
  persist(
    (set) => ({
      ...DEFAULT_FILTERS,
      setPeriod: (period, extra = {}) =>
        set({
          period,
          quarter: period === "quarter" ? (extra.quarter ?? null) : null,
          start: period === "custom" ? (extra.start ?? null) : null,
          end: period === "custom" ? (extra.end ?? null) : null,
        }),
      setMulti: (key, values) => set({ [key]: values } as Partial<FilterState>),
      clearAll: () => set({ ...DEFAULT_FILTERS }),
    }),
    { name: "gtm-filters", storage: createJSONStorage(() => sessionStorage) },
  ),
);

/** Plain, serialisable filter snapshot (used in query keys and URLs). */
export function selectFilters(s: FilterState): Filters {
  return {
    period: s.period,
    quarter: s.quarter,
    start: s.start,
    end: s.end,
    vertical: s.vertical,
    practice: s.practice,
    platform: s.platform,
    account: s.account,
    client_partner: s.client_partner,
    deal_source: s.deal_source,
    geography: s.geography,
  };
}

export function useFilters(): Filters {
  // Select primitives/arrays individually to keep referential stability.
  const period = useFilterStore((s) => s.period);
  const quarter = useFilterStore((s) => s.quarter);
  const start = useFilterStore((s) => s.start);
  const end = useFilterStore((s) => s.end);
  const vertical = useFilterStore((s) => s.vertical);
  const practice = useFilterStore((s) => s.practice);
  const platform = useFilterStore((s) => s.platform);
  const account = useFilterStore((s) => s.account);
  const client_partner = useFilterStore((s) => s.client_partner);
  const deal_source = useFilterStore((s) => s.deal_source);
  const geography = useFilterStore((s) => s.geography);
  return {
    period,
    quarter,
    start,
    end,
    vertical,
    practice,
    platform,
    account,
    client_partner,
    deal_source,
    geography,
  };
}

export function activeFilterCount(f: Filters): number {
  const multi = MULTI_KEYS.reduce((n, k) => n + (f[k].length ? 1 : 0), 0);
  return multi + (f.period !== "fytd" ? 1 : 0);
}

/** Serialise filters to query params; multi-value keys repeat (`?vertical=A&vertical=B`). */
export function filtersToParams(f: Filters, params = new URLSearchParams()): URLSearchParams {
  params.set("period", f.period);
  if (f.period === "quarter" && f.quarter) params.set("quarter", f.quarter);
  if (f.period === "custom") {
    if (f.start) params.set("start", f.start);
    if (f.end) params.set("end", f.end);
  }
  for (const k of MULTI_KEYS) for (const v of f[k]) params.append(k, v);
  return params;
}
