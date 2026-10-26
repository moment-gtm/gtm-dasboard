/**
 * EXE-10 spotlight — the leadership call-to-action tile: how many large deals need attention,
 * the TCV at risk and the three biggest, with a jump to the full "Deals needing attention" widget.
 * Reuses the same query as DealsNeedingAttention (TanStack Query dedupes it).
 */
import { SpotlightCard } from "@/components/common/SpotlightCard";
import { Money } from "@/components/common/Money";
import { FlagBadge } from "@/components/data/opportunityColumns";
import { useDealsAttention } from "@/hooks/useExecutiveData";
import { useDrilldown } from "@/state/drilldown";

export function AttentionSpotlight() {
  const q = useDealsAttention();
  const open = useDrilldown((s) => s.open);
  const d = q.data;
  const meta = (d?.metric.meta ?? {}) as { total_tcv?: number };
  const top = [...(d?.rows ?? [])].sort((a, b) => b.tcv - a.tcv).slice(0, 3);
  const count = d?.metric.value ?? 0;

  return (
    <SpotlightCard
      testId="spotlight-attention"
      eyebrow="Needs your attention"
      tone={count ? "alert" : "ok"}
      title={
        count
          ? `${count} large deals are ageing, stalled or past close`
          : "No large deals need attention"
      }
      isLoading={q.isLoading}
      error={q.error}
      onRetry={() => q.refetch()}
      stats={[
        { label: "Deals flagged", value: count },
        { label: "TCV at risk", value: <Money value={meta.total_tcv ?? 0} /> },
      ]}
      actions={
        <>
          <button
            type="button"
            className="btn btn-primary"
            onClick={() =>
              open({ metricId: "EXE-10", segment: null, title: "Deals needing attention" })
            }
            data-testid="spotlight-review"
          >
            Review flagged deals
          </button>
          <a href="#deals-attention" className="btn no-underline">
            See breakdown ↓
          </a>
        </>
      }
    >
      {top.length ? (
        <ol className="m-0 flex list-none flex-col gap-2 p-0" aria-label="Largest flagged deals">
          {top.map((r) => (
            <li
              key={r.opportunity_id}
              className="flex items-center justify-between gap-2 rounded-xl px-3 py-2 text-sm"
              style={{ background: "var(--spotlight-row)" }}
            >
              <span className="min-w-0 truncate" title={`${r.name} — ${r.account_name}`}>
                {r.account_name}
              </span>
              <span className="flex shrink-0 items-center gap-2">
                <span className="font-semibold tabular">
                  <Money value={r.tcv} />
                </span>
                <FlagBadge flag={r.flag} />
              </span>
            </li>
          ))}
        </ol>
      ) : null}
    </SpotlightCard>
  );
}
