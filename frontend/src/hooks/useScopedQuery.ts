/** Shared module query hook — query key is [module, name, filters, role] so widgets refetch on change. */
import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { useFilters } from "@/state/filters";
import { useRole } from "@/state/role";

export function useScopedQuery<T>(
  module: string,
  name: string,
  fn: (f: ReturnType<typeof useFilters>) => Promise<T>,
  enabled = true,
) {
  const filters = useFilters();
  const role = useRole();
  return useQuery({
    queryKey: [module, name, filters, role],
    queryFn: () => fn(filters),
    placeholderData: keepPreviousData,
    enabled,
  });
}
