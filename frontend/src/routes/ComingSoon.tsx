/** Placeholder for modules not yet built — names the roadmap step that delivers each. */
import { EmptyState } from "@/components/common/EmptyState";
import { ModuleLayout } from "@/components/layout/ModuleLayout";
import { MODULES } from "@/components/layout/modules";

export function ComingSoon({ moduleKey }: { moduleKey: string }) {
  const m = MODULES.find((x) => x.key === moduleKey);
  return (
    <ModuleLayout
      title={m?.label ?? "Module"}
      description="This module is planned in the implementation roadmap."
    >
      <div data-testid={`coming-soon-${moduleKey}`}>
        <EmptyState
          reason="no-data"
          title={`${m?.label ?? "This module"} arrives in ${m?.step ?? "a later step"}`}
          hint="Global filters and your persona carry over when it ships. See docs/plans/Moment_GTM_Dashboard_IMPLEMENTATION_ORDER.md."
        />
      </div>
    </ModuleLayout>
  );
}
