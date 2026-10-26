/** FR-PIP-03 / PIP-04 — open TCV by primary platform, qualified vs early-stage (Identify). */
import { ChartTable } from "@/components/charts/ChartTable";
import { StackedSplitChart } from "@/components/charts/StackedSplitChart";
import { Money } from "@/components/common/Money";
import { WidgetCard } from "@/components/common/WidgetCard";
import { usePipelineByPlatform } from "@/hooks/usePipelineData";
import { useDrilldown } from "@/state/drilldown";
import { formatMoney } from "@/utils/format";

interface PlatformRow {
  platform: string;
  qualified: number;
  identify: number;
  total: number;
}

const PARTS = [
  { key: "qualified", label: "Qualified (Qualify or later)" },
  { key: "identify", label: "Early stage (Identify)" },
];

export function PipelineByPlatform() {
  const q = usePipelineByPlatform();
  const open = useDrilldown((s) => s.open);
  const rows = (q.data?.breakdown ?? []) as unknown as PlatformRow[];
  const drill = (platform: string, part: string) =>
    open({
      metricId: "PIP-04",
      segment: `${platform}|${part}`,
      title: `${platform} — ${part === "qualified" ? "qualified" : "Identify"} pipeline`,
    });
  const summary = rows
    .map(
      (r) =>
        `${r.platform}: qualified ${formatMoney(r.qualified)}, Identify ${formatMoney(r.identify)}`,
    )
    .join("; ");
  return (
    <WidgetCard
      testId="widget-pipeline-by-platform"
      title="Pipeline by platform"
      description="Open TCV by primary technology platform, split into qualified and early-stage (Identify)."
      metricId="PIP-04"
      isLoading={q.isLoading}
      isFetching={q.isFetching}
      error={q.error}
      onRetry={() => q.refetch()}
      empty={q.data && rows.every((r) => r.total === 0) ? "no-match-filters" : false}
    >
      <StackedSplitChart
        data={rows.map((r) => ({
          category: r.platform,
          qualified: r.qualified,
          identify: r.identify,
        }))}
        parts={PARTS}
        onSelect={drill}
        ariaLabel={`Open pipeline by platform. ${summary}`}
      />
      <ChartTable
        caption="Open pipeline by platform"
        rows={rows}
        rowKey={(r) => r.platform}
        columns={[
          { header: "Platform", cell: (r) => r.platform },
          { header: "Qualified", cell: (r) => <Money value={r.qualified} /> },
          { header: "Identify", cell: (r) => <Money value={r.identify} /> },
          { header: "Total", cell: (r) => <Money value={r.total} /> },
        ]}
      />
    </WidgetCard>
  );
}
