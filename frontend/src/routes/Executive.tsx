/** Executive summary (FR-EXE-01..05) — composes shared components only. */
import { EmptyState } from "@/components/common/EmptyState";
import { ErrorState } from "@/components/common/ErrorState";
import { ExportViewButton } from "@/components/common/ExportViewButton";
import { StatusSummary } from "@/components/common/StatusSummary";
import { BentoGrid, BentoItem } from "@/components/layout/BentoGrid";
import { ModuleLayout } from "@/components/layout/ModuleLayout";
import { AttentionSpotlight } from "@/components/widgets/executive/AttentionSpotlight";
import { BookingsByQuarter } from "@/components/widgets/executive/BookingsByQuarter";
import { BookingsRunway } from "@/components/widgets/executive/BookingsRunway";
import { DealsNeedingAttention } from "@/components/widgets/executive/DealsNeedingAttention";
import { NorthStarKpis } from "@/components/widgets/executive/NorthStarKpis";
import { PipelineByVertical } from "@/components/widgets/executive/PipelineByVertical";
import { useKpis } from "@/hooks/useExecutiveData";
import { useMe } from "@/hooks/useReference";

function Scorecard() {
  const kpis = useKpis();
  return (
    <StatusSummary label="North-star scorecard" statuses={(kpis.data ?? []).map((k) => k.status)} />
  );
}

export function Executive() {
  const me = useMe();
  const description =
    "Bookings, coverage and pipeline health for the fiscal year — the weekly GTM review in one view.";

  if (me.isLoading) return <div className="skeleton" style={{ height: 320 }} />;
  if (me.isError) return <ErrorState error={me.error} onRetry={() => me.refetch()} />;
  if (me.data && !me.data.modules.includes("executive"))
    return (
      <ModuleLayout title="Executive summary" description={description}>
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
      eyebrow="Leadership view"
      title="Executive summary"
      description={description}
      highlights={<Scorecard />}
      actions={<ExportViewButton module="executive" />}
    >
      <div data-testid="executive-view" className="flex flex-col gap-5">
        <BentoGrid>
          <BentoItem span={8}>
            <BookingsRunway />
          </BentoItem>
          <BentoItem span={4}>
            <AttentionSpotlight />
          </BentoItem>
          <BentoItem span={12}>
            <NorthStarKpis />
          </BentoItem>
          <BentoItem span={6}>
            <BookingsByQuarter />
          </BentoItem>
          <BentoItem span={6}>
            <PipelineByVertical />
          </BentoItem>
          <BentoItem span={12} id="deals-attention">
            <DealsNeedingAttention />
          </BentoItem>
        </BentoGrid>
      </div>
    </ModuleLayout>
  );
}
