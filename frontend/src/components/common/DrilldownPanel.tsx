/**
 * Drill-down side sheet: opportunity list behind any aggregate, backed by /api/opportunities.
 * Radix Dialog gives focus trap + Escape to close (FR-GEN-06, NFR-08).
 */
import * as Dialog from "@radix-ui/react-dialog";
import { useEffect, useState } from "react";
import { DataRegister } from "@/components/data/DataRegister";
import { opportunityColumns } from "@/components/data/opportunityColumns";
import { useOpportunities } from "@/hooks/useExecutiveData";
import { useDrilldown } from "@/state/drilldown";
import { EmptyState } from "./EmptyState";
import { ErrorState } from "./ErrorState";
import { ExportMenu } from "./ExportMenu";
import { Money } from "./Money";

const PAGE_SIZE = 25;

export function DrilldownPanel() {
  const request = useDrilldown((s) => s.request);
  const close = useDrilldown((s) => s.close);
  const [sort, setSort] = useState("tcv");
  const [order, setOrder] = useState<"asc" | "desc">("desc");
  const [search, setSearch] = useState("");
  const [debounced, setDebounced] = useState("");
  const [page, setPage] = useState(1);

  // Reset paging/search when a new aggregate is opened.
  useEffect(() => {
    setPage(1);
    setSearch("");
    setDebounced("");
  }, [request?.metricId, request?.segment]);

  useEffect(() => {
    const t = setTimeout(() => {
      setDebounced(search);
      setPage(1);
    }, 250);
    return () => clearTimeout(t);
  }, [search]);

  const q = useOpportunities(
    {
      metricId: request?.metricId,
      segment: request?.segment,
      sort,
      order,
      search: debounced,
      page,
      pageSize: PAGE_SIZE,
    },
    !!request,
  );

  return (
    <Dialog.Root open={!!request} onOpenChange={(o) => (!o ? close() : undefined)}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 z-40" style={{ background: "rgba(0,0,0,0.25)" }} />
        <Dialog.Content
          data-testid="drilldown-panel"
          className="fixed top-0 right-0 z-50 flex h-full w-full flex-col gap-3 overflow-y-auto p-4 sm:w-[min(960px,92vw)]"
          style={{ background: "var(--surface)", boxShadow: "-8px 0 24px rgba(0,0,0,0.15)" }}
        >
          <div className="flex items-start justify-between gap-2">
            <div>
              <Dialog.Title className="m-0 text-lg font-semibold">
                {q.data?.title ?? request?.title ?? "Opportunities"}
              </Dialog.Title>
              <Dialog.Description className="m-0 mt-1 text-sm" style={{ color: "var(--ink-2)" }}>
                {request?.metricId ? `${request.metricId} · ` : ""}
                {q.data ? (
                  <>
                    {q.data.total_count.toLocaleString("en-US")} opportunities ·{" "}
                    <Money value={q.data.total_tcv} /> TCV
                  </>
                ) : (
                  "Underlying opportunities for the selected figure"
                )}
              </Dialog.Description>
            </div>
            <div className="flex items-center gap-1">
              {request?.metricId ? (
                <ExportMenu
                  metricId={request.metricId}
                  path="/api/exports/opportunities"
                  extra={{ segment: request.segment }}
                  label="Export opportunities for"
                />
              ) : null}
              <Dialog.Close asChild>
                <button
                  type="button"
                  className="btn"
                  aria-label="Close drill-down"
                  data-testid="drilldown-close"
                >
                  Close
                </button>
              </Dialog.Close>
            </div>
          </div>
          {q.data?.aggregated_other ? (
            <p
              className="m-0 rounded-md p-2 text-sm"
              data-testid="aggregated-other"
              style={{ background: "var(--page)", border: "1px solid var(--grid)" }}
            >
              {q.data.aggregated_other.note} ({q.data.aggregated_other.count} opportunities,{" "}
              <Money value={q.data.aggregated_other.tcv} />)
            </p>
          ) : null}
          {q.isLoading ? (
            <div className="skeleton" style={{ height: 240 }} />
          ) : q.isError ? (
            <ErrorState error={q.error} onRetry={() => q.refetch()} />
          ) : q.data && q.data.total_count === 0 && !debounced ? (
            <EmptyState reason="no-match-filters" />
          ) : q.data ? (
            <DataRegister
              testId="drilldown-register"
              caption="Underlying opportunities"
              columns={opportunityColumns}
              data={q.data.rows}
              getRowId={(r) => r.opportunity_id}
              server={{
                sort,
                order,
                onSort: (s, o) => {
                  setSort(s);
                  setOrder(o);
                  setPage(1);
                },
                search,
                onSearch: setSearch,
                page,
                pageSize: PAGE_SIZE,
                total: q.data.total_count,
                onPage: setPage,
              }}
            />
          ) : null}
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
