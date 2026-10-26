/** FR-ADM-04 — data-quality console: ADM-01 completeness gate, rules DQ-01..09, findings, export. */
import { useState } from "react";
import { adminApi } from "@/api/admin";
import { WidgetCard } from "@/components/common/WidgetCard";
import { useCompleteness, useDq, useDqFindings } from "@/hooks/useAdminData";
import { Field, inputStyle, Notice } from "./fields";

const pct = (v: number | null | undefined) => (v == null ? "–" : `${(v * 100).toFixed(1)}%`);

export function CompletenessGate() {
  const q = useCompleteness();
  const gate = q.data?.meta.gate as { met: boolean; required: number; weeks: number } | undefined;
  const series = (q.data?.meta.series ?? []) as {
    week_start: string;
    qualified: number;
    complete: number;
    completeness: number | null;
  }[];
  return (
    <WidgetCard
      title="Mandatory-field completeness"
      description="Qualified opportunities with offering, practice, platform, deal source and owner filled in."
      metricId="ADM-01"
      exportable={false}
      status={q.data?.status}
      statusBasis={q.data?.status_basis}
      isLoading={q.isLoading}
      error={q.error}
      onRetry={() => q.refetch()}
    >
      {q.data && gate ? (
        <div className="flex flex-col gap-3">
          <p className="m-0 text-2xl font-semibold tabular" data-testid="adm01-value">
            {pct(q.data.value)}
          </p>
          <div data-testid="gate-status">
            <Notice>
              Go-live gate (≥{pct(gate.required)} for {gate.weeks} consecutive weeks):{" "}
              <strong>{gate.met ? "met" : "not met yet"}</strong>.
            </Notice>
          </div>
          <table className="w-full text-sm">
            <caption className="sr-only">Completeness by week</caption>
            <thead>
              <tr>
                {["Week of", "Qualified", "Complete", "Completeness"].map((h) => (
                  <th key={h} scope="col" className="p-1 text-left">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {[...series].reverse().map((w) => (
                <tr key={w.week_start}>
                  <td className="p-1">{w.week_start}</td>
                  <td className="p-1 tabular">{w.qualified}</td>
                  <td className="p-1 tabular">{w.complete}</td>
                  <td className="p-1 tabular">{pct(w.completeness)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : null}
    </WidgetCard>
  );
}

function Findings({ rule, owner }: { rule: string; owner: string }) {
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const q = useDqFindings({
    rule_id: rule || undefined,
    owner: owner || undefined,
    q: search || undefined,
    page,
  });
  const last = q.data ? Math.max(1, Math.ceil(q.data.total / q.data.page_size)) : 1;
  return (
    <div className="flex flex-col gap-2" data-testid="dq-findings">
      <div className="flex flex-wrap items-end gap-3">
        <Field label="Search record or detail">
          {(id) => (
            <input
              id={id}
              style={inputStyle}
              value={search}
              onChange={(e) => {
                setSearch(e.target.value);
                setPage(1);
              }}
            />
          )}
        </Field>
        <a
          className="btn"
          href={adminApi.exportUrl(rule || undefined)}
          download
          data-testid="dq-export"
        >
          Export findings (CSV)
        </a>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <caption className="sr-only">DQ findings</caption>
          <thead>
            <tr>
              {["Rule", "Severity", "Record", "Detail", "Owner"].map((h) => (
                <th key={h} scope="col" className="p-1 text-left">
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {q.data?.rows.map((r) => (
              <tr key={`${r.rule_id}-${r.record_id}-${r.detail}`}>
                <td className="p-1">{r.rule_id}</td>
                <td className="p-1">{r.severity}</td>
                <td className="p-1">{r.record_id}</td>
                <td className="p-1">{r.detail}</td>
                <td className="p-1">{r.owner}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {q.data && q.data.total === 0 ? <Notice>No findings match.</Notice> : null}
      <div className="flex items-center gap-2 text-sm">
        <button
          type="button"
          className="btn"
          disabled={page <= 1}
          onClick={() => setPage(page - 1)}
        >
          Previous
        </button>
        <span>
          Page {page} of {last} · {q.data?.total ?? 0} findings
        </span>
        <button
          type="button"
          className="btn"
          disabled={page >= last}
          onClick={() => setPage(page + 1)}
        >
          Next
        </button>
      </div>
    </div>
  );
}

export function DqConsole() {
  const q = useDq();
  const [rule, setRule] = useState("");
  const [owner, setOwner] = useState("");
  return (
    <WidgetCard
      title="Data-quality console"
      description="Rules DQ-01 to DQ-09 with owners. Fix records at the source; findings clear on the next refresh."
      testId="widget-dq"
      isLoading={q.isLoading}
      error={q.error}
      onRetry={() => q.refetch()}
    >
      {q.data ? (
        <div className="flex flex-col gap-4">
          <div className="overflow-x-auto">
            <table className="w-full text-sm" data-testid="dq-rules">
              <caption className="sr-only">Data-quality rules</caption>
              <thead>
                <tr>
                  {["Rule", "What it catches", "Handling", "Severity", "Records", ""].map((h) => (
                    <th key={h} scope="col" className="p-1 text-left">
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {q.data.rules.map((r) => (
                  <tr key={r.rule_id} data-testid={`dq-rule-${r.rule_id}`}>
                    <td className="p-1">{r.rule_id}</td>
                    <td className="p-1">{r.description}</td>
                    <td className="p-1">{r.handling}</td>
                    <td className="p-1">{r.severity}</td>
                    <td className="p-1 tabular">
                      {r.active ? (
                        r.records
                      ) : (
                        <span title={r.inactive_reason ?? ""}>Not active</span>
                      )}
                    </td>
                    <td className="p-1">
                      {r.active ? (
                        <button
                          type="button"
                          className="btn"
                          aria-pressed={rule === r.rule_id}
                          aria-label={`Show ${r.rule_id} findings`}
                          onClick={() => setRule(rule === r.rule_id ? "" : r.rule_id)}
                        >
                          {rule === r.rule_id ? "Clear" : "Show"}
                        </button>
                      ) : null}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <Field label="Owner">
            {(id) => (
              <select
                id={id}
                style={{ ...inputStyle, maxWidth: 360 }}
                value={owner}
                onChange={(e) => setOwner(e.target.value)}
              >
                <option value="">All owners</option>
                {q.data.by_owner.map((o) => (
                  <option key={o.owner} value={o.owner}>
                    {o.owner} ({o.records})
                  </option>
                ))}
              </select>
            )}
          </Field>
          <Findings key={`${rule}|${owner}`} rule={rule} owner={owner} />
        </div>
      ) : null}
    </WidgetCard>
  );
}
