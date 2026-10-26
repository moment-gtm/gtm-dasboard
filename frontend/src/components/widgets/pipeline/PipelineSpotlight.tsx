/**
 * Pipeline spotlight — Pipeline metrics carry no thresholds (so no status), so the leadership tile
 * leads with the ageing exposure instead: deals past the review line (PIP-02), open TCV and count
 * (PIP-05), week-over-week change (PIP-07) and overall conversion (PIP-01). Values only, as served
 * by the semantic layer; the same queries the widgets use (deduped).
 */
import { Money } from "@/components/common/Money";
import { SpotlightCard } from "@/components/common/SpotlightCard";
import {
  useAgeing,
  useFunnel,
  useSizeDistribution,
  useStageMovement,
} from "@/hooks/usePipelineData";
import { formatCount, formatPct } from "@/utils/format";

export function PipelineSpotlight() {
  const ageing = useAgeing();
  const size = useSizeDistribution();
  const movement = useStageMovement();
  const funnel = useFunnel();
  const pastReview = (ageing.data?.meta as { past_review?: number } | undefined)?.past_review;
  const open = ageing.data?.value ?? null;
  const totalTcv = (size.data?.meta as { total_tcv?: number } | undefined)?.total_tcv ?? null;
  const delta = movement.data?.value ?? null;
  const qs = [ageing, size, movement, funnel];

  return (
    <SpotlightCard
      testId="spotlight-pipeline"
      eyebrow="Needs your attention"
      title={
        pastReview != null && open != null
          ? `${formatCount(pastReview)} of ${formatCount(open)} open deals are past the review line`
          : "Pipeline at a glance"
      }
      isLoading={qs.some((q) => q.isLoading)}
      error={ageing.error}
      onRetry={() => ageing.refetch()}
      stats={[
        { label: "Open pipeline", value: <Money value={totalTcv} /> },
        { label: "Open deals", value: formatCount(open) },
      ]}
      actions={
        <a href="#pipeline-ageing" className="btn no-underline">
          See ageing ↓
        </a>
      }
    >
      <ul className="m-0 flex list-none flex-col gap-2 p-0 text-sm">
        <li
          className="flex items-center justify-between gap-2 rounded-xl px-3 py-2"
          style={{ background: "var(--spotlight-row)" }}
        >
          <span>Week-over-week change</span>
          <span className="font-semibold tabular">
            {delta != null && delta > 0 ? "+" : ""}
            <Money value={delta} />
          </span>
        </li>
        <li
          className="flex items-center justify-between gap-2 rounded-xl px-3 py-2"
          style={{ background: "var(--spotlight-row)" }}
        >
          <span>Identify → Closed Won conversion</span>
          <span className="font-semibold tabular">{formatPct(funnel.data?.value)}</span>
        </li>
      </ul>
    </SpotlightCard>
  );
}
