/** Market Signals API client (FR-MKT-01..04, MKT-01..04). */
import type { Filters } from "@/state/filters";
import { api } from "./client";
import type { MetricResult } from "./types";

export const marketApi = {
  thoughtLeadership: (f: Filters) =>
    api.get<MetricResult>("/api/market/thought-leadership", f),
  workshopFunnel: (f: Filters) =>
    api.get<MetricResult>("/api/market/workshop-funnel", f),
  campaignSourced: (f: Filters) =>
    api.get<MetricResult>("/api/market/campaign-sourced", f),
  analystPositioning: (f: Filters) =>
    api.get<MetricResult>("/api/market/analyst-positioning", f),
};
