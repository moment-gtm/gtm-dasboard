/** FR-OFF-03 / OFF-03 — AI-led pipeline validation; the unvalidated open TCV is the risk figure. */
import { ChartTable } from "@/components/charts/ChartTable";
import { ProgressToTarget } from "@/components/charts/ProgressToTarget";
import { Money } from "@/components/common/Money";
import { WidgetCard } from "@/components/common/WidgetCard";
import { useAiValidation } from "@/hooks/useOfferingsData";
import { formatMoney } from "@/utils/format";

interface Row {
  state: string;
  label: string;
  count: number;
  tcv: number;
  share: number | null;
}
interface Deal {
  opportunity_id: string;
  name: string;
  account_name: string;
  stage: string;
  tcv_usd: number;
  validation: string;
}

export function AiValidation() {
  const q = useAiValidation();
  const rows = (q.data?.breakdown ?? []) as unknown as Row[];
  const meta = (q.data?.meta ?? {}) as { largest_unvalidated?: Deal[] };
  const deals = meta.largest_unvalidated ?? [];
  return (
    <WidgetCard
      testId="widget-ai-validation"
      title="AI-led validation"
      description="Open pipeline by validation state. The headline is AI-led TCV without a validated Validation ID."
      metricId="OFF-03"
      isLoading={q.isLoading}
      isFetching={q.isFetching}
      error={q.error}
      onRetry={() => q.refetch()}
      empty={q.data && rows.length === 0 ? "no-match-filters" : false}
    >
      <div className="flex flex-col gap-3">
        <p className="m-0 text-sm" data-testid="unvalidated-value">
          <span className="text-2xl font-semibold">
            <Money value={q.data?.value} />
          </span>{" "}
          <span style={{ color: "var(--ink-2)" }}>of AI-led open TCV is unvalidated</span>
        </p>
        <ProgressToTarget
          testIdPrefix="validation"
          rows={rows.map((r) => ({
            key: r.state,
            label: r.label,
            value: r.share,
            detail: `${r.count} deals · ${formatMoney(r.tcv)}`,
          }))}
        />
        {deals.length ? (
          <div>
            <h3 className="m-0 mb-1 text-sm font-semibold">Largest unvalidated deals</h3>
            <ChartTable
              caption="Largest unvalidated AI-led deals"
              rows={deals}
              rowKey={(d) => d.opportunity_id}
              columns={[
                { header: "Deal", cell: (d) => d.name },
                { header: "Account", cell: (d) => d.account_name },
                { header: "Stage", cell: (d) => d.stage },
                { header: "TCV", cell: (d) => <Money value={d.tcv_usd} /> },
                { header: "Validation", cell: (d) => d.validation },
              ]}
            />
          </div>
        ) : null}
      </div>
    </WidgetCard>
  );
}
