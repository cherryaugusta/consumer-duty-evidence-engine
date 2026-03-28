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

export async function fetchReviewTasks(): Promise<PaginatedReviewTasks> {
  const response = await api.get<PaginatedReviewTasks>("/review-tasks/");
  return response.data;
}

export async function fetchReviewTask(id: string): Promise<ReviewTask> {
  const response = await api.get<ReviewTask>(`/review-tasks/${id}/`);
  return response.data;
}