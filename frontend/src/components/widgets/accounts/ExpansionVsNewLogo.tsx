/** FR-ACC-03 / ACC-03 — fiscal-year wins from existing customers (expansion) vs new logos. */
import { ChartTable } from "@/components/charts/ChartTable";
import { ProgressToTarget } from "@/components/charts/ProgressToTarget";
import { Money } from "@/components/common/Money";
import { WidgetCard } from "@/components/common/WidgetCard";
import { useExpansion } from "@/hooks/useAccountsData";
import { formatPct } from "@/utils/format";

interface Row {
  kind: "expansion" | "new_logo";
  label: string;
  count: number;
  tcv: number;
  share: number | null;
}

export function ExpansionVsNewLogo() {
  const q = useExpansion();
  const rows = (q.data?.breakdown ?? []) as unknown as Row[];
  const meta = (q.data?.meta ?? {}) as { deals?: number };
  return (
    <WidgetCard
      testId="widget-expansion"
      title="Expansion vs new logo"
      description="Won TCV split by whether the account had a booking in the prior 24 months."
      metricId="ACC-03"
      isLoading={q.isLoading}
      isFetching={q.isFetching}
      error={q.error}
      onRetry={() => q.refetch()}
      empty={q.data && !meta.deals ? "no-match-filters" : false}
      emptyHint="No won deals in the current filters."
    >
      <div className="flex flex-col gap-3">
        <p className="m-0 text-sm" data-testid="expansion-summary">
          <span className="text-2xl font-semibold">{formatPct(q.data?.value)}</span>{" "}
          <span style={{ color: "var(--ink-2)" }}>of won TCV is expansion</span>
        </p>
        <ProgressToTarget
          testIdPrefix="expansion"
          rows={rows.map((r) => ({
            key: r.kind,
            label: r.label,
            value: r.share,
            detail: `${r.count} deals`,
          }))}
        />
        <ChartTable
          caption="Expansion vs new logo"
          rows={rows}
          rowKey={(r) => r.kind}
          columns={[
            { header: "Type", cell: (r) => r.label },
            { header: "Deals", cell: (r) => r.count },
            { header: "TCV", cell: (r) => <Money value={r.tcv} /> },
            { header: "Share", cell: (r) => formatPct(r.share) },
          ]}
        />
      </div>
    </WidgetCard>
  );
}
