/** Accounts API client (FR-ACC-01..05, ACC-01..04). */
import type { Filters } from "@/state/filters";
import { api } from "./client";
import type { MetricResult, OpportunityPage } from "./types";

export const accountsApi = {
  penetration: (f: Filters) => api.get<MetricResult>("/api/accounts/penetration", f),
  whitespace: (f: Filters) => api.get<MetricResult>("/api/accounts/whitespace", f),
  expansion: (f: Filters) => api.get<MetricResult>("/api/accounts/expansion", f),
  planHealth: (f: Filters) => api.get<MetricResult>("/api/accounts/plan-health", f),
  opportunities: (accountId: string, f: Filters) =>
    api.get<OpportunityPage>(`/api/accounts/${encodeURIComponent(accountId)}/opportunities`, f),
};
