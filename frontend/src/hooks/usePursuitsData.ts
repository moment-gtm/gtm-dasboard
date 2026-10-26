/** Pursuits data hooks — query key includes filters + role so widgets refetch on change. */
import { pursuitsApi } from "@/api/pursuits";
import { useScopedQuery } from "./useScopedQuery";

export const useWinRate = () => useScopedQuery("pursuits", "win-rate", pursuitsApi.winRate);
export const useLossReasons = () =>
  useScopedQuery("pursuits", "loss-reasons", pursuitsApi.lossReasons);
export const useSourceMix = () => useScopedQuery("pursuits", "source-mix", pursuitsApi.sourceMix);
export const useBidDiscipline = () =>
  useScopedQuery("pursuits", "bid-discipline", pursuitsApi.bidDiscipline);
export const useOralsConversion = () =>
  useScopedQuery("pursuits", "orals-conversion", pursuitsApi.oralsConversion);
export const useMargin = (enabled: boolean) =>
  useScopedQuery("pursuits", "margin", pursuitsApi.margin, enabled);
