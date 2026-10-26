/** Partners (FR-PAR-01..03) — composes shared components only. */
import { ExportViewButton } from "@/components/common/ExportViewButton";
import { ModuleGate } from "@/components/common/ModuleGate";
import {
  HeadlineScorecard,
  HeadlineSpotlight,
  toHeadlines,
} from "@/components/common/ModuleHeadlines";
import { BentoGrid, BentoItem, BentoRow } from "@/components/layout/BentoGrid";
import { Certifications } from "@/components/widgets/partners/Certifications";
import { CoSell } from "@/components/widgets/partners/CoSell";
import { PartnerPipeline } from "@/components/widgets/partners/PartnerPipeline";
import { useCertifications, useCoSell, usePartnerPipeline } from "@/hooks/usePartnersData";

const useHeadlines = () => toHeadlines([usePartnerPipeline(), useCoSell(), useCertifications()]);

export function Partners() {
  return (
    <ModuleGate
      moduleKey="partners"
      eyebrow="Ecosystem"
      title="Partners"
      description="Partner-sourced and influenced pipeline, co-sell win rate and certification coverage."
      highlights={<HeadlineScorecard label="Partners scorecard" useHeadlines={useHeadlines} />}
      actions={<ExportViewButton module="partners" />}
    >
      <div data-testid="partners-view">
        <BentoGrid>
          <BentoRow>
            <BentoItem span={8}>
              <PartnerPipeline />
            </BentoItem>
            <BentoItem span={4} sticky>
              <HeadlineSpotlight useHeadlines={useHeadlines} />
            </BentoItem>
          </BentoRow>
          <BentoItem span={6}>
            <CoSell />
          </BentoItem>
          <BentoItem span={6}>
            <Certifications />
          </BentoItem>
        </BentoGrid>
      </div>
    </ModuleGate>
  );
}
