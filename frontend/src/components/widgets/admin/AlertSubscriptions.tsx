/** FR-ALR-03 — User-managed alert and weekly digest channel subscriptions (email + Teams). */
import { adminApi, type SubscriptionRow } from "@/api/admin";
import { WidgetCard } from "@/components/common/WidgetCard";
import { useAdminMutation, useAlertSubscriptions } from "@/hooks/useAdminData";
import { FormError, Notice } from "./fields";

export function AlertSubscriptions() {
  const q = useAlertSubscriptions();
  const save = useAdminMutation((subs: { target_id: string; email: boolean; teams: boolean }[]) =>
    adminApi.updateSubscriptions(subs),
  );
  const rows = q.data?.subscriptions ?? [];

  const toggle = (row: SubscriptionRow, channel: "email" | "teams") => {
    const next = rows.map((r) => ({
      target_id: r.target_id,
      email: r.target_id === row.target_id && channel === "email" ? !r.email : r.email,
      teams: r.target_id === row.target_id && channel === "teams" ? !r.teams : r.teams,
    }));
    save.mutate(next);
  };

  return (
    <WidgetCard
      testId="widget-alert-subscriptions"
      title="My alert & digest subscriptions"
      description="Opt in or out of individual threshold alerts and the weekly digest across Email and Microsoft Teams."
      isLoading={q.isLoading}
      error={q.error}
      onRetry={() => q.refetch()}
    >
      <div className="flex flex-col gap-3">
        {q.data ? (
          <Notice>
            Subscriptions for <strong>{q.data.display_name}</strong> ({q.data.upn} · {q.data.role}).
            Alerts only deliver metrics and deals permitted by your RLS scope.
          </Notice>
        ) : null}
        <div className="overflow-x-auto">
          <table className="w-full text-sm" data-testid="alert-subscriptions-table">
            <caption className="sr-only">Alert and digest channel subscriptions</caption>
            <thead>
              <tr>
                {["Subscription", "Type", "Metric", "Email", "Microsoft Teams"].map((h) => (
                  <th key={h} scope="col" className="p-1 text-left">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.map((r) => (
                <tr key={r.target_id} data-testid={`sub-row-${r.target_id}`}>
                  <td className="p-1">
                    <div className="font-medium">{r.name}</div>
                    <div className="text-xs" style={{ color: "var(--ink-2)" }}>
                      {r.description}
                    </div>
                  </td>
                  <td className="p-1">
                    {r.target_type === "digest" ? "Weekly digest" : "Alert rule"}
                  </td>
                  <td className="p-1">{r.metric_id}</td>
                  <td className="p-1">
                    <label className="inline-flex items-center gap-1">
                      <input
                        type="checkbox"
                        checked={r.email}
                        disabled={save.isPending}
                        onChange={() => toggle(r, "email")}
                        aria-label={`Email notifications for ${r.name}`}
                        data-testid={`sub-email-${r.target_id}`}
                      />
                      <span>{r.email ? "Subscribed" : "Off"}</span>
                    </label>
                  </td>
                  <td className="p-1">
                    <label className="inline-flex items-center gap-1">
                      <input
                        type="checkbox"
                        checked={r.teams}
                        disabled={save.isPending}
                        onChange={() => toggle(r, "teams")}
                        aria-label={`Teams notifications for ${r.name}`}
                        data-testid={`sub-teams-${r.target_id}`}
                      />
                      <span>{r.teams ? "Subscribed" : "Off"}</span>
                    </label>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <FormError error={save.error} />
      </div>
    </WidgetCard>
  );
}
