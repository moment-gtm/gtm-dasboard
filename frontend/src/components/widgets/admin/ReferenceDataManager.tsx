/** FR-ADM-03 — reference data: editable sets (verticals, practices, platforms, probabilities,
 *  bands, settings) and read-only sets owned by other systems. */
import { useState } from "react";
import { adminApi, type ReferenceSet } from "@/api/admin";
import { WidgetCard } from "@/components/common/WidgetCard";
import { useAdminMutation, useReferenceSet, useReferences } from "@/hooks/useAdminData";
import { Field, FormError, fmtDate, inputStyle, Notice } from "./fields";

type Row = Record<string, string | number | boolean | null>;
const NAME_SETS = new Set(["verticals", "practices", "platforms"]);
const LOCKED_COLUMNS: Record<string, string[]> = {
  stage_probability: ["stage"],
  settings: ["key"],
};

function SetEditor({ set }: { set: ReferenceSet }) {
  const save = useAdminMutation((b: { values: unknown[]; reason: string }) =>
    adminApi.editReference(set.key, b),
  );
  const isNames = NAME_SETS.has(set.key);
  const [text, setText] = useState(isNames ? (set.values as string[]).join("\n") : "");
  const [rows, setRows] = useState<Row[]>(
    isNames ? [] : (set.values as Row[]).map((r) => ({ ...r })),
  );
  const [reason, setReason] = useState("");
  const [saved, setSaved] = useState<number | null>(null);
  const cols = rows[0] ? Object.keys(rows[0]) : [];
  const locked = LOCKED_COLUMNS[set.key] ?? [];

  const values = () =>
    isNames
      ? text
          .split("\n")
          .map((s) => s.trim())
          .filter(Boolean)
      : rows;

  const setCell = (i: number, col: string, raw: string | boolean) =>
    setRows(
      rows.map((r, j) => {
        if (j !== i) return r;
        const prev = set.values[i] as Row;
        if (typeof raw === "boolean") return { ...r, [col]: raw };
        if (typeof prev[col] === "number" || prev[col] === null) {
          // Open-ended bands keep an empty bound as null; any other numeric cell stays numeric.
          if (raw === "") return { ...r, [col]: col.startsWith("max") ? null : 0 };
          return { ...r, [col]: Number(raw) };
        }
        return { ...r, [col]: raw };
      }),
    );

  return (
    <form
      className="flex flex-col gap-3"
      aria-label={`Edit ${set.label}`}
      data-testid={`reference-form-${set.key}`}
      onSubmit={(e) => {
        e.preventDefault();
        setSaved(null);
        save.mutate({ values: values(), reason }, { onSuccess: (r) => setSaved(r.version) });
      }}
    >
      {isNames ? (
        <Field label={`${set.label} (one per line)`}>
          {(id) => (
            <textarea
              id={id}
              rows={Math.min(12, Math.max(4, text.split("\n").length + 1))}
              style={{ ...inputStyle, fontFamily: "inherit" }}
              value={text}
              onChange={(e) => setText(e.target.value)}
              data-testid="reference-names"
            />
          )}
        </Field>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <caption className="sr-only">{set.label}</caption>
            <thead>
              <tr>
                {cols.map((c) => (
                  <th key={c} scope="col" className="p-1 text-left">
                    {c.replace(/_/g, " ")}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.map((r, i) => (
                <tr key={i}>
                  {cols.map((c) => (
                    <td key={c} className="p-1">
                      {typeof r[c] === "boolean" ? (
                        <input
                          type="checkbox"
                          aria-label={`${c} row ${i + 1}`}
                          checked={r[c] as boolean}
                          onChange={(e) => setCell(i, c, e.target.checked)}
                        />
                      ) : locked.includes(c) ? (
                        <span>{String(r[c])}</span>
                      ) : (
                        <input
                          aria-label={`${c} row ${i + 1}`}
                          type={typeof r[c] === "string" ? "text" : "number"}
                          step="any"
                          style={{ ...inputStyle, width: typeof r[c] === "string" ? 150 : 110 }}
                          value={r[c] === null ? "" : String(r[c])}
                          onChange={(e) => setCell(i, c, e.target.value)}
                        />
                      )}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      <div className="flex flex-wrap items-end gap-3">
        <Field label="Reason">
          {(id) => (
            <input
              id={id}
              required
              minLength={3}
              maxLength={300}
              style={{ ...inputStyle, minWidth: 260 }}
              value={reason}
              onChange={(e) => setReason(e.target.value)}
            />
          )}
        </Field>
        <button
          type="submit"
          className="btn"
          disabled={save.isPending}
          data-testid="reference-save"
        >
          Save new version
        </button>
      </div>
      <FormError error={save.error} />
      {saved ? (
        <Notice>
          Saved {set.label} as version {saved}.
        </Notice>
      ) : null}
    </form>
  );
}

function ReadOnly({ set }: { set: ReferenceSet }) {
  const rows = set.values as Row[];
  const cols = rows[0] ? Object.keys(rows[0]) : [];
  return (
    <div className="flex flex-col gap-2" data-testid={`reference-readonly-${set.key}`}>
      <Notice>{set.description}</Notice>
      <div className="max-h-72 overflow-auto">
        <table className="w-full text-sm">
          <caption className="sr-only">{set.label}</caption>
          <thead>
            <tr>
              {cols.map((c) => (
                <th key={c} scope="col" className="p-1 text-left">
                  {c.replace(/_/g, " ")}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((r, i) => (
              <tr key={i}>
                {cols.map((c) => (
                  <td key={c} className="p-1">
                    {String(r[c] ?? "")}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function Selected({ keyName }: { keyName: string }) {
  const q = useReferenceSet(keyName);
  if (q.isLoading) return <div className="skeleton" style={{ height: 120 }} />;
  if (q.error || !q.data) return <FormError error={q.error} />;
  const set = q.data;
  return (
    <div className="flex flex-col gap-3">
      {set.editable ? (
        // Re-mount when a new version lands so the form shows the stored values.
        <SetEditor key={`${set.key}-${set.history[0]?.version ?? 1}`} set={set} />
      ) : (
        <ReadOnly set={set} />
      )}
      {set.history.length ? (
        <ul className="m-0 list-none p-0 text-sm" data-testid="reference-history">
          {set.history.map((h) => (
            <li key={h.version}>
              v{h.version} · {h.changed_by} · {fmtDate(h.changed_at)} · {h.reason}
            </li>
          ))}
        </ul>
      ) : null}
    </div>
  );
}

export function ReferenceDataManager() {
  const q = useReferences();
  const [key, setKey] = useState("verticals");
  return (
    <WidgetCard
      title="Reference data"
      description="Verticals, practices, platforms, stage probabilities, bands and settings. Sets owned by other systems are read-only."
      testId="widget-reference"
      isLoading={q.isLoading}
      error={q.error}
      onRetry={() => q.refetch()}
    >
      <div className="flex flex-col gap-3">
        <Field label="Reference set">
          {(id) => (
            <select
              id={id}
              style={{ ...inputStyle, maxWidth: 320 }}
              value={key}
              onChange={(e) => setKey(e.target.value)}
              data-testid="reference-select"
            >
              {q.data?.map((s) => (
                <option key={s.key} value={s.key}>
                  {s.label}
                  {s.editable ? "" : " (read-only)"}
                </option>
              ))}
            </select>
          )}
        </Field>
        <Selected key={key} keyName={key} />
      </div>
    </WidgetCard>
  );
}
