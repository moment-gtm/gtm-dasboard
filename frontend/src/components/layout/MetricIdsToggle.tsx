/** Global header toggle to show/hide metric ID chips and inline source badges across all widgets (FR-GEN-07). */
import { useMetricIdsStore } from "@/state/metricIds";

export function MetricIdsToggle() {
  const show = useMetricIdsStore((s) => s.showMetricIds);
  const setShow = useMetricIdsStore((s) => s.setShowMetricIds);
  return (
    <label
      className="btn flex cursor-pointer items-center gap-1.5 text-sm select-none"
      data-testid="toggle-metric-ids-label"
    >
      <input
        type="checkbox"
        checked={show}
        onChange={(e) => setShow(e.target.checked)}
        data-testid="toggle-metric-ids"
        className="m-0 cursor-pointer"
      />
      <span>Show metric IDs and sources</span>
    </label>
  );
}
