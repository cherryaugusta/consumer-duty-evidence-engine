import { api } from "./client";

export type MetricsOverview = {
  total_cases: number;
  needs_review_cases: number;
  approved_cases: number;
  escalated_cases: number;
  degraded_mode_cases: number;
  total_review_tasks: number;
  unassigned_review_tasks: number;
  assigned_review_tasks: number;
  approved_review_tasks: number;
  escalated_review_tasks: number;
  overridden_review_tasks: number;
};

export async function fetchMetricsOverview(): Promise<MetricsOverview> {
  const response = await api.get<MetricsOverview>("/metrics/overview/");
  return response.data;
}