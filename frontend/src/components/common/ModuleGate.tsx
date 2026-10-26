/** Wraps a module route: loading / error / access-denied handling shared by Step 5 modules. */
import type { ReactNode } from "react";
import { EmptyState } from "@/components/common/EmptyState";
import { ErrorState } from "@/components/common/ErrorState";
import { ModuleLayout } from "@/components/layout/ModuleLayout";
import { useMe } from "@/hooks/useReference";

export function ModuleGate({
  moduleKey,
  title,
  description,
  eyebrow,
  actions,
  highlights,
  children,
}: {
  moduleKey: string;
  title: string;
  description: string;
  eyebrow?: string;
  actions?: ReactNode;
  highlights?: ReactNode;
  children: ReactNode;
}) {
  const me = useMe();
  if (me.isLoading) return <div className="skeleton" style={{ height: 320 }} />;
  if (me.isError) return <ErrorState error={me.error} onRetry={() => me.refetch()} />;
  if (me.data && !me.data.modules.includes(moduleKey))
    return (
      <ModuleLayout title={title} description={description} eyebrow={eyebrow}>
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
      title={title}
      description={description}
      eyebrow={eyebrow}
      actions={actions}
      highlights={highlights}
    >
      {children}
    </ModuleLayout>
  );
}
