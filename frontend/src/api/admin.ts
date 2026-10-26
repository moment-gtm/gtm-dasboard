/** Administration API client (FR-ADM-01..04, change control). */
import { api } from "@/api/client";
import { currentRole } from "@/state/role";
import type { MetricResult } from "@/api/types";

export interface TargetVersion {
  version: string;
  fiscal_year: number;
  created_at: string;
  total_usd: number;
  source: "planning" | "admin";
  note: string | null;
  created_by: string | null;
  active: boolean;
}
export interface TargetCell {
  fiscal_year: number;
  quarter: number;
  practice: string;
  amount_usd: number;
  version: string;
}
export interface TargetsResponse {
  active: { fiscal_year: number; version: string; total_usd: number }[];
  versions: TargetVersion[];
  practices: string[];
  grid: TargetCell[];
}
export interface ThresholdRow {
  metric_id: string;
  name: string;
  direction: "higher" | "lower";
  on_track: number;
  watch: number;
  unit: string;
  label: string;
  version: number;
  reason: string | null;
  changed_by: string | null;
}
export interface ThresholdHistory {
  version: number;
  on_track: number;
  watch: number;
  reason: string;
  changed_by: string;
  changed_at: string;
}
export interface ReferenceSummary {
  key: string;
  label: string;
  description: string;
  editable: boolean;
  count: number;
  version: number;
}
export interface ReferenceSet extends ReferenceSummary {
  values: (string | Record<string, string | number | boolean | null>)[];
  history: { version: number; reason: string; changed_by: string; changed_at: string }[];
}
export interface DqRule {
  rule_id: string;
  name: string;
  description: string;
  handling: string;
  severity: "high" | "medium" | "low";
  active: boolean;
  inactive_reason: string | null;
  records: number;
}
export interface CompletenessWeek {
  week_start: string;
  week_end: string;
  qualified: number;
  complete: number;
  completeness: number | null;
}
export interface DqSummary {
  rules: DqRule[];
  by_owner: { owner: string; records: number }[];
  completeness: CompletenessWeek[];
  gate: { met: boolean; required: number; weeks: number; latest: CompletenessWeek[] };
}
export interface DqFinding {
  rule_id: string;
  severity: string;
  record_type: string;
  record_id: string;
  detail: string;
  owner: string;
  handling: string;
  detected_at: string;
}
export interface DqFindingsPage {
  total: number;
  page: number;
  page_size: number;
  rows: DqFinding[];
}
export interface ChangeRequest {
  id: number;
  metric_id: string | null;
  title: string;
  description: string;
  requested_by: string;
  status: "logged" | "assessed" | "approved" | "rejected" | "released";
  assessments: { role: string; by: string; note: string; at: string }[];
  decision_by: string | null;
  decision_note: string | null;
  release_window: string | null;
  created_at: string;
}
export interface AuditEntry {
  ts: string;
  upn: string | null;
  role: string | null;
  action: string;
  resource: string;
  status: number;
  detail: Record<string, unknown> | null;
}

export interface AlertRuleDeal {
  opportunity_id: string;
  deal_name: string;
  account_name: string;
  lead_practice: string;
  stage: string;
  tcv: number;
  close_date: string;
  days_in_stage?: number;
  is_stalled?: boolean;
  ai_validated?: boolean;
}

export interface AlertRuleRow {
  rule_id: string;
  name: string;
  description: string;
  metric_id: string;
  kind: "coverage_drop" | "large_deal_slip" | "unvalidated_ai_propose" | "metric_threshold";
  operator: "lt" | "lte" | "gt" | "gte" | "eq";
  threshold: number;
  threshold_label: string;
  unit: string;
  severity: "critical" | "warning";
  channels: ("email" | "teams")[];
  enabled: boolean;
  triggered: boolean;
  status: "on_track" | "watch" | "off_track" | "neutral";
  observed_value: number | null;
  observed_label: string;
  summary: string;
  matching_deals: AlertRuleDeal[];
  deep_link: string;
  subscription: { email: boolean; teams: boolean };
  updated_by?: string;
  updated_at?: string;
}

export interface AlertRulesResponse {
  rules: AlertRuleRow[];
  triggered_count: number;
  can_manage: boolean;
}

export interface AlertRuleInput {
  rule_id?: string;
  name: string;
  description: string;
  metric_id: string;
  kind?: "coverage_drop" | "large_deal_slip" | "unvalidated_ai_propose" | "metric_threshold";
  operator: "lt" | "lte" | "gt" | "gte" | "eq";
  threshold: number;
  unit: string;
  severity: "critical" | "warning";
  channels: ("email" | "teams")[];
  enabled?: boolean;
}

export interface SubscriptionRow {
  target_id: string;
  target_type: "digest" | "rule";
  name: string;
  description: string;
  metric_id: string;
  severity: string;
  rule_enabled: boolean;
  email: boolean;
  teams: boolean;
}

export interface SubscriptionsResponse {
  upn: string;
  role: string;
  display_name: string;
  subscriptions: SubscriptionRow[];
}

export interface DigestKpiRow {
  metric_id: string;
  label: string;
  value: number | null;
  formatted_value: string;
  goal: number | null;
  formatted_goal: string | null;
  delta_vs_prior: number | null;
  formatted_delta: string | null;
  status: "on_track" | "watch" | "off_track" | "neutral";
  status_basis: string | null;
  deep_link: string;
}

export interface DigestRun {
  id: number;
  sent_at: string;
  triggered_by: string;
  recipient_upn: string;
  recipient_role: string;
  channels: ("email" | "teams")[];
  kpi_count: number;
  stalled_deal_count: number;
  over_capacity_count: number;
  triggered_alert_count: number;
  status: string;
}

export interface DigestSchedule {
  enabled: boolean;
  day_of_week:
    | "Monday"
    | "Tuesday"
    | "Wednesday"
    | "Thursday"
    | "Friday"
    | "Saturday"
    | "Sunday";
  hour_utc: number;
  channels: ("email" | "teams")[];
  updated_by?: string;
  updated_at?: string;
}

export interface DigestResponse {
  generated_at: string;
  as_of_date: string;
  recipient: {
    upn: string;
    display_name: string;
    role: string;
    role_label: string;
    practice: string | null;
    subscription: { email: boolean; teams: boolean };
  };
  schedule: DigestSchedule;
  kpis: DigestKpiRow[];
  stalled_deals: {
    metric_id: string;
    total_count: number;
    total_tcv: number;
    formatted_tcv: string;
    deals: AlertRuleDeal[];
    deep_link: string;
  };
  over_capacity_architects: {
    metric_id: string;
    over_count: number;
    stretched_count: number;
    healthy_count: number;
    narrative: string | null;
    architects: {
      resource_id: string;
      architect: string;
      practice?: string;
      open_pursuits: number;
      tcv: number;
      band: string;
    }[];
    deep_link: string;
  };
  triggered_alerts: {
    rule_id: string;
    name: string;
    metric_id: string;
    severity: string;
    summary: string;
    deep_link: string;
  }[];
  dashboard_links: { label: string; module: string; path: string }[];
  email_preview: { to: string; subject: string; body_markdown: string };
  teams_preview: {
    channel: string;
    title: string;
    summary: string;
    facts: { name: string; value: string }[];
    actions: { label: string; module: string; path: string }[];
  };
  history: DigestRun[];
}

export interface DigestDispatchResponse {
  dispatched: number;
  runs: DigestRun[];
  digest: DigestResponse;
}

const A = "/api/admin";
const ALR = "/api/alerts";
const enc = encodeURIComponent;

export const adminApi = {
  targets: () => api.get<TargetsResponse>(`${A}/targets`),
  createTarget: (body: {
    fiscal_year: number;
    note: string;
    rows: { quarter: number; practice: string; amount_usd: number }[];
  }) => api.post<{ version: string }>(`${A}/targets`, body),
  thresholds: () => api.get<ThresholdRow[]>(`${A}/thresholds`),
  editThreshold: (id: string, body: { on_track: number; watch: number; reason: string }) =>
    api.put<ThresholdRow>(`${A}/thresholds/${enc(id)}`, body),
  thresholdHistory: (id: string) =>
    api.get<ThresholdHistory[]>(`${A}/thresholds/${enc(id)}/history`),
  references: () => api.get<ReferenceSummary[]>(`${A}/reference`),
  referenceSet: (key: string) => api.get<ReferenceSet>(`${A}/reference/${enc(key)}`),
  editReference: (key: string, body: { values: unknown[]; reason: string }) =>
    api.put<{ key: string; version: number }>(`${A}/reference/${enc(key)}`, body),
  dq: () => api.get<DqSummary>(`${A}/dq`),
  completeness: () => api.get<MetricResult>(`${A}/dq/completeness`),
  findings: (q: { rule_id?: string; owner?: string; q?: string; page: number }) =>
    api.get<DqFindingsPage>(`${A}/dq/findings`, undefined, { ...q, page_size: 10 }),
  exportUrl: (rule_id?: string) =>
    api.downloadUrl(`${A}/dq/export`, undefined, { rule_id, role: currentRole() }),
  changeRequests: () => api.get<ChangeRequest[]>(`${A}/change-requests`),
  logChange: (body: { metric_id?: string | null; title: string; description: string }) =>
    api.post<ChangeRequest>(`${A}/change-requests`, body),
  assess: (id: number, note: string) =>
    api.post<ChangeRequest>(`${A}/change-requests/${id}/assess`, { note }),
  decide: (id: number, decision: "approve" | "reject", note: string) =>
    api.post<ChangeRequest>(`${A}/change-requests/${id}/decide`, { decision, note }),
  release: (id: number) => api.post<ChangeRequest>(`${A}/change-requests/${id}/release`, {}),
  audit: () => api.get<AuditEntry[]>(`${A}/audit`),
  alertRules: () => api.get<AlertRulesResponse>(`${ALR}/rules`),
  createAlertRule: (body: AlertRuleInput) => api.post<AlertRuleRow>(`${ALR}/rules`, body),
  updateAlertRule: (id: string, body: AlertRuleInput) =>
    api.put<AlertRuleRow>(`${ALR}/rules/${enc(id)}`, body),
  subscriptions: () => api.get<SubscriptionsResponse>(`${ALR}/subscriptions`),
  updateSubscriptions: (
    subscriptions: { target_id: string; email: boolean; teams: boolean }[],
  ) => api.put<SubscriptionsResponse>(`${ALR}/subscriptions`, { subscriptions }),
  digest: (preview_role?: string) =>
    api.get<DigestResponse>(
      `${ALR}/digest`,
      undefined,
      preview_role ? { preview_role } : undefined,
    ),
  updateDigestSchedule: (body: {
    enabled: boolean;
    day_of_week: DigestSchedule["day_of_week"];
    hour_utc: number;
    channels: ("email" | "teams")[];
  }) => api.put<DigestSchedule>(`${ALR}/digest/schedule`, body),
  sendDigest: (body: {
    scope: "self" | "all_subscribed";
    channels?: ("email" | "teams")[];
  }) => api.post<DigestDispatchResponse>(`${ALR}/digest`, body),
};
