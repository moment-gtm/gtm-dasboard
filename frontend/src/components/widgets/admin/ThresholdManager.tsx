/** FR-ADM-02 — versioned RAG thresholds. Bands come from ref_threshold; edits apply everywhere. */
import { useState } from "react";
import { adminApi, type ThresholdRow } from "@/api/admin";
import { WidgetCard } from "@/components/common/WidgetCard";
import { useAdminMutation, useThresholdHistory, useThresholds } from "@/hooks/useAdminData";
import { Field, FormError, fmtDate, inputStyle, Notice } from "./fields";

const PCT = new Set(["pct", "ratio_to_pace", "ratio_to_goal"]);
const scale = (t: ThresholdRow) => (PCT.has(t.unit) ? 100 : 1);
const show = (t: ThresholdRow, v: number) =>
  `${+(v * scale(t)).toFixed(2)}${PCT.has(t.unit) ? "%" : ""}`;

function EditForm({ row, onClose }: { row: ThresholdRow; onClose: () => void }) {
  const save = useAdminMutation((b: { on_track: number; watch: number; reason: string }) =>
    adminApi.editThreshold(row.metric_id, b),
  );
  const [onTrack, setOnTrack] = useState(String(+(row.on_track * scale(row)).toFixed(2)));
  const [watch, setWatch] = useState(String(+(row.watch * scale(row)).toFixed(2)));
  const [reason, setReason] = useState("");
  const unit = PCT.has(row.unit) ? "%" : row.unit;
  return (
    <form
      aria-label={`Edit ${row.metric_id} thresholds`}
      className="flex flex-col gap-2 rounded p-3"
      style={{ border: "1px solid var(--grid)" }}
      data-testid={`threshold-form-${row.metric_id}`}
      onSubmit={(e) => {
        e.preventDefault();
        save.mutate(
          {
            on_track: Number(onTrack) / scale(row),
            watch: Number(watch) / scale(row),
            reason,
          },
          { onSuccess: onClose },
        );
      }}
    >
      <p className="m-0 text-sm" style={{ color: "var(--ink-2)" }}>
        {row.direction === "higher"
          ? "Higher is better: on track must be above watch."
          : "Lower is better: on track must be below watch."}
      </p>
      <div className="flex flex-wrap items-end gap-3">
        <Field label={`On track (${unit})`}>
          {(id) => (
            <input
              id={id}
              type="number"
              step="any"
              required
              style={{ ...inputStyle, width: 110 }}
              value={onTrack}
              onChange={(e) => setOnTrack(e.target.value)}
            />
          )}
        </Field>
        <Field label={`Watch (${unit})`}>
          {(id) => (
            <input
              id={id}
              type="number"
              step="any"
              required
              style={{ ...inputStyle, width: 110 }}
              value={watch}
              onChange={(e) => setWatch(e.target.value)}
            />
          )}
        </Field>
        <Field label="Reason">
          {(id) => (
            <input
              id={id}
              required
              minLength={3}
              maxLength={300}
              style={{ ...inputStyle, minWidth: 240 }}
              value={reason}
              onChange={(e) => setReason(e.target.value)}
            />
          )}
        </Field>
        <button
          type="submit"
          className="btn"
          disabled={save.isPending}
          data-testid="threshold-save"
        >
          Save new version
        </button>
        <button type="button" className="btn" onClick={onClose}>
          Cancel
        </button>
      </div>
      <FormError error={save.error} />
    </form>
  );
}

function History({ id }: { id: string }) {
  const h = useThresholdHistory(id);
  if (h.isLoading) return <div className="skeleton" style={{ height: 40 }} />;
  if (!h.data?.length) return <Notice>No edits yet — this is the original v1 definition.</Notice>;
  return (
    <table className="w-full text-sm" data-testid={`threshold-history-${id}`}>
      <caption className="sr-only">{id} version history</caption>
      <thead>
        <tr>
          {["Version", "On track", "Watch", "Changed by", "When", "Reason"].map((c) => (
            <th key={c} scope="col" className="p-1 text-left">
              {c}
            </th>
          ))}
        </tr>
      </thead>
      <tbody>
        {h.data.map((r) => (
          <tr key={r.version}>
            <td className="p-1">v{r.version}</td>
            <td className="p-1">{r.on_track}</td>
            <td className="p-1">{r.watch}</td>
            <td className="p-1">{r.changed_by}</td>
            <td className="p-1">{fmtDate(r.changed_at)}</td>
            <td className="p-1">{r.reason}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

export function ThresholdManager() {
  const q = useThresholds();
  const [editing, setEditing] = useState<string | null>(null);
  const [history, setHistory] = useState<string | null>(null);
  return (
    <WidgetCard
      title="Thresholds"
      description="On-track and watch bands behind every status badge. Edits are versioned with a reason."
      testId="widget-thresholds"
      isLoading={q.isLoading}
      error={q.error}
      onRetry={() => q.refetch()}
    >
      <div className="overflow-x-auto">
        <table className="w-full text-sm" data-testid="threshold-table">
          <caption className="sr-only">Metric thresholds</caption>
          <thead>
            <tr>
              {["Metric", "Name", "On track", "Watch", "Bands", "Version", "Actions"].map((h) => (
                <th key={h} scope="col" className="p-1 text-left">
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {q.data?.map((t) => (
              <tr key={t.metric_id} data-testid={`threshold-row-${t.metric_id}`}>
                <td className="p-1">{t.metric_id}</td>
                <td className="p-1">{t.name}</td>
                <td className="p-1 tabular">{show(t, t.on_track)}</td>
                <td className="p-1 tabular">{show(t, t.watch)}</td>
                <td className="p-1">{t.label}</td>
                <td className="p-1">v{t.version}</td>
                <td className="p-1">
                  <div className="flex gap-1">
                    <button
                      type="button"
                      className="btn"
                      aria-label={`Edit ${t.metric_id} thresholds`}
                      onClick={() => setEditing(editing === t.metric_id ? null : t.metric_id)}
                    >
                      Edit
                    </button>
                    <button
                      type="button"
                      className="btn"
                      aria-label={`${t.metric_id} threshold history`}
                      onClick={() => setHistory(history === t.metric_id ? null : t.metric_id)}
                    >
                      History
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {editing && q.data ? (
        <div className="mt-3">
          <EditForm
            key={editing + (q.data.find((t) => t.metric_id === editing)?.version ?? 0)}
            row={q.data.find((t) => t.metric_id === editing) as ThresholdRow}
            onClose={() => setEditing(null)}
          />
        </div>
      ) : null}
      {history ? (
        <div className="mt-3">
          <History id={history} />
        </div>
      ) : null}
    </WidgetCard>
  );
}
