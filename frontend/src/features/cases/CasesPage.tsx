import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { getCases } from "../../api/cases";

export function CasesPage() {
  const { data, isLoading, isError, error } = useQuery({
    queryKey: ["cases"],
    queryFn: getCases,
  });

  if (isLoading) {
    return <div className="panel">Loading cases…</div>;
  }

  if (isError) {
    return (
      <div className="panel error-panel">
        Failed to load cases.
        <pre>{String(error)}</pre>
      </div>
    );
  }

  const cases = data ?? [];

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <h2>Cases</h2>
          <p>Current review cases from the backend API.</p>
        </div>
        <div className="stat-chip">{cases.length} total</div>
      </div>

      <div className="panel">
        {cases.length === 0 ? (
          <p>No cases returned.</p>
        ) : (
          <table className="data-table">
            <thead>
              <tr>
                <th>Reference</th>
                <th>Title</th>
                <th>Status</th>
                <th>Review</th>
                <th>Priority</th>
                <th>Case Type</th>
                <th>Updated</th>
              </tr>
            </thead>
            <tbody>
              {cases.map((item) => (
                <tr key={item.id}>
                  <td>
                    <Link to={`/cases/${item.id}`}>{item.reference_code}</Link>
                  </td>
                  <td>{item.title}</td>
                  <td>{item.status}</td>
                  <td>{item.review_status}</td>
                  <td>{item.priority}</td>
                  <td>{item.case_type}</td>
                  <td>{new Date(item.updated_at).toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}