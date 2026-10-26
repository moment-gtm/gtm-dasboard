/** FR-CAP-02 / CAP-02 — RFP turnaround: share of responses submitted within SLA, by quarter. */
import { ChartTable } from "@/components/charts/ChartTable";
import { WidgetCard } from "@/components/common/WidgetCard";
import { PctBars } from "@/components/widgets/pursuits/PctBars";
import { useRfpTurnaround } from "@/hooks/useCapacityData";
import { useDrilldown } from "@/state/drilldown";
import { formatDays, formatPct } from "@/utils/format";

interface Row {
  quarter: string;
  label: string;
  submitted: number;
  on_time: number;
  sla_share: number | null;
  avg_days: number | null;
  partial: boolean;
}

export function RfpTurnaround() {
  const q = useRfpTurnaround();
  const open = useDrilldown((s) => s.open);
  const rows = (q.data?.breakdown ?? []) as unknown as Row[];
  const meta = (q.data?.meta ?? {}) as { submitted?: number; avg_days?: number | null };
  return (
    <WidgetCard
      testId="widget-rfp-turnaround"
      title="RFP turnaround"
      description="Share of RFP responses submitted within the SLA, by submission quarter."
      metricId="CAP-02"
      status={q.data?.status}
      statusBasis={q.data?.status_basis}
      isLoading={q.isLoading}
      isFetching={q.isFetching}
      error={q.error}
      onRetry={() => q.refetch()}
      empty={q.data && !meta.submitted ? "no-match-filters" : false}
      emptyHint="No submitted RFP responses in the current filters."
    >
      <div className="flex flex-col gap-3">
        <p className="m-0 text-sm" data-testid="rfp-turnaround-value">
          <span className="text-2xl font-semibold">{formatPct(q.data?.value)}</span>{" "}
          <span style={{ color: "var(--ink-2)" }}>
            within SLA · average {formatDays(meta.avg_days)} to submit
          </span>
        </p>
        <PctBars
          testIdPrefix="rfp"
          rows={rows.map((r) => ({
            key: r.quarter,
            label: r.partial ? `${r.label} (in progress)` : r.label,
            value: r.sla_share,
            goal: q.data?.goal,
            detail: `${r.on_time} of ${r.submitted} on time`,
          }))}
          onSelect={(quarter) =>
            open({ metricId: "CAP-02", segment: quarter, title: `Submitted — ${quarter}` })
          }
        />
        <ChartTable
          caption="RFP turnaround by quarter"
          rows={rows}
          rowKey={(r) => r.quarter}
          columns={[
            { header: "Quarter", cell: (r) => r.label },
            { header: "Submitted", cell: (r) => r.submitted },
            { header: "On time", cell: (r) => r.on_time },
            { header: "Within SLA", cell: (r) => formatPct(r.sla_share) },
            { header: "Avg days", cell: (r) => formatDays(r.avg_days) },
          ]}
        />
      </div>
    </WidgetCard>
  );
}
