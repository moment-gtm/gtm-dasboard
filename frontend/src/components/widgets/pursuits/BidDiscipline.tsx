/** FR-PUR-04 / PUR-04 — bid discipline: no-bid rate, pursued-RFP win rate, SLA, with a rule-based callout. */
import type { StatusValue } from "@/api/types";
import { ChartTable } from "@/components/charts/ChartTable";
import { StatusBadge } from "@/components/common/StatusBadge";
import { WidgetCard } from "@/components/common/WidgetCard";
import { useBidDiscipline } from "@/hooks/usePursuitsData";
import { useDrilldown } from "@/state/drilldown";
import { formatPct } from "@/utils/format";

interface Measure {
  key: string;
  label: string;
  value: number | null;
  detail: string;
  target: number | null;
  target_label: string | null;
  status: StatusValue | null;
  segment: string;
}

export function BidDiscipline() {
  const q = useBidDiscipline();
  const open = useDrilldown((s) => s.open);
  const rows = (q.data?.breakdown ?? []) as unknown as Measure[];
  const meta = (q.data?.meta ?? {}) as { total?: number };
  return (
    <WidgetCard
      testId="widget-bid-discipline"
      title="Bid discipline"
      description="RFPs that reached the bid/no-bid gate in the last four quarters. Select a tile to list its deals."
      metricId="PUR-04"
      isLoading={q.isLoading}
      isFetching={q.isFetching}
      error={q.error}
      onRetry={() => q.refetch()}
      empty={q.data && !meta.total ? "no-match-filters" : false}
      emptyHint="Bid-tool data (SRC-03) has no RFPs for the current filters."
    >
      <div className="flex flex-col gap-3">
        {q.data?.narrative ? (
          <p
            className="m-0 rounded p-3 text-sm"
            role="note"
            data-testid="bid-callout"
            style={{ background: "var(--page)", border: "1px solid var(--border)" }}
          >
            <strong>
              <span aria-hidden="true">⚠ </span>Bid discipline:
            </strong>{" "}
            {q.data.narrative}
          </p>
        ) : null}
        <div
          className="grid gap-3"
          style={{ gridTemplateColumns: "repeat(auto-fit, minmax(11rem, 1fr))" }}
        >
          {rows.map((r) => (
            <button
              key={r.key}
              type="button"
              className="card flex min-w-0 flex-col gap-1 p-3 text-left"
              onClick={() => open({ metricId: "PUR-04", segment: r.segment, title: r.label })}
              data-testid={`bid-${r.key}`}
              aria-label={`${r.label}: ${formatPct(r.value)}, ${r.detail}. View deals`}
            >
              <span className="text-sm font-medium" style={{ color: "var(--ink-2)" }}>
                {r.label}
              </span>
              <span className="text-2xl font-semibold">{formatPct(r.value)}</span>
              <span className="text-xs" style={{ color: "var(--ink-2)" }}>
                {r.detail}
              </span>
              {r.target != null ? (
                <span className="text-xs" style={{ color: "var(--ink-2)" }}>
                  Target {formatPct(r.target, 0)}+
                </span>
              ) : null}
              <StatusBadge status={r.status} size="sm" />
            </button>
          ))}
        </div>
        <ChartTable
          caption="Bid discipline"
          rows={rows}
          rowKey={(r) => r.key}
          columns={[
            { header: "Measure", cell: (r) => r.label },
            { header: "Value", cell: (r) => formatPct(r.value) },
            { header: "Basis", cell: (r) => r.detail },
            {
              header: "Target",
              cell: (r) => (r.target == null ? "—" : `${formatPct(r.target, 0)}+`),
            },
          ]}
        />
      </div>
    </WidgetCard>
  );
}
