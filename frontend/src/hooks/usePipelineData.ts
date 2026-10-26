/** Pipeline data hooks — query key includes filters + role so widgets refetch on change. */
import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { pipelineApi } from "@/api/pipeline";
import { useFilters } from "@/state/filters";
import { useRole } from "@/state/role";

function useScopedQuery<T>(name: string, fn: (f: ReturnType<typeof useFilters>) => Promise<T>) {
  const filters = useFilters();
  const role = useRole();
  return useQuery({
    queryKey: ["pipeline", name, filters, role],
    queryFn: () => fn(filters),
    placeholderData: keepPreviousData,
  });
}

export const useFunnel = () => useScopedQuery("funnel", pipelineApi.funnel);
export const useAgeing = () => useScopedQuery("ageing", pipelineApi.ageing);
export const usePipelineByPractice = () => useScopedQuery("by-practice", pipelineApi.byPractice);
export const usePipelineByPlatform = () => useScopedQuery("by-platform", pipelineApi.byPlatform);
export const useSizeDistribution = () =>
  useScopedQuery("size-distribution", pipelineApi.sizeDistribution);
export const useRegisterSummary = () => useScopedQuery("register", pipelineApi.register);
export const useStageMovement = () => useScopedQuery("stage-movement", pipelineApi.stageMovement);
