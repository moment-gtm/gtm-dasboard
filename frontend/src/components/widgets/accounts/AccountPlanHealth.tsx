/** FR-ACC-04 / ACC-04 — account-plan health for strategic accounts (Current / Needs update / Overdue). */
import type { ColumnDef } from "@tanstack/react-table";
import { WidgetCard } from "@/components/common/WidgetCard";
import { DataRegister } from "@/components/data/DataRegister";
import { usePlanHealth } from "@/hooks/useAccountsData";
import { useAccountDetail } from "@/state/accountDetail";
import { formatDate, formatPct } from "@/utils/format";

interface Row {
  account_id: string;
  account_name: string;
  client_partner: string;
  plan_status: string | null;
  last_review_date: string | null;
  days_since_review: number | null;
  health: "current" | "needs_update" | "overdue";
  label: string;
}

const GLYPH: Record<Row["health"], string> = { current: "✓", needs_update: "!", overdue: "✕" };

export function AccountPlanHealth() {
  const q = usePlanHealth();
  const open = useAccountDetail((s) => s.open);
  const rows = (q.data?.breakdown ?? []) as unknown as Row[];
  const meta = (q.data?.meta ?? {}) as {
    current?: number;
    needs_update?: number;
    overdue?: number;
    strategic_accounts?: number;
    current_days?: number;
    overdue_days?: number;
  };
  const columns: ColumnDef<Row, unknown>[] = [
    {
      accessorKey: "account_name",
      header: "Account",
      cell: (c) => (
        <button
          type="button"
          style={{ background: "transparent", border: 0, cursor: "pointer", padding: 0 }}
          onClick={() => open(c.row.original.account_id, c.row.original.account_name)}
          aria-label={`Open ${c.row.original.account_name} account detail`}
        >
          <span style={{ color: "var(--accent-strong)", fontWeight: 500 }}>
            {c.row.original.account_name}
          </span>
        </button>
      ),
    },
    { accessorKey: "client_partner", header: "Client partner" },
    {
      accessorKey: "last_review_date",
      header: "Last review",
      cell: (c) => formatDate(c.getValue<string | null>()),
    },
    {
      accessorKey: "days_since_review",
      header: "Days since review",
      cell: (c) => c.getValue<number | null>() ?? "No plan",
    },
    {
      accessorKey: "label",
      header: "Plan health",
      cell: (c) => (
        <span data-health={c.row.original.health}>
          <span aria-hidden="true">{GLYPH[c.row.original.health]} </span>
          {c.getValue<string>()}
        </span>
      ),
    },
  ];
  return (
    <WidgetCard
      testId="widget-plan-health"
      title="Account-plan health"
      description="Strategic accounts and how recently their plan was reviewed."
      metricId="ACC-04"
      isLoading={q.isLoading}
      isFetching={q.isFetching}
      error={q.error}
      onRetry={() => q.refetch()}
      empty={q.data && rows.length === 0 ? "no-match-filters" : false}
      emptyHint="No strategic accounts are in scope for the current filters."
    >
      <div className="flex flex-col gap-3">
        <p className="m-0 text-sm" data-testid="plan-health-summary">
          <strong>{formatPct(q.data?.value, 0)}</strong> of {meta.strategic_accounts} strategic
          plans are current · {meta.needs_update} need an update · {meta.overdue} overdue (reviewed{" "}
          {meta.current_days}–{meta.overdue_days}+ days ago or no plan)
        </p>
        <DataRegister
          testId="plan-health-register"
          caption="Account-plan health"
          columns={columns}
          data={rows}
          getRowId={(r) => r.account_id}
          rowHighlight={(r) => r.health === "overdue"}
          searchPlaceholder="Search accounts"
        />
      </div>
    </WidgetCard>
  );
}
