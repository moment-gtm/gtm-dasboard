/** FR-PIP-05 / PIP-06 — sortable, searchable, exportable register of open deals; ageing rows carry a text flag. */
import { useEffect, useState } from "react";
import { DataRegister } from "@/components/data/DataRegister";
import { flagColumn, opportunityColumns } from "@/components/data/opportunityColumns";
import { EmptyState } from "@/components/common/EmptyState";
import { ExportMenu } from "@/components/common/ExportMenu";
import { Money } from "@/components/common/Money";
import { WidgetCard } from "@/components/common/WidgetCard";
import { useOpportunities } from "@/hooks/useExecutiveData";

const PAGE_SIZE = 25;
const COLUMNS = [...opportunityColumns, flagColumn];

export function OpportunityRegister({
  stage,
  onClearStage,
}: {
  stage: string | null;
  onClearStage: () => void;
}) {
  const [sort, setSort] = useState("tcv");
  const [order, setOrder] = useState<"asc" | "desc">("desc");
  const [search, setSearch] = useState("");
  const [debounced, setDebounced] = useState("");
  const [page, setPage] = useState(1);

  useEffect(() => setPage(1), [stage]);
  useEffect(() => {
    const t = setTimeout(() => {
      setDebounced(search);
      setPage(1);
    }, 250);
    return () => clearTimeout(t);
  }, [search]);

  const q = useOpportunities(
    {
      metricId: "PIP-06",
      segment: stage,
      sort,
      order,
      search: debounced,
      page,
      pageSize: PAGE_SIZE,
    },
    true,
  );
  const d = q.data;
  return (
    <WidgetCard
      testId="widget-opportunity-register"
      title="Opportunity register"
      description="Every open deal in your scope. Sort any column, search by deal, account or owner, and export. Ageing and stalled deals are flagged in text."
      metricId="PIP-06"
      exportable={false}
      isLoading={q.isLoading}
      isFetching={q.isFetching}
      error={q.error}
      onRetry={() => q.refetch()}
    >
      <div className="flex flex-col gap-3">
        <div className="flex flex-wrap items-center justify-between gap-2 text-sm">
          <p className="m-0" data-testid="register-summary">
            {stage ? (
              <>
                Stage: <strong>{stage}</strong>{" "}
                <button
                  type="button"
                  className="btn"
                  onClick={onClearStage}
                  data-testid="clear-stage-filter"
                >
                  Clear stage filter
                </button>{" "}
                ·{" "}
              </>
            ) : null}
            {d ? (
              <>
                {d.total_count.toLocaleString("en-US")} deals · <Money value={d.total_tcv} /> TCV
              </>
            ) : null}
          </p>
          <ExportMenu
            metricId="PIP-06"
            path="/api/exports/opportunities"
            extra={{ segment: stage }}
          />
        </div>
        {d?.aggregated_other ? (
          <p
            className="m-0 rounded-md p-2 text-sm"
            data-testid="aggregated-other"
            style={{ background: "var(--page)", border: "1px solid var(--grid)" }}
          >
            {d.aggregated_other.note} ({d.aggregated_other.count} opportunities,{" "}
            <Money value={d.aggregated_other.tcv} />)
          </p>
        ) : null}
        {d && d.total_count === 0 && !debounced ? (
          <EmptyState reason="no-match-filters" />
        ) : d ? (
          <DataRegister
            testId="pipeline-register"
            caption="Open opportunities"
            columns={COLUMNS}
            data={d.rows}
            getRowId={(r) => r.opportunity_id}
            rowHighlight={(r) => r.flag != null}
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
              total: d.total_count,
              onPage: setPage,
            }}
          />
        ) : null}
      </div>
    </WidgetCard>
  );
}
