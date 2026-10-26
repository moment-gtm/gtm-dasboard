/** FR-OFF-02 / OFF-02 — attach rate: won deals by number of practices involved. */
import { ChartTable } from "@/components/charts/ChartTable";
import { ProgressToTarget } from "@/components/charts/ProgressToTarget";
import { Money } from "@/components/common/Money";
import { WidgetCard } from "@/components/common/WidgetCard";
import { useAttachRate } from "@/hooks/useOfferingsData";
import { formatPct } from "@/utils/format";

interface Row {
  practices: number;
  label: string;
  deals: number;
  tcv: number;
  share: number | null;
}

export function AttachRate() {
  const q = useAttachRate();
  const rows = (q.data?.breakdown ?? []) as unknown as Row[];
  const meta = (q.data?.meta ?? {}) as { deals?: number; multi_practice?: number };
  return (
    <WidgetCard
      testId="widget-attach-rate"
      title="Attach rate"
      description="Share of won deals that involved two or more practices."
      metricId="OFF-02"
      status={q.data?.status}
      statusBasis={q.data?.status_basis}
      isLoading={q.isLoading}
      isFetching={q.isFetching}
      error={q.error}
      onRetry={() => q.refetch()}
      empty={q.data && !meta.deals ? "no-match-filters" : false}
      emptyHint="No won deals in the current filters."
    >
      <div className="flex flex-col gap-3">
        <p className="m-0 text-sm" data-testid="attach-rate-value">
          <span className="text-2xl font-semibold">{formatPct(q.data?.value)}</span>{" "}
          <span style={{ color: "var(--ink-2)" }}>
            {meta.multi_practice} of {meta.deals} won deals attach a second practice
          </span>
        </p>
        <ProgressToTarget
          testIdPrefix="attach"
          rows={rows.map((r) => ({
            key: String(r.practices),
            label: r.label,
            value: r.share,
            detail: `${r.deals} deals`,
          }))}
        />
        <ChartTable
          caption="Won deals by practices involved"
          rows={rows}
          rowKey={(r) => String(r.practices)}
          columns={[
            { header: "Practices", cell: (r) => r.label },
            { header: "Deals", cell: (r) => r.deals },
            { header: "TCV", cell: (r) => <Money value={r.tcv} /> },
            { header: "Share", cell: (r) => formatPct(r.share) },
          ]}
        />
      </div>
    </WidgetCard>
  );
}
