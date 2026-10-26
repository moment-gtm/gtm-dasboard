/** Drill-down request shared by every widget (FR-GEN-06). One DrilldownPanel per view reads it. */
import { create } from "zustand";

export interface DrilldownRequest {
  metricId: string | null;
  segment: string | null;
  title: string;
}

interface DrilldownState {
  request: DrilldownRequest | null;
  open: (req: DrilldownRequest) => void;
  close: () => void;
}

export const useDrilldown = create<DrilldownState>()((set) => ({
  request: null,
  open: (request) => set({ request }),
  close: () => set({ request: null }),
}));
