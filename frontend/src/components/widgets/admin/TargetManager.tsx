/** FR-ADM-01 — versioned planning targets: view the active plan, publish a new version. */
import { useMemo, useState } from "react";
import { adminApi } from "@/api/admin";
import { Money } from "@/components/common/Money";
import { WidgetCard } from "@/components/common/WidgetCard";
import { useAdminMutation, useTargets } from "@/hooks/useAdminData";
import { Field, FormError, inputStyle, Notice } from "./fields";

const M = 1_000_000;

export function TargetManager() {
  const q = useTargets();
  const publish = useAdminMutation(adminApi.createTarget);
  const [fy, setFy] = useState<number | null>(null);
  const [edits, setEdits] = useState<Record<string, string>>({});
  const [note, setNote] = useState("");
  const [reviewing, setReviewing] = useState(false);
  const [done, setDone] = useState<string | null>(null);

  const year = fy ?? q.data?.active[0]?.fiscal_year ?? null;
  const cells = useMemo(
    () => q.data?.grid.filter((g) => g.fiscal_year === year) ?? [],
    [q.data, year],
  );
  const key = (quarter: number, practice: string) => `${quarter}|${practice}`;
  const amount = (c: { quarter: number; practice: string; amount_usd: number }) => {
    const e = edits[key(c.quarter, c.practice)];
    return e === undefined || e === "" || Number.isNaN(Number(e)) ? c.amount_usd : Number(e) * M;
  };
  const before = cells.reduce((s, c) => s + c.amount_usd, 0);
  const after = cells.reduce((s, c) => s + amount(c), 0);
  const changed = Object.keys(edits).length > 0;
  const practices = q.data?.practices ?? [];

  const submit = () =>
    publish.mutate(
      {
        fiscal_year: year as number,
        note,
        rows: cells.map((c) => ({
          quarter: c.quarter,
          practice: c.practice,
          amount_usd: amount(c),
        })),
      },
      {
        onSuccess: (r) => {
          setDone(r.version);
          setEdits({});
          setNote("");
          setReviewing(false);
        },
      },
    );

  return (
    <WidgetCard
      title="Targets"
      description="Planning targets by quarter and practice. Each change publishes a new version; history is kept."
      testId="widget-targets"
      isLoading={q.isLoading}
      error={q.error}
      onRetry={() => q.refetch()}
    >
      {q.data && year !== null ? (
        <div className="flex flex-col gap-4">
          <div className="flex flex-wrap items-end gap-3">
            <Field label="Fiscal year">
              {(id) => (
                <select
                  id={id}
                  style={inputStyle}
                  value={year}
                  onChange={(e) => {
                    setFy(Number(e.target.value));
                    setEdits({});
                    setReviewing(false);
                  }}
                >
                  {q.data.active.map((a) => (
                    <option key={a.fiscal_year} value={a.fiscal_year}>
                      FY{a.fiscal_year % 100}
                    </option>
                  ))}
                </select>
              )}
            </Field>
            <p className="m-0 text-sm" data-testid="active-target-version">
              Active version:{" "}
              <strong>{q.data.active.find((a) => a.fiscal_year === year)?.version}</strong> · total{" "}
              <Money value={before} />
            </p>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm" data-testid="target-grid">
              <caption className="sr-only">Targets in $M by practice and quarter</caption>
              <thead>
                <tr>
                  <th scope="col" className="p-1 text-left">
                    Practice
                  </th>
                  {[1, 2, 3, 4].map((n) => (
                    <th key={n} scope="col" className="p-1 text-right">
                      Q{n} ($M)
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {practices.map((p) => (
                  <tr key={p}>
                    <th scope="row" className="p-1 text-left font-medium">
                      {p}
                    </th>
                    {[1, 2, 3, 4].map((n) => {
                      const c = cells.find((x) => x.quarter === n && x.practice === p);
                      if (!c) return <td key={n} />;
                      const k = key(n, p);
                      return (
                        <td key={n} className="p-1 text-right">
                          <input
                            aria-label={`${p} Q${n} target in $M`}
                            type="number"
                            step="0.1"
                            min="0"
                            style={{ ...inputStyle, width: 88, textAlign: "right" }}
                            value={edits[k] ?? (c.amount_usd / M).toFixed(1)}
                            onChange={(e) => {
                              setEdits({ ...edits, [k]: e.target.value });
                              setReviewing(false);
                              setDone(null);
                            }}
                          />
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="flex flex-wrap items-end gap-3">
            <Field label="Reason for the change">
              {(id) => (
                <input
                  id={id}
                  style={{ ...inputStyle, minWidth: 260 }}
                  value={note}
                  maxLength={300}
                  onChange={(e) => setNote(e.target.value)}
                />
              )}
            </Field>
            <button
              type="button"
              className="btn"
              disabled={!changed || note.trim().length < 3}
              onClick={() => setReviewing(true)}
              data-testid="target-review"
            >
              Review change
            </button>
          </div>
          {reviewing ? (
            <div
              role="group"
              aria-label="Confirm new target version"
              className="flex flex-col gap-2 rounded p-3"
              style={{ border: "1px solid var(--grid)" }}
              data-testid="target-confirm"
            >
              <p className="m-0 text-sm">
                Publish a new FY{(year ?? 0) % 100} version? Total moves from{" "}
                <Money value={before} /> to <Money value={after} />. Statuses against target update
                everywhere.
              </p>
              <div className="flex gap-2">
                <button
                  type="button"
                  className="btn"
                  onClick={submit}
                  disabled={publish.isPending}
                  data-testid="target-publish"
                >
                  {publish.isPending ? "Publishing…" : "Publish version"}
                </button>
                <button type="button" className="btn" onClick={() => setReviewing(false)}>
                  Cancel
                </button>
              </div>
            </div>
          ) : null}
          <FormError error={publish.error} />
          {done ? <Notice>Published {done}.</Notice> : null}
          <div className="overflow-x-auto">
            <table className="w-full text-sm" data-testid="target-versions">
              <caption className="m-0 p-1 text-left font-semibold">Version history</caption>
              <thead>
                <tr>
                  {["Version", "Source", "Created", "Total", "Reason"].map((h) => (
                    <th key={h} scope="col" className="p-1 text-left">
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {q.data.versions
                  .filter((v) => v.fiscal_year === year)
                  .map((v) => (
                    <tr key={v.version}>
                      <td className="p-1">
                        {v.version}
                        {v.active ? " (active)" : ""}
                      </td>
                      <td className="p-1">
                        {v.source === "admin" ? v.created_by : "Planning tool"}
                      </td>
                      <td className="p-1">{v.created_at.slice(0, 10)}</td>
                      <td className="p-1">
                        <Money value={v.total_usd} />
                      </td>
                      <td className="p-1">{v.note ?? "Imported plan"}</td>
                    </tr>
                  ))}
              </tbody>
            </table>
          </div>
        </div>
      ) : null}
    </WidgetCard>
  );
}
