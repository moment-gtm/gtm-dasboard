/** Administration & Governance (FR-ADM-01..05) — composes admin widgets behind accessible tabs. */
import { useRef, useState, type KeyboardEvent } from "react";
import { EmptyState } from "@/components/common/EmptyState";
import { ErrorState } from "@/components/common/ErrorState";
import { ModuleLayout } from "@/components/layout/ModuleLayout";
import { AlertRules } from "@/components/widgets/admin/AlertRules";
import { AlertSubscriptions } from "@/components/widgets/admin/AlertSubscriptions";
import { AuditTrail } from "@/components/widgets/admin/AuditTrail";
import { ChangeControl } from "@/components/widgets/admin/ChangeControl";
import { DigestConfig } from "@/components/widgets/admin/DigestConfig";
import { CompletenessGate, DqConsole } from "@/components/widgets/admin/DqConsole";
import { ReferenceDataManager } from "@/components/widgets/admin/ReferenceDataManager";
import { TargetManager } from "@/components/widgets/admin/TargetManager";
import { ThresholdManager } from "@/components/widgets/admin/ThresholdManager";
import { useMe } from "@/hooks/useReference";

const TABS = [
  { id: "targets", label: "Targets", panel: () => <TargetManager /> },
  { id: "thresholds", label: "Thresholds", panel: () => <ThresholdManager /> },
  { id: "reference", label: "Reference data", panel: () => <ReferenceDataManager /> },
  {
    id: "dq",
    label: "Data quality",
    panel: () => (
      <div className="flex flex-col gap-4">
        <CompletenessGate />
        <DqConsole />
      </div>
    ),
  },
  { id: "change", label: "Change control", panel: () => <ChangeControl /> },
  { id: "audit", label: "Audit trail", panel: () => <AuditTrail /> },
  {
    id: "alerts",
    label: "Alerts & digest",
    panel: () => (
      <div className="flex flex-col gap-4">
        <AlertRules />
        <AlertSubscriptions />
        <DigestConfig />
      </div>
    ),
  },
];

export function Admin() {
  const me = useMe();
  const [active, setActive] = useState(TABS[0].id);
  const refs = useRef<Record<string, HTMLButtonElement | null>>({});
  const description =
    "Manage targets, thresholds and reference data, monitor data quality, configure alerts & weekly digests, and control metric changes.";

  if (me.isLoading) return <div className="skeleton" style={{ height: 320 }} />;
  if (me.isError) return <ErrorState error={me.error} onRetry={() => me.refetch()} />;
  if (me.data && !me.data.modules.includes("admin"))
    return (
      <ModuleLayout title="Administration & Governance" description={description}>
        <div className="flex flex-col gap-4">
          <div data-testid="access-denied">
            <EmptyState
              reason="access-denied"
              hint={`${me.data.label} personas use ${me.data.modules.join(", ").replace(/_/g, " ")}. Administration is limited to the GTM Lead and Sales Operations.`}
            />
          </div>
          <AlertSubscriptions />
        </div>
      </ModuleLayout>
    );

  const onKey = (e: KeyboardEvent, i: number) => {
    const step = e.key === "ArrowRight" ? 1 : e.key === "ArrowLeft" ? -1 : 0;
    const next =
      e.key === "Home"
        ? 0
        : e.key === "End"
          ? TABS.length - 1
          : (i + step + TABS.length) % TABS.length;
    if (!step && e.key !== "Home" && e.key !== "End") return;
    e.preventDefault();
    setActive(TABS[next].id);
    refs.current[TABS[next].id]?.focus();
  };
  const current = TABS.find((t) => t.id === active) ?? TABS[0];

  return (
    <ModuleLayout
      eyebrow="Governance"
      title="Administration & Governance"
      description={description}
    >
      <div data-testid="admin-view" className="flex flex-col gap-4">
        <div
          role="tablist"
          aria-label="Administration sections"
          className="card flex flex-wrap gap-1 p-1.5 self-start"
          style={{ borderRadius: 16 }}
        >
          {TABS.map((t, i) => (
            <button
              key={t.id}
              ref={(el) => {
                refs.current[t.id] = el;
              }}
              type="button"
              role="tab"
              id={`tab-${t.id}`}
              aria-selected={t.id === active}
              aria-controls={`panel-${t.id}`}
              tabIndex={t.id === active ? 0 : -1}
              className={t.id === active ? "btn btn-primary" : "btn btn-ghost"}
              onClick={() => setActive(t.id)}
              onKeyDown={(e) => onKey(e, i)}
              data-testid={`tab-${t.id}`}
            >
              {t.label}
            </button>
          ))}
        </div>
        <div role="tabpanel" id={`panel-${current.id}`} aria-labelledby={`tab-${current.id}`}>
          {current.panel()}
        </div>
      </div>
    </ModuleLayout>
  );
}
