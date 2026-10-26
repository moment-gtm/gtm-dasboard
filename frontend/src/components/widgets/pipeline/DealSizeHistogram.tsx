/** FR-PIP-04 / PIP-05 — open deals by deal-size band (bands come from ref_size_band). */
import { ChartTable } from "@/components/charts/ChartTable";
import { DistributionHistogram } from "@/components/charts/DistributionHistogram";
import { Money } from "@/components/common/Money";
import { WidgetCard } from "@/components/common/WidgetCard";
import { useSizeDistribution } from "@/hooks/usePipelineData";
import { useDrilldown } from "@/state/drilldown";
import { formatMoney } from "@/utils/format";

interface BandRow {
  band: string;
  label: string;
  count: number;
  tcv: number;
}

export function DealSizeHistogram() {
  const q = useSizeDistribution();
  const open = useDrilldown((s) => s.open);
  const rows = (q.data?.breakdown ?? []) as unknown as BandRow[];
  const drill = (band: string) => {
    const b = rows.find((r) => r.band === band);
    open({ metricId: "PIP-05", segment: band, title: `Open pipeline — ${b?.label ?? band}` });
  };
  return (
    <WidgetCard
      testId="widget-deal-size"
      title="Deal-size distribution"
      description="Open deals by TCV band. Select a band to list its deals."
      metricId="PIP-05"
      isLoading={q.isLoading}
      isFetching={q.isFetching}
      error={q.error}
      onRetry={() => q.refetch()}
      empty={q.data && !q.data.value ? "no-match-filters" : false}
    >
      <DistributionHistogram
        bands={rows.map((r) => ({ key: r.band, label: r.label, count: r.count, value: r.tcv }))}
        onSelect={drill}
        formatValue={formatMoney}
        ariaLabel={`Deal-size distribution. ${rows.map((r) => `${r.label}: ${r.count} deals`).join("; ")}`}
      />
      <ChartTable
        caption="Deal-size distribution"
        rows={rows}
        rowKey={(r) => r.band}
        columns={[
          { header: "Band", cell: (r) => r.label },
          { header: "Deals", cell: (r) => r.count },
          { header: "TCV", cell: (r) => <Money value={r.tcv} /> },
        ]}
      />
    </WidgetCard>
  );
}
