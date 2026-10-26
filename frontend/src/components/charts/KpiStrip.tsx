/** Responsive strip of KpiCards (1 → 2 → 3 → 6 columns). */
import type { ReactNode } from "react";

export function KpiStrip({
  children,
  testId = "kpi-strip",
}: {
  children: ReactNode;
  testId?: string;
}) {
  return (
    <div
      data-testid={testId}
      className="grid grid-cols-1 gap-4min-[420px]:grid-cols-2 md:grid-cols-3 2xl:grid-cols-6"
    >
      {children}
    </div>
  );
}
