/** FR-ALR-02 — Threshold alert rules evaluated live through the semantic layer and scoped by RLS. */
import { useState } from "react";
import { Link } from "react-router-dom";
import { adminApi, type AlertRuleInput, type AlertRuleRow } from "@/api/admin";
import { Money } from "@/components/common/Money";
import { StatusBadge } from "@/components/common/StatusBadge";
import { WidgetCard } from "@/components/common/WidgetCard";
import { useAdminMutation, useAlertRules } from "@/hooks/useAdminData";
import { Field, FormError, inputStyle } from "./fields";

function EditRuleForm({ row, onClose }: { row: AlertRuleRow; onClose: () => void }) {
  const save = useAdminMutation((b: AlertRuleInput) => adminApi.updateAlertRule(row.rule_id, b));
  const [threshold, setThreshold] = useState(String(row.threshold));
  const [severity, setSeverity] = useState<"critical" | "warning">(row.severity);
  const [enabled, setEnabled] = useState(row.enabled);
  const [email, setEmail] = useState(row.channels.includes("email"));
  const [teams, setTeams] = useState(row.channels.includes("teams"));

  return (
    <form
      aria-label={`Edit alert rule ${row.name}`}
      className="mt-2 flex flex-col gap-2 rounded p-3"
      style={{ border: "1px solid var(--grid)" }}
      data-testid={`alert-rule-edit-form-${row.rule_id}`}
      onSubmit={(e) => {
        e.preventDefault();
        const channels: ("email" | "teams")[] = [];
        if (email) channels.push("email");
        if (teams) channels.push("teams");
        save.mutate(
          {
            rule_id: row.rule_id,
            name: row.name,
            description: row.description,
            metric_id: row.metric_id,
            kind: row.kind,
            operator: row.operator,
            threshold: Number(threshold),
            unit: row.unit,
            severity,
            channels: channels.length ? channels : ["email"],
            enabled,
          },
          { onSuccess: onClose },
        );
      }}
    >
      <div className="flex flex-wrap items-end gap-3">
        <Field label={`Threshold (${row.unit})`}>
          {(id) => (
            <input
              id={id}
              type="number"
              step="any"
              required
              style={{ ...inputStyle, width: 120 }}
              value={threshold}
              onChange={(e) => setThreshold(e.target.value)}
            />
          )}
        </Field>
        <Field label="Severity">
          {(id) => (
            <select
              id={id}
              style={inputStyle}
              value={severity}
              onChange={(e) => setSeverity(e.target.value as "critical" | "warning")}
            >
              <option value="critical">Critical</option>
              <option value="warning">Warning</option>
            </select>
          )}
        </Field>
        <label className="flex items-center gap-1 text-sm">
          <input type="checkbox" checked={email} onChange={(e) => setEmail(e.target.checked)} />
          Email
        </label>
        <label className="flex items-center gap-1 text-sm">
          <input type="checkbox" checked={teams} onChange={(e) => setTeams(e.target.checked)} />
          Teams
        </label>
        <label className="flex items-center gap-1 text-sm">
          <input type="checkbox" checked={enabled} onChange={(e) => setEnabled(e.target.checked)} />
          Enabled
        </label>
        <button
          type="submit"
          className="btn"
          disabled={save.isPending}
          data-testid={`alert-rule-save-${row.rule_id}`}
        >
          Save rule
        </button>
        <button type="button" className="btn" onClick={onClose}>
          Cancel
        </button>
      </div>
      <FormError error={save.error} />
    </form>
  );
}

function CreateRuleForm({ onClose }: { onClose: () => void }) {
  const create = useAdminMutation((b: AlertRuleInput) => adminApi.createAlertRule(b));
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [metricId, setMetricId] = useState("EXE-03");
  const [operator, setOperator] = useState<"lt" | "lte" | "gt" | "gte" | "eq">("lt");
  const [threshold, setThreshold] = useState("0.40");
  const [unit, setUnit] = useState("pct");
  const [severity, setSeverity] = useState<"critical" | "warning">("warning");

  return (
    <form
      aria-label="Create alert rule"
      className="mt-3 flex flex-col gap-2 rounded p-3"
      style={{ border: "1px solid var(--grid)" }}
      data-testid="alert-rule-create-form"
      onSubmit={(e) => {
        e.preventDefault();
        create.mutate(
          {
            name,
            description,
            metric_id: metricId,
            operator,
            threshold: Number(threshold),
            unit,
            severity,
            channels: ["email", "teams"],
            enabled: true,
          },
          { onSuccess: onClose },
        );
      }}
    >
      <div className="flex flex-wrap items-end gap-3">
        <Field label="Rule name">
          {(id) => (
            <input
              id={id}
              required
              minLength={3}
              style={{ ...inputStyle, minWidth: 200 }}
              value={name}
              onChange={(e) => setName(e.target.value)}
            />
          )}
        </Field>
        <Field label="Metric ID">
          {(id) => (
            <select
              id={id}
              style={inputStyle}
              value={metricId}
              onChange={(e) => setMetricId(e.target.value)}
            >
              {["EXE-01", "EXE-02", "EXE-03", "EXE-04", "EXE-05", "MKT-02", "CAP-02", "CAP-03"].map(
                (m) => (
                  <option key={m} value={m}>
                    {m}
                  </option>
                ),
              )}
            </select>
          )}
        </Field>
        <Field label="Operator">
          {(id) => (
            <select
              id={id}
              style={inputStyle}
              value={operator}
              onChange={(e) => setOperator(e.target.value as "lt" | "lte" | "gt" | "gte" | "eq")}
            >
              <option value="lt">&lt; (below)</option>
              <option value="lte">≤ (at or below)</option>
              <option value="gt">&gt; (above)</option>
              <option value="gte">≥ (at or above)</option>
            </select>
          )}
        </Field>
        <Field label="Threshold">
          {(id) => (
            <input
              id={id}
              type="number"
              step="any"
              required
              style={{ ...inputStyle, width: 100 }}
              value={threshold}
              onChange={(e) => setThreshold(e.target.value)}
            />
          )}
        </Field>
        <Field label="Unit">
          {(id) => (
            <select
              id={id}
              style={inputStyle}
              value={unit}
              onChange={(e) => setUnit(e.target.value)}
            >
              <option value="pct">pct</option>
              <option value="x">x</option>
              <option value="usd">usd</option>
              <option value="count">count</option>
            </select>
          )}
        </Field>
        <Field label="Severity">
          {(id) => (
            <select
              id={id}
              style={inputStyle}
              value={severity}
              onChange={(e) => setSeverity(e.target.value as "critical" | "warning")}
            >
              <option value="warning">Warning</option>
              <option value="critical">Critical</option>
            </select>
          )}
        </Field>
      </div>
      <div className="flex flex-wrap items-end gap-3">
        <Field label="Description">
          {(id) => (
            <input
              id={id}
              required
              minLength={3}
              style={{ ...inputStyle, minWidth: 320 }}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
            />
          )}
        </Field>
        <button
          type="submit"
          className="btn"
          disabled={create.isPending}
          data-testid="alert-rule-create-submit"
        >
          Create rule
        </button>
        <button type="button" className="btn" onClick={onClose}>
          Cancel
        </button>
      </div>
      <FormError error={create.error} />
    </form>
  );
}

export function AlertRules() {
  const q = useAlertRules();
  const [editing, setEditing] = useState<string | null>(null);
  const [expanded, setExpanded] = useState<string | null>("large_deal_slip");
  const [creating, setCreating] = useState(false);

  const rules = q.data?.rules ?? [];
  const canManage = q.data?.can_manage ?? false;

  return (
    <WidgetCard
      testId="widget-alert-rules"
      title="Threshold alert rules"
      description="Live semantic-layer evaluation of pipeline coverage drops, ≥$5M deal slips, and unvalidated AI-led deals in Propose — scoped to the recipient's RLS permissions."
      isLoading={q.isLoading}
      error={q.error}
      onRetry={() => q.refetch()}
    >
      <div className="flex flex-col gap-3">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <p className="m-0 text-sm" data-testid="alert-rules-summary">
            <strong>{q.data?.triggered_count ?? 0}</strong> of {rules.length} active alert rules
            currently triggered in your RLS scope.
          </p>
          {canManage ? (
            <button
              type="button"
              className="btn"
              onClick={() => setCreating((v) => !v)}
              data-testid="alert-rule-new-btn"
            >
              New alert rule
            </button>
          ) : null}
        </div>
        {creating ? <CreateRuleForm onClose={() => setCreating(false)} /> : null}
        <div className="overflow-x-auto">
          <table className="w-full text-sm" data-testid="alert-rules-table">
            <caption className="sr-only">Configured threshold alert rules</caption>
            <thead>
              <tr>
                {["Rule", "Metric", "Condition", "Observed", "State", "Channels", "Actions"].map(
                  (h) => (
                    <th key={h} scope="col" className="p-1 text-left">
                      {h}
                    </th>
                  ),
                )}
              </tr>
            </thead>
            <tbody>
              {rules.map((r) => (
                <tr key={r.rule_id} data-testid={`alert-rule-row-${r.rule_id}`}>
                  <td className="p-1">
                    <div className="font-medium">{r.name}</div>
                    <div className="text-xs" style={{ color: "var(--ink-2)" }}>
                      {r.summary}
                    </div>
                  </td>
                  <td className="p-1">{r.metric_id}</td>
                  <td className="p-1 tabular">{r.threshold_label}</td>
                  <td className="p-1 font-semibold tabular">{r.observed_label}</td>
                  <td className="p-1">
                    {r.status === "neutral" ? (
                      <span className="text-xs" style={{ color: "var(--ink-2)" }}>
                        Disabled
                      </span>
                    ) : (
                      <StatusBadge status={r.status} size="sm" />
                    )}
                  </td>
                  <td className="p-1">{r.channels.join(", ")}</td>
                  <td className="p-1">
                    <div className="flex flex-wrap gap-1">
                      {r.matching_deals.length > 0 ? (
                        <button
                          type="button"
                          className="btn"
                          onClick={() => setExpanded(expanded === r.rule_id ? null : r.rule_id)}
                          data-testid={`alert-rule-deals-btn-${r.rule_id}`}
                        >
                          Deals ({r.matching_deals.length})
                        </button>
                      ) : null}
                      <Link className="btn" to={r.deep_link}>
                        Open view
                      </Link>
                      {canManage ? (
                        <button
                          type="button"
                          className="btn"
                          onClick={() => setEditing(editing === r.rule_id ? null : r.rule_id)}
                          data-testid={`alert-rule-edit-btn-${r.rule_id}`}
                        >
                          Edit
                        </button>
                      ) : null}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {editing ? (
          <div>
            {rules
              .filter((r) => r.rule_id === editing)
              .map((r) => (
                <EditRuleForm key={r.rule_id} row={r} onClose={() => setEditing(null)} />
              ))}
          </div>
        ) : null}
        {expanded
          ? rules
              .filter((r) => r.rule_id === expanded && r.matching_deals.length > 0)
              .map((r) => (
                <div
                  key={r.rule_id}
                  className="rounded p-2"
                  style={{ border: "1px solid var(--grid)" }}
                  data-testid={`alert-rule-deals-${r.rule_id}`}
                >
                  <p className="m-0 mb-2 text-xs font-semibold">
                    Matching deals for {r.name} (RLS-filtered)
                  </p>
                  <table className="w-full text-xs">
                    <caption className="sr-only">Matching deals for {r.name}</caption>
                    <thead>
                      <tr>
                        {["Opportunity", "Account", "Practice", "Stage", "TCV", "Close date"].map(
                          (h) => (
                            <th key={h} scope="col" className="p-1 text-left">
                              {h}
                            </th>
                          ),
                        )}
                      </tr>
                    </thead>
                    <tbody>
                      {r.matching_deals.map((d) => (
                        <tr key={d.opportunity_id}>
                          <td className="p-1 font-medium">
                            {d.opportunity_id} — {d.deal_name}
                          </td>
                          <td className="p-1">{d.account_name}</td>
                          <td className="p-1">{d.lead_practice}</td>
                          <td className="p-1">{d.stage}</td>
                          <td className="p-1 tabular">
                            <Money value={d.tcv} />
                          </td>
                          <td className="p-1">{d.close_date}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ))
          : null}
      </div>
    </WidgetCard>
  );
}
