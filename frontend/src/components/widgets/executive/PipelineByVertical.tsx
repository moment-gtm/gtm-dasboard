/** FR-EXE-04 / EXE-09 — open pipeline by vertical, qualified vs early-stage (Identify). */
import { ChartTable } from "@/components/charts/ChartTable";
import { StackedSplitChart } from "@/components/charts/StackedSplitChart";
import { Money } from "@/components/common/Money";
import { WidgetCard } from "@/components/common/WidgetCard";
import { usePipelineByVertical } from "@/hooks/useExecutiveData";
import { useDrilldown } from "@/state/drilldown";
import { formatMoney } from "@/utils/format";

interface VerticalRow {
  vertical: string;
  qualified: number;
  identify: number;
  total: number;
}

const PARTS = [
  { key: "qualified", label: "Qualified (Qualify or later)" },
  { key: "identify", label: "Early stage (Identify)" },
];

export function PipelineByVertical() {
  const q = usePipelineByVertical();
  const open = useDrilldown((s) => s.open);
  const rows = (q.data?.breakdown ?? []) as unknown as VerticalRow[];
  const drill = (vertical: string, part: string) =>
    open({
      metricId: "EXE-09",
      segment: `${vertical}|${part}`,
      title: `${vertical} — ${part === "qualified" ? "qualified" : "Identify"} pipeline`,
    });
  const summary = rows
    .map(
      (r) =>
        `${r.vertical}: qualified ${formatMoney(r.qualified)}, Identify ${formatMoney(r.identify)}`,
    )
    .join("; ");
  return (
    <WidgetCard
      testId="widget-pipeline-by-vertical"
      title="Open pipeline by vertical"
      description="Open TCV by account vertical, split into qualified and early-stage (Identify)."
      metricId="EXE-09"
      isLoading={q.isLoading}
      isFetching={q.isFetching}
      error={q.error}
      onRetry={() => q.refetch()}
      empty={q.data && rows.every((r) => r.total === 0) ? "no-match-filters" : false}
    >
      <StackedSplitChart
        data={rows.map((r) => ({
          category: r.vertical,
          qualified: r.qualified,
          identify: r.identify,
        }))}
        parts={PARTS}
        onSelect={drill}
        ariaLabel={`Open pipeline by vertical. ${summary}`}
      />
      <ChartTable
        caption="Open pipeline by vertical"
        rows={rows}
        rowKey={(r) => r.vertical}
        columns={[
          { header: "Vertical", cell: (r) => r.vertical },
          { header: "Qualified", cell: (r) => <Money value={r.qualified} /> },
          { header: "Identify", cell: (r) => <Money value={r.identify} /> },
          { header: "Total", cell: (r) => <Money value={r.total} /> },
        ]}
        onSelect={(r) => drill(r.vertical, "qualified")}
        selectLabel={(r) => `View ${r.vertical} qualified deals`}
      />
    </WidgetCard>
  );
}
