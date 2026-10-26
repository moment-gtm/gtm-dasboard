/** FR-PIP-01 / PIP-01 — open pipeline by stage with trailing-4Q conversion; click a stage to filter the register. */
import { FunnelChart } from "@/components/charts/FunnelChart";
import { ChartTable } from "@/components/charts/ChartTable";
import { Money } from "@/components/common/Money";
import { WidgetCard } from "@/components/common/WidgetCard";
import { useFunnel } from "@/hooks/usePipelineData";
import { formatMoney, formatPct } from "@/utils/format";

interface StageRow {
  stage: string;
  open_count: number;
  open_tcv: number;
  reached: number;
  next_stage: string | null;
  conversion: number | null;
}

export function StageFunnel({
  selectedStage,
  onSelectStage,
}: {
  selectedStage: string | null;
  onSelectStage: (stage: string) => void;
}) {
  const q = useFunnel();
  const rows = (q.data?.breakdown ?? []) as unknown as StageRow[];
  const open = rows.filter((r) => r.stage !== "Closed Won");
  return (
    <WidgetCard
      variant="hero"
      testId="widget-stage-funnel"
      title="Stage funnel"
      description="Open deals and TCV at each stage, with conversion to the next stage over the trailing four quarters. Select a stage to filter the register."
      metricId="PIP-01"
      isLoading={q.isLoading}
      isFetching={q.isFetching}
      error={q.error}
      onRetry={() => q.refetch()}
      empty={q.data && open.every((r) => r.open_count === 0) ? "no-match-filters" : false}
    >
      <div className="flex flex-col gap-3">
        <FunnelChart
          steps={open.map((r) => ({
            key: r.stage,
            label: r.stage,
            count: r.open_count,
            value: r.open_tcv,
            conversion: r.conversion,
            note: `${r.reached} reached`,
          }))}
          selectedKey={selectedStage}
          onSelect={onSelectStage}
          formatValue={formatMoney}
          ariaLabel="Open pipeline stage funnel"
        />
        <p className="m-0 text-sm" style={{ color: "var(--ink-2)" }}>
          Overall Identify → Closed Won conversion: <strong>{formatPct(q.data?.value)}</strong> (
          {rows.at(-1)?.reached ?? 0} won of {rows[0]?.reached ?? 0} created in the window).
        </p>
        <ChartTable
          caption="Stage funnel"
          rows={rows}
          rowKey={(r) => r.stage}
          columns={[
            { header: "Stage", cell: (r) => r.stage },
            { header: "Open deals", cell: (r) => r.open_count },
            { header: "Open TCV", cell: (r) => <Money value={r.open_tcv} /> },
            { header: "Reached (4Q)", cell: (r) => r.reached },
            { header: "Conversion to next", cell: (r) => formatPct(r.conversion) },
          ]}
        />
      </div>
    </WidgetCard>
  );
}
