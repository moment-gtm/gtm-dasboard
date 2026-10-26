/** Executive data hooks — query key includes filters + role so widgets refetch on change. */
import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { executiveApi, fetchOpportunities, type OpportunityQuery } from "@/api/executive";
import { useFilters } from "@/state/filters";
import { useRole } from "@/state/role";

function useScopedQuery<T>(name: string, fn: (f: ReturnType<typeof useFilters>) => Promise<T>) {
  const filters = useFilters();
  const role = useRole();
  return useQuery({
    queryKey: ["executive", name, filters, role],
    queryFn: () => fn(filters),
    // Hold the previous render while refetching — no skeleton flash (dataviz anti-pattern).
    placeholderData: keepPreviousData,
  });
}

export const useRunway = () => useScopedQuery("runway", executiveApi.runway);
export const useKpis = () => useScopedQuery("kpis", executiveApi.kpis);
export const useBookingsByQuarter = () =>
  useScopedQuery("bookings-by-quarter", executiveApi.bookingsByQuarter);
export const usePipelineByVertical = () =>
  useScopedQuery("pipeline-by-vertical", executiveApi.pipelineByVertical);
export const useDealsAttention = () =>
  useScopedQuery("deals-attention", executiveApi.dealsAttention);

export function useOpportunities(q: OpportunityQuery, enabled: boolean) {
  const filters = useFilters();
  const role = useRole();
  return useQuery({
    queryKey: ["opportunities", q, filters, role],
    queryFn: () => fetchOpportunities(filters, q),
    enabled,
    placeholderData: keepPreviousData,
  });
}
