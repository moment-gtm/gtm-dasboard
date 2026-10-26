/** Offerings data hooks — query key includes filters + role so widgets refetch on change. */
import { offeringsApi } from "@/api/offerings";
import { useScopedQuery } from "./useScopedQuery";

export const useByOffering = () =>
  useScopedQuery("offerings", "by-offering", offeringsApi.byOffering);
export const useAttachRate = () =>
  useScopedQuery("offerings", "attach-rate", offeringsApi.attachRate);
export const useAiValidation = () =>
  useScopedQuery("offerings", "ai-validation", offeringsApi.aiValidation);
export const useAssetReuse = () =>
  useScopedQuery("offerings", "asset-reuse", offeringsApi.assetReuse);
export const useAssetBuild = () =>
  useScopedQuery("offerings", "asset-build", offeringsApi.assetBuild);
