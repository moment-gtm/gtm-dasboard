/**
 * FR-ACC-05 — account detail: every opportunity for one account. Radix Dialog gives the focus trap
 * and Escape to close. Backed by /api/accounts/{id}/opportunities (RLS-scoped, 404 outside scope).
 */
import * as Dialog from "@radix-ui/react-dialog";
import { EmptyState } from "@/components/common/EmptyState";
import { ErrorState } from "@/components/common/ErrorState";
import { Money } from "@/components/common/Money";
import { DataRegister } from "@/components/data/DataRegister";
import { opportunityColumns } from "@/components/data/opportunityColumns";
import { useAccountOpportunities } from "@/hooks/useAccountsData";
import { useAccountDetail } from "@/state/accountDetail";

export function AccountDetailPanel() {
  const { accountId, title, close } = useAccountDetail();
  const q = useAccountOpportunities(accountId);
  return (
    <Dialog.Root open={!!accountId} onOpenChange={(o) => (!o ? close() : undefined)}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 z-40" style={{ background: "rgba(0,0,0,0.25)" }} />
        <Dialog.Content
          data-testid="account-detail-panel"
          className="fixed top-0 right-0 z-50 flex h-full w-full flex-col gap-3 overflow-y-auto p-4 sm:w-[min(960px,92vw)]"
          style={{ background: "var(--surface)", boxShadow: "-8px 0 24px rgba(0,0,0,0.15)" }}
        >
          <div className="flex items-start justify-between gap-2">
            <div>
              <Dialog.Title className="m-0 text-lg font-semibold">{title}</Dialog.Title>
              <Dialog.Description className="m-0 mt-1 text-sm" style={{ color: "var(--ink-2)" }}>
                {q.data ? (
                  <>
                    {q.data.total_count} opportunities · <Money value={q.data.total_tcv} /> TCV
                    across all stages
                  </>
                ) : (
                  "All opportunities for this account"
                )}
              </Dialog.Description>
            </div>
            <Dialog.Close asChild>
              <button
                type="button"
                className="btn"
                aria-label="Close account detail"
                data-testid="account-detail-close"
              >
                Close
              </button>
            </Dialog.Close>
          </div>
          {q.isLoading ? (
            <div className="skeleton" style={{ height: 240 }} />
          ) : q.isError ? (
            <ErrorState error={q.error} onRetry={() => q.refetch()} />
          ) : q.data && q.data.rows.length === 0 ? (
            <EmptyState reason="no-match-filters" />
          ) : q.data ? (
            <DataRegister
              testId="account-detail-register"
              caption="Account opportunities"
              columns={opportunityColumns}
              data={q.data.rows}
              getRowId={(r) => r.opportunity_id}
              searchPlaceholder="Search opportunities"
            />
          ) : null}
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
