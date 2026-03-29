import { useMemo, useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";

import { fetchEvalCaseLookup, fetchLatestEvalReport } from "../../api/evals";

function formatNumber(value: number): string {
  return value.toLocaleString();
}

function formatPercent(value: number): string {
  return `${(value * 100).toFixed(1)}%`;
}

function getErrorMessage(error: unknown): string {
  if (error instanceof Error) {
    return error.message;
  }

  return "Unknown error";
}

export function EvalDashboardPage() {
  const navigate = useNavigate();
  const [selectedScenario, setSelectedScenario] = useState<string>("all");
  const [selectedFailedCheck, setSelectedFailedCheck] = useState<string>("all");
  const [minimumScore, setMinimumScore] = useState<string>("0");

  const { data, isLoading, isError, error, refetch, isFetching } = useQuery({
    queryKey: ["eval-latest-report"],
    queryFn: fetchLatestEvalReport,
  });

  const openCaseMutation = useMutation({
    mutationFn: async (evalCaseId: string) => fetchEvalCaseLookup(evalCaseId),
    onSuccess: (payload) => {
      navigate(`/cases/${payload.case_id}`);
    },
  });

  const minimumScoreNumber = Number(minimumScore);
  const normalizedMinimumScore = Number.isNaN(minimumScoreNumber)
    ? 0
    : minimumScoreNumber;

  const scenarioRows = useMemo(() => {
    if (!data) {
      return [];
    }

    return Object.entries(data.scenario_breakdown).sort((a, b) =>
      a[0].localeCompare(b[0]),
    );
  }, [data]);

  const scenarioOptions = useMemo(() => {
    if (!data) {
      return [];
    }

    return Array.from(
      new Set(data.results.map((result) => result.scenario_type)),
    ).sort((a, b) => a.localeCompare(b));
  }, [data]);

  const failedCheckOptions = useMemo(() => {
    if (!data) {
      return [];
    }

    return Array.from(
      new Set(
        data.results.flatMap((result) => result.summary.failed_checks ?? []),
      ),
    ).sort((a, b) => a.localeCompare(b));
  }, [data]);

  const filteredResults = useMemo(() => {
    if (!data) {
      return [];
    }

    return data.results.filter((result) => {
      const matchesScenario =
        selectedScenario === "all" || result.scenario_type === selectedScenario;

      const matchesFailedCheck =
        selectedFailedCheck === "all" ||
        result.summary.failed_checks.includes(selectedFailedCheck);

      const scoreAsPercent = result.summary.score * 100;
      const matchesMinimumScore = scoreAsPercent >= normalizedMinimumScore;

      return matchesScenario && matchesFailedCheck && matchesMinimumScore;
    });
  }, [data, normalizedMinimumScore, selectedFailedCheck, selectedScenario]);

  const filteredAverageScore = useMemo(() => {
    if (filteredResults.length === 0) {
      return 0;
    }

    const total = filteredResults.reduce(
      (sum, result) => sum + result.summary.score,
      0,
    );

    return total / filteredResults.length;
  }, [filteredResults]);

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

      {openCaseMutation.isError ? (
        <div className="panel error-panel">
          <p>Failed to open the linked case.</p>
          <pre>{getErrorMessage(openCaseMutation.error)}</pre>
        </div>
      ) : null}

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

        <div className="panel" style={{ marginBottom: 16 }}>
          <h4>Filters</h4>
          <p className="panel-subtitle">
            Narrow the latest eval results by scenario, failed check, and score.
          </p>

          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
              gap: 12,
              alignItems: "end",
            }}
          >
            <label style={{ display: "grid", gap: 6 }}>
              <span>Scenario</span>
              <select
                value={selectedScenario}
                onChange={(event) => setSelectedScenario(event.target.value)}
                className="select-input"
              >
                <option value="all">All scenarios</option>
                {scenarioOptions.map((scenario) => (
                  <option key={scenario} value={scenario}>
                    {scenario}
                  </option>
                ))}
              </select>
            </label>

            <label style={{ display: "grid", gap: 6 }}>
              <span>Failed check</span>
              <select
                value={selectedFailedCheck}
                onChange={(event) => setSelectedFailedCheck(event.target.value)}
                className="select-input"
              >
                <option value="all">All failed checks</option>
                {failedCheckOptions.map((failedCheck) => (
                  <option key={failedCheck} value={failedCheck}>
                    {failedCheck}
                  </option>
                ))}
              </select>
            </label>

            <label style={{ display: "grid", gap: 6 }}>
              <span>Minimum score (%)</span>
              <input
                type="number"
                min="0"
                max="100"
                step="1"
                value={minimumScore}
                onChange={(event) => setMinimumScore(event.target.value)}
                className="text-input"
              />
            </label>

            <button
              type="button"
              onClick={() => {
                setSelectedScenario("all");
                setSelectedFailedCheck("all");
                setMinimumScore("0");
              }}
            >
              Clear filters
            </button>
          </div>

          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
              gap: 12,
              marginTop: 16,
            }}
          >
            <div className="stat-chip">
              Filtered results: {formatNumber(filteredResults.length)}
            </div>
            <div className="stat-chip">
              Filtered average score: {formatPercent(filteredAverageScore)}
            </div>
          </div>
        </div>

        {filteredResults.length === 0 ? (
          <p>No eval results match the selected filters.</p>
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
                {filteredResults.map((result) => (
                  <tr key={result.case_id}>
                    <td>
                      <button
                        type="button"
                        onClick={() => openCaseMutation.mutate(result.case_id)}
                        disabled={openCaseMutation.isPending}
                      >
                        {result.case_id}
                      </button>
                    </td>
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