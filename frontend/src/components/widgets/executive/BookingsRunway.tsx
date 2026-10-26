/** FR-EXE-01 / EXE-07 — bookings runway with FY target + plan pace markers and narrative. */
import { RunwayChart } from "@/components/charts/RunwayChart";
import { Money } from "@/components/common/Money";
import { WidgetCard } from "@/components/common/WidgetCard";
import { useRunway } from "@/hooks/useExecutiveData";
import { useDrilldown } from "@/state/drilldown";

const LABELS: Record<string, string> = {
  booked: "Booked FY TCV",
  commit: "Weighted commit (this quarter)",
  best_case: "Weighted best case (this quarter)",
};

export function BookingsRunway() {
  const q = useRunway();
  const open = useDrilldown((s) => s.open);
  const m = q.data;
  const meta = (m?.meta ?? {}) as Record<string, number | string | undefined>;
  const segments =
    m?.breakdown.map((b) => ({
      key: String(b.component),
      label: String(b.label ?? LABELS[String(b.component)] ?? b.component),
      value: Number(b.value ?? 0),
    })) ?? [];
  const markers = [
    { key: "pace", label: "Plan pace", value: Number(meta.plan_pace ?? 0) },
    { key: "target", label: "FY target", value: Number(meta.fy_target ?? m?.target ?? 0) },
  ];
  const empty = !!m && segments.every((s) => s.value === 0) && !m.target;
  const booked = segments.find((s) => s.key === "booked")?.value ?? null;

  return (
    <WidgetCard
      testId="widget-runway"
      variant="hero"
      eyebrow="Headline · fiscal year"
      headline={
        <div className="flex flex-wrap items-end gap-x-8 gap-y-2">
          <div>
            <p className="m-0 text-xs font-medium" style={{ color: "var(--ink-2)" }}>
              Booked TCV
            </p>
            <p className="hero-number m-0" style={{ color: "var(--nav)" }}>
              <Money value={booked} />
            </p>
          </div>
          {markers.map((mk) => (
            <div key={mk.key}>
              <p className="m-0 text-xs font-medium" style={{ color: "var(--ink-2)" }}>
                {mk.label}
              </p>
              <p className="m-0 text-xl font-semibold tabular" style={{ color: "var(--ink)" }}>
                <Money value={mk.value} />
              </p>
            </div>
          ))}
        </div>
      }
      title="Bookings runway"
      description="Booked TCV this fiscal year plus weighted commit and best case for the current quarter, against plan pace and the full-year target."
      metricId="EXE-07"
      status={m?.status}
      statusBasis={m?.status_basis}
      prorated={m?.target_prorated}
      proratedBasis={m?.target_basis}
      isLoading={q.isLoading}
      isFetching={q.isFetching}
      error={q.error}
      onRetry={() => q.refetch()}
      empty={empty ? "no-match-filters" : false}
    >
      {m ? (
        <div className="flex flex-col gap-3">
          <RunwayChart
            segments={segments}
            markers={markers}
            onSelect={(key) =>
              open({ metricId: "EXE-07", segment: key, title: LABELS[key] ?? "Bookings runway" })
            }
          />
          {m.narrative ? (
            <p
              className="m-0 rounded-[14px] px-4 py-3 text-[15px] leading-relaxed"
              data-testid="runway-narrative"
              style={{ color: "var(--ink)", background: "var(--accent-wash)" }}
            >
              {m.narrative}
            </p>
          ) : null}
        </div>
      ) : null}
    </WidgetCard>
  );
}
