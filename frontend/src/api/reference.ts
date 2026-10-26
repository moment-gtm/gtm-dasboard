import { api } from "./client";
import type { FilterOptions, Health, MetricMeta, Persona, Threshold } from "./types";

export const referenceApi = {
  me: () => api.get<Persona>("/api/me"),
  roles: () => api.get<Persona[]>("/api/reference/roles"),
  filters: () => api.get<FilterOptions>("/api/reference/filters"),
  metrics: () => api.get<MetricMeta[]>("/api/reference/metrics"),
  thresholds: () => api.get<Threshold[]>("/api/reference/thresholds"),
  health: () => api.get<Health>("/api/health"),
};
