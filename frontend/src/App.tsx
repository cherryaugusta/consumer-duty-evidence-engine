import { Link, Navigate, Route, Routes } from "react-router-dom";
import { useEffect, useState } from "react";
import { CasesPage } from "./features/cases/CasesPage";
import { CaseDetailPage } from "./features/cases/CaseDetailPage";

function App() {
  const [token, setToken] = useState<string>(() => localStorage.getItem("access_token") ?? "");

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
          <Route path="/cases/:id" element={<CaseDetailPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
    </div>
  );
}

export default App;