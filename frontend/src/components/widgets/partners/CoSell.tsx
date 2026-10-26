/** FR-PAR-02 / PAR-02 — win rate with vs without a partner on the deal. */
import { ChartTable } from "@/components/charts/ChartTable";
import { ProgressToTarget } from "@/components/charts/ProgressToTarget";
import { Money } from "@/components/common/Money";
import { WidgetCard } from "@/components/common/WidgetCard";
import { useCoSell } from "@/hooks/usePartnersData";
import { formatPct } from "@/utils/format";

interface Row {
  group: "with_partner" | "without_partner";
  label: string;
  won: number;
  lost: number;
  decided: number;
  won_tcv: number;
  win_rate: number | null;
}

export function CoSell() {
  const q = useCoSell();
  const rows = (q.data?.breakdown ?? []) as unknown as Row[];
  const meta = (q.data?.meta ?? {}) as {
    partner_share_of_bookings?: number;
    co_sell_wins?: number;
  };
  const withP = rows.find((r) => r.group === "with_partner");
  const without = rows.find((r) => r.group === "without_partner");
  const delta =
    withP?.win_rate != null && without?.win_rate != null ? withP.win_rate - without.win_rate : null;
  return (
    <WidgetCard
      testId="widget-co-sell"
      title="Co-sell performance"
      description="Win rate on decided deals with a partner involved versus without."
      metricId="PAR-02"
      isLoading={q.isLoading}
      isFetching={q.isFetching}
      error={q.error}
      onRetry={() => q.refetch()}
      empty={q.data && !rows.some((r) => r.decided > 0) ? "no-match-filters" : false}
      emptyHint="No decided deals in the current filters."
    >
      <div className="flex flex-col gap-3">
        <p className="m-0 text-sm" data-testid="co-sell-summary">
          {delta == null ? (
            "Not enough decided deals to compare."
          ) : (
            <>
              <span className="text-2xl font-semibold">
                {delta >= 0 ? "+" : "−"}
                {formatPct(Math.abs(delta))}
              </span>{" "}
              <span style={{ color: "var(--ink-2)" }}>
                win rate with a partner · partners touched{" "}
                {formatPct(meta.partner_share_of_bookings)} of bookings · {meta.co_sell_wins}{" "}
                co-sell wins
              </span>
            </>
          )}
        </p>
        <ProgressToTarget
          testIdPrefix="cosell"
          rows={rows.map((r) => ({
            key: r.group,
            label: r.label,
            value: r.win_rate,
            goal: r.group === "with_partner" ? q.data?.goal : null,
            detail: `${r.won} won / ${r.decided} decided`,
          }))}
        />
        <ChartTable
          caption="Win rate with and without a partner"
          rows={rows}
          rowKey={(r) => r.group}
          columns={[
            { header: "Group", cell: (r) => r.label },
            { header: "Won", cell: (r) => r.won },
            { header: "Lost", cell: (r) => r.lost },
            { header: "Won TCV", cell: (r) => <Money value={r.won_tcv} /> },
            { header: "Win rate", cell: (r) => formatPct(r.win_rate) },
          ]}
        />
      </div>
    </WidgetCard>
  );
}
