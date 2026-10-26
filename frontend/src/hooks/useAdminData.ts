/** Administration data hooks. Admin data is not filter-scoped; writes invalidate every query so
 *  statuses, targets and filter options recompute everywhere. */
import { keepPreviousData, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { adminApi } from "@/api/admin";
import { useRole } from "@/state/role";

function useAdminQuery<T>(key: unknown[], fn: () => Promise<T>) {
  const role = useRole();
  return useQuery({ queryKey: ["admin", ...key, role], queryFn: fn });
}

export const useTargets = () => useAdminQuery(["targets"], adminApi.targets);
export const useThresholds = () => useAdminQuery(["thresholds"], adminApi.thresholds);
export const useThresholdHistory = (id: string | null) => {
  const role = useRole();
  return useQuery({
    queryKey: ["admin", "threshold-history", id, role],
    queryFn: () => adminApi.thresholdHistory(id as string),
    enabled: !!id,
  });
};
export const useReferences = () => useAdminQuery(["references"], adminApi.references);
export const useReferenceSet = (key: string) => {
  const role = useRole();
  return useQuery({
    queryKey: ["admin", "reference", key, role],
    queryFn: () => adminApi.referenceSet(key),
  });
};
export const useDq = () => useAdminQuery(["dq"], adminApi.dq);
export const useCompleteness = () => useAdminQuery(["completeness"], adminApi.completeness);
export const useDqFindings = (q: {
  rule_id?: string;
  owner?: string;
  q?: string;
  page: number;
}) => {
  const role = useRole();
  return useQuery({
    queryKey: ["admin", "findings", q, role],
    queryFn: () => adminApi.findings(q),
    placeholderData: keepPreviousData,
  });
};
export const useChangeRequests = () => useAdminQuery(["changes"], adminApi.changeRequests);
export const useAudit = () => useAdminQuery(["audit"], adminApi.audit);
export const useAlertRules = () => useAdminQuery(["alert-rules"], adminApi.alertRules);
export const useAlertSubscriptions = () =>
  useAdminQuery(["alert-subscriptions"], adminApi.subscriptions);
export const useDigest = (previewRole?: string) => {
  const role = useRole();
  return useQuery({
    queryKey: ["admin", "digest", previewRole ?? "self", role],
    queryFn: () => adminApi.digest(previewRole),
  });
};

export function useAdminMutation<A, R>(fn: (arg: A) => Promise<R>) {
  const qc = useQueryClient();
  return useMutation({ mutationFn: fn, onSuccess: () => qc.invalidateQueries() });
}
