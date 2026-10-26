/** FR-MKT-04 / MKT-04 — Analyst positioning with prior placement, current placement, and text + icon change direction. */
import { WidgetCard } from "@/components/common/WidgetCard";
import { useAnalystPositioning } from "@/hooks/useMarketData";
import { tokens } from "@/theme/tokens";
import { formatDate } from "@/utils/format";

interface EvalRow {
  eval_id: string;
  firm: string;
  report_series: string;
  report_title: string;
  practice: string;
  platform: string;
  published_date: string;
  current_placement: string;
  prior_placement: string;
  direction: "up" | "flat" | "down";
  direction_icon: string;
  direction_label: string;
  direction_display: string;
  score_delta: number;
  lead_analyst: string;
  summary_note: string;
}

const DIRECTION_STYLE: Record<EvalRow["direction"], { bg: string; fg: string; border: string }> = {
  up: {
    bg: tokens.status.on_track.bg,
    fg: tokens.status.on_track.text,
    border: tokens.status.on_track.fill,
  },
  flat: {
    bg: tokens.page,
    fg: tokens.ink.secondary,
    border: tokens.border,
  },
  down: {
    bg: tokens.status.watch.bg,
    fg: tokens.status.watch.text,
    border: tokens.status.watch.fill,
  },
};

export function AnalystPositioning() {
  const q = useAnalystPositioning();
  const rows = (q.data?.breakdown ?? []) as unknown as EvalRow[];
  const meta = (q.data?.meta ?? {}) as {
    evaluations?: number;
    leaders?: number;
    improved?: number;
    maintained?: number;
    declined?: number;
  };

  return (
    <WidgetCard
      testId="widget-analyst-positioning"
      title="Analyst positioning"
      description="Latest placement in major analyst evaluations vs prior edition, with explicit direction icon and label (Microsoft 365 AR tracker)."
      metricId="MKT-04"
      status={q.data?.status}
      statusBasis={q.data?.status_basis}
      isLoading={q.isLoading}
      isFetching={q.isFetching}
      error={q.error}
      onRetry={() => q.refetch()}
      empty={q.data && !rows.length ? "no-match-filters" : false}
      emptyHint="No analyst evaluations match the current practice or platform filter."
    >
      <div className="flex flex-col gap-3">
        <p className="m-0 text-sm" data-testid="analyst-positioning-summary">
          <span className="text-2xl font-semibold">{meta.leaders ?? 0}</span>{" "}
          <span style={{ color: "var(--ink-2)" }}>
            Leader placements across {meta.evaluations ?? rows.length} evaluations ·{" "}
            {meta.improved ?? 0} ↑ Improved · {meta.maintained ?? 0} → Unchanged ·{" "}
            {meta.declined ?? 0} ↓ Declined
          </span>
        </p>
        <div className="overflow-x-auto">
          <table className="w-full text-sm" data-testid="analyst-positioning-table">
            <caption className="sr-only">Analyst evaluations and placement movement</caption>
            <thead>
              <tr>
                {[
                  "Firm & report",
                  "Practice",
                  "Platform",
                  "Prior placement",
                  "Current placement",
                  "Movement",
                  "Published",
                ].map((h) => (
                  <th key={h} scope="col" className="p-1 text-left">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.map((r) => {
                const st = DIRECTION_STYLE[r.direction] ?? DIRECTION_STYLE.flat;
                return (
                  <tr key={r.eval_id} data-testid={`analyst-row-${r.eval_id}`}>
                    <td className="p-1">
                      <div className="font-medium">
                        {r.firm} — {r.report_series}
                      </div>
                      <div className="text-xs" style={{ color: "var(--ink-2)" }}>
                        {r.report_title}
                      </div>
                    </td>
                    <td className="p-1">{r.practice}</td>
                    <td className="p-1">{r.platform}</td>
                    <td className="p-1">{r.prior_placement}</td>
                    <td className="p-1 font-semibold">{r.current_placement}</td>
                    <td className="p-1">
                      <span
                        className="inline-flex items-center gap-1 rounded px-2 py-0.5 text-xs font-semibold whitespace-nowrap"
                        style={{
                          background: st.bg,
                          color: st.fg,
                          border: `1px solid ${st.border}`,
                        }}
                        data-testid={`analyst-direction-${r.eval_id}`}
                      >
                        <span aria-hidden="true">{r.direction_icon}</span>
                        <span>{r.direction_label}</span>
                      </span>
                    </td>
                    <td className="p-1 whitespace-nowrap">{formatDate(r.published_date)}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </WidgetCard>
  );
}
