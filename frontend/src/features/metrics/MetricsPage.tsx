import { useQuery } from "@tanstack/react-query";

import { fetchMetricsOverview } from "../../api/metrics";

function metricValue(value: number): string {
  return value.toLocaleString();
}

export function MetricsPage() {
  const { data, isLoading, isError, error, refetch, isFetching } = useQuery({
    queryKey: ["metrics-overview"],
    queryFn: fetchMetricsOverview,
  });

  if (isLoading) {
    return (
      <section>
        <div className="page-header">
          <div>
            <h2>Metrics</h2>
            <p>Operational overview from the backend metrics endpoint.</p>
          </div>
        </div>
        <div className="panel">
          <p>Loading metrics overview...</p>
        </div>
      </section>
    );
  }

  if (isError) {
    return (
      <section>
        <div className="page-header">
          <div>
            <h2>Metrics</h2>
            <p>Operational overview from the backend metrics endpoint.</p>
          </div>
        </div>
        <div className="panel error-panel">
          <p>Failed to load metrics overview.</p>
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
            <h2>Metrics</h2>
            <p>No metrics overview was returned.</p>
          </div>
        </div>
      </section>
    );
  }

  return (
    <section>
      <div className="page-header">
        <div>
          <h2>Metrics</h2>
          <p>Operational overview from the backend metrics endpoint.</p>
        </div>
        <div className="header-actions">
          <button type="button" onClick={() => refetch()} disabled={isFetching}>
            {isFetching ? "Refreshing..." : "Refresh"}
          </button>
        </div>
      </div>

      <div className="stats-grid">
        <article className="stat-card">
          <span className="stat-label">Total Cases</span>
          <strong className="stat-value">{metricValue(data.total_cases)}</strong>
        </article>
        <article className="stat-card">
          <span className="stat-label">Needs Review</span>
          <strong className="stat-value">
            {metricValue(data.needs_review_cases)}
          </strong>
        </article>
        <article className="stat-card">
          <span className="stat-label">Approved Cases</span>
          <strong className="stat-value">
            {metricValue(data.approved_cases)}
          </strong>
        </article>
        <article className="stat-card">
          <span className="stat-label">Escalated Cases</span>
          <strong className="stat-value">
            {metricValue(data.escalated_cases)}
          </strong>
        </article>
      </div>

      <div className="panel-grid">
        <div className="panel">
          <h3>Case overview</h3>
          <p className="panel-subtitle">
            High-level case routing and degraded mode counts.
          </p>
          <div className="metrics-list">
            <div className="metric-row">
              <span>Total cases</span>
              <strong>{metricValue(data.total_cases)}</strong>
            </div>
            <div className="metric-row">
              <span>Needs review cases</span>
              <strong>{metricValue(data.needs_review_cases)}</strong>
            </div>
            <div className="metric-row">
              <span>Approved cases</span>
              <strong>{metricValue(data.approved_cases)}</strong>
            </div>
            <div className="metric-row">
              <span>Escalated cases</span>
              <strong>{metricValue(data.escalated_cases)}</strong>
            </div>
            <div className="metric-row">
              <span>Degraded mode cases</span>
              <strong>{metricValue(data.degraded_mode_cases)}</strong>
            </div>
          </div>
        </div>

        <div className="panel">
          <h3>Review operations</h3>
          <p className="panel-subtitle">
            Review task state distribution from the human-review queue.
          </p>
          <div className="metrics-list">
            <div className="metric-row">
              <span>Total review tasks</span>
              <strong>{metricValue(data.total_review_tasks)}</strong>
            </div>
            <div className="metric-row">
              <span>Unassigned review tasks</span>
              <strong>{metricValue(data.unassigned_review_tasks)}</strong>
            </div>
            <div className="metric-row">
              <span>Assigned review tasks</span>
              <strong>{metricValue(data.assigned_review_tasks)}</strong>
            </div>
            <div className="metric-row">
              <span>Approved review tasks</span>
              <strong>{metricValue(data.approved_review_tasks)}</strong>
            </div>
            <div className="metric-row">
              <span>Escalated review tasks</span>
              <strong>{metricValue(data.escalated_review_tasks)}</strong>
            </div>
            <div className="metric-row">
              <span>Overridden review tasks</span>
              <strong>{metricValue(data.overridden_review_tasks)}</strong>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}