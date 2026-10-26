import { useQuery } from "@tanstack/react-query";
import { referenceApi } from "@/api/reference";
import { useRole } from "@/state/role";

export function useRoles() {
  return useQuery({ queryKey: ["roles"], queryFn: referenceApi.roles, staleTime: Infinity });
}

export function useMe() {
  const role = useRole();
  return useQuery({ queryKey: ["me", role], queryFn: referenceApi.me });
}

export function useFilterOptions() {
  const role = useRole();
  return useQuery({ queryKey: ["filter-options", role], queryFn: referenceApi.filters });
}

export function useMetricMeta(metricId?: string) {
  const role = useRole();
  const q = useQuery({
    queryKey: ["metric-meta", role],
    queryFn: referenceApi.metrics,
    staleTime: 5 * 60_000,
  });
  return { ...q, meta: metricId ? q.data?.find((m) => m.metric_id === metricId) : undefined };
}

export function useHealth() {
  return useQuery({
    queryKey: ["health"],
    queryFn: referenceApi.health,
    refetchInterval: 60_000,
  });
}
