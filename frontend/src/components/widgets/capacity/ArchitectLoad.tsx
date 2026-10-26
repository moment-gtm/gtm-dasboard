/** FR-CAP-01 / CAP-01 — open pursuits per Solution Architect; over-capacity architects are called out. */
import type { StatusValue } from "@/api/types";
import { ChartTable } from "@/components/charts/ChartTable";
import { Money } from "@/components/common/Money";
import { StatusBadge } from "@/components/common/StatusBadge";
import { WidgetCard } from "@/components/common/WidgetCard";
import { PctBars } from "@/components/widgets/pursuits/PctBars";
import { useArchitectLoad } from "@/hooks/useCapacityData";
import { useDrilldown } from "@/state/drilldown";

interface Row {
  resource_id: string;
  architect: string;
  open_pursuits: number;
  tcv: number;
  band: StatusValue;
}

export function ArchitectLoad() {
  const q = useArchitectLoad();
  const open = useDrilldown((s) => s.open);
  const rows = (q.data?.breakdown ?? []) as unknown as Row[];
  const meta = (q.data?.meta ?? {}) as {
    healthy?: number;
    stretched?: number;
    over_capacity?: number;
  };
  const max = Math.max(1, ...rows.map((r) => r.open_pursuits));
  return (
    <WidgetCard
      variant="hero"
      testId="widget-architect-load"
      title="Architect load"
      description="Open pursuits assigned to each Solution Architect."
      metricId="CAP-01"
      status={q.data?.status}
      statusBasis={q.data?.status_basis}
      isLoading={q.isLoading}
      isFetching={q.isFetching}
      error={q.error}
      onRetry={() => q.refetch()}
      empty={q.data && !rows.length ? "no-match-filters" : false}
    >
      <div className="flex flex-col gap-3">
        <p className="m-0 text-sm" data-testid="architect-load-callout">
          {q.data?.narrative}
        </p>
        <p className="m-0 text-sm" style={{ color: "var(--ink-2)" }}>
          {meta.healthy} healthy · {meta.stretched} stretched · {meta.over_capacity} over capacity
        </p>
        <PctBars
          testIdPrefix="architect"
          rows={rows.slice(0, 12).map((r) => ({
            key: r.resource_id,
            label: r.architect,
            value: r.open_pursuits / max,
            detail: `${r.open_pursuits} open`,
            emphasis: r.band === "off_track",
            badge:
              r.band === "off_track"
                ? "over capacity"
                : r.band === "watch"
                  ? "stretched"
                  : undefined,
          }))}
          onSelect={(id) => {
            const r = rows.find((x) => x.resource_id === id);
            open({
              metricId: "CAP-01",
              segment: id,
              title: `Open pursuits — ${r?.architect ?? id}`,
            });
          }}
        />
        <ChartTable
          caption="Open pursuits per architect"
          rows={rows}
          rowKey={(r) => r.resource_id}
          columns={[
            { header: "Architect", cell: (r) => r.architect },
            { header: "Open pursuits", cell: (r) => r.open_pursuits },
            { header: "TCV", cell: (r) => <Money value={r.tcv} /> },
            { header: "Load", cell: (r) => <StatusBadge status={r.band} size="sm" /> },
          ]}
        />
      </div>
    </WidgetCard>
  );
}
