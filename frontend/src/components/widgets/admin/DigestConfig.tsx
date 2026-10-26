/** FR-ALR-01 — Weekly digest schedule, RLS-scoped Email/Teams preview, and delivery log. */
import { useState } from "react";
import { Link } from "react-router-dom";
import { adminApi, type DigestSchedule } from "@/api/admin";
import { StatusBadge } from "@/components/common/StatusBadge";
import { WidgetCard } from "@/components/common/WidgetCard";
import { useAdminMutation, useDigest } from "@/hooks/useAdminData";
import { Field, FormError, fmtDate, inputStyle, Notice } from "./fields";

const DAYS: DigestSchedule["day_of_week"][] = [
  "Monday",
  "Tuesday",
  "Wednesday",
  "Thursday",
  "Friday",
  "Saturday",
  "Sunday",
];

const PREVIEW_ROLES = [
  { value: "", label: "My role (default)" },
  { value: "gtm_lead", label: "GTM Lead" },
  { value: "leadership", label: "Moment Leadership" },
  { value: "finance", label: "Finance" },
  { value: "practice_lead", label: "Practice Lead (DxP)" },
  { value: "client_partner", label: "Client Partner" },
  { value: "alliance_manager", label: "Alliance Manager" },
  { value: "solutions_lead", label: "Solutions Lead" },
  { value: "marketing", label: "Marketing" },
  { value: "sales_ops", label: "Sales Operations" },
];

export function DigestConfig() {
  const [previewRole, setPreviewRole] = useState<string>("");
  const q = useDigest(previewRole || undefined);
  const sendNow = useAdminMutation((scope: "self" | "all_subscribed") =>
    adminApi.sendDigest({ scope }),
  );
  const saveSchedule = useAdminMutation(
    (b: {
      enabled: boolean;
      day_of_week: DigestSchedule["day_of_week"];
      hour_utc: number;
      channels: ("email" | "teams")[];
    }) => adminApi.updateDigestSchedule(b),
  );

  const d = q.data;
  const [day, setDay] = useState<DigestSchedule["day_of_week"] | null>(null);
  const [hour, setHour] = useState<string | null>(null);

  const selectedDay = day ?? d?.schedule.day_of_week ?? "Monday";
  const selectedHour = hour ?? String(d?.schedule.hour_utc ?? 7);

  return (
    <WidgetCard
      testId="widget-digest-config"
      title="Weekly digest (Email & Microsoft Teams)"
      description="Summarises KPI changes (EXE-01..06), newly stalled deals (EXE-10), and over-capacity architects (CAP-01) with direct dashboard links, scoped to each recipient's RLS permissions."
      isLoading={q.isLoading}
      error={q.error}
      onRetry={() => q.refetch()}
    >
      {d ? (
        <div className="flex flex-col gap-4">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <span className="text-xs font-medium" style={{ color: "var(--ink-2)" }}>
              Manual dispatch &amp; schedule configuration
            </span>
            <div className="flex flex-wrap gap-2">
              <button
                type="button"
                className="btn"
                disabled={sendNow.isPending}
                onClick={() => sendNow.mutate("self")}
                data-testid="digest-send-now"
              >
                Send my digest now
              </button>
              <button
                type="button"
                className="btn"
                disabled={sendNow.isPending}
                onClick={() => sendNow.mutate("all_subscribed")}
                data-testid="digest-send-all"
              >
                Dispatch to all personas
              </button>
            </div>
          </div>
          <form
            aria-label="Weekly digest schedule"
            className="flex flex-wrap items-end gap-3 rounded p-3"
            style={{ border: "1px solid var(--grid)" }}
            data-testid="digest-schedule-form"
            onSubmit={(e) => {
              e.preventDefault();
              saveSchedule.mutate({
                enabled: true,
                day_of_week: selectedDay,
                hour_utc: Number(selectedHour),
                channels: d.schedule.channels,
              });
            }}
          >
            <Field label="Delivery day">
              {(id) => (
                <select
                  id={id}
                  style={inputStyle}
                  value={selectedDay}
                  onChange={(e) => setDay(e.target.value as DigestSchedule["day_of_week"])}
                >
                  {DAYS.map((dayName) => (
                    <option key={dayName} value={dayName}>
                      {dayName}
                    </option>
                  ))}
                </select>
              )}
            </Field>
            <Field label="Hour (UTC)">
              {(id) => (
                <input
                  id={id}
                  type="number"
                  min={0}
                  max={23}
                  style={{ ...inputStyle, width: 90 }}
                  value={selectedHour}
                  onChange={(e) => setHour(e.target.value)}
                />
              )}
            </Field>
            <button
              type="submit"
              className="btn"
              disabled={saveSchedule.isPending}
              data-testid="digest-schedule-save"
            >
              Update schedule
            </button>
            <Field label="Preview as persona (RLS scope)">
              {(id) => (
                <select
                  id={id}
                  style={inputStyle}
                  value={previewRole}
                  onChange={(e) => setPreviewRole(e.target.value)}
                  data-testid="digest-preview-role"
                >
                  {PREVIEW_ROLES.map((r) => (
                    <option key={r.value} value={r.value}>
                      {r.label}
                    </option>
                  ))}
                </select>
              )}
            </Field>
          </form>
          <FormError error={saveSchedule.error ?? sendNow.error} />

          <Notice>
            Previewing digest for <strong>{d.recipient.display_name}</strong> (
            {d.recipient.role_label}
            {d.recipient.practice ? ` · ${d.recipient.practice}` : ""}) · Scheduled every{" "}
            <strong>
              {d.schedule.day_of_week} at {String(d.schedule.hour_utc).padStart(2, "0")}:00 UTC
            </strong>{" "}
            via {d.schedule.channels.join(" & ")}.
          </Notice>

          <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
            <div
              className="flex flex-col gap-2 rounded p-3"
              style={{ border: "1px solid var(--grid)" }}
              data-testid="digest-kpi-summary"
            >
              <h4 className="m-0 text-sm font-semibold">KPI changes (EXE-01..06)</h4>
              <table className="w-full text-sm">
                <caption className="sr-only">Digest KPI summary</caption>
                <thead>
                  <tr>
                    {["Metric", "Value", "Goal", "Delta", "Status"].map((h) => (
                      <th key={h} scope="col" className="p-1 text-left">
                        {h}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {d.kpis.map((k) => (
                    <tr key={k.metric_id}>
                      <td className="p-1 font-medium">
                        {k.metric_id} · {k.label}
                      </td>
                      <td className="p-1 tabular">{k.formatted_value}</td>
                      <td className="p-1 tabular">{k.formatted_goal ?? "—"}</td>
                      <td className="p-1 tabular">{k.formatted_delta ?? "—"}</td>
                      <td className="p-1">
                        <StatusBadge status={k.status === "neutral" ? null : k.status} size="sm" />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div
              className="flex flex-col gap-3 rounded p-3"
              style={{ border: "1px solid var(--grid)" }}
              data-testid="digest-highlights"
            >
              <div>
                <h4 className="m-0 text-sm font-semibold">
                  Stalled & attention deals ({d.stalled_deals.metric_id})
                </h4>
                <p className="m-0 text-xs" style={{ color: "var(--ink-2)" }}>
                  {d.stalled_deals.total_count} deals ({d.stalled_deals.formatted_tcv}) in recipient
                  scope.
                </p>
              </div>
              <div>
                <h4 className="m-0 text-sm font-semibold">
                  Over-capacity Solution Architects ({d.over_capacity_architects.metric_id})
                </h4>
                <p className="m-0 text-xs" style={{ color: "var(--ink-2)" }}>
                  {d.over_capacity_architects.over_count} over capacity ·{" "}
                  {d.over_capacity_architects.stretched_count} stretched ·{" "}
                  {d.over_capacity_architects.healthy_count} healthy
                </p>
              </div>
              <div>
                <h4 className="m-0 text-sm font-semibold">Direct dashboard links</h4>
                <div className="mt-1 flex flex-wrap gap-2">
                  {d.dashboard_links.map((l) => (
                    <Link
                      key={l.module}
                      to={l.path}
                      className="btn text-xs"
                      data-testid={`digest-link-${l.module}`}
                    >
                      {l.label}
                    </Link>
                  ))}
                </div>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
            <div
              className="flex flex-col gap-1 rounded p-3"
              style={{ border: "1px solid var(--grid)" }}
              data-testid="digest-email-preview"
            >
              <h4 className="m-0 text-sm font-semibold">Email preview</h4>
              <p className="m-0 text-xs" style={{ color: "var(--ink-2)" }}>
                To: {d.email_preview.to} · Subject: <strong>{d.email_preview.subject}</strong>
              </p>
              <pre
                className="m-0 mt-1 overflow-x-auto whitespace-pre-wrap rounded p-2 text-xs"
                style={{ background: "var(--surface-2)" }}
              >
                {d.email_preview.body_markdown}
              </pre>
            </div>
            <div
              className="flex flex-col gap-2 rounded p-3"
              style={{ border: "1px solid var(--grid)" }}
              data-testid="digest-teams-preview"
            >
              <h4 className="m-0 text-sm font-semibold">
                Microsoft Teams card ({d.teams_preview.channel})
              </h4>
              <p className="m-0 text-xs font-medium">{d.teams_preview.title}</p>
              <p className="m-0 text-xs" style={{ color: "var(--ink-2)" }}>
                {d.teams_preview.summary}
              </p>
              <dl className="m-0 grid grid-cols-2 gap-1 text-xs">
                {d.teams_preview.facts.map((f) => (
                  <div key={f.name}>
                    <dt className="font-semibold">{f.name}</dt>
                    <dd className="m-0" style={{ color: "var(--ink-2)" }}>
                      {f.value}
                    </dd>
                  </div>
                ))}
              </dl>
            </div>
          </div>

          <div className="overflow-x-auto">
            <h4 className="m-0 mb-1 text-sm font-semibold">Digest delivery log</h4>
            {d.history.length === 0 ? (
              <p className="m-0 text-xs" style={{ color: "var(--ink-2)" }}>
                No digests dispatched in this session yet — click “Send my digest now” to log a
                delivery run.
              </p>
            ) : (
              <table className="w-full text-sm" data-testid="digest-history-table">
                <caption className="sr-only">Weekly digest delivery history</caption>
                <thead>
                  <tr>
                    {[
                      "Sent at",
                      "Recipient",
                      "Role",
                      "Channels",
                      "KPIs",
                      "Stalled deals",
                      "Status",
                    ].map((h) => (
                      <th key={h} scope="col" className="p-1 text-left">
                        {h}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {d.history.map((run) => (
                    <tr key={run.id} data-testid={`digest-run-${run.id}`}>
                      <td className="p-1">{fmtDate(run.sent_at)}</td>
                      <td className="p-1">{run.recipient_upn}</td>
                      <td className="p-1">{run.recipient_role}</td>
                      <td className="p-1">{run.channels.join(", ")}</td>
                      <td className="p-1 tabular">{run.kpi_count}</td>
                      <td className="p-1 tabular">{run.stalled_deal_count}</td>
                      <td className="p-1">{run.status}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>
      ) : null}
    </WidgetCard>
  );
}
