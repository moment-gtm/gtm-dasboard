import type { Filters } from "@/state/filters";
import { api } from "./client";
import type { MetricResult } from "./types";

export const pipelineApi = {
  funnel: (f: Filters) => api.get<MetricResult>("/api/pipeline/funnel", f),
  ageing: (f: Filters) => api.get<MetricResult>("/api/pipeline/ageing", f),
  byPractice: (f: Filters) => api.get<MetricResult>("/api/pipeline/by-practice", f),
  byPlatform: (f: Filters) => api.get<MetricResult>("/api/pipeline/by-platform", f),
  sizeDistribution: (f: Filters) => api.get<MetricResult>("/api/pipeline/size-distribution", f),
  register: (f: Filters) => api.get<MetricResult>("/api/pipeline/register", f),
  stageMovement: (f: Filters) => api.get<MetricResult>("/api/pipeline/stage-movement", f),
};
