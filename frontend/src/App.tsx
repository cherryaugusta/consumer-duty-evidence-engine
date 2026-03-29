import { useEffect, useState } from "react";
import { Link, Navigate, Route, Routes } from "react-router-dom";

import { CaseDetailPage } from "./features/cases/CaseDetailPage";
import { CasesPage } from "./features/cases/CasesPage";
import { NewCasePage } from "./features/cases/NewCasePage";
import { EvalDashboardPage } from "./features/evals/EvalDashboardPage";
import { MetricsPage } from "./features/metrics/MetricsPage";
import { ReviewQueuePage } from "./features/reviews/ReviewQueuePage";
import { ReviewTaskDetailPage } from "./features/reviews/ReviewTaskDetailPage";

function App() {
  const [token, setToken] = useState<string>(
    () => localStorage.getItem("access_token") ?? "",
  );

  useEffect(() => {
    if (token.trim()) {
      localStorage.setItem("access_token", token.trim());
    } else {
      localStorage.removeItem("access_token");
    }
  }, [token]);

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <h1>Consumer Duty Evidence Engine</h1>
          <p>Workflow UI bootstrap</p>
        </div>

        <nav className="nav">
          <Link to="/">Cases</Link>
          <Link to="/cases/new">New Case</Link>
          <Link to="/review-tasks">Review Queue</Link>
          <Link to="/metrics">Metrics</Link>
          <Link to="/evals">Evals</Link>
        </nav>

        <div className="token-panel">
          <label htmlFor="access-token">Access token</label>
          <textarea
            id="access-token"
            value={token}
            onChange={(e) => setToken(e.target.value)}
            placeholder="Paste JWT access token here"
            rows={8}
          />
          <button type="button" onClick={() => setToken("")}>
            Clear token
          </button>
        </div>
      </aside>

      <main className="main-content">
        <Routes>
          <Route path="/" element={<CasesPage />} />
          <Route path="/cases/new" element={<NewCasePage />} />
          <Route path="/cases/:id" element={<CaseDetailPage />} />
          <Route path="/review-tasks" element={<ReviewQueuePage />} />
          <Route path="/review-tasks/:id" element={<ReviewTaskDetailPage />} />
          <Route path="/metrics" element={<MetricsPage />} />
          <Route path="/evals" element={<EvalDashboardPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
    </div>
  );
}

export default App;