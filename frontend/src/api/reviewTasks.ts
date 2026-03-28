import { api } from "./client";

export type ReviewTaskUser = {
  id: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
};

export type ReviewTaskCase = {
  id: string;
  reference_code: string;
  title: string;
  status: string;
  review_status: string;
  priority: string;
  case_type: string;
  degraded_mode_active: boolean;
  created_at: string;
  updated_at: string;
};

export type ReviewerAction = {
  id: string;
  review_task: string;
  reviewer: ReviewTaskUser;
  action_type: string;
  old_value: Record<string, unknown> | null;
  new_value: Record<string, unknown> | null;
  comment: string;
  override_reason_code: string | null;
  created_at: string;
};

export type ReviewTask = {
  id: string;
  case: ReviewTaskCase;
  queue_name: string;
  assigned_to: ReviewTaskUser | null;
  status: string;
  reason_code: string;
  sla_due_at: string;
  created_at: string;
  updated_at: string;
  actions: ReviewerAction[];
};

export type PaginatedReviewTasks = {
  count: number;
  next: string | null;
  previous: string | null;
  results: ReviewTask[];
};

export type AssignReviewTaskInput = {
  assignee_id?: number;
  comment?: string;
};

export type ApproveReviewTaskInput = {
  comment: string;
};

export type EscalateReviewTaskInput = {
  comment: string;
};

export type OverrideReviewTaskInput = {
  recommended_action:
    | "approve"
    | "review"
    | "escalate"
    | "request_more_evidence";
  override_reason_code: string;
  comment: string;
  recommended_priority?: string;
  executive_summary?: string;
  structured_rationale?: Record<string, unknown>;
};

export async function fetchReviewTasks(): Promise<PaginatedReviewTasks> {
  const response = await api.get<PaginatedReviewTasks>("/review-tasks/");
  return response.data;
}

export async function fetchReviewTask(id: string): Promise<ReviewTask> {
  const response = await api.get<ReviewTask>(`/review-tasks/${id}/`);
  return response.data;
}

export async function assignReviewTask(
  id: string,
  payload: AssignReviewTaskInput,
): Promise<ReviewTask> {
  const response = await api.post<ReviewTask>(
    `/review-tasks/${id}/assign/`,
    payload,
  );
  return response.data;
}

export async function approveReviewTask(
  id: string,
  payload: ApproveReviewTaskInput,
): Promise<ReviewTask> {
  const response = await api.post<ReviewTask>(
    `/review-tasks/${id}/approve/`,
    payload,
  );
  return response.data;
}

export async function escalateReviewTask(
  id: string,
  payload: EscalateReviewTaskInput,
): Promise<ReviewTask> {
  const response = await api.post<ReviewTask>(
    `/review-tasks/${id}/escalate/`,
    payload,
  );
  return response.data;
}

export async function overrideReviewTask(
  id: string,
  payload: OverrideReviewTaskInput,
): Promise<ReviewTask> {
  const response = await api.post<ReviewTask>(
    `/review-tasks/${id}/override/`,
    payload,
  );
  return response.data;
}