/** Mirrors backend/app/schemas/common.py — change both together. */

export type StatusValue = "on_track" | "watch" | "off_track";
export type Unit = "usd" | "x" | "pct" | "days" | "count";

export interface PeriodInfo {
  kind: "fytd" | "quarter" | "qtd" | "custom";
  start: string;
  end: string;
  label: string;
  fiscal_year: number;
}

export interface SparkPoint {
  label: string;
  value: number | null;
  partial: boolean;
}

export interface MetricResult {
  metric_id: string;
  name: string;
  unit: Unit;
  value: number | null;
  target: number | null;
  target_prorated: boolean;
  target_basis: string | null;
  goal: number | null;
  goal_label: string | null;
  attainment: number | null;
  status: StatusValue | null;
  status_basis: string | null;
  breakdown: Record<string, unknown>[];
  sparkline: SparkPoint[];
  narrative: string | null;
  period: PeriodInfo;
  as_of: string | null;
  sources: string[];
  meta: Record<string, unknown>;
}

export interface AggregatedOther {
  count: number;
  tcv: number;
  note: string;
}

export interface OpportunityRow {
  opportunity_id: string;
  name: string;
  account_id: string;
  account_name: string;
  vertical: string;
  geography: string;
  lead_practice: string;
  primary_platform: string;
  stage: string;
  tcv: number;
  weighted_tcv: number;
  std_probability: number;
  rep_probability: number | null;
  created_date: string;
  close_date: string;
  days_in_stage: number | null;
  offering: string | null;
  offering_class: string;
  lead_source: string;
  partner: string | null;
  owner_name: string;
  flag: string | null;
  crm_url: string;
}

export interface OpportunityPage {
  metric_id: string | null;
  segment: string | null;
  title: string;
  total_count: number;
  total_tcv: number;
  page: number;
  page_size: number;
  rows: OpportunityRow[];
  aggregated_other: AggregatedOther | null;
}

export interface DealsAttention {
  metric: MetricResult;
  rows: OpportunityRow[];
  aggregated_other: AggregatedOther | null;
}

export interface Option {
  value: string;
  label: string;
}

export interface FilterOptions {
  fiscal_year: number;
  today: string;
  current_quarter: string;
  periods: Option[];
  quarters: Option[];
  verticals: Option[];
  practices: Option[];
  platforms: Option[];
  accounts: Option[];
  client_partners: Option[];
  deal_sources: Option[];
  geographies: Option[];
}

export interface MetricMeta {
  metric_id: string;
  name: string;
  definition: string;
  calculation: string;
  sources: { source_id: string; name: string }[];
  owner: string;
  refresh: string;
  dimensions: string[];
  period_sensitive: boolean;
  goal_label: string | null;
  last_refresh: string | null;
}

export interface SourceHealth {
  source_id: string;
  key: string;
  name: string;
  cadence: string;
  last_success: string | null;
  last_attempt: string | null;
  status: "fresh" | "stale" | "failed";
  rows: number;
  message: string | null;
}

export interface Health {
  status: "ok" | "degraded";
  as_of_date: string;
  built_at: string;
  stale: boolean;
  sources: SourceHealth[];
}

export interface Persona {
  role: string;
  label: string;
  name: string;
  upn: string;
  scope: string;
  scope_detail: string;
  modules: string[];
  restricted: boolean;
  default_view: string;
}

export interface Threshold {
  metric_id: string;
  direction: "higher" | "lower";
  on_track: number;
  watch: number;
  unit: string;
  label: string;
}
