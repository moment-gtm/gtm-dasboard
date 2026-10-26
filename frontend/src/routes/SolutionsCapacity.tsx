/** Solutions Capacity (FR-CAP-01..04) — composes shared components only. CAP-03 shows for restricted personas only. */
import { ExportViewButton } from "@/components/common/ExportViewButton";
import { ModuleGate } from "@/components/common/ModuleGate";
import {
  HeadlineScorecard,
  HeadlineSpotlight,
  toHeadlines,
} from "@/components/common/ModuleHeadlines";
import { BentoGrid, BentoItem, BentoRow } from "@/components/layout/BentoGrid";
import { ArchitectLoad } from "@/components/widgets/capacity/ArchitectLoad";
import { CostOfSale } from "@/components/widgets/capacity/CostOfSale";
import { QualityScores } from "@/components/widgets/capacity/QualityScores";
import { RfpTurnaround } from "@/components/widgets/capacity/RfpTurnaround";
import {
  useArchitectLoad,
  useCostOfSale,
  useQualityScores,
  useRfpTurnaround,
} from "@/hooks/useCapacityData";
import { useMe } from "@/hooks/useReference";

/** Headline metrics; cost of sale (CAP-03) is only fetched for restricted personas. */
function useHeadlines() {
  const restricted = !!useMe().data?.restricted;
  return toHeadlines([
    useArchitectLoad(),
    useRfpTurnaround(),
    useQualityScores(),
    useCostOfSale(restricted),
  ]);
}

export function SolutionsCapacity() {
  const me = useMe();
  const restricted = !!me.data?.restricted;
  return (
    <ModuleGate
      moduleKey="solutions_capacity"
      eyebrow="Delivery readiness"
      title="Solutions capacity"
      description="Architect load, RFP turnaround, cost of sale and bid quality — can Moment pursue what it sells."
      highlights={<HeadlineScorecard label="Capacity scorecard" useHeadlines={useHeadlines} />}
      actions={<ExportViewButton module="solutions_capacity" />}
    >
      <div data-testid="capacity-view">
        <BentoGrid>
          <BentoRow>
            <BentoItem span={8}>
              <ArchitectLoad />
            </BentoItem>
            <BentoItem span={4} sticky>
              <HeadlineSpotlight useHeadlines={useHeadlines} />
            </BentoItem>
          </BentoRow>
          <BentoItem span={restricted ? 4 : 6}>
            <RfpTurnaround />
          </BentoItem>
          <BentoItem span={restricted ? 4 : 6}>
            <QualityScores />
          </BentoItem>
          {restricted ? (
            <BentoItem span={4}>
              <CostOfSale />
            </BentoItem>
          ) : null}
        </BentoGrid>
      </div>
    </ModuleGate>
  );
}
