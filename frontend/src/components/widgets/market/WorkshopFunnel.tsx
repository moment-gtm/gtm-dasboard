/** FR-MKT-02 / MKT-02 — Discovery workshop conversion funnel (Workshops -> Opps <=90d -> Qualified -> Won). */
import { ChartTable } from "@/components/charts/ChartTable";
import { FunnelChart } from "@/components/charts/FunnelChart";
import { Money } from "@/components/common/Money";
import { WidgetCard } from "@/components/common/WidgetCard";
import { useWorkshopFunnel } from "@/hooks/useMarketData";
import { useDrilldown } from "@/state/drilldown";
import { formatDays, formatMoney, formatPct } from "@/utils/format";

interface StageRow {
  key: string;
  stage: string;
  label: string;
  count: number;
  tcv: number;
  conversion_from_start: number | null;
  step_conversion: number | null;
}

export function WorkshopFunnel() {
  const q = useWorkshopFunnel();
  const open = useDrilldown((s) => s.open);
  const rows = (q.data?.breakdown ?? []) as unknown as StageRow[];
  const meta = (q.data?.meta ?? {}) as {
    workshops_held?: number;
    opps_created_90d?: number;
    pipeline_originated_tcv?: number;
    avg_days_to_opportunity?: number | null;
  };

  return (
    <WidgetCard
      testId="widget-workshop-funnel"
      title="Discovery workshop funnel"
      description="Workshops held through opportunities created within 90 days, qualified and won (50% conversion goal)."
      metricId="MKT-02"
      status={q.data?.status}
      statusBasis={q.data?.status_basis}
      isLoading={q.isLoading}
      isFetching={q.isFetching}
      error={q.error}
      onRetry={() => q.refetch()}
      empty={q.data && !meta.workshops_held ? "no-match-filters" : false}
      emptyHint="No discovery workshops match the current filters."
    >
      <div className="flex flex-col gap-3">
        <p className="m-0 text-sm" data-testid="workshop-funnel-summary">
          <span className="text-2xl font-semibold">{formatPct(q.data?.value)}</span>{" "}
          <span style={{ color: "var(--ink-2)" }}>
            workshop-to-opportunity conversion vs {formatPct(q.data?.goal)} goal ·{" "}
            <strong>{formatMoney(meta.pipeline_originated_tcv)}</strong> pipeline originated
            {meta.avg_days_to_opportunity != null
              ? ` · avg ${formatDays(meta.avg_days_to_opportunity)} to opp`
              : ""}
          </span>
        </p>
        <FunnelChart
          steps={rows.map((r, idx) => ({
            key: r.key,
            label: r.label,
            count: r.count,
            value: r.tcv,
            conversion: idx < rows.length - 1 ? rows[idx + 1]?.step_conversion : null,
            note:
              r.conversion_from_start != null
                ? `${formatPct(r.conversion_from_start)} of held`
                : undefined,
          }))}
          onSelect={(key) => {
            const stage = rows.find((r) => r.key === key);
            open({
              metricId: "MKT-02",
              segment: key,
              title: `Workshop funnel — ${stage?.label ?? key}`,
            });
          }}
          formatValue={formatMoney}
          ariaLabel="Discovery workshop conversion funnel"
        />
        <ChartTable
          caption="Discovery workshop funnel stages"
          rows={rows}
          rowKey={(r) => r.key}
          columns={[
            { header: "Stage", cell: (r) => r.label },
            { header: "Count", cell: (r) => r.count },
            { header: "TCV", cell: (r) => <Money value={r.tcv} /> },
            { header: "Share of workshops", cell: (r) => formatPct(r.conversion_from_start) },
            { header: "Step conversion", cell: (r) => formatPct(r.step_conversion) },
          ]}
        />
      </div>
    </WidgetCard>
  );
}
