/** Pursuits & Wins (FR-PUR-01..05) — composes shared components only. Margin (PUR-06) is restricted-only. */
import { EmptyState } from "@/components/common/EmptyState";
import { ErrorState } from "@/components/common/ErrorState";
import { ExportViewButton } from "@/components/common/ExportViewButton";
import {
  HeadlineScorecard,
  HeadlineSpotlight,
  toHeadlines,
} from "@/components/common/ModuleHeadlines";
import { BentoGrid, BentoItem, BentoRow } from "@/components/layout/BentoGrid";
import { ModuleLayout } from "@/components/layout/ModuleLayout";
import { BidDiscipline } from "@/components/widgets/pursuits/BidDiscipline";
import { LossReasons } from "@/components/widgets/pursuits/LossReasons";
import { MarginBidVsDelivery } from "@/components/widgets/pursuits/MarginBidVsDelivery";
import { OralsConversion } from "@/components/widgets/pursuits/OralsConversion";
import { SourceMix } from "@/components/widgets/pursuits/SourceMix";
import { WinRateTrend } from "@/components/widgets/pursuits/WinRateTrend";
import {
  useBidDiscipline,
  useLossReasons,
  useMargin,
  useOralsConversion,
  useSourceMix,
  useWinRate,
} from "@/hooks/usePursuitsData";
import { useMe } from "@/hooks/useReference";

/** Headline metrics; margin (PUR-06) is only fetched for restricted personas. */
function useHeadlines() {
  const restricted = !!useMe().data?.restricted;
  return toHeadlines([
    useWinRate(),
    useLossReasons(),
    useSourceMix(),
    useBidDiscipline(),
    useOralsConversion(),
    useMargin(restricted),
  ]);
}

export function Pursuits() {
  const me = useMe();
  const restricted = !!me.data?.restricted;
  const description =
    "Win rate, loss reasons, deal-source performance and bid discipline — where Moment wins and loses.";

  if (me.isLoading) return <div className="skeleton" style={{ height: 320 }} />;
  if (me.isError) return <ErrorState error={me.error} onRetry={() => me.refetch()} />;
  if (me.data && !me.data.modules.includes("pursuits"))
    return (
      <ModuleLayout title="Pursuits & Wins" description={description}>
        <div data-testid="access-denied">
          <EmptyState
            reason="access-denied"
            hint={`${me.data.label} personas use ${me.data.modules.join(", ").replace(/_/g, " ")}. Switch persona, or ask Sales Operations to review your access group.`}
          />
        </div>
      </ModuleLayout>
    );

  return (
    <ModuleLayout
      eyebrow="Win / loss"
      title="Pursuits & Wins"
      description={description}
      highlights={<HeadlineScorecard label="Pursuits scorecard" useHeadlines={useHeadlines} />}
      actions={<ExportViewButton module="pursuits" />}
    >
      <div data-testid="pursuits-view">
        <BentoGrid>
          <BentoRow>
            <BentoItem span={8}>
              <WinRateTrend />
            </BentoItem>
            <BentoItem span={4} sticky>
              <HeadlineSpotlight useHeadlines={useHeadlines} />
            </BentoItem>
          </BentoRow>
          <BentoItem span={6}>
            <LossReasons />
          </BentoItem>
          <BentoItem span={6}>
            <SourceMix />
          </BentoItem>
          <BentoItem span={6}>
            <BidDiscipline />
          </BentoItem>
          <BentoItem span={6}>
            <OralsConversion />
          </BentoItem>
          {restricted ? (
            <BentoItem span={12}>
              <MarginBidVsDelivery />
            </BentoItem>
          ) : null}
        </BentoGrid>
      </div>
    </ModuleLayout>
  );
}
