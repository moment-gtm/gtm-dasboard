/** FR-ACC-02 / ACC-02 — whitespace by practice: how much of the unsold space is already being pursued. */
import { ChartTable } from "@/components/charts/ChartTable";
import { ProgressToTarget } from "@/components/charts/ProgressToTarget";
import { WidgetCard } from "@/components/common/WidgetCard";
import { useWhitespace } from "@/hooks/useAccountsData";
import { formatPct } from "@/utils/format";

interface Row {
  practice: string;
  sold: number;
  open: number;
  not_addressed: number;
  pursued_share: number | null;
}

export function WhitespaceSummary() {
  const q = useWhitespace();
  const rows = (q.data?.breakdown ?? []) as unknown as Row[];
  const meta = (q.data?.meta ?? {}) as {
    whitespace?: number;
    pursued?: number;
    not_addressed?: number;
  };
  return (
    <WidgetCard
      testId="widget-whitespace"
      title="Whitespace summary"
      description="Of the account-practice pairs not yet sold, the share with an open pursuit."
      metricId="ACC-02"
      status={q.data?.status}
      statusBasis={q.data?.status_basis}
      isLoading={q.isLoading}
      isFetching={q.isFetching}
      error={q.error}
      onRetry={() => q.refetch()}
      empty={q.data && rows.length === 0 ? "no-match-filters" : false}
    >
      <div className="flex flex-col gap-3">
        <p className="m-0 text-sm" data-testid="whitespace-summary">
          <span className="text-2xl font-semibold">{formatPct(q.data?.value)}</span>{" "}
          <span style={{ color: "var(--ink-2)" }}>
            of {meta.whitespace} whitespace pairs are pursued · {meta.not_addressed} not addressed
          </span>
        </p>
        <ProgressToTarget
          testIdPrefix="whitespace"
          rows={rows.map((r) => ({
            key: r.practice,
            label: r.practice,
            value: r.pursued_share,
            goal: q.data?.goal,
            detail: `${r.open} open · ${r.not_addressed} not addressed`,
          }))}
        />
        <ChartTable
          caption="Whitespace by practice"
          rows={rows}
          rowKey={(r) => r.practice}
          columns={[
            { header: "Practice", cell: (r) => r.practice },
            { header: "Sold", cell: (r) => r.sold },
            { header: "Open", cell: (r) => r.open },
            { header: "Not addressed", cell: (r) => r.not_addressed },
            { header: "Pursued share", cell: (r) => formatPct(r.pursued_share) },
          ]}
        />
      </div>
    </WidgetCard>
  );
}
