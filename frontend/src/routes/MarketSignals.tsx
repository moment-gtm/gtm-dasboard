/** Market Signals (FR-MKT-01..04) — composes shared components only. */
import { ExportViewButton } from "@/components/common/ExportViewButton";
import { ModuleGate } from "@/components/common/ModuleGate";
import {
  HeadlineScorecard,
  HeadlineSpotlight,
  toHeadlines,
} from "@/components/common/ModuleHeadlines";
import { BentoGrid, BentoItem, BentoRow } from "@/components/layout/BentoGrid";
import { AnalystPositioning } from "@/components/widgets/market/AnalystPositioning";
import { CampaignPipeline } from "@/components/widgets/market/CampaignPipeline";
import { ThoughtLeadership } from "@/components/widgets/market/ThoughtLeadership";
import { WorkshopFunnel } from "@/components/widgets/market/WorkshopFunnel";
import {
  useAnalystPositioning,
  useCampaignSourced,
  useThoughtLeadership,
  useWorkshopFunnel,
} from "@/hooks/useMarketData";

const useHeadlines = () =>
  toHeadlines([
    useThoughtLeadership(),
    useWorkshopFunnel(),
    useCampaignSourced(),
    useAnalystPositioning(),
  ]);

export function MarketSignals() {
  return (
    <ModuleGate
      moduleKey="market_signals"
      eyebrow="Market presence"
      title="Market signals"
      description="Thought-leadership output & engagement, discovery workshop conversion funnel, campaign-sourced pipeline and analyst positioning."
      highlights={<HeadlineScorecard label="Market scorecard" useHeadlines={useHeadlines} />}
      actions={<ExportViewButton module="market_signals" />}
    >
      <div data-testid="market-signals-view">
        <BentoGrid>
          <BentoRow>
            <BentoItem span={8}>
              <ThoughtLeadership />
            </BentoItem>
            <BentoItem span={4} sticky>
              <HeadlineSpotlight useHeadlines={useHeadlines} />
            </BentoItem>
          </BentoRow>
          <BentoItem span={6}>
            <WorkshopFunnel />
          </BentoItem>
          <BentoItem span={6}>
            <CampaignPipeline />
          </BentoItem>
          <BentoItem span={12}>
            <AnalystPositioning />
          </BentoItem>
        </BentoGrid>
      </div>
    </ModuleGate>
  );
}
