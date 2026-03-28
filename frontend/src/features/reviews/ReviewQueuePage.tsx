import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";

import { fetchReviewTasks } from "../../api/reviewTasks";

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

export function ReviewQueuePage() {
  const { data, isLoading, isError, error, refetch, isFetching } = useQuery({
    queryKey: ["review-tasks"],
    queryFn: fetchReviewTasks,
  });

  if (isLoading) {
    return (
      <section>
        <div className="page-header">
          <div>
            <h2>Review Queue</h2>
            <p>Human-review workload from the backend API.</p>
          </div>
        </div>
        <div className="panel">
          <p>Loading review tasks...</p>
        </div>
      </section>
    );
  }

  if (isError) {
    return (
      <section>
        <div className="page-header">
          <div>
            <h2>Review Queue</h2>
            <p>Human-review workload from the backend API.</p>
          </div>
        </div>
        <div className="panel error-panel">
          <p>Failed to load review tasks.</p>
          <pre>{error instanceof Error ? error.message : "Unknown error"}</pre>
          <button type="button" onClick={() => refetch()}>
            Retry
          </button>
        </div>
      </section>
    );
  }

  const reviewTasks = data?.results ?? [];

  return (
    <section>
      <div className="page-header">
        <div>
          <h2>Review Queue</h2>
          <p>Human-review workload from the backend API.</p>
        </div>

        <div className="header-actions">
          <button type="button" onClick={() => refetch()} disabled={isFetching}>
            {isFetching ? "Refreshing..." : "Refresh"}
          </button>
        </div>
      </div>

      <div className="stats-grid">
        <article className="stat-card">
          <span className="stat-label">Total review tasks</span>
          <strong className="stat-value">{data?.count ?? 0}</strong>
        </article>
        <article className="stat-card">
          <span className="stat-label">Visible on page</span>
          <strong className="stat-value">{reviewTasks.length}</strong>
        </article>
      </div>

      <div className="panel">
        <h3>Review tasks</h3>
        <p className="panel-subtitle">
          Queue, assignee, SLA, and linked case status.
        </p>

        {reviewTasks.length === 0 ? (
          <p>No review tasks found.</p>
        ) : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Case</th>
                  <th>Title</th>
                  <th>Queue</th>
                  <th>Reason</th>
                  <th>Status</th>
                  <th>Assigned To</th>
                  <th>Case Status</th>
                  <th>Priority</th>
                  <th>SLA Due</th>
                </tr>
              </thead>
              <tbody>
                {reviewTasks.map((task) => (
                  <tr key={task.id}>
                    <td>
                      <Link to={`/cases/${task.case.id}`}>
                        {task.case.reference_code}
                      </Link>
                    </td>
                    <td>{task.case.title}</td>
                    <td>{task.queue_name}</td>
                    <td>{task.reason_code}</td>
                    <td>{task.status}</td>
                    <td>{assignedLabel(task.assigned_to)}</td>
                    <td>{task.case.status}</td>
                    <td>{task.case.priority}</td>
                    <td>{formatDateTime(task.sla_due_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {data?.next || data?.previous ? (
          <p className="pagination-note">
            Backend pagination is active. This page currently renders the first
            result page only.
          </p>
        ) : null}
      </div>
    </section>
  );
}