/** Offerings (FR-OFF-01..05) — composes shared components only. */
import { ExportViewButton } from "@/components/common/ExportViewButton";
import { ModuleGate } from "@/components/common/ModuleGate";
import {
  HeadlineScorecard,
  HeadlineSpotlight,
  toHeadlines,
} from "@/components/common/ModuleHeadlines";
import { BentoGrid, BentoItem, BentoRow } from "@/components/layout/BentoGrid";
import { AiValidation } from "@/components/widgets/offerings/AiValidation";
import { AssetBuild } from "@/components/widgets/offerings/AssetBuild";
import { AssetReuse } from "@/components/widgets/offerings/AssetReuse";
import { AttachRate } from "@/components/widgets/offerings/AttachRate";
import { OfferingPipelineWins } from "@/components/widgets/offerings/OfferingPipelineWins";
import {
  useAiValidation,
  useAssetBuild,
  useAssetReuse,
  useAttachRate,
  useByOffering,
} from "@/hooks/useOfferingsData";

const useHeadlines = () =>
  toHeadlines([
    useByOffering(),
    useAttachRate(),
    useAiValidation(),
    useAssetBuild(),
    useAssetReuse(),
  ]);

export function Offerings() {
  return (
    <ModuleGate
      moduleKey="offerings"
      eyebrow="Offering-led growth"
      title="Offerings"
      description="Offering-led pipeline, attach rate, AI-led validation and the asset library."
      highlights={<HeadlineScorecard label="Offerings scorecard" useHeadlines={useHeadlines} />}
      actions={<ExportViewButton module="offerings" />}
    >
      <div data-testid="offerings-view">
        <BentoGrid>
          <BentoRow>
            <BentoItem span={8}>
              <OfferingPipelineWins />
            </BentoItem>
            <BentoItem span={4} sticky>
              <HeadlineSpotlight useHeadlines={useHeadlines} />
            </BentoItem>
          </BentoRow>
          <BentoItem span={4}>
            <AttachRate />
          </BentoItem>
          <BentoItem span={4}>
            <AiValidation />
          </BentoItem>
          <BentoItem span={4}>
            <AssetBuild />
          </BentoItem>
          <BentoItem span={12}>
            <AssetReuse />
          </BentoItem>
        </BentoGrid>
      </div>
    </ModuleGate>
  );
}
