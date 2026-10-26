/** FR-PIP-03 / PIP-03 — open TCV by practice, lead vs contributing (from opportunity line items). */
import { ChartTable } from "@/components/charts/ChartTable";
import { StackedSplitChart } from "@/components/charts/StackedSplitChart";
import { Money } from "@/components/common/Money";
import { WidgetCard } from "@/components/common/WidgetCard";
import { usePipelineByPractice } from "@/hooks/usePipelineData";
import { useDrilldown } from "@/state/drilldown";
import { formatMoney } from "@/utils/format";

interface PracticeRow {
  practice: string;
  lead: number;
  contributing: number;
  total: number;
}

const PARTS = [
  { key: "lead", label: "Lead practice" },
  { key: "contributing", label: "Contributing practice" },
];

export function PipelineByPractice() {
  const q = usePipelineByPractice();
  const open = useDrilldown((s) => s.open);
  const rows = (q.data?.breakdown ?? []) as unknown as PracticeRow[];
  const drill = (practice: string, part: string) =>
    open({
      metricId: "PIP-03",
      segment: `${practice}|${part}`,
      title: `${practice} — ${part} pipeline`,
    });
  const summary = rows
    .map(
      (r) =>
        `${r.practice}: lead ${formatMoney(r.lead)}, contributing ${formatMoney(r.contributing)}`,
    )
    .join("; ");
  return (
    <WidgetCard
      testId="widget-pipeline-by-practice"
      title="Pipeline by practice"
      description="Open TCV by practice from line items, split into deals the practice leads and deals it contributes to."
      metricId="PIP-03"
      isLoading={q.isLoading}
      isFetching={q.isFetching}
      error={q.error}
      onRetry={() => q.refetch()}
      empty={q.data && rows.every((r) => r.total === 0) ? "no-match-filters" : false}
    >
      <StackedSplitChart
        data={rows.map((r) => ({
          category: r.practice,
          lead: r.lead,
          contributing: r.contributing,
        }))}
        parts={PARTS}
        onSelect={drill}
        ariaLabel={`Open pipeline by practice. ${summary}`}
      />
      <ChartTable
        caption="Open pipeline by practice"
        rows={rows}
        rowKey={(r) => r.practice}
        columns={[
          { header: "Practice", cell: (r) => r.practice },
          { header: "Lead", cell: (r) => <Money value={r.lead} /> },
          { header: "Contributing", cell: (r) => <Money value={r.contributing} /> },
          { header: "Total", cell: (r) => <Money value={r.total} /> },
        ]}
      />
    </WidgetCard>
  );
}
