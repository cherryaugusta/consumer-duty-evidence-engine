import { useQuery } from "@tanstack/react-query";

import { fetchLatestEvalReport } from "../../api/evals";

function formatNumber(value: number): string {
  return value.toLocaleString();
}

function formatPercent(value: number): string {
  return `${(value * 100).toFixed(1)}%`;
}

export function EvalDashboardPage() {
  const { data, isLoading, isError, error, refetch, isFetching } = useQuery({
    queryKey: ["eval-latest-report"],
    queryFn: fetchLatestEvalReport,
  });

  if (isLoading) {
    return (
      <section>
        <div className="page-header">
          <div>
            <h2>Evals</h2>
            <p>Latest evaluation report from the backend eval report endpoint.</p>
          </div>
        </div>
        <div className="panel">
          <p>Loading latest eval report...</p>
        </div>
      </section>
    );
  }

  if (isError) {
    return (
      <section>
        <div className="page-header">
          <div>
            <h2>Evals</h2>
            <p>Latest evaluation report from the backend eval report endpoint.</p>
          </div>
        </div>
        <div className="panel error-panel">
          <p>Failed to load latest eval report.</p>
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
            <h2>Evals</h2>
            <p>No eval report was returned.</p>
          </div>
        </div>
      </section>
    );
  }

  const scenarioRows = Object.entries(data.scenario_breakdown).sort((a, b) =>
    a[0].localeCompare(b[0]),
  );

  return (
    <section>
      <div className="page-header">
        <div>
          <h2>Evals</h2>
          <p>Latest evaluation report from the backend eval report endpoint.</p>
        </div>
        <div className="header-actions">
          <button type="button" onClick={() => refetch()} disabled={isFetching}>
            {isFetching ? "Refreshing..." : "Refresh"}
          </button>
        </div>
      </div>

      <div className="panel">
        <h3>Latest eval run</h3>
        <p className="panel-subtitle">
          Current report label and total evaluated cases.
        </p>
        <dl className="detail-grid">
          <div>
            <dt>Run label</dt>
            <dd>{data.run_label}</dd>
          </div>
          <div>
            <dt>Total cases</dt>
            <dd>{formatNumber(data.total_cases)}</dd>
          </div>
        </dl>
      </div>

      <div className="stats-grid">
        <article className="stat-card">
          <span className="stat-label">Pass Rate</span>
          <strong className="stat-value">
            {formatPercent(data.summary_metrics.pass_rate)}
          </strong>
        </article>
        <article className="stat-card">
          <span className="stat-label">Mapping Accuracy</span>
          <strong className="stat-value">
            {formatPercent(data.summary_metrics.mapping_accuracy)}
          </strong>
        </article>
        <article className="stat-card">
          <span className="stat-label">Routing Accuracy</span>
          <strong className="stat-value">
            {formatPercent(data.summary_metrics.routing_accuracy)}
          </strong>
        </article>
        <article className="stat-card">
          <span className="stat-label">Citation Validity</span>
          <strong className="stat-value">
            {formatPercent(data.summary_metrics.citation_validity_rate)}
          </strong>
        </article>
      </div>

      <div className="panel-grid">
        <div className="panel">
          <h3>Summary metrics</h3>
          <p className="panel-subtitle">
            Core evaluation metrics from the latest run.
          </p>
          <div className="metrics-list">
            <div className="metric-row">
              <span>Claim precision</span>
              <strong>{formatPercent(data.summary_metrics.claim_precision)}</strong>
            </div>
            <div className="metric-row">
              <span>Claim recall</span>
              <strong>{formatPercent(data.summary_metrics.claim_recall)}</strong>
            </div>
            <div className="metric-row">
              <span>Mapping accuracy</span>
              <strong>{formatPercent(data.summary_metrics.mapping_accuracy)}</strong>
            </div>
            <div className="metric-row">
              <span>Citation validity rate</span>
              <strong>
                {formatPercent(data.summary_metrics.citation_validity_rate)}
              </strong>
            </div>
            <div className="metric-row">
              <span>Routing accuracy</span>
              <strong>{formatPercent(data.summary_metrics.routing_accuracy)}</strong>
            </div>
            <div className="metric-row">
              <span>Support status accuracy</span>
              <strong>
                {formatPercent(data.summary_metrics.support_status_accuracy)}
              </strong>
            </div>
            <div className="metric-row">
              <span>Degraded mode success rate</span>
              <strong>
                {formatPercent(data.summary_metrics.degraded_mode_success_rate)}
              </strong>
            </div>
            <div className="metric-row">
              <span>Pass rate</span>
              <strong>{formatPercent(data.summary_metrics.pass_rate)}</strong>
            </div>
          </div>
        </div>

        <div className="panel">
          <h3>Thresholds</h3>
          <p className="panel-subtitle">
            Current benchmark thresholds for the eval report.
          </p>
          <div className="metrics-list">
            <div className="metric-row">
              <span>Mapping accuracy minimum</span>
              <strong>{formatPercent(data.thresholds.mapping_accuracy_min)}</strong>
            </div>
            <div className="metric-row">
              <span>False negative rate maximum</span>
              <strong>
                {formatPercent(data.thresholds.false_negative_rate_max)}
              </strong>
            </div>
            <div className="metric-row">
              <span>Citation validity minimum</span>
              <strong>{formatPercent(data.thresholds.citation_validity_min)}</strong>
            </div>
            <div className="metric-row">
              <span>Support status accuracy minimum</span>
              <strong>
                {formatPercent(data.thresholds.support_status_accuracy_min)}
              </strong>
            </div>
            <div className="metric-row">
              <span>Degraded mode success minimum</span>
              <strong>
                {formatPercent(data.thresholds.degraded_mode_success_min)}
              </strong>
            </div>
          </div>
        </div>
      </div>

      <div className="panel-grid">
        <div className="panel">
          <h3>Failure breakdown</h3>
          <p className="panel-subtitle">
            Failed check counts across the latest eval run.
          </p>
          <div className="metrics-list">
            <div className="metric-row">
              <span>Claims</span>
              <strong>{formatNumber(data.failure_breakdown.claims)}</strong>
            </div>
            <div className="metric-row">
              <span>Mapping</span>
              <strong>{formatNumber(data.failure_breakdown.mapping)}</strong>
            </div>
            <div className="metric-row">
              <span>Support</span>
              <strong>{formatNumber(data.failure_breakdown.support)}</strong>
            </div>
            <div className="metric-row">
              <span>Routing</span>
              <strong>{formatNumber(data.failure_breakdown.routing)}</strong>
            </div>
            <div className="metric-row">
              <span>Citation</span>
              <strong>{formatNumber(data.failure_breakdown.citation)}</strong>
            </div>
          </div>
        </div>

        <div className="panel">
          <h3>Scenario breakdown</h3>
          <p className="panel-subtitle">
            Coverage and average score by scenario type.
          </p>
          {scenarioRows.length === 0 ? (
            <p>No scenario breakdown data found.</p>
          ) : (
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Scenario</th>
                    <th>Total Cases</th>
                    <th>Fully Passed</th>
                    <th>Average Score</th>
                  </tr>
                </thead>
                <tbody>
                  {scenarioRows.map(([scenarioName, scenarioData]) => (
                    <tr key={scenarioName}>
                      <td>{scenarioName}</td>
                      <td>{formatNumber(scenarioData.total_cases)}</td>
                      <td>{formatNumber(scenarioData.fully_passed_cases)}</td>
                      <td>{formatPercent(scenarioData.average_score)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

      <div className="panel-grid">
        <div className="panel">
          <h3>Top failures</h3>
          <p className="panel-subtitle">
            Lowest-scoring or failed cases from the latest report.
          </p>
          {data.top_failures.length === 0 ? (
            <p>No failed cases recorded.</p>
          ) : (
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Case ID</th>
                    <th>Scenario</th>
                    <th>Score</th>
                    <th>Failed Checks</th>
                  </tr>
                </thead>
                <tbody>
                  {data.top_failures.map((item) => (
                    <tr key={item.case_id}>
                      <td>{item.case_id}</td>
                      <td>{item.scenario_type}</td>
                      <td>{formatPercent(item.score)}</td>
                      <td>
                        {item.failed_checks.length > 0
                          ? item.failed_checks.join(", ")
                          : "None"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        <div className="panel">
          <h3>Top successes</h3>
          <p className="panel-subtitle">
            Strongest passing cases from the latest report.
          </p>
          {data.top_successes.length === 0 ? (
            <p>No successful cases recorded.</p>
          ) : (
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Case ID</th>
                    <th>Scenario</th>
                    <th>Score</th>
                    <th>Failed Checks</th>
                  </tr>
                </thead>
                <tbody>
                  {data.top_successes.map((item) => (
                    <tr key={item.case_id}>
                      <td>{item.case_id}</td>
                      <td>{item.scenario_type}</td>
                      <td>{formatPercent(item.score)}</td>
                      <td>
                        {item.failed_checks.length > 0
                          ? item.failed_checks.join(", ")
                          : "None"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

      <div className="panel">
        <h3>Latest eval results</h3>
        <p className="panel-subtitle">
          Per-case summary for the latest eval report.
        </p>
        {data.results.length === 0 ? (
          <p>No eval results found.</p>
        ) : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Case ID</th>
                  <th>Scenario</th>
                  <th>Score</th>
                  <th>Passed Checks</th>
                  <th>Total Checks</th>
                  <th>All Passed</th>
                  <th>Failed Checks</th>
                </tr>
              </thead>
              <tbody>
                {data.results.map((result) => (
                  <tr key={result.case_id}>
                    <td>{result.case_id}</td>
                    <td>{result.scenario_type}</td>
                    <td>{formatPercent(result.summary.score)}</td>
                    <td>{formatNumber(result.summary.passed_checks)}</td>
                    <td>{formatNumber(result.summary.total_checks)}</td>
                    <td>{result.summary.all_passed ? "Yes" : "No"}</td>
                    <td>
                      {result.summary.failed_checks.length > 0
                        ? result.summary.failed_checks.join(", ")
                        : "None"}
                    </td>
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