/** Partners API client (FR-PAR-01..03, PAR-01..03). */
import type { Filters } from "@/state/filters";
import { api } from "./client";
import type { MetricResult } from "./types";

export const partnersApi = {
  pipeline: (f: Filters) => api.get<MetricResult>("/api/partners/pipeline", f),
  coSell: (f: Filters) => api.get<MetricResult>("/api/partners/co-sell", f),
  certifications: (f: Filters) => api.get<MetricResult>("/api/partners/certifications", f),
};
