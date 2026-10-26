/** FR-PIP-06 / PIP-07 — week-over-week stage movement from the two latest weekly snapshots. */
import { ChartTable } from "@/components/charts/ChartTable";
import { Money } from "@/components/common/Money";
import { WidgetCard } from "@/components/common/WidgetCard";
import { useStageMovement } from "@/hooks/usePipelineData";
import { useDrilldown } from "@/state/drilldown";

interface MovementRow {
  movement: string;
  label: string;
  count: number;
  tcv: number;
}

const ICON: Record<string, string> = {
  created: "＋",
  advanced: "▲",
  regressed: "▼",
  slipped: "→",
  closed: "✓",
};

export function StageMovement() {
  const q = useStageMovement();
  const open = useDrilldown((s) => s.open);
  const rows = (q.data?.breakdown ?? []) as unknown as MovementRow[];
  const meta = (q.data?.meta ?? {}) as {
    previous_snapshot?: string | null;
    latest_snapshot?: string | null;
  };
  const drill = (r: MovementRow) =>
    open({ metricId: "PIP-07", segment: r.movement, title: `${r.label} deals` });
  return (
    <WidgetCard
      testId="widget-stage-movement"
      title="Week-over-week stage movement"
      description="Change in open pipeline between the two latest weekly snapshots. Select a tile to list its deals."
      metricId="PIP-07"
      isLoading={q.isLoading}
      isFetching={q.isFetching}
      error={q.error}
      onRetry={() => q.refetch()}
      empty={q.data && !meta.latest_snapshot ? "no-match-filters" : false}
      emptyHint="Weekly snapshots are taken every Monday; at least two are needed."
    >
      <div className="flex flex-col gap-3">
        <p className="m-0 text-sm" style={{ color: "var(--ink-2)" }} data-testid="movement-basis">
          {q.data?.status_basis}
          {meta.previous_snapshot && meta.latest_snapshot
            ? ` (${meta.previous_snapshot} → ${meta.latest_snapshot})`
            : ""}
        </p>
        <div
          className="grid gap-3"
          style={{ gridTemplateColumns: "repeat(auto-fit, minmax(9rem, 1fr))" }}
        >
          {rows.map((r) => (
            <button
              key={r.movement}
              type="button"
              className="card flex min-w-0 flex-col gap-1 p-3 text-left"
              disabled={r.count === 0}
              onClick={() => drill(r)}
              data-testid={`movement-${r.movement}`}
              aria-label={`${r.label}: ${r.count} deals. View deals`}
              style={{ cursor: r.count ? "pointer" : "default" }}
            >
              <span className="text-sm font-medium" style={{ color: "var(--ink-2)" }}>
                <span aria-hidden="true">{ICON[r.movement]} </span>
                {r.label}
              </span>
              <span className="text-2xl font-semibold">{r.count}</span>
              <span className="text-xs" style={{ color: "var(--ink-2)" }}>
                <Money value={r.tcv} />
              </span>
            </button>
          ))}
        </div>
        <ChartTable
          caption="Stage movement"
          rows={rows}
          rowKey={(r) => r.movement}
          columns={[
            { header: "Movement", cell: (r) => r.label },
            { header: "Deals", cell: (r) => r.count },
            { header: "TCV", cell: (r) => <Money value={r.tcv} /> },
          ]}
        />
      </div>
    </WidgetCard>
  );
}
