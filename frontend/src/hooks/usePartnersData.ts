/** Partners data hooks — query key includes filters + role so widgets refetch on change. */
import { partnersApi } from "@/api/partners";
import { useScopedQuery } from "./useScopedQuery";

export const usePartnerPipeline = () =>
  useScopedQuery("partners", "pipeline", partnersApi.pipeline);
export const useCoSell = () => useScopedQuery("partners", "co-sell", partnersApi.coSell);
export const useCertifications = () =>
  useScopedQuery("partners", "certifications", partnersApi.certifications);
