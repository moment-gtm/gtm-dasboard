/** Solutions Capacity API client (Step 6). CAP-03 is restricted: non-restricted roles get 403. */
import type { Filters } from "@/state/filters";
import { api } from "./client";
import type { MetricResult } from "./types";

export const capacityApi = {
  architectLoad: (f: Filters) => api.get<MetricResult>("/api/capacity/architect-load", f),
  rfpTurnaround: (f: Filters) => api.get<MetricResult>("/api/capacity/rfp-turnaround", f),
  costOfSale: (f: Filters) => api.get<MetricResult>("/api/capacity/cost-of-sale", f),
  qualityScores: (f: Filters) => api.get<MetricResult>("/api/capacity/quality-scores", f),
};
