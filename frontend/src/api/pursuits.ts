import type { Filters } from "@/state/filters";
import { api } from "./client";
import type { MetricResult } from "./types";

export const pursuitsApi = {
  winRate: (f: Filters) => api.get<MetricResult>("/api/pursuits/win-rate", f),
  lossReasons: (f: Filters) => api.get<MetricResult>("/api/pursuits/loss-reasons", f),
  sourceMix: (f: Filters) => api.get<MetricResult>("/api/pursuits/source-mix", f),
  bidDiscipline: (f: Filters) => api.get<MetricResult>("/api/pursuits/bid-discipline", f),
  oralsConversion: (f: Filters) => api.get<MetricResult>("/api/pursuits/orals-conversion", f),
  margin: (f: Filters) => api.get<MetricResult>("/api/pursuits/margin", f),
};
