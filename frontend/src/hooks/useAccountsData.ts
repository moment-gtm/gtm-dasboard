/** Accounts data hooks — query key includes filters + role so widgets refetch on change. */
import { accountsApi } from "@/api/accounts";
import { useScopedQuery } from "./useScopedQuery";

export const usePenetration = () =>
  useScopedQuery("accounts", "penetration", accountsApi.penetration);
export const useWhitespace = () => useScopedQuery("accounts", "whitespace", accountsApi.whitespace);
export const useExpansion = () => useScopedQuery("accounts", "expansion", accountsApi.expansion);
export const usePlanHealth = () =>
  useScopedQuery("accounts", "plan-health", accountsApi.planHealth);
export const useAccountOpportunities = (accountId: string | null) =>
  useScopedQuery(
    "accounts",
    `opps-${accountId}`,
    (f) => accountsApi.opportunities(accountId ?? "", f),
    !!accountId,
  );
