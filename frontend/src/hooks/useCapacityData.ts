/** Solutions Capacity data hooks. CAP-03 is only fetched for restricted personas. */
import { capacityApi } from "@/api/capacity";
import { useScopedQuery } from "./useScopedQuery";

export const useArchitectLoad = () =>
  useScopedQuery("capacity", "architect-load", capacityApi.architectLoad);
export const useRfpTurnaround = () =>
  useScopedQuery("capacity", "rfp-turnaround", capacityApi.rfpTurnaround);
export const useCostOfSale = (enabled: boolean) =>
  useScopedQuery("capacity", "cost-of-sale", capacityApi.costOfSale, enabled);
export const useQualityScores = () =>
  useScopedQuery("capacity", "quality-scores", capacityApi.qualityScores);
