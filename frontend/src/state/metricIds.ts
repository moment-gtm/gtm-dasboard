/** Global toggle for showing metric IDs and inline source badges across all widgets (FR-GEN-07). */
import { create } from "zustand";
import { createJSONStorage, persist } from "zustand/middleware";

interface MetricIdsState {
  showMetricIds: boolean;
  setShowMetricIds: (show: boolean) => void;
  toggleMetricIds: () => void;
}

export const useMetricIdsStore = create<MetricIdsState>()(
  persist(
    (set) => ({
      showMetricIds: false,
      setShowMetricIds: (showMetricIds) => set({ showMetricIds }),
      toggleMetricIds: () => set((s) => ({ showMetricIds: !s.showMetricIds })),
    }),
    { name: "gtm-metric-ids", storage: createJSONStorage(() => sessionStorage) },
  ),
);

export function useShowMetricIds(): boolean {
  return useMetricIdsStore((s) => s.showMetricIds);
}
