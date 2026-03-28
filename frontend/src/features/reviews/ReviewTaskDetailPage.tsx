import { useState } from "react";
import {
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";
import { Link, useParams } from "react-router-dom";

import {
  approveReviewTask,
  assignReviewTask,
  escalateReviewTask,
  fetchReviewTask,
} from "../../api/reviewTasks";

function formatDateTime(value: string): string {
  return new Date(value).toLocaleString();
}

function assignedLabel(
  assignedTo: {
    first_name: string;
    last_name: string;
    username: string;
  } | null,
): string {
  if (!assignedTo) {
    return "Unassigned";
  }

  const fullName = `${assignedTo.first_name} ${assignedTo.last_name}`.trim();
  return fullName || assignedTo.username;
}

function reviewerLabel(reviewer: {
  first_name: string;
  last_name: string;
  username: string;
}): string {
  const fullName = `${reviewer.first_name} ${reviewer.last_name}`.trim();
  return fullName || reviewer.username;
}

function getErrorMessage(error: unknown): string {
  if (error instanceof Error) {
    return error.message;
  }

  return "Unknown error";
}

export function ReviewTaskDetailPage() {
  const { id } = useParams<{ id: string }>();
  const queryClient = useQueryClient();
  const [assignComment, setAssignComment] = useState("");
  const [assignFeedback, setAssignFeedback] = useState("");
  const [assignError, setAssignError] = useState("");
  const [approveComment, setApproveComment] = useState("");
  const [approveFeedback, setApproveFeedback] = useState("");
  const [approveError, setApproveError] = useState("");
  const [escalateComment, setEscalateComment] = useState("");
  const [escalateFeedback, setEscalateFeedback] = useState("");
  const [escalateError, setEscalateError] = useState("");

  const { data, isLoading, isError, error, refetch, isFetching } = useQuery({
    queryKey: ["review-task", id],
    queryFn: () => fetchReviewTask(id as string),
    enabled: Boolean(id),
  });

  const assignMutation = useMutation({
    mutationFn: async () => {
      if (!id) {
        throw new Error("Review task identifier is missing.");
      }

      return assignReviewTask(id, {
        comment: assignComment.trim(),
      });
    },
    onSuccess: async () => {
      setAssignError("");
      setAssignFeedback("Review task assigned successfully.");
      setAssignComment("");

      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["review-task", id] }),
        queryClient.invalidateQueries({ queryKey: ["review-tasks"] }),
      ]);
    },
    onError: (mutationError) => {
      setAssignFeedback("");
      setAssignError(getErrorMessage(mutationError));
    },
  });

  const approveMutation = useMutation({
    mutationFn: async () => {
      if (!id) {
        throw new Error("Review task identifier is missing.");
      }

      const trimmedComment = approveComment.trim();
      if (!trimmedComment) {
        throw new Error("Approval comment is required.");
      }

      return approveReviewTask(id, {
        comment: trimmedComment,
      });
    },
    onSuccess: async () => {
      setApproveError("");
      setApproveFeedback("Review task approved successfully.");
      setApproveComment("");

      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["review-task", id] }),
        queryClient.invalidateQueries({ queryKey: ["review-tasks"] }),
      ]);
    },
    onError: (mutationError) => {
      setApproveFeedback("");
      setApproveError(getErrorMessage(mutationError));
    },
  });

  const escalateMutation = useMutation({
    mutationFn: async () => {
      if (!id) {
        throw new Error("Review task identifier is missing.");
      }

      const trimmedComment = escalateComment.trim();
      if (!trimmedComment) {
        throw new Error("Escalation comment is required.");
      }

      return escalateReviewTask(id, {
        comment: trimmedComment,
      });
    },
    onSuccess: async () => {
      setEscalateError("");
      setEscalateFeedback("Review task escalated successfully.");
      setEscalateComment("");

      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["review-task", id] }),
        queryClient.invalidateQueries({ queryKey: ["review-tasks"] }),
      ]);
    },
    onError: (mutationError) => {
      setEscalateFeedback("");
      setEscalateError(getErrorMessage(mutationError));
    },
  });

  if (!id) {
    return (
      <section>
        <div className="page-header">
          <div>
            <h2>Review Task</h2>
            <p>Review task identifier is missing.</p>
          </div>
        </div>
      </section>
    );
  }

  if (isLoading) {
    return (
      <section>
        <div className="page-header">
          <div>
            <h2>Review Task</h2>
            <p>Loading review task detail from the backend API.</p>
          </div>
        </div>
        <div className="panel">
          <p>Loading review task detail...</p>
        </div>
      </section>
    );
  }

  if (isError) {
    return (
      <section>
        <div className="page-header">
          <div>
            <h2>Review Task</h2>
            <p>Failed to load review task detail from the backend API.</p>
          </div>
        </div>
        <div className="panel error-panel">
          <p>Failed to load review task detail.</p>
          <pre>{error instanceof Error ? error.message : "Unknown error"}</pre>
          <button type="button" onClick={() => refetch()} disabled={isFetching}>
            {isFetching ? "Retrying..." : "Retry"}
          </button>
        </div>
      </section>
    );
  }

  if (!data) {
    return (
      <section>
        <div className="page-header">
          <div>
            <h2>Review Task</h2>
            <p>No review task detail was returned.</p>
          </div>
        </div>
      </section>
    );
  }

  return (
    <section>
      <div className="page-header">
        <div>
          <h2>Review Task {data.case.reference_code}</h2>
          <p>Detail view from the backend review task endpoint.</p>
        </div>
        <div className="header-actions">
          <Link to="/review-tasks">Back to review queue</Link>
        </div>
      </div>

      <div className="stats-grid">
        <article className="stat-card">
          <span className="stat-label">Task Status</span>
          <strong className="stat-value">{data.status}</strong>
        </article>
        <article className="stat-card">
          <span className="stat-label">Reason Code</span>
          <strong className="stat-value">{data.reason_code}</strong>
        </article>
      </div>

      <div className="panel">
        <h3>Task summary</h3>
        <p className="panel-subtitle">
          Queue, assignee, SLA, and timestamps for this review task.
        </p>
        <dl className="detail-grid">
          <div>
            <dt>Task ID</dt>
            <dd>{data.id}</dd>
          </div>
          <div>
            <dt>Queue</dt>
            <dd>{data.queue_name}</dd>
          </div>
          <div>
            <dt>Assigned To</dt>
            <dd>{assignedLabel(data.assigned_to)}</dd>
          </div>
          <div>
            <dt>SLA Due</dt>
            <dd>{formatDateTime(data.sla_due_at)}</dd>
          </div>
          <div>
            <dt>Created</dt>
            <dd>{formatDateTime(data.created_at)}</dd>
          </div>
          <div>
            <dt>Updated</dt>
            <dd>{formatDateTime(data.updated_at)}</dd>
          </div>
        </dl>
      </div>

      <div className="panel">
        <h3>Linked case summary</h3>
        <p className="panel-subtitle">
          Case metadata linked to this review task.
        </p>
        <dl className="detail-grid">
          <div>
            <dt>Reference</dt>
            <dd>
              <Link to={`/cases/${data.case.id}`}>{data.case.reference_code}</Link>
            </dd>
          </div>
          <div>
            <dt>Title</dt>
            <dd>{data.case.title}</dd>
          </div>
          <div>
            <dt>Case Status</dt>
            <dd>{data.case.status}</dd>
          </div>
          <div>
            <dt>Review Status</dt>
            <dd>{data.case.review_status}</dd>
          </div>
          <div>
            <dt>Priority</dt>
            <dd>{data.case.priority}</dd>
          </div>
          <div>
            <dt>Case Type</dt>
            <dd>{data.case.case_type}</dd>
          </div>
          <div>
            <dt>Degraded Mode</dt>
            <dd>{data.case.degraded_mode_active ? "Active" : "Inactive"}</dd>
          </div>
          <div>
            <dt>Case Updated</dt>
            <dd>{formatDateTime(data.case.updated_at)}</dd>
          </div>
        </dl>
      </div>

      <div className="panel">
        <h3>Task actions</h3>
        <p className="panel-subtitle">
          Minimal frontend action surface for assigning, approving, and escalating
          this review task.
        </p>

        {assignFeedback ? <p>{assignFeedback}</p> : null}

        {assignError ? (
          <div className="error-panel">
            <p>Assign action failed.</p>
            <pre>{assignError}</pre>
          </div>
        ) : null}

        <label htmlFor="assign-comment">Assignment comment</label>
        <textarea
          id="assign-comment"
          value={assignComment}
          onChange={(event) => setAssignComment(event.target.value)}
          rows={3}
          placeholder="Optional note for the assignment action"
        />

        <div className="header-actions">
          <button
            type="button"
            onClick={() => assignMutation.mutate()}
            disabled={assignMutation.isPending}
          >
            {assignMutation.isPending ? "Assigning..." : "Assign to me"}
          </button>
        </div>

        <hr style={{ margin: "1.5rem 0" }} />

        {approveFeedback ? <p>{approveFeedback}</p> : null}

        {approveError ? (
          <div className="error-panel">
            <p>Approve action failed.</p>
            <pre>{approveError}</pre>
          </div>
        ) : null}

        <label htmlFor="approve-comment">Approval comment</label>
        <textarea
          id="approve-comment"
          value={approveComment}
          onChange={(event) => setApproveComment(event.target.value)}
          rows={3}
          placeholder="Required note for the approval action"
        />

        <div className="header-actions">
          <button
            type="button"
            onClick={() => approveMutation.mutate()}
            disabled={approveMutation.isPending}
          >
            {approveMutation.isPending ? "Approving..." : "Approve task"}
          </button>
        </div>

        <hr style={{ margin: "1.5rem 0" }} />

        {escalateFeedback ? <p>{escalateFeedback}</p> : null}

        {escalateError ? (
          <div className="error-panel">
            <p>Escalate action failed.</p>
            <pre>{escalateError}</pre>
          </div>
        ) : null}

        <label htmlFor="escalate-comment">Escalation comment</label>
        <textarea
          id="escalate-comment"
          value={escalateComment}
          onChange={(event) => setEscalateComment(event.target.value)}
          rows={3}
          placeholder="Required note for the escalation action"
        />

        <div className="header-actions">
          <button
            type="button"
            onClick={() => escalateMutation.mutate()}
            disabled={escalateMutation.isPending}
          >
            {escalateMutation.isPending ? "Escalating..." : "Escalate task"}
          </button>
        </div>
      </div>

      <div className="panel">
        <h3>Reviewer actions</h3>
        <p className="panel-subtitle">
          Recorded analyst actions for this task.
        </p>

        {data.actions.length === 0 ? (
          <p>No reviewer actions recorded yet.</p>
        ) : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Action Type</th>
                  <th>Reviewer</th>
                  <th>Comment</th>
                  <th>Override Reason</th>
                  <th>Created</th>
                </tr>
              </thead>
              <tbody>
                {data.actions.map((action) => (
                  <tr key={action.id}>
                    <td>{action.action_type}</td>
                    <td>{reviewerLabel(action.reviewer)}</td>
                    <td>{action.comment}</td>
                    <td>{action.override_reason_code ?? "\u2014"}</td>
                    <td>{formatDateTime(action.created_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </section>
  );
}