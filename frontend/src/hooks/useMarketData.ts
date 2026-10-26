/** Market Signals data hooks — query key includes filters + role so widgets refetch on change. */
import { marketApi } from "@/api/market";
import { useScopedQuery } from "./useScopedQuery";

export const useThoughtLeadership = () =>
  useScopedQuery("market", "thought-leadership", marketApi.thoughtLeadership);
export const useWorkshopFunnel = () =>
  useScopedQuery("market", "workshop-funnel", marketApi.workshopFunnel);
export const useCampaignSourced = () =>
  useScopedQuery("market", "campaign-sourced", marketApi.campaignSourced);
export const useAnalystPositioning = () =>
  useScopedQuery("market", "analyst-positioning", marketApi.analystPositioning);
