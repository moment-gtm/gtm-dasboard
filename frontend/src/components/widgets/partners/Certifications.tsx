/** FR-PAR-03 / PAR-03 — certified vs required headcount per partner, with expired and in-progress. */
import type { StatusValue } from "@/api/types";
import { ChartTable } from "@/components/charts/ChartTable";
import { ProgressToTarget } from "@/components/charts/ProgressToTarget";
import { WidgetCard } from "@/components/common/WidgetCard";
import { useCertifications } from "@/hooks/usePartnersData";
import { formatPct } from "@/utils/format";

interface Row {
  partner: string;
  tier: string | null;
  required: number;
  certified: number;
  expired: number;
  in_progress: number;
  gap: number;
  progress: number | null;
  status: StatusValue | null;
}

export function Certifications() {
  const q = useCertifications();
  const rows = (q.data?.breakdown ?? []) as unknown as Row[];
  const meta = (q.data?.meta ?? {}) as {
    required?: number;
    certified?: number;
    in_progress?: number;
  };
  return (
    <WidgetCard
      testId="widget-certifications"
      title="Partner certifications"
      description="Active certifications against the count each partner programme requires."
      metricId="PAR-03"
      status={q.data?.status}
      statusBasis={q.data?.status_basis}
      isLoading={q.isLoading}
      isFetching={q.isFetching}
      error={q.error}
      onRetry={() => q.refetch()}
      empty={q.data && rows.length === 0 ? "no-match-filters" : false}
    >
      <div className="flex flex-col gap-3">
        <p className="m-0 text-sm" data-testid="cert-summary">
          <span className="text-2xl font-semibold">{formatPct(q.data?.value, 0)}</span>{" "}
          <span style={{ color: "var(--ink-2)" }}>
            {meta.certified} of {meta.required} required certifications held · {meta.in_progress} in
            progress
          </span>
        </p>
        <ProgressToTarget
          testIdPrefix="cert"
          rows={rows.map((r) => ({
            key: r.partner,
            label: `${r.partner}${r.tier ? ` · ${r.tier}` : ""}`,
            value: r.progress,
            goal: q.data?.goal,
            detail: `${r.certified} of ${r.required} certified`,
            status: r.status,
          }))}
        />
        <ChartTable
          caption="Partner certifications"
          rows={rows}
          rowKey={(r) => r.partner}
          columns={[
            { header: "Partner", cell: (r) => r.partner },
            { header: "Tier", cell: (r) => r.tier ?? "—" },
            { header: "Required", cell: (r) => r.required },
            { header: "Certified", cell: (r) => r.certified },
            { header: "Expired", cell: (r) => r.expired },
            { header: "In progress", cell: (r) => r.in_progress },
            { header: "Gap", cell: (r) => r.gap },
          ]}
        />
      </div>
    </WidgetCard>
  );
}
