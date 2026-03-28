import { api } from "./client";

export type EvalSummaryMetrics = {
  claim_precision: number;
  claim_recall: number;
  mapping_accuracy: number;
  citation_validity_rate: number;
  routing_accuracy: number;
  support_status_accuracy: number;
  degraded_mode_success_rate: number;
  pass_rate: number;
};

export type EvalThresholds = {
  mapping_accuracy_min: number;
  false_negative_rate_max: number;
  citation_validity_min: number;
  support_status_accuracy_min: number;
  degraded_mode_success_min: number;
};

export type EvalFailureBreakdown = {
  claims: number;
  mapping: number;
  support: number;
  routing: number;
  citation: number;
};

export type EvalScenarioBreakdownItem = {
  total_cases: number;
  fully_passed_cases: number;
  average_score: number;
};

export type EvalTopCase = {
  case_id: string;
  scenario_type: string;
  score: number;
  failed_checks: string[];
};

export type EvalResultItem = {
  case_id: string;
  scenario_type: string;
  summary: {
    case_id: string;
    score: number;
    passed_checks: number;
    total_checks: number;
    all_passed: boolean;
    failed_checks: string[];
  };
};

export type EvalLatestReport = {
  run_label: string;
  summary_metrics: EvalSummaryMetrics;
  thresholds: EvalThresholds;
  total_cases: number;
  failure_breakdown: EvalFailureBreakdown;
  scenario_breakdown: Record<string, EvalScenarioBreakdownItem>;
  top_failures: EvalTopCase[];
  top_successes: EvalTopCase[];
  results: EvalResultItem[];
};

export async function fetchLatestEvalReport(): Promise<EvalLatestReport> {
  const response = await api.get<EvalLatestReport>("/evals/reports/latest/");
  return response.data;
}