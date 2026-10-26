import type { Filters } from "@/state/filters";
import { api } from "./client";
import type { DealsAttention, MetricResult, OpportunityPage } from "./types";

export const executiveApi = {
  runway: (f: Filters) => api.get<MetricResult>("/api/executive/runway", f),
  kpis: (f: Filters) => api.get<MetricResult[]>("/api/executive/kpis", f),
  bookingsByQuarter: (f: Filters) => api.get<MetricResult>("/api/executive/bookings-by-quarter", f),
  pipelineByVertical: (f: Filters) =>
    api.get<MetricResult>("/api/executive/pipeline-by-vertical", f),
  dealsAttention: (f: Filters) => api.get<DealsAttention>("/api/executive/deals-attention", f),
};

export interface OpportunityQuery {
  metricId?: string | null;
  segment?: string | null;
  sort?: string;
  order?: "asc" | "desc";
  search?: string;
  page?: number;
  pageSize?: number;
}

export function fetchOpportunities(f: Filters, q: OpportunityQuery): Promise<OpportunityPage> {
  return api.get<OpportunityPage>("/api/opportunities", f, {
    metric_id: q.metricId,
    segment: q.segment,
    sort: q.sort,
    order: q.order,
    search: q.search,
    page: q.page,
    page_size: q.pageSize,
  });
}

export function logViewExport(view: string, format: "pdf" | "pptx" = "pdf"): Promise<void> {
  return api.post<void>("/api/exports/view", { view, format });
}
