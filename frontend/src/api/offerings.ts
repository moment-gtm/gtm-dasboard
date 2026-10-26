/** Offerings API client (FR-OFF-01..05, OFF-01..05). */
import type { Filters } from "@/state/filters";
import { api } from "./client";
import type { MetricResult } from "./types";

export const offeringsApi = {
  byOffering: (f: Filters) => api.get<MetricResult>("/api/offerings/by-offering", f),
  attachRate: (f: Filters) => api.get<MetricResult>("/api/offerings/attach-rate", f),
  aiValidation: (f: Filters) => api.get<MetricResult>("/api/offerings/ai-validation", f),
  assetReuse: (f: Filters) => api.get<MetricResult>("/api/offerings/asset-reuse", f),
  assetBuild: (f: Filters) => api.get<MetricResult>("/api/offerings/asset-build", f),
};
