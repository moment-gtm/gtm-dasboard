/** Pipeline (FR-PIP-01..06) — composes shared components only. */
import { useState } from "react";
import { EmptyState } from "@/components/common/EmptyState";
import { ErrorState } from "@/components/common/ErrorState";
import { ExportViewButton } from "@/components/common/ExportViewButton";
import { HeadlineScorecard, toHeadlines } from "@/components/common/ModuleHeadlines";
import { BentoGrid, BentoItem, BentoRow } from "@/components/layout/BentoGrid";
import { ModuleLayout } from "@/components/layout/ModuleLayout";
import { AgeingHeatmap } from "@/components/widgets/pipeline/AgeingHeatmap";
import { DealSizeHistogram } from "@/components/widgets/pipeline/DealSizeHistogram";
import { OpportunityRegister } from "@/components/widgets/pipeline/OpportunityRegister";
import { PipelineByPlatform } from "@/components/widgets/pipeline/PipelineByPlatform";
import { PipelineByPractice } from "@/components/widgets/pipeline/PipelineByPractice";
import { PipelineSpotlight } from "@/components/widgets/pipeline/PipelineSpotlight";
import { StageFunnel } from "@/components/widgets/pipeline/StageFunnel";
import { StageMovement } from "@/components/widgets/pipeline/StageMovement";
import {
  useAgeing,
  useFunnel,
  usePipelineByPlatform,
  usePipelineByPractice,
  useSizeDistribution,
  useStageMovement,
} from "@/hooks/usePipelineData";
import { useMe } from "@/hooks/useReference";

const useHeadlines = () =>
  toHeadlines([
    useFunnel(),
    useAgeing(),
    usePipelineByPractice(),
    usePipelineByPlatform(),
    useSizeDistribution(),
    useStageMovement(),
  ]);

export function Pipeline() {
  const me = useMe();
  const [stage, setStage] = useState<string | null>(null);
  const description =
    "Open pipeline by stage, ageing, practice, platform and deal size — the weekly pipeline review.";

  if (me.isLoading) return <div className="skeleton" style={{ height: 320 }} />;
  if (me.isError) return <ErrorState error={me.error} onRetry={() => me.refetch()} />;
  if (me.data && !me.data.modules.includes("pipeline"))
    return (
      <ModuleLayout title="Pipeline" description={description}>
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
      eyebrow="Pipeline health"
      title="Pipeline"
      description={description}
      highlights={<HeadlineScorecard label="Pipeline scorecard" useHeadlines={useHeadlines} />}
      actions={<ExportViewButton module="pipeline" />}
    >
      <div data-testid="pipeline-view">
        <BentoGrid>
          <BentoRow>
            <BentoItem span={8}>
              <StageFunnel
                selectedStage={stage}
                onSelectStage={(s) => setStage((cur) => (cur === s ? null : s))}
              />
            </BentoItem>
            <BentoItem span={4} sticky>
              <PipelineSpotlight />
            </BentoItem>
          </BentoRow>
          <BentoItem span={6} id="pipeline-ageing">
            <AgeingHeatmap />
          </BentoItem>
          <BentoItem span={6}>
            <DealSizeHistogram />
          </BentoItem>
          <BentoItem span={6}>
            <PipelineByPractice />
          </BentoItem>
          <BentoItem span={6}>
            <PipelineByPlatform />
          </BentoItem>
          <BentoItem span={12}>
            <StageMovement />
          </BentoItem>
          <BentoItem span={12}>
            <OpportunityRegister stage={stage} onClearStage={() => setStage(null)} />
          </BentoItem>
        </BentoGrid>
      </div>
    </ModuleLayout>
  );
}
