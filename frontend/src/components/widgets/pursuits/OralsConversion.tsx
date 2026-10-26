/** FR-PUR-04 / PUR-05 — of pursuits that reached orals, how many were won. */
import { ChartTable } from "@/components/charts/ChartTable";
import { WidgetCard } from "@/components/common/WidgetCard";
import { useOralsConversion } from "@/hooks/usePursuitsData";
import { useDrilldown } from "@/state/drilldown";
import { formatPct } from "@/utils/format";

interface OutcomeRow {
  outcome: string;
  label: string;
  count: number;
}

export function OralsConversion() {
  const q = useOralsConversion();
  const open = useDrilldown((s) => s.open);
  const rows = (q.data?.breakdown ?? []) as unknown as OutcomeRow[];
  const total = rows.reduce((n, r) => n + r.count, 0);
  return (
    <WidgetCard
      testId="widget-orals-conversion"
      title="Orals conversion"
      description="Pursuits that reached orals: Won ÷ (Won + Lost). Select an outcome to list its deals."
      metricId="PUR-05"
      status={q.data?.status}
      statusBasis={q.data?.status_basis}
      isLoading={q.isLoading}
      isFetching={q.isFetching}
      error={q.error}
      onRetry={() => q.refetch()}
      empty={q.data && !total ? "no-match-filters" : false}
    >
      <div className="flex flex-col gap-3">
        <p className="m-0 text-sm" data-testid="orals-headline">
          <strong className="text-2xl">{formatPct(q.data?.value)}</strong>{" "}
          <span style={{ color: "var(--ink-2)" }}>
            (goal {formatPct(q.data?.goal, 0)}+) · {q.data?.status_basis}
          </span>
        </p>
        <div
          className="grid gap-3"
          style={{ gridTemplateColumns: "repeat(auto-fit, minmax(8rem, 1fr))" }}
        >
          {rows.map((r) => (
            <button
              key={r.outcome}
              type="button"
              className="card flex min-w-0 flex-col gap-1 p-3 text-left"
              disabled={r.count === 0}
              onClick={() =>
                open({ metricId: "PUR-05", segment: r.outcome, title: `Orals — ${r.label}` })
              }
              data-testid={`orals-${r.outcome}`}
              aria-label={`${r.label}: ${r.count} deals. View deals`}
            >
              <span className="text-sm font-medium" style={{ color: "var(--ink-2)" }}>
                {r.label}
              </span>
              <span className="text-2xl font-semibold">{r.count}</span>
            </button>
          ))}
        </div>
        <ChartTable
          caption="Orals conversion"
          rows={rows}
          rowKey={(r) => r.outcome}
          columns={[
            { header: "Outcome", cell: (r) => r.label },
            { header: "Deals", cell: (r) => r.count },
          ]}
        />
      </div>
    </WidgetCard>
  );
}
