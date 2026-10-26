/** FR-PAR-01 / PAR-01 — open partner pipeline by partner, split Sourced vs Influenced. */
import { ChartTable } from "@/components/charts/ChartTable";
import { StackedSplitChart } from "@/components/charts/StackedSplitChart";
import { Money } from "@/components/common/Money";
import { WidgetCard } from "@/components/common/WidgetCard";
import { usePartnerPipeline } from "@/hooks/usePartnersData";
import { formatPct } from "@/utils/format";

interface Row {
  partner: string;
  sourced_tcv: number;
  sourced_count: number;
  influenced_tcv: number;
  influenced_count: number;
  total_tcv: number;
}

export function PartnerPipeline() {
  const q = usePartnerPipeline();
  const rows = (q.data?.breakdown ?? []) as unknown as Row[];
  const meta = (q.data?.meta ?? {}) as { partner_share_of_open?: number };
  return (
    <WidgetCard
      variant="hero"
      testId="widget-partner-pipeline"
      title="Pipeline by partner"
      description="Open partner-sourced and partner-influenced pipeline for each technology partner."
      metricId="PAR-01"
      isLoading={q.isLoading}
      isFetching={q.isFetching}
      error={q.error}
      onRetry={() => q.refetch()}
      empty={q.data && rows.length === 0 ? "no-match-filters" : false}
    >
      <div className="flex flex-col gap-3">
        <p className="m-0 text-sm" data-testid="partner-pipeline-total">
          <span className="text-2xl font-semibold">
            <Money value={q.data?.value} />
          </span>{" "}
          <span style={{ color: "var(--ink-2)" }}>
            open partner pipeline · {formatPct(meta.partner_share_of_open)} of all open pipeline
          </span>
        </p>
        <StackedSplitChart
          ariaLabel="Open partner pipeline by partner, sourced and influenced"
          parts={[
            { key: "sourced", label: "Partner-sourced" },
            { key: "influenced", label: "Partner-influenced" },
          ]}
          data={rows.map((r) => ({
            category: r.partner,
            sourced: r.sourced_tcv,
            influenced: r.influenced_tcv,
          }))}
        />
        <ChartTable
          caption="Open partner pipeline"
          rows={rows}
          rowKey={(r) => r.partner}
          columns={[
            { header: "Partner", cell: (r) => r.partner },
            { header: "Sourced", cell: (r) => <Money value={r.sourced_tcv} /> },
            { header: "Sourced deals", cell: (r) => r.sourced_count },
            { header: "Influenced", cell: (r) => <Money value={r.influenced_tcv} /> },
            { header: "Influenced deals", cell: (r) => r.influenced_count },
          ]}
        />
      </div>
    </WidgetCard>
  );
}
