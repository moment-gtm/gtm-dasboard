/** FR-ACC-01 / ACC-01 — account × practice penetration matrix (Sold / Open / Not addressed). */
import {
  MatrixGrid,
  MatrixLegend,
  type CellState,
  type MatrixRow,
} from "@/components/charts/MatrixGrid";
import { WidgetCard } from "@/components/common/WidgetCard";
import { usePenetration } from "@/hooks/useAccountsData";
import { useAccountDetail } from "@/state/accountDetail";
import { formatPct } from "@/utils/format";

interface Row {
  account_id: string;
  account_name: string;
  strategic: boolean;
  vertical: string;
  client_partner: string;
  cells: Record<string, CellState>;
  sold: number;
  open: number;
}

export function PenetrationMatrix() {
  const q = usePenetration();
  const open = useAccountDetail((s) => s.open);
  const rows = (q.data?.breakdown ?? []) as unknown as Row[];
  const meta = (q.data?.meta ?? {}) as {
    practices?: string[];
    accounts?: number;
    sold?: number;
    open?: number;
    not_addressed?: number;
  };
  const matrix: MatrixRow[] = rows.map((r) => ({
    key: r.account_id,
    label: r.account_name,
    sublabel: `${r.strategic ? "Strategic · " : ""}${r.vertical}`,
    cells: r.cells,
  }));
  return (
    <WidgetCard
      variant="hero"
      testId="widget-penetration"
      title="Practice penetration"
      description="Where each account has bought from, is being pursued by, or has not been approached by each practice. Select an account for its detail."
      metricId="ACC-01"
      isLoading={q.isLoading}
      isFetching={q.isFetching}
      error={q.error}
      onRetry={() => q.refetch()}
      empty={q.data && rows.length === 0 ? "no-match-filters" : false}
      emptyHint="No accounts are in scope for the current filters."
    >
      <div className="flex flex-col gap-3">
        <p className="m-0 text-sm" data-testid="penetration-summary">
          <strong>{formatPct(q.data?.value)}</strong> of {meta.accounts} accounts × practices are
          sold · {meta.open} open · {meta.not_addressed} not addressed
        </p>
        <MatrixLegend />
        <MatrixGrid
          testId="penetration-matrix"
          caption="Account by practice penetration"
          columns={meta.practices ?? []}
          rows={matrix}
          onSelectRow={(r) => open(r.key, r.label)}
        />
      </div>
    </WidgetCard>
  );
}
