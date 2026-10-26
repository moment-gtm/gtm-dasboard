/** FR-EXE-05 / EXE-10 — large open deals ageing (61–90 days) or stalled (>90 days) in stage. */
import { useState } from "react";
import { Heatmap, type HeatmapRow } from "@/components/charts/Heatmap";
import { StackedSplitChart } from "@/components/charts/StackedSplitChart";
import { DataRegister } from "@/components/data/DataRegister";
import { FlagBadge, flagColumn, opportunityColumns } from "@/components/data/opportunityColumns";
import { Money } from "@/components/common/Money";
import { WidgetCard } from "@/components/common/WidgetCard";
import { useDealsAttention } from "@/hooks/useExecutiveData";
import { useDrilldown } from "@/state/drilldown";
import { tokens } from "@/theme/tokens";
import type { OpportunityRow } from "@/api/types";
import { formatMoney } from "@/utils/format";

const FLAGS = ["Ageing", "Stalled", "Past close date"] as const;
const FLAG_KEYS: Record<string, (typeof FLAGS)[number]> = {
  ageing: "Ageing",
  stalled: "Stalled",
  past_close: "Past close date",
};
const PARTS = [
  { key: "ageing", label: "Ageing (61–90 days)" },
  { key: "stalled", label: "Stalled (over 90 days)" },
  { key: "past_close", label: "Past close date" },
];

interface VerticalFlags {
  vertical: string;
  count: number;
  tcv: number;
  [flag: string]: unknown;
}

function Tile({ label, value, sub }: { label: string; value: React.ReactNode; sub?: string }) {
  return (
    <div className="card flex min-w-0 flex-col gap-1 p-3" data-testid="attention-tile">
      <p className="m-0 text-sm font-medium" style={{ color: "var(--ink-2)" }}>
        {label}
      </p>
      <p className="m-0 text-2xl font-semibold">{value}</p>
      {sub ? (
        <p className="m-0 text-xs" style={{ color: "var(--ink-2)" }}>
          {sub}
        </p>
      ) : null}
    </div>
  );
}

/** Top deals by TCV with a days-in-stage bar and the review / stalled threshold lines. */
function TopDeals({
  rows,
  reviewDays,
  stalledDays,
  onSelect,
}: {
  rows: OpportunityRow[];
  reviewDays: number;
  stalledDays: number;
  onSelect: (flag: string) => void;
}) {
  const top = [...rows].sort((a, b) => b.tcv - a.tcv).slice(0, 5);
  const scale = Math.max(stalledDays * 1.3, ...top.map((r) => r.days_in_stage ?? 0));
  const pct = (d: number) => `${Math.min(100, (d / scale) * 100)}%`;
  if (!top.length) return null;
  return (
    <ol
      className="m-0 flex list-none flex-col gap-2 p-0"
      aria-label="Largest deals needing attention"
    >
      {top.map((r) => {
        const days = r.days_in_stage ?? 0;
        const tone = days > stalledDays ? tokens.status.off_track.fill : tokens.status.watch.fill;
        return (
          <li
            key={r.opportunity_id}
            className="grid items-center gap-2"
            style={{ gridTemplateColumns: "minmax(0,14rem) 1fr auto" }}
          >
            <span className="min-w-0 truncate text-sm" title={`${r.name} — ${r.account_name}`}>
              {r.account_name} · <Money value={r.tcv} />
            </span>
            <span
              className="relative h-3 rounded-sm"
              style={{ background: tokens.page, border: `1px solid ${tokens.grid}` }}
              role="img"
              aria-label={`${r.name}: ${days} days in stage; review line ${reviewDays}, stalled line ${stalledDays}`}
            >
              <span
                className="absolute top-0 left-0 h-full rounded-sm"
                style={{ width: pct(days), background: tone }}
              />
              <span
                className="absolute top-[-3px] h-[18px] w-px"
                style={{ left: pct(reviewDays), background: tokens.ink.secondary }}
              />
              <span
                className="absolute top-[-3px] h-[18px] w-px"
                style={{ left: pct(stalledDays), background: tokens.ink.primary }}
              />
            </span>
            <button
              type="button"
              className="border-0 bg-transparent p-0"
              onClick={() => r.flag && onSelect(r.flag)}
              aria-label={`${r.name}: ${days} days, ${r.flag ?? "no flag"}. Show ${r.flag ?? ""} deals`}
            >
              <FlagBadge flag={r.flag} />
            </button>
          </li>
        );
      })}
      <li className="text-xs" style={{ color: "var(--ink-muted)" }}>
        Bar = days in stage · thin lines mark {reviewDays} days (Ageing) and {stalledDays} days
        (Stalled).
      </li>
    </ol>
  );
}

export function DealsNeedingAttention() {
  const q = useDealsAttention();
  const open = useDrilldown((s) => s.open);
  const [showAll, setShowAll] = useState(false);
  const d = q.data;
  const meta = (d?.metric.meta ?? {}) as {
    value_threshold?: number;
    review_days?: number;
    stalled_days?: number;
    total_tcv?: number;
    by_vertical?: VerticalFlags[];
  };
  const reviewDays = meta.review_days ?? 60;
  const stalledDays = meta.stalled_days ?? 90;
  const byVertical = meta.by_vertical ?? [];
  const description = `Open deals of ${formatMoney(meta.value_threshold ?? 2_000_000)} or more that have been in their current stage over ${reviewDays} days — Ageing ${reviewDays + 1}–${stalledDays}, Stalled over ${stalledDays} — or are past their close date.`;
  const drill = (segment: string | null, title: string) =>
    open({ metricId: "EXE-10", segment, title });
  const flagTotals = (key: "count" | "tcv") =>
    Object.fromEntries(
      Object.entries(FLAG_KEYS).map(([k, flag]) => [
        k,
        byVertical.reduce(
          (s, v) => s + ((v[flag] as { count: number; tcv: number } | undefined)?.[key] ?? 0),
          0,
        ),
      ]),
    );
  const tcvByFlag = flagTotals("tcv");
  const countByFlag = flagTotals("count");
  const heatRows: HeatmapRow[] = byVertical.map((v) => ({
    key: v.vertical,
    label: v.vertical,
    cells: Object.fromEntries(
      FLAGS.map((f) => {
        const c = v[f] as { count: number; tcv: number } | undefined;
        return [f, { count: c?.count ?? 0, value: c?.tcv ?? 0 }];
      }),
    ),
  }));
  return (
    <WidgetCard
      testId="widget-deals-attention"
      title="Deals needing attention"
      description={description}
      metricId="EXE-10"
      isLoading={q.isLoading}
      isFetching={q.isFetching}
      error={q.error}
      onRetry={() => q.refetch()}
      empty={d && d.rows.length === 0 && !d.aggregated_other ? "no-match-filters" : false}
      emptyHint="No large deals are ageing or stalled for the current filters — nothing needs attention."
    >
      {d ? (
        <div className="flex flex-col gap-4">
          <div
            className="grid gap-3"
            style={{ gridTemplateColumns: "repeat(auto-fit, minmax(10rem, 1fr))" }}
          >
            <Tile
              label="Deals needing attention"
              value={d.metric.value ?? 0}
              sub={d.metric.status_basis ?? undefined}
            />
            <Tile
              label="TCV at risk"
              value={<Money value={meta.total_tcv ?? 0} />}
              sub="Open TCV of flagged deals"
            />
            <Tile
              label="Stalled (over 90 days)"
              value={countByFlag.stalled ?? 0}
              sub="Highest risk — review first"
            />
          </div>
          {d.aggregated_other ? (
            <p
              className="m-0 rounded-md p-2 text-sm"
              data-testid="aggregated-other"
              style={{ background: "var(--page)", border: "1px solid var(--grid)" }}
            >
              {d.aggregated_other.note} ({d.aggregated_other.count} deals,{" "}
              <Money value={d.aggregated_other.tcv} />)
            </p>
          ) : null}
          <section aria-label="Flagged TCV by reason" className="flex flex-col gap-1">
            <h4 className="m-0 text-sm font-semibold">Why deals are flagged (TCV)</h4>
            <StackedSplitChart
              data={[{ category: "Flagged deals", ...tcvByFlag }]}
              parts={PARTS}
              onSelect={(_c, part) =>
                drill(FLAG_KEYS[part] ?? null, `Deals needing attention — ${FLAG_KEYS[part] ?? ""}`)
              }
              ariaLabel={`Flagged TCV by reason. ${PARTS.map((p) => `${p.label}: ${formatMoney(tcvByFlag[p.key] ?? 0)}`).join("; ")}`}
            />
          </section>
          <section aria-label="Flagged deals by vertical" className="flex flex-col gap-1">
            <h4 className="m-0 text-sm font-semibold">
              Where they sit — vertical × reason (deals · TCV)
            </h4>
            <Heatmap
              rows={heatRows}
              columns={FLAGS.map((f) => ({ key: f, label: <FlagBadge flag={f} /> }))}
              formatValue={formatMoney}
              onSelect={(vertical, flag) =>
                drill(`${vertical}|${flag}`, `Deals needing attention — ${flag} (${vertical})`)
              }
              ariaLabel="Deals needing attention by vertical and reason"
            />
          </section>
          <section aria-label="Largest flagged deals" className="flex flex-col gap-1">
            <h4 className="m-0 text-sm font-semibold">Largest flagged deals — days in stage</h4>
            <TopDeals
              rows={d.rows}
              reviewDays={reviewDays}
              stalledDays={stalledDays}
              onSelect={(f) => drill(f, `Deals needing attention — ${f}`)}
            />
          </section>
          <section aria-label="All flagged deals" className="flex flex-col gap-2">
            <button
              type="button"
              className="self-start text-sm"
              aria-expanded={showAll}
              onClick={() => setShowAll((v) => !v)}
              data-testid="attention-toggle-register"
            >
              {showAll ? "Hide" : "Show"} all {d.rows.length} deals ·{" "}
              <Money value={d.rows.reduce((s, r) => s + r.tcv, 0)} /> TCV
            </button>
            {showAll ? (
              <DataRegister
                testId="attention-register"
                caption="Deals needing attention"
                columns={[flagColumn, ...opportunityColumns]}
                data={d.rows}
                getRowId={(r) => r.opportunity_id}
                rowHighlight={(r) => r.flag === "Stalled"}
              />
            ) : null}
          </section>
        </div>
      ) : null}
    </WidgetCard>
  );
}
