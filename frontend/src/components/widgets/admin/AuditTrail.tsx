/** Audit trail of administration activity: edits (before/after), exports, denied attempts. */
import { WidgetCard } from "@/components/common/WidgetCard";
import { useAudit } from "@/hooks/useAdminData";
import { fmtDate, Notice } from "./fields";

export function AuditTrail() {
  const q = useAudit();
  return (
    <WidgetCard
      title="Audit trail"
      description="Who changed what and when, including denied attempts and exports. Kept for 24 months."
      testId="widget-audit"
      isLoading={q.isLoading}
      error={q.error}
      onRetry={() => q.refetch()}
    >
      {q.data?.length === 0 ? <Notice>No administration activity recorded yet.</Notice> : null}
      <div
        className="max-h-96 overflow-auto"
        tabIndex={0}
        role="region"
        aria-label="Audit trail table"
      >
        <table className="w-full text-sm" data-testid="audit-table">
          <caption className="sr-only">Administration audit trail</caption>
          <thead>
            <tr>
              {["When (UTC)", "Who", "Action", "Resource", "Result"].map((h) => (
                <th key={h} scope="col" className="p-1 text-left">
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {q.data?.map((a, i) => (
              <tr key={`${a.ts}-${i}`}>
                <td className="p-1">{fmtDate(a.ts)}</td>
                <td className="p-1">{a.upn ?? a.role ?? "unknown"}</td>
                <td className="p-1">{a.action}</td>
                <td className="p-1">{a.resource}</td>
                <td className="p-1">{a.status}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </WidgetCard>
  );
}
