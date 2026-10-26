/** Empty state: says what is missing and how to fix it (FR-GEN-13). */
import type { ReactNode } from "react";

export type EmptyReason = "no-match-filters" | "no-data" | "access-denied";

const COPY: Record<EmptyReason, { title: string; hint: string }> = {
  "no-match-filters": {
    title: "No opportunities match the current filters",
    hint: "Widen the period or clear one of the active filters in the filter bar.",
  },
  "no-data": {
    title: "No data has been loaded for this view yet",
    hint: "Check the data freshness indicator; the source may not have completed its first load.",
  },
  "access-denied": {
    title: "Your role does not include this module",
    hint: "Switch persona, or ask the GTM Lead / Sales Operations to review your access group.",
  },
};

export function EmptyState({
  reason = "no-match-filters",
  title,
  hint,
  action,
}: {
  reason?: EmptyReason;
  title?: string;
  hint?: string;
  action?: ReactNode;
}) {
  const c = COPY[reason];
  return (
    <div
      role="status"
      data-testid={`empty-state-${reason}`}
      className="flex flex-col items-start gap-2 rounded-lg p-4"
      style={{ background: "var(--page)", border: "1px dashed var(--grid)" }}
    >
      <p className="m-0 text-sm font-semibold">{title ?? c.title}</p>
      <p className="m-0 text-sm" style={{ color: "var(--ink-2)" }}>
        {hint ?? c.hint}
      </p>
      {action}
    </div>
  );
}
